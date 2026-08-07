from __future__ import annotations
import uuid
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.auth import ROLE_LABELS, can, hash_password, require_admin, require_user, save_token_image, verify_password
from app.db import get_db
from app.config import get_settings
from app.models import Entity, User, UserEntityList, UserEntityListItem
from app.visibility import visible_types

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["app_version"] = "0.32.5"
templates.env.globals["app_name"] = get_settings().app_name
router = APIRouter()


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


def _safe_next(value: str | None) -> str:
    return value if value and value.startswith("/") and not value.startswith("//") else "/"


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/"):
    if request.state.user:
        return RedirectResponse(_safe_next(next), 303)
    return templates.TemplateResponse(request, "login.html", {"next": _safe_next(next)})


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), next: str = Form("/"), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.username) == username.strip().lower()))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request, "login.html", {"next": _safe_next(next), "error": "Invalid username or password"}, status_code=401)
    request.session.clear(); request.session["user_id"] = user.id
    return RedirectResponse(_safe_next(next), 303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", 303)


@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    current = db.get(User, user.id)
    source_rows = db.execute(
        select(Entity.source_document, Entity.source_display_name)
        .where(Entity.is_active == True, Entity.source_document.is_not(None))
        .distinct().order_by(Entity.source_display_name, Entity.source_document)
    ).all()
    preferred_sources = [
        {"key": key, "name": display or key}
        for key, display in source_rows if key
    ]
    return templates.TemplateResponse(request, "profile.html", {"profile_user": current, "preferred_sources": preferred_sources})


@router.post("/profile")
def update_profile(request: Request, display_name: str = Form(...), email: str = Form(""), password: str = Form(""), preferred_source_document: str = Form(""), user: User = Depends(require_user), db: Session = Depends(get_db)):
    current = db.get(User, user.id)
    current.display_name = display_name.strip() or current.username
    current.email = email.strip() or None
    current.preferred_source_document = preferred_source_document.strip() or None
    if password:
        try: current.password_hash = hash_password(password)
        except ValueError as exc: raise HTTPException(400, str(exc))
    db.commit()
    return RedirectResponse("/profile?saved=1", 303)


@router.post("/profile/token")
async def update_token(image: UploadFile = File(...), user: User = Depends(require_user), db: Session = Depends(get_db)):
    current = db.get(User, user.id)
    await save_token_image(db, current, image)
    return RedirectResponse("/profile?saved=1", 303)


@router.get("/settings/user-management", response_class=HTMLResponse)
def user_management(request: Request, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.username)).all()
    return templates.TemplateResponse(request, "settings_users.html", {"settings_section": "user-management", "users": users, "role_labels": ROLE_LABELS})


@router.post("/settings/user-management")
def create_user(username: str = Form(...), display_name: str = Form(...), email: str = Form(""), role: str = Form("user"), password: str = Form(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if role not in ROLE_LABELS: raise HTTPException(400, "Invalid role")
    if db.scalar(select(User).where(func.lower(User.username) == username.strip().lower())): raise HTTPException(409, "Username already exists")
    try: hashed = hash_password(password)
    except ValueError as exc: raise HTTPException(400, str(exc))
    db.add(User(public_id=_uid("usr"), username=username.strip(), display_name=display_name.strip() or username.strip(), email=email.strip() or None, password_hash=hashed, role=role, is_active=True))
    db.commit(); return RedirectResponse("/settings/user-management?created=1", 303)


@router.get("/settings/user-management/{public_id}", response_class=HTMLResponse)
def edit_user_page(request: Request, public_id: str, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.scalar(select(User).where(User.public_id == public_id))
    if not target: raise HTTPException(404, "User not found")
    return templates.TemplateResponse(request, "settings_user_edit.html", {"settings_section": "user-management", "target": target, "role_labels": ROLE_LABELS})


@router.post("/settings/user-management/{public_id}")
def edit_user(public_id: str, username: str = Form(...), display_name: str = Form(...), email: str = Form(""), role: str = Form(...), is_active: str | None = Form(None), password: str = Form(""), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.scalar(select(User).where(User.public_id == public_id))
    if not target: raise HTTPException(404, "User not found")
    if role not in ROLE_LABELS: raise HTTPException(400, "Invalid role")
    if target.id == admin.id and (role != "administrator" or not is_active): raise HTTPException(400, "You cannot disable or demote your current administrator account")
    target.username=username.strip(); target.display_name=display_name.strip() or target.username; target.email=email.strip() or None; target.role=role; target.is_active=bool(is_active)
    if password:
        try: target.password_hash=hash_password(password)
        except ValueError as exc: raise HTTPException(400, str(exc))
    db.commit(); return RedirectResponse("/settings/user-management?saved=1", 303)


@router.post("/settings/user-management/{public_id}/delete")
def delete_user(public_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target=db.scalar(select(User).where(User.public_id==public_id))
    if not target: raise HTTPException(404, "User not found")
    if target.id == admin.id: raise HTTPException(400, "You cannot delete your current account")
    if target.role == "administrator" and db.scalar(select(func.count(User.id)).where(User.role=="administrator", User.is_active==True)) <= 1: raise HTTPException(400, "At least one active administrator is required")
    db.delete(target); db.commit(); return RedirectResponse("/settings/user-management?deleted=1",303)


@router.get("/lists", response_class=HTMLResponse)
def my_lists(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    all_lists=list(db.scalars(select(UserEntityList).options(selectinload(UserEntityList.items), selectinload(UserEntityList.owner)).order_by(UserEntityList.updated_at.desc())).all())
    own_lists=[row for row in all_lists if row.owner_id==user.id]
    shared_lists=[row for row in all_lists if row.owner_id!=user.id and row.is_public]
    return templates.TemplateResponse(request,"lists.html",{"lists":own_lists,"shared_lists":shared_lists})


@router.post("/lists")
def create_list(name: str=Form(...), description: str=Form(""), is_public: str|None=Form(None), user: User=Depends(require_user), db:Session=Depends(get_db)):
    row=UserEntityList(public_id=_uid("lst"),owner_id=user.id,name=name.strip(),description=description.strip() or None,is_public=bool(is_public))
    db.add(row); db.commit(); return RedirectResponse(f"/lists/{row.public_id}",303)


def _list_access(db: Session, public_id: str, user: User | None):
    row=db.scalar(select(UserEntityList).where(UserEntityList.public_id==public_id).options(selectinload(UserEntityList.items).selectinload(UserEntityListItem.entity), selectinload(UserEntityList.owner)))
    if not row: raise HTTPException(404,"List not found")
    if not row.is_public and (not user or row.owner_id != user.id): raise HTTPException(404,"List not found")
    return row


@router.get("/lists/{public_id}", response_class=HTMLResponse)
def view_list(request: Request, public_id: str, db: Session=Depends(get_db)):
    row=_list_access(db,public_id,request.state.user)
    allowed_types = visible_types(db, request.state.user)
    items=[item for item in row.items if item.entity_type in allowed_types]
    if row.sort_mode=="name": items.sort(key=lambda x:x.entity.name.casefold())
    return templates.TemplateResponse(request,"list_detail.html",{"entity_list":row,"items":items,"can_edit":bool(request.state.user and row.owner_id==request.state.user.id)})


@router.post("/lists/{public_id}/settings")
def update_list(public_id:str,name:str=Form(...),description:str=Form(""),is_public:str|None=Form(None),sort_mode:str=Form("manual"),user:User=Depends(require_user),db:Session=Depends(get_db)):
    row=db.scalar(select(UserEntityList).where(UserEntityList.public_id==public_id))
    if not row or row.owner_id!=user.id: raise HTTPException(403)
    row.name=name.strip(); row.description=description.strip() or None; row.is_public=bool(is_public); row.sort_mode=sort_mode if sort_mode in {"manual","name"} else "manual"; db.commit()
    return RedirectResponse(f"/lists/{public_id}",303)


@router.post("/lists/{public_id}/delete")
def delete_list(public_id:str,user:User=Depends(require_user),db:Session=Depends(get_db)):
    row=db.scalar(select(UserEntityList).where(UserEntityList.public_id==public_id))
    if not row or row.owner_id!=user.id: raise HTTPException(403)
    db.delete(row); db.commit(); return RedirectResponse("/lists",303)


@router.post("/entities/{entity_public_id}/lists/add")
def add_to_list(entity_public_id:str,list_id:str=Form(""),new_list_name:str=Form(""),new_list_public:str|None=Form(None),return_to:str=Form("/compendium"),user:User=Depends(require_user),db:Session=Depends(get_db)):
    entity=db.scalar(select(Entity).where(Entity.public_id==entity_public_id,Entity.is_active==True))
    if not entity: raise HTTPException(404,"Entity not found")
    if new_list_name.strip():
        target=UserEntityList(public_id=_uid("lst"),owner_id=user.id,name=new_list_name.strip(),is_public=bool(new_list_public)); db.add(target); db.flush()
    else:
        target=db.scalar(select(UserEntityList).where(UserEntityList.public_id==list_id,UserEntityList.owner_id==user.id))
        if not target: raise HTTPException(404,"List not found")
    canonical=entity.canonical_key or entity.slug
    exists=db.scalar(select(UserEntityListItem).where(UserEntityListItem.list_id==target.id,UserEntityListItem.entity_type==entity.entity_type,UserEntityListItem.canonical_key==canonical))
    destination = _safe_next(return_to)
    separator = "&" if "?" in destination else "?"
    if exists:
        return RedirectResponse(f"{destination}{separator}list_status=already_added",303)
    position=(db.scalar(select(func.coalesce(func.max(UserEntityListItem.position),0)).where(UserEntityListItem.list_id==target.id)) or 0)+10
    db.add(UserEntityListItem(list_id=target.id,entity_id=entity.id,entity_type=entity.entity_type,canonical_key=canonical,position=position)); db.commit()
    return RedirectResponse(f"{destination}{separator}list_status=added",303)




@router.post("/lists/bulk-add")
async def bulk_add_to_list(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    form = await request.form()
    entity_ids = [str(value) for value in form.getlist("entity_id") if str(value).strip()]
    list_id = str(form.get("list_id", "")).strip()
    new_list_name = str(form.get("new_list_name", "")).strip()
    new_list_public = bool(form.get("new_list_public"))
    return_to = _safe_next(str(form.get("return_to", "/lists")))
    if not entity_ids:
        separator = "&" if "?" in return_to else "?"
        return RedirectResponse(f"{return_to}{separator}list_status=no_items", 303)
    if new_list_name:
        target = UserEntityList(public_id=_uid("lst"), owner_id=user.id, name=new_list_name, is_public=new_list_public)
        db.add(target); db.flush()
    else:
        target = db.scalar(select(UserEntityList).where(UserEntityList.public_id == list_id, UserEntityList.owner_id == user.id))
        if not target: raise HTTPException(404, "List not found")
    entities = list(db.scalars(select(Entity).where(Entity.public_id.in_(entity_ids), Entity.is_active.is_(True))).all())
    existing = {(row.entity_type, row.canonical_key) for row in db.scalars(select(UserEntityListItem).where(UserEntityListItem.list_id == target.id)).all()}
    position = (db.scalar(select(func.coalesce(func.max(UserEntityListItem.position), 0)).where(UserEntityListItem.list_id == target.id)) or 0)
    added = 0
    for entity in entities:
        canonical = entity.canonical_key or entity.slug
        key = (entity.entity_type, canonical)
        if key in existing: continue
        position += 10
        db.add(UserEntityListItem(list_id=target.id, entity_id=entity.id, entity_type=entity.entity_type, canonical_key=canonical, position=position))
        existing.add(key); added += 1
    db.commit()
    separator = "&" if "?" in return_to else "?"
    return RedirectResponse(f"{return_to}{separator}list_status=added&list_items_added={added}", 303)


@router.post("/lists/{public_id}/items/{item_id}/remove")
def remove_list_item(public_id:str,item_id:int,user:User=Depends(require_user),db:Session=Depends(get_db)):
    row=db.scalar(select(UserEntityList).where(UserEntityList.public_id==public_id))
    if not row or row.owner_id!=user.id: raise HTTPException(403)
    item=db.scalar(select(UserEntityListItem).where(UserEntityListItem.id==item_id,UserEntityListItem.list_id==row.id))
    if item: db.delete(item); db.commit()
    return RedirectResponse(f"/lists/{public_id}",303)


@router.post("/lists/{public_id}/reorder")
async def reorder_list(public_id:str,request:Request,user:User=Depends(require_user),db:Session=Depends(get_db)):
    row=db.scalar(select(UserEntityList).where(UserEntityList.public_id==public_id))
    if not row or row.owner_id!=user.id: raise HTTPException(403)
    form=await request.form()
    raw_order = str(form.get("item_order", ""))
    item_ids = []
    for value in raw_order.split(","):
        try: item_ids.append(int(value))
        except ValueError: continue
    if item_ids:
        valid_items = {item.id:item for item in db.scalars(select(UserEntityListItem).where(UserEntityListItem.list_id==row.id, UserEntityListItem.id.in_(item_ids))).all()}
        for index, item_id in enumerate(item_ids, start=1):
            item = valid_items.get(item_id)
            if item: item.position = index * 10
    row.sort_mode="manual"; db.commit(); return RedirectResponse(f"/lists/{public_id}?ordered=1",303)
