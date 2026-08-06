from __future__ import annotations
import hashlib, ipaddress, socket, uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Asset, Entity, EntityAsset
from app.services import public_id

settings = get_settings()
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MAX_BYTES = 15 * 1024 * 1024

def _paths() -> tuple[Path, Path]:
    originals = settings.asset_root / "originals"
    thumbnails = settings.asset_root / "thumbnails"
    originals.mkdir(parents=True, exist_ok=True)
    thumbnails.mkdir(parents=True, exist_ok=True)
    return originals, thumbnails

def _reject_private_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(400, "Only public HTTP/HTTPS image URLs are allowed")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HTTPException(400, "Asset host could not be resolved") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise HTTPException(400, "Private and local network asset URLs are blocked")

def _save_image(db: Session, entity: Entity, content: bytes, original_name: str | None,
                media_type: str | None, source_url: str | None, attribution: str | None,
                license_name: str | None) -> Asset:
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Image is larger than 15 MB")
    try:
        image = Image.open(BytesIO(content)); image.verify()
        image = Image.open(BytesIO(content)); width, height = image.size
        detected = Image.MIME.get(image.format or "")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(400, "The supplied file is not a supported image") from exc
    media_type = detected or media_type or "application/octet-stream"
    if media_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Supported image types are JPEG, PNG, WebP, and GIF")
    checksum = hashlib.sha256(content).hexdigest()
    existing = db.query(Asset).filter(Asset.checksum == checksum).first()
    originals, thumbnails = _paths()
    if existing is None:
        storage_name = f"{uuid.uuid4().hex}{ALLOWED_TYPES[media_type]}"
        (originals / storage_name).write_bytes(content)
        thumb = Image.open(BytesIO(content)); thumb.thumbnail((640, 640))
        if thumb.mode not in ("RGB", "RGBA"): thumb = thumb.convert("RGB")
        thumb.save(thumbnails / storage_name)
        existing = Asset(public_id=public_id("ast"), storage_name=storage_name,
            original_name=original_name, media_type=media_type, byte_size=len(content),
            width=width, height=height, checksum=checksum, source_url=source_url,
            attribution=attribution, license_name=license_name)
        db.add(existing); db.flush()
    for link in entity.assets:
        if link.is_primary: link.is_primary = False
    if not any(link.asset_id == existing.id and link.role == "portrait" for link in entity.assets):
        db.add(EntityAsset(entity_id=entity.id, asset_id=existing.id, role="portrait",
                           alt_text=entity.name, is_primary=True))
    db.commit(); db.refresh(existing)
    return existing

async def save_upload(db: Session, entity: Entity, upload: UploadFile,
                      attribution: str | None, license_name: str | None) -> Asset:
    content = await upload.read(MAX_BYTES + 1)
    return _save_image(db, entity, content, upload.filename, upload.content_type, None,
                       attribution, license_name)

async def save_url(db: Session, entity: Entity, url: str,
                   attribution: str | None, license_name: str | None) -> Asset:
    _reject_private_url(url)
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "DND-Compendium/0.1"})
        response.raise_for_status()
        content = response.content
    name = Path(urlparse(url).path).name or None
    return _save_image(db, entity, content, name, response.headers.get("content-type"), url,
                       attribution, license_name)
