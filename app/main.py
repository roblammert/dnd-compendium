from pathlib import Path
from urllib.parse import urlencode
import json
import os
import signal
import threading
import time
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt
from markupsafe import Markup
from sqlalchemy import func, select, text, tuple_
from sqlalchemy.orm import Session, selectinload
from app.config import get_settings
from app.db import Base, engine, ensure_schema_columns, get_db
from app.models import Entity, EntityTypeVisibility, LexiconTerm, SyncEndpoint, SyncRun, UserEntityList
from app.schemas import EntityCreate, EntityOut, EntityUpdate
from app.services import backfill_canonical_keys, build_item_card, build_magic_item_card, build_monster_card, build_species_card, build_weapon_card, build_spell_card, build_spell_school_card, build_weapon_property_card, build_skill_card, build_service_card, build_language_card, build_size_card, canonical_entity_key, create_homebrew, descriptor_badge, ensure_unique_slug, init_search, rebuild_search_row
from app.sync import ACTIVE_SYNC_STATUSES, create_sync_run, recover_interrupted_syncs, run_open5e_sync
from app.assets import save_upload, save_url
from app.auth import UserContextMiddleware, can, ensure_default_admin, require_admin, require_editor, require_user
from app.user_routes import router as user_router, templates as user_templates
from app.visibility import VIEW_LABELS, can_view_type, ensure_visibility_rows, visibility_map, visible_types
from app.endpoint_defaults import endpoint_default

settings=get_settings(); base=Path(__file__).parent
settings.asset_root.mkdir(parents=True, exist_ok=True)
APP_VERSION = "0.24.0"
app=FastAPI(title=settings.app_name, version=APP_VERSION)
app.add_middleware(UserContextMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, session_cookie=settings.session_cookie_name, max_age=settings.session_max_age, same_site="lax", https_only=settings.session_https_only)
app.include_router(user_router)
app.mount("/static", StaticFiles(directory=base/"static"), name="static")
app.mount("/assets", StaticFiles(directory=settings.asset_root), name="assets")
templates=Jinja2Templates(directory=base/"templates")
templates.env.globals["app_version"] = APP_VERSION
templates.env.globals["app_name"] = settings.app_name
templates.env.globals["descriptor_badge"] = descriptor_badge
_markdown = MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": False}).enable("table")
def _render_markdown(value):
    if value in (None, ""):
        return Markup("")
    return Markup(_markdown.render(str(value)))


def _render_inline_markdown(value):
    if value in (None, ""):
        return Markup("")
    return Markup(_markdown.renderInline(str(value)))


def _card_summary(entity: Entity) -> str:
    if entity.summary:
        return str(entity.summary)
    data = entity.data_json or {}
    for key in ("short_desc", "desc", "description", "text", "summary"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for nested_key in ("as_string", "text", "description", "desc", "name"):
                nested = value.get(nested_key)
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
    return "No summary available."

templates.env.filters["render_markdown"] = _render_markdown
templates.env.filters["render_inline_markdown"] = _render_inline_markdown
templates.env.globals["card_summary"] = _card_summary

ENV_PATH = Path(os.environ.get("COMPENDIUM_ENV_FILE", ".env")).resolve()


def _lexicon_map(db: Session) -> dict[str, str]:
    return {row.original_term.casefold(): row.display_term for row in db.scalars(select(LexiconTerm)).all()}


def _display_term(term: str | None, lexicon: dict[str, str]) -> str:
    if not term:
        return "—"
    return lexicon.get(str(term).casefold(), str(term).replace("_", " ").replace("-", " ").title())


def _env_key(field_name: str) -> str:
    return field_name.upper()


def _env_value(value) -> str:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _quote_env(value: str) -> str:
    clean = value.replace("\r", "").replace("\n", "\n")
    if not clean or any(ch.isspace() for ch in clean) or any(ch in clean for ch in "#='\""):
        return json.dumps(clean)
    return clean


def _restart_process() -> None:
    time.sleep(1.0)
    if Path("/.dockerenv").exists():
        os.kill(os.getpid(), signal.SIGTERM)

@app.on_event("startup")
def startup():
    settings.asset_root.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    ensure_schema_columns()
    with Session(engine) as db:
        init_search(db)
        backfill_canonical_keys(db)
        recover_interrupted_syncs(db)
        ensure_default_admin(db)
        ensure_visibility_rows(db)

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session=Depends(get_db)):
    allowed_types = visible_types(db, request.state.user)
    counts=dict(db.execute(select(Entity.entity_type, func.count()).where(Entity.is_active==True, Entity.entity_type.in_(allowed_types or {"__none__"})).group_by(Entity.entity_type)).all())
    recent=db.scalars(select(Entity).where(Entity.is_active==True, Entity.entity_type.in_(allowed_types or {"__none__"})).order_by(Entity.updated_at.desc()).limit(12)).all()
    lexicon = _lexicon_map(db)
    count_rows = [
        {"entity_type": entity_type, "count": count, "label": _display_term(entity_type, lexicon)}
        for entity_type, count in sorted(counts.items(), key=lambda item: _display_term(item[0], lexicon).casefold())
    ]
    entity_type_labels = {entity_type: _display_term(entity_type, lexicon) for entity_type in counts}
    return templates.TemplateResponse(request,"home.html",{
        "counts": counts, "count_rows": count_rows, "entities": recent,
        "entity_type_labels": entity_type_labels,
    })

@app.get("/compendium", response_class=HTMLResponse)
def compendium(
    request: Request,
    q: str = "",
    entity_type: str | None = None,
    source_kind: str | None = None,
    source_display_name: str | None = None,
    game_system_name: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Browse canonical entities with SQL-level grouping and pagination."""
    allowed_page_sizes = (10, 25, 50, 100)
    if page_size not in allowed_page_sizes:
        try:
            saved_size = int(request.cookies.get("compendium_page_size", "25"))
        except ValueError:
            saved_size = 25
        page_size = saved_size if saved_size in allowed_page_sizes else 25

    ids: list[int] | None = None
    if q.strip():
        rows = db.execute(
            text(
                "SELECT entity_id, bm25(entity_search) rank FROM entity_search "
                "WHERE entity_search MATCH :q ORDER BY rank LIMIT 5000"
            ),
            {"q": q.strip()},
        ).all()
        ids = [int(row[0]) for row in rows] or [-1]

    allowed_types = visible_types(db, request.state.user)
    if entity_type and entity_type not in allowed_types:
        raise HTTPException(404, "Entity type not found")
    filtered = select(
        Entity.id.label("entity_id"),
        Entity.entity_type.label("entity_type"),
        Entity.canonical_key.label("canonical_key"),
    ).where(Entity.is_active == True, Entity.entity_type.in_(allowed_types or {"__none__"}))
    if ids is not None:
        filtered = filtered.where(Entity.id.in_(ids))
    if entity_type:
        filtered = filtered.where(Entity.entity_type == entity_type)
    if source_kind:
        filtered = filtered.where(Entity.source_kind == source_kind)
    if source_display_name:
        filtered = filtered.where(Entity.source_display_name == source_display_name)
    if game_system_name:
        filtered = filtered.where(Entity.game_system_name == game_system_name)
    filtered_sq = filtered.subquery()

    grouped = (
        select(
            filtered_sq.c.entity_type,
            filtered_sq.c.canonical_key,
            func.min(filtered_sq.c.entity_id).label("representative_id"),
        )
        .group_by(filtered_sq.c.entity_type, filtered_sq.c.canonical_key)
        .subquery()
    )
    total = int(db.scalar(select(func.count()).select_from(grouped)) or 0)
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, pages)

    page_groups = db.execute(
        select(grouped.c.entity_type, grouped.c.canonical_key, grouped.c.representative_id)
        .join(Entity, Entity.id == grouped.c.representative_id)
        .order_by(func.lower(Entity.name), grouped.c.entity_type)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    representative_ids = [row.representative_id for row in page_groups]
    representatives = {
        entity.id: entity
        for entity in db.scalars(select(Entity).where(Entity.id.in_(representative_ids))).all()
    } if representative_ids else {}

    group_keys = [(row.entity_type, row.canonical_key) for row in page_groups]
    visibility = visibility_map(db)
    if not can_view_type(request.state.user, entity_type, visibility):
        raise HTTPException(404, "Entity not found")
    variants = list(db.scalars(
        select(Entity)
        .where(Entity.is_active == True, tuple_(Entity.entity_type, Entity.canonical_key).in_(group_keys))
        .order_by(Entity.name, Entity.source_display_name, Entity.id)
    ).all()) if group_keys else []

    variants_by_key: dict[tuple[str, str], list[Entity]] = {}
    for variant in variants:
        variants_by_key.setdefault((variant.entity_type, variant.canonical_key), []).append(variant)

    groups = []
    for row in page_groups:
        representative = representatives.get(row.representative_id)
        if representative is None:
            continue
        key = (row.entity_type, row.canonical_key)
        source_variants = variants_by_key.get(key, [representative])
        sources = sorted({
            item.source_display_name or item.source_document or item.source_kind
            for item in source_variants
        })
        systems = sorted({item.game_system_name for item in source_variants if item.game_system_name})
        groups.append({
            "entity": representative,
            "canonical_key": row.canonical_key,
            "source_count": len(sources),
            "system_count": len(systems),
            "sources": sources,
            "systems": systems,
            "source_badges": [descriptor_badge(value, "source") for value in sources],
            "system_badges": [descriptor_badge(value, "system") for value in systems],
        })

    types = db.scalars(
        select(Entity.entity_type).where(Entity.is_active == True, Entity.entity_type.in_(allowed_types or {"__none__"})).distinct().order_by(Entity.entity_type)
    ).all()
    lexicon = _lexicon_map(db)
    type_options = [{"value": value, "label": _display_term(value, lexicon)} for value in types]
    for group in groups:
        group["type_label"] = _display_term(group["entity"].entity_type, lexicon)
    source_names = db.scalars(
        select(Entity.source_display_name)
        .where(Entity.is_active == True, Entity.entity_type.in_(allowed_types or {"__none__"}), Entity.source_display_name.is_not(None))
        .distinct().order_by(Entity.source_display_name)
    ).all()
    game_systems = db.scalars(
        select(Entity.game_system_name)
        .where(Entity.is_active == True, Entity.entity_type.in_(allowed_types or {"__none__"}), Entity.game_system_name.is_not(None))
        .distinct().order_by(Entity.game_system_name)
    ).all()
    browse_params = {
        "q": q, "entity_type": entity_type or "", "source_kind": source_kind or "",
        "source_display_name": source_display_name or "", "game_system_name": game_system_name or "",
        "page_size": page_size, "page": page,
    }
    browse_return_url = "/compendium?" + urlencode(browse_params)
    context = {
        "groups": groups, "q": q, "entity_type": entity_type,
        "source_kind": source_kind, "source_display_name": source_display_name,
        "game_system_name": game_system_name, "types": types, "type_options": type_options,
        "source_names": source_names, "game_systems": game_systems,
        "page": page, "pages": pages, "page_size": page_size,
        "page_sizes": allowed_page_sizes, "total": total,
        "browse_return_url": browse_return_url,
    }
    template = "fragments/results.html" if request.headers.get("HX-Request") == "true" else "compendium.html"
    response = templates.TemplateResponse(request, template, context)
    response.set_cookie(
        "compendium_page_size", str(page_size), max_age=60 * 60 * 24 * 365,
        samesite="lax", httponly=True,
    )
    return response


@app.get("/compendium/{entity_type}/{canonical_key}", response_class=HTMLResponse)
def entity_detail(
    request: Request,
    entity_type: str,
    canonical_key: str,
    source: str | None = None,
    return_to: str | None = None,
    db: Session = Depends(get_db),
):
    variants = list(db.scalars(
        select(Entity)
        .options(selectinload(Entity.assets))
        .where(
            Entity.entity_type == entity_type,
            Entity.is_active == True,
            (Entity.canonical_key == canonical_key) | (Entity.slug == canonical_key),
        )
        .order_by(Entity.source_display_name, Entity.id)
    ).all())
    if not variants:
        raise HTTPException(404, "Entity not found")
    resolved_key = variants[0].canonical_key or canonical_entity_key(entity_type, variants[0].name)
    # Include every variant when an old source-specific slug resolved the group.
    variants = list(db.scalars(
        select(Entity).options(selectinload(Entity.assets)).where(
            Entity.entity_type == entity_type, Entity.canonical_key == resolved_key, Entity.is_active == True
        ).order_by(Entity.source_display_name, Entity.id)
    ).all()) or variants
    entity = next((item for item in variants if item.public_id == source), variants[0])

    shared_assets = []
    seen_asset_ids = set()
    for variant in variants:
        for link in variant.assets:
            if link.asset_id not in seen_asset_ids:
                seen_asset_ids.add(link.asset_id)
                shared_assets.append(link)
    primary_asset = next((link for link in shared_assets if link.is_primary), shared_assets[0] if shared_assets else None)
    monster = build_monster_card(entity) if entity_type == "monster" else None
    magic_item = build_magic_item_card(entity) if entity_type in {"magicitem", "magic-item"} else None
    species = build_species_card(entity) if entity_type == "species" else None
    item_card = build_item_card(entity) if entity_type == "item" else None
    weapon = build_weapon_card(entity) if entity_type == "weapon" else None
    reference_card = None
    if entity_type == "spell": reference_card = build_spell_card(entity)
    elif entity_type == "spellschool": reference_card = build_spell_school_card(entity)
    elif entity_type in {"weaponpropertie", "weaponproperty"}: reference_card = build_weapon_property_card(entity)
    elif entity_type == "skill": reference_card = build_skill_card(entity)
    elif entity_type == "service": reference_card = build_service_card(entity)
    elif entity_type == "language": reference_card = build_language_card(entity)
    elif entity_type == "size": reference_card = build_size_card(entity)
    safe_return_to = return_to if return_to and return_to.startswith("/compendium?") else "/compendium"
    descriptor_badges = []
    if monster:
        descriptor_badges.extend(monster["identity_badges"])
    elif magic_item:
        descriptor_badges.extend(magic_item["identity_badges"])
    elif species:
        descriptor_badges.extend(species["identity_badges"])
    elif item_card:
        descriptor_badges.extend(item_card["identity_badges"])
    elif weapon:
        descriptor_badges.extend(weapon["identity_badges"])
    elif reference_card:
        descriptor_badges.extend(reference_card["identity_badges"])
    if entity.source_display_name:
        descriptor_badges.append(descriptor_badge(entity.source_display_name, "source"))
    if entity.game_system_name:
        descriptor_badges.append(descriptor_badge(entity.game_system_name, "system"))
    if len(variants) > 1:
        descriptor_badges.append(descriptor_badge(str(len(variants)), "versions"))
    user_lists = []
    if request.state.user:
        user_lists = list(db.scalars(select(UserEntityList).where(UserEntityList.owner_id == request.state.user.id).order_by(UserEntityList.name)).all())
    return templates.TemplateResponse(request, "entity_detail.html", {
        "entity": entity, "variants": variants, "canonical_key": resolved_key,
        "shared_assets": shared_assets, "primary_asset": primary_asset, "monster": monster,
        "magic_item": magic_item, "species": species, "item_card": item_card, "weapon": weapon, "reference_card": reference_card,
        "descriptor_badges": descriptor_badges, "return_to": safe_return_to,
        "user_lists": user_lists, "can_view_json": can(request.state.user, "editor"),
        "can_upload_artwork": can(request.state.user, "editor"),
    })


@app.get("/homebrew/new", response_class=HTMLResponse)
def new_homebrew(request:Request, _=Depends(require_editor)): return templates.TemplateResponse(request,"homebrew_form.html",{})

@app.post("/homebrew/new")
def create_homebrew_form(entity_type:str=Form(...),name:str=Form(...),summary:str=Form(""),description:str=Form(""),_=Depends(require_editor),db:Session=Depends(get_db)):
    entity=create_homebrew(db,EntityCreate(entity_type=entity_type,name=name,summary=summary,data={"description":description}))
    return RedirectResponse(f"/compendium/{entity.entity_type}/{entity.canonical_key or entity.slug}?source={entity.public_id}",303)

@app.post("/admin/sync/open5e")
def sync_route(background_tasks: BackgroundTasks, _=Depends(require_admin), db:Session=Depends(get_db)):
    run, created = create_sync_run(db)
    if created:
        background_tasks.add_task(run_open5e_sync, run.id)
    return RedirectResponse(f"/settings/open5e-sync?sync={run.id}", 303)

def _sync_runs(db: Session):
    return db.scalars(
        select(SyncRun).options(selectinload(SyncRun.endpoints))
        .order_by(SyncRun.id.desc()).limit(20)
    ).all()

@app.get("/admin")
def legacy_admin():
    return RedirectResponse("/settings/open5e-sync", 307)

@app.get("/settings")
def settings_home(_=Depends(require_admin)):
    return RedirectResponse("/settings/open5e-sync", 307)

@app.get("/settings/open5e-sync", response_class=HTMLResponse)
def settings_open5e_sync(request: Request, _=Depends(require_admin), db: Session = Depends(get_db)):
    runs = _sync_runs(db)
    active_run = next((run for run in runs if run.status in ACTIVE_SYNC_STATUSES), None)
    lexicon = _lexicon_map(db)
    endpoint_labels = {row.endpoint: _display_term(row.endpoint, lexicon) for run in runs for row in run.endpoints}
    invisible_types = {key for key, value in visibility_map(db).items() if value == "invisible"}
    return templates.TemplateResponse(request, "settings_open5e_sync.html", {
        "runs": runs, "active_run": active_run, "settings_section": "open5e-sync",
        "endpoint_labels": endpoint_labels, "invisible_types": invisible_types,
    })

@app.get("/admin/sync/status", response_class=HTMLResponse)
def sync_status(request: Request, _=Depends(require_admin), db: Session=Depends(get_db)):
    runs = _sync_runs(db)
    active_run = next((run for run in runs if run.status in ACTIVE_SYNC_STATUSES), None)
    lexicon = _lexicon_map(db)
    endpoint_labels = {row.endpoint: _display_term(row.endpoint, lexicon) for run in runs for row in run.endpoints}
    return templates.TemplateResponse(
        request, "fragments/sync_status.html", {"runs": runs, "active_run": active_run, "endpoint_labels": endpoint_labels,
        "invisible_types": {key for key, value in visibility_map(db).items() if value == "invisible"}}
    )

@app.get("/settings/site-lexicon")
def legacy_lexicon(): return RedirectResponse("/settings/endpoint-management", 303)

@app.get("/settings/view-management")
def legacy_view_management(): return RedirectResponse("/settings/endpoint-management", 303)

@app.get("/settings/endpoint-management", response_class=HTMLResponse)
def endpoint_management(request: Request, _=Depends(require_admin), db: Session = Depends(get_db)):
    known=set(db.scalars(select(Entity.entity_type).distinct()).all())
    known.update(db.scalars(select(SyncEndpoint.endpoint).distinct()).all())
    existing_lex={row.original_term:row for row in db.scalars(select(LexiconTerm)).all()}
    existing_vis={row.entity_type:row for row in db.scalars(select(EntityTypeVisibility)).all()}
    rows=[]
    for term in sorted(x for x in known if x):
        if term not in existing_vis:
            default=endpoint_default(term); row=EntityTypeVisibility(entity_type=term, minimum_role=default["minimum_role"]); db.add(row); db.flush(); existing_vis[term]=row
        rows.append({"original":term,"display":existing_lex.get(term).display_term if term in existing_lex else endpoint_default(term)["display"],"minimum_role":existing_vis[term].minimum_role})
    db.commit()
    return templates.TemplateResponse(request,"settings_endpoint_management.html",{"settings_section":"endpoint-management","rows":rows,"view_labels":VIEW_LABELS})

@app.post("/settings/endpoint-management/{term}", response_class=HTMLResponse)
async def update_endpoint_management(term: str, request: Request, _=Depends(require_admin), db: Session=Depends(get_db)):
    form=await request.form(); display=str(form.get("display_term","")).strip(); visibility=str(form.get("minimum_role","user"))
    lex=db.scalar(select(LexiconTerm).where(LexiconTerm.original_term==term))
    if lex: lex.display_term=display or _display_term(term,{})
    else: db.add(LexiconTerm(original_term=term,display_term=display or _display_term(term,{})))
    vis=db.scalar(select(EntityTypeVisibility).where(EntityTypeVisibility.entity_type==term))
    if not vis: vis=EntityTypeVisibility(entity_type=term); db.add(vis)
    vis.minimum_role=visibility if visibility in VIEW_LABELS else "user"
    db.commit()
    return templates.TemplateResponse(request,"fragments/endpoint_management_row.html",{"row":{"original":term,"display":lex.display_term if lex else display,"minimum_role":vis.minimum_role},"view_labels":VIEW_LABELS,"saved":True})

@app.get("/settings/site-config", response_class=HTMLResponse)
def settings_config(request: Request, _=Depends(require_admin)):
    current = get_settings()
    groups={"Application":[],"Storage":[],"Open5e Synchronization":[],"Authentication and Sessions":[]}
    for name, field in current.model_fields.items():
        item={"name":name,"env":_env_key(name),"value":_env_value(getattr(current,name)),"secret":"secret" in name.lower() or "password" in name.lower()}
        group="Open5e Synchronization" if name.startswith("open5e_") else "Authentication and Sessions" if name in {"secret_key","default_admin_username","default_admin_password","session_cookie_name","session_max_age","session_https_only"} else "Storage" if name in {"database_url","asset_root"} else "Application"
        groups[group].append(item)
    return templates.TemplateResponse(request,"settings_config.html",{"settings_section":"site-config","config_groups":groups,"env_path":str(ENV_PATH),"saved":request.query_params.get("saved"),"is_docker":Path("/.dockerenv").exists()})

@app.post("/settings/site-config")
async def save_site_config(request: Request, _=Depends(require_admin)):
    form = await request.form()
    lines = []
    for name in get_settings().model_fields:
        key = _env_key(name)
        value = str(form.get(key, ""))
        lines.append(f"{key}={_quote_env(value)}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    get_settings.cache_clear()
    refreshed=get_settings()
    templates.env.globals["app_name"]=refreshed.app_name
    user_templates.env.globals["app_name"]=refreshed.app_name
    app.title=refreshed.app_name
    return RedirectResponse("/settings/site-config?saved=1", 303)

@app.post("/settings/restart")
def restart_service(request: Request, background_tasks: BackgroundTasks, _=Depends(require_admin)):
    background_tasks.add_task(_restart_process)
    return templates.TemplateResponse(request, "restart.html", {"is_docker": Path("/.dockerenv").exists()})

@app.post("/entities/{public_id}/assets/upload")
async def upload_asset(public_id:str, image:UploadFile=File(...), attribution:str=Form(""), license_name:str=Form(""), _=Depends(require_editor), db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.public_id==public_id))
    if not entity: raise HTTPException(404,"Entity not found")
    await save_upload(db,entity,image,attribution or None,license_name or None)
    return RedirectResponse(f"/compendium/{entity.entity_type}/{entity.canonical_key or entity.slug}?source={entity.public_id}",303)

@app.post("/entities/{public_id}/assets/download")
async def download_asset(public_id:str, image_url:str=Form(...), attribution:str=Form(""), license_name:str=Form(""), _=Depends(require_editor), db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.public_id==public_id))
    if not entity: raise HTTPException(404,"Entity not found")
    await save_url(db,entity,image_url,attribution or None,license_name or None)
    return RedirectResponse(f"/compendium/{entity.entity_type}/{entity.canonical_key or entity.slug}?source={entity.public_id}",303)

@app.get("/api/v1/entities", response_model=list[EntityOut])
def api_entities(q:str="", entity_type:str|None=None, source_kind:str|None=None,
                 source_display_name:str|None=None, game_system_name:str|None=None,
                 limit:int=Query(50,ge=1,le=500), offset:int=Query(0,ge=0),
                 db:Session=Depends(get_db)):
    stmt=select(Entity).where(Entity.is_active==True)
    if q: stmt=stmt.where(Entity.name.ilike(f"%{q}%"))
    if entity_type: stmt=stmt.where(Entity.entity_type==entity_type)
    if source_kind: stmt=stmt.where(Entity.source_kind==source_kind)
    if source_display_name: stmt=stmt.where(Entity.source_display_name==source_display_name)
    if game_system_name: stmt=stmt.where(Entity.game_system_name==game_system_name)
    return list(db.scalars(stmt.order_by(Entity.name).offset(offset).limit(limit)).all())

@app.get("/api/v1/entities/{public_id}",response_model=EntityOut)
def api_entity(public_id:str,db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.public_id==public_id))
    if not entity: raise HTTPException(404,"Entity not found")
    return entity

@app.post("/api/v1/homebrew",response_model=EntityOut,status_code=201)
def api_create(payload:EntityCreate,_=Depends(require_editor),db:Session=Depends(get_db)): return create_homebrew(db,payload)

@app.put("/api/v1/homebrew/{public_id}",response_model=EntityOut)
def api_update(public_id:str,payload:EntityUpdate,_=Depends(require_editor),db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.public_id==public_id,Entity.source_kind=="homebrew"))
    if not entity: raise HTTPException(404,"Homebrew entity not found")
    if payload.name is not None: entity.name=payload.name; entity.slug=ensure_unique_slug(db,entity.entity_type,payload.name,entity.id); entity.canonical_key=canonical_entity_key(entity.entity_type,payload.name)
    if payload.summary is not None: entity.summary=payload.summary
    if payload.data is not None: entity.data_json=payload.data
    if payload.is_active is not None: entity.is_active=payload.is_active
    db.flush(); rebuild_search_row(db,entity); db.commit(); db.refresh(entity); return entity
