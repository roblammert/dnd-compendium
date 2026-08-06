from __future__ import annotations
import hashlib
import hmac
import os
import uuid
from io import BytesIO
from pathlib import Path
from fastapi import Depends, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
from app.db import SessionLocal, get_db
from app.models import Asset, User

ROLE_RANK = {"user": 10, "editor": 20, "administrator": 30}
ROLE_LABELS = {"user": "Users", "editor": "Editors", "administrator": "Administrators"}
def hash_password(value: str) -> str:
    if len(value) < 10:
        raise ValueError("Passwords must be at least 10 characters long")
    salt = os.urandom(16)
    digest = hashlib.scrypt(value.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, digest_hex = hashed.split("$", 5)
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(plain.encode("utf-8"), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p), dklen=len(bytes.fromhex(digest_hex)))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def can(user: User | None, minimum: str) -> bool:
    return bool(user and user.is_active and ROLE_RANK.get(user.role, 0) >= ROLE_RANK[minimum])


class UserContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        user_id = request.session.get("user_id")
        if user_id:
            with SessionLocal() as db:
                user = db.get(User, int(user_id))
                if user and user.is_active:
                    db.expunge(user)
                    request.state.user = user
                else:
                    request.session.clear()
        return await call_next(request)


def _required(request: Request, role: str) -> User:
    user = getattr(request.state, "user", None)
    if not user:
        next_url = request.url.path
        if request.url.query:
            next_url += "?" + request.url.query
        raise HTTPException(303, headers={"Location": f"/login?next={next_url}"})
    if not can(user, role):
        raise HTTPException(403, "You do not have permission to access this page")
    return user


def require_user(request: Request) -> User:
    return _required(request, "user")


def require_editor(request: Request) -> User:
    return _required(request, "editor")


def require_admin(request: Request) -> User:
    return _required(request, "administrator")


def ensure_default_admin(db: Session) -> User | None:
    if db.scalar(select(func.count(User.id))) > 0:
        return None
    settings = get_settings()
    user = User(
        public_id="usr_" + uuid.uuid4().hex[:24],
        username=settings.default_admin_username.strip() or "admin",
        display_name="Administrator",
        password_hash=hash_password(settings.default_admin_password),
        role="administrator",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def save_token_image(db: Session, user: User, upload: UploadFile) -> Asset:
    content = await upload.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Token image is larger than 5 MB")
    try:
        image = Image.open(BytesIO(content)); image.verify()
        image = Image.open(BytesIO(content)); image.thumbnail((512, 512))
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(400, "The supplied file is not a supported image") from exc
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")
    settings = get_settings()
    folder = settings.asset_root / "tokens"
    folder.mkdir(parents=True, exist_ok=True)
    storage_name = f"token-{uuid.uuid4().hex}.webp"
    out = folder / storage_name
    image.save(out, "WEBP", quality=88)
    content_out = out.read_bytes()
    asset = Asset(
        public_id="ast_" + uuid.uuid4().hex[:24], storage_name=storage_name,
        original_name=upload.filename, media_type="image/webp", byte_size=len(content_out),
        width=image.width, height=image.height, checksum=hashlib.sha256(content_out).hexdigest(),
    )
    db.add(asset); db.flush()
    user.token_asset_id = asset.id
    db.commit(); db.refresh(asset)
    return asset
