from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import Base, engine, get_db
from app.models import Entity, SyncRun
from app.schemas import EntityCreate, EntityOut, EntityUpdate
from app.services import create_homebrew, ensure_unique_slug, init_search, rebuild_search_row
from app.sync import sync_open5e
from app.assets import save_upload, save_url

settings=get_settings(); base=Path(__file__).parent
settings.asset_root.mkdir(parents=True, exist_ok=True)
app=FastAPI(title=settings.app_name, version="0.1.0")
app.mount("/static", StaticFiles(directory=base/"static"), name="static")
app.mount("/assets", StaticFiles(directory=settings.asset_root), name="assets")
templates=Jinja2Templates(directory=base/"templates")

@app.on_event("startup")
def startup():
    settings.asset_root.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with Session(engine) as db: init_search(db)

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session=Depends(get_db)):
    counts=dict(db.execute(select(Entity.entity_type, func.count()).where(Entity.is_active==True).group_by(Entity.entity_type)).all())
    recent=db.scalars(select(Entity).where(Entity.is_active==True).order_by(Entity.updated_at.desc()).limit(12)).all()
    return templates.TemplateResponse(request,"home.html",{"counts":counts,"entities":recent})

@app.get("/compendium", response_class=HTMLResponse)
def compendium(request: Request, q: str="", entity_type: str|None=None, source_kind: str|None=None,
               page:int=Query(1,ge=1), db:Session=Depends(get_db)):
    page_size=24; params={}; ids=None
    if q.strip():
        rows=db.execute(text("SELECT entity_id, bm25(entity_search) rank FROM entity_search WHERE entity_search MATCH :q ORDER BY rank LIMIT 500"),{"q":q.strip()}).all()
        ids=[int(r[0]) for r in rows] or [-1]
    stmt=select(Entity).where(Entity.is_active==True)
    if ids is not None: stmt=stmt.where(Entity.id.in_(ids))
    if entity_type: stmt=stmt.where(Entity.entity_type==entity_type)
    if source_kind: stmt=stmt.where(Entity.source_kind==source_kind)
    total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    entities=db.scalars(stmt.order_by(Entity.name).offset((page-1)*page_size).limit(page_size)).all()
    types=db.scalars(select(Entity.entity_type).distinct().order_by(Entity.entity_type)).all()
    template="fragments/results.html" if request.headers.get("HX-Request")=="true" else "compendium.html"
    return templates.TemplateResponse(request,template,{"entities":entities,"q":q,"entity_type":entity_type,"source_kind":source_kind,"types":types,"page":page,"pages":max(1,(total+page_size-1)//page_size)})

@app.get("/compendium/{entity_type}/{slug}", response_class=HTMLResponse)
def entity_detail(request:Request,entity_type:str,slug:str,db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.entity_type==entity_type,Entity.slug==slug,Entity.is_active==True))
    if not entity: raise HTTPException(404,"Entity not found")
    return templates.TemplateResponse(request,"entity_detail.html",{"entity":entity})

@app.get("/homebrew/new", response_class=HTMLResponse)
def new_homebrew(request:Request): return templates.TemplateResponse(request,"homebrew_form.html",{})

@app.post("/homebrew/new")
def create_homebrew_form(entity_type:str=Form(...),name:str=Form(...),summary:str=Form(""),description:str=Form(""),db:Session=Depends(get_db)):
    entity=create_homebrew(db,EntityCreate(entity_type=entity_type,name=name,summary=summary,data={"description":description}))
    return RedirectResponse(f"/compendium/{entity.entity_type}/{entity.slug}",303)

@app.post("/admin/sync/open5e")
async def sync_route(db:Session=Depends(get_db)):
    run=await sync_open5e(db); return RedirectResponse(f"/admin?sync={run.id}",303)

@app.get("/admin", response_class=HTMLResponse)
def admin(request:Request,db:Session=Depends(get_db)):
    runs=db.scalars(select(SyncRun).order_by(SyncRun.id.desc()).limit(20)).all()
    return templates.TemplateResponse(request,"admin.html",{"runs":runs})

@app.post("/entities/{public_id}/assets/upload")
async def upload_asset(public_id:str, image:UploadFile=File(...), attribution:str=Form(""), license_name:str=Form(""), db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.public_id==public_id))
    if not entity: raise HTTPException(404,"Entity not found")
    await save_upload(db,entity,image,attribution or None,license_name or None)
    return RedirectResponse(f"/compendium/{entity.entity_type}/{entity.slug}",303)

@app.post("/entities/{public_id}/assets/download")
async def download_asset(public_id:str, image_url:str=Form(...), attribution:str=Form(""), license_name:str=Form(""), db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.public_id==public_id))
    if not entity: raise HTTPException(404,"Entity not found")
    await save_url(db,entity,image_url,attribution or None,license_name or None)
    return RedirectResponse(f"/compendium/{entity.entity_type}/{entity.slug}",303)

@app.get("/api/v1/entities", response_model=list[EntityOut])
def api_entities(q:str="",entity_type:str|None=None,source_kind:str|None=None,limit:int=Query(50,ge=1,le=500),offset:int=Query(0,ge=0),db:Session=Depends(get_db)):
    stmt=select(Entity).where(Entity.is_active==True)
    if q: stmt=stmt.where(Entity.name.ilike(f"%{q}%"))
    if entity_type: stmt=stmt.where(Entity.entity_type==entity_type)
    if source_kind: stmt=stmt.where(Entity.source_kind==source_kind)
    return list(db.scalars(stmt.order_by(Entity.name).offset(offset).limit(limit)).all())

@app.get("/api/v1/entities/{public_id}",response_model=EntityOut)
def api_entity(public_id:str,db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.public_id==public_id))
    if not entity: raise HTTPException(404,"Entity not found")
    return entity

@app.post("/api/v1/homebrew",response_model=EntityOut,status_code=201)
def api_create(payload:EntityCreate,db:Session=Depends(get_db)): return create_homebrew(db,payload)

@app.put("/api/v1/homebrew/{public_id}",response_model=EntityOut)
def api_update(public_id:str,payload:EntityUpdate,db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.public_id==public_id,Entity.source_kind=="homebrew"))
    if not entity: raise HTTPException(404,"Homebrew entity not found")
    if payload.name is not None: entity.name=payload.name; entity.slug=ensure_unique_slug(db,entity.entity_type,payload.name,entity.id)
    if payload.summary is not None: entity.summary=payload.summary
    if payload.data is not None: entity.data_json=payload.data
    if payload.is_active is not None: entity.is_active=payload.is_active
    db.flush(); rebuild_search_row(db,entity); db.commit(); db.refresh(entity); return entity
