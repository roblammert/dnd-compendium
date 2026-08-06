from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any

from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.models import Entity


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or uuid.uuid4().hex[:12]


def canonical_entity_key(entity_type: str, name: str) -> str:
    """Stable grouping key shared by source variants of the same named entity."""
    return slugify(name)




def descriptor_badge(value: str, kind: str) -> dict[str, str]:
    """Build a stable site-wide descriptor badge presentation."""
    display = str(value or "").strip()
    normalized = slugify(display)
    alignment_colors = {
        "lawful-good": (216, 58, 28),
        "neutral-good": (202, 48, 34),
        "chaotic-good": (178, 47, 31),
        "lawful-neutral": (231, 32, 38),
        "true-neutral": (42, 12, 38),
        "neutral": (42, 12, 38),
        "chaotic-neutral": (28, 55, 40),
        "lawful-evil": (334, 55, 31),
        "neutral-evil": (351, 65, 34),
        "chaotic-evil": (4, 72, 39),
        "unaligned": (38, 10, 42),
    }
    if kind == "alignment" and normalized in alignment_colors:
        hue, saturation, lightness = alignment_colors[normalized]
    elif kind == "source":
        # A deliberately separated palette gives every source a stable, recognizable tag.
        source_palette = [
            (4, 58, 36), (24, 64, 35), (43, 65, 32), (78, 46, 31),
            (116, 38, 31), (153, 42, 30), (181, 48, 31), (202, 57, 35),
            (222, 52, 38), (245, 43, 42), (270, 43, 39), (300, 40, 36),
            (326, 50, 37), (15, 42, 42), (164, 34, 38), (211, 36, 31),
        ]
        digest = hashlib.sha256(display.casefold().encode("utf-8")).digest()
        hue, saturation, lightness = source_palette[int.from_bytes(digest[:2], "big") % len(source_palette)]
    else:
        digest = hashlib.sha256(f"{kind}:{display.casefold()}".encode("utf-8")).digest()
        hue = int.from_bytes(digest[:2], "big") % 360
        saturation = 32 + digest[2] % 24
        lightness = 30 + digest[3] % 12
    return {
        "kind": kind,
        "value": display,
        "class_name": normalized,
        "style": f"--badge-h:{hue};--badge-s:{saturation}%;--badge-l:{lightness}%",
    }

def public_id(prefix: str = "ent") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def canonical_checksum(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(flatten_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(flatten_text(v) for v in value)
    return str(value)


def ensure_unique_slug(db: Session, entity_type: str, desired: str, exclude_id: int | None = None) -> str:
    base = slugify(desired)
    candidate = base
    n = 2
    while True:
        q = select(Entity.id).where(Entity.entity_type == entity_type, Entity.slug == candidate)
        if exclude_id:
            q = q.where(Entity.id != exclude_id)
        if db.scalar(q) is None:
            return candidate
        candidate = f"{base}-{n}"
        n += 1


def rebuild_search_row(db: Session, entity: Entity) -> None:
    db.execute(text("DELETE FROM entity_search WHERE entity_id=:id"), {"id": entity.id})
    body = flatten_text(entity.data_json)
    db.execute(
        text(
            """
            INSERT INTO entity_search(entity_id,name,entity_type,source_document,summary,body)
            VALUES(:id,:name,:type,:source,:summary,:body)
            """
        ),
        {
            "id": entity.id,
            "name": entity.name,
            "type": entity.entity_type,
            "source": entity.source_document or "",
            "summary": entity.summary or "",
            "body": body,
        },
    )


def init_search(db: Session) -> None:
    db.execute(
        text(
            """CREATE VIRTUAL TABLE IF NOT EXISTS entity_search USING fts5(
              entity_id UNINDEXED, name, entity_type, source_document, summary, body,
              tokenize='unicode61 remove_diacritics 2'
            )"""
        )
    )
    db.commit()


def backfill_canonical_keys(db: Session) -> int:
    rows = db.scalars(select(Entity).where((Entity.canonical_key.is_(None)) | (Entity.canonical_key == ""))).all()
    for entity in rows:
        entity.canonical_key = canonical_entity_key(entity.entity_type, entity.name)
    if rows:
        db.commit()
    return len(rows)


def create_homebrew(db: Session, payload) -> Entity:
    entity = Entity(
        public_id=public_id(),
        entity_type=payload.entity_type,
        name=payload.name,
        slug=ensure_unique_slug(db, payload.entity_type, payload.name),
        canonical_key=canonical_entity_key(payload.entity_type, payload.name),
        source_kind="homebrew",
        source_document=payload.source_document or "homebrew",
        source_display_name="Homebrew",
        is_homebrew=True,
        summary=payload.summary,
        data_json=payload.data,
    )
    db.add(entity)
    db.flush()
    rebuild_search_row(db, entity)
    db.commit()
    db.refresh(entity)
    return entity


def _first(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


def _display_name(value: Any, default: str = "") -> str:
    """Return a human label from Open5e reference objects or scalar values."""
    if isinstance(value, dict):
        for key in ("name", "display_name", "title", "label", "key", "slug"):
            candidate = value.get(key)
            if candidate not in (None, ""):
                return str(candidate)
        return default
    if value in (None, ""):
        return default
    return str(value)


def _format_number(value: Any, decimals: int = 1) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{number:.{decimals}f}"


def _format_measurement(value: Any, fallback_unit: str | None = None, decimals: int | None = None) -> str:
    if isinstance(value, dict):
        number = value.get("value", value.get("distance", value.get("amount", value.get("speed"))))
        unit = value.get("unit") or value.get("units") or fallback_unit
        if number not in (None, ""):
            rendered = _format_number(number, decimals) if decimals is not None else str(number)
            return f"{rendered}{f' {unit}' if unit else ''}"
        text = _display_name(value)
        return text or "—"
    if value in (None, ""):
        return "—"
    text = str(value)
    if fallback_unit and not any(char.isalpha() for char in text):
        rendered = _format_number(value, decimals) if decimals is not None else text
        return f"{rendered} {fallback_unit}"
    return text


def _format_speed(value: Any) -> str:
    """Normalize Open5e speed mappings into labels such as 'Walk 30 feet'."""
    if isinstance(value, dict):
        inherited_unit = value.get("unit") or value.get("units")
        parts: list[str] = []
        for key, child in value.items():
            if key in {"unit", "units", "as_string", "text", "description"}:
                continue
            if child in (None, "", False, [], {}):
                continue
            label = str(key).replace("_", " ").title()
            parts.append(f"{label} {_format_measurement(child, inherited_unit)}")
        if parts:
            return ", ".join(parts)
        return str(value.get("as_string") or value.get("text") or "—")
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                kind = _display_name(item.get("type") or item.get("movement") or item.get("name"), "Speed")
                parts.append(f"{kind.title()} {_format_measurement(item)}")
            elif item not in (None, ""):
                parts.append(str(item))
        return ", ".join(parts) or "—"
    return str(value or "—")


def _normalize_languages(value: Any) -> list[dict[str, str]]:
    """Return language rows with a stable name and optional description."""
    if not value:
        return []
    if isinstance(value, dict):
        data = value.get("data")
        if isinstance(data, list):
            return _normalize_languages(data)
        as_string = value.get("as_string") or value.get("text")
        if as_string:
            return [{"name": part.strip(), "description": ""} for part in str(as_string).split(",") if part.strip()]
        name = _display_name(value)
        description = str(value.get("desc") or value.get("description") or "").strip()
        if description and description[-1] not in ".!?":
            description += "."
        return [{"name": name, "description": description}] if name else []
    if isinstance(value, list):
        rows: list[dict[str, str]] = []
        for item in value:
            if isinstance(item, dict):
                name = _display_name(item)
                description = item.get("desc") or item.get("description") or item.get("text") or ""
                description = str(description).strip()
                if description and description[-1] not in ".!?":
                    description += "."
                if name:
                    rows.append({"name": name, "description": description})
            elif item not in (None, ""):
                rows.append({"name": str(item), "description": ""})
        return rows
    return [{"name": part.strip(), "description": ""} for part in str(value).split(",") if part.strip()]


def _saving_throw_value(data: dict[str, Any], short: str, long: str, fallback: str) -> str:
    aliases = {short.lower(), long.lower(), long[:3].lower()}
    saves = _first(data, "saving_throws", "saves", "saving_throw_modifiers", default={})

    def modifier(value: Any) -> str | None:
        if isinstance(value, dict):
            for key in ("modifier", "value", "bonus", "total", "score"):
                if key in value:
                    result = modifier(value[key])
                    if result is not None:
                        return result
        if isinstance(value, bool) or value in (None, ""):
            return None
        try:
            return f"{int(value):+d}"
        except (TypeError, ValueError):
            text = str(value).strip()
            return text if text.startswith(("+", "-")) else text

    if isinstance(saves, dict):
        for key, value in saves.items():
            if str(key).lower() in aliases:
                return modifier(value) or fallback
    elif isinstance(saves, list):
        for item in saves:
            if not isinstance(item, dict):
                continue
            identity = item.get("ability") or item.get("stat") or item.get("name") or item.get("key")
            identity = _display_name(identity).lower()
            if identity in aliases:
                return modifier(item) or fallback
    return fallback

def _ability_score(data: dict[str, Any], short: str, long: str) -> int | None:
    """Read ability scores across Open5e v1/v2 and common homebrew shapes."""
    aliases = {short.lower(), long.lower(), long[:3].lower()}

    def scalar_score(value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, dict):
            for key in ("score", "value", "base", "total"):
                if key in value:
                    result = scalar_score(value[key])
                    if result is not None:
                        return result
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    # Classic flat shapes: {"strength": 12} or {"str": {"score": 12}}
    for key in aliases:
        if key in data:
            result = scalar_score(data[key])
            if result is not None:
                return result

    # Nested mapping shapes: {"abilities": {"strength": 12}}
    for container_key in ("abilities", "ability_scores", "stats", "attributes"):
        container = data.get(container_key)
        if isinstance(container, dict):
            for key, value in container.items():
                if str(key).lower() in aliases:
                    result = scalar_score(value)
                    if result is not None:
                        return result
        # Open5e v2/list shapes, e.g. {"ability": {"key": "str"}, "score": 12}
        if isinstance(container, list):
            for item in container:
                if not isinstance(item, dict):
                    continue
                identity = item.get("ability") or item.get("stat") or item.get("name") or item.get("key")
                if isinstance(identity, dict):
                    identity = identity.get("key") or identity.get("slug") or identity.get("name")
                if identity and str(identity).lower() in aliases:
                    result = scalar_score(item)
                    if result is not None:
                        return result

    # Last-resort recursive search for an explicitly named ability object.
    def walk(value: Any) -> int | None:
        if isinstance(value, dict):
            identity = value.get("key") or value.get("slug") or value.get("name")
            if identity and str(identity).lower() in aliases:
                result = scalar_score(value)
                if result is not None:
                    return result
            for key, child in value.items():
                if str(key).lower() in aliases:
                    result = scalar_score(child)
                    if result is not None:
                        return result
                result = walk(child)
                if result is not None:
                    return result
        elif isinstance(value, list):
            for child in value:
                result = walk(child)
                if result is not None:
                    return result
        return None

    return walk(data)


def ability_modifier(score: int | None) -> str:
    if score is None:
        return "—"
    modifier = (score - 10) // 2
    return f"{modifier:+d}"


def _normalize_skill_bonuses(value: Any) -> list[dict[str, str]]:
    """Normalize skill modifiers from mappings, wrappers, and Open5e list records."""
    if not value:
        return []
    if isinstance(value, dict):
        for wrapper in ("data", "results", "skills"):
            if isinstance(value.get(wrapper), (dict, list)):
                return _normalize_skill_bonuses(value[wrapper])
        rows = []
        for key, raw in value.items():
            if key in {"as_string", "text", "description"}:
                continue
            label = _display_name(raw.get("skill") if isinstance(raw, dict) else None) or str(key).replace("_", " ")
            modifier = _skill_modifier(raw)
            if modifier is not None:
                rows.append({"name": label.title(), "modifier": modifier})
        return sorted(rows, key=lambda row: row["name"])
    if isinstance(value, list):
        rows = []
        for item in value:
            if not isinstance(item, dict):
                continue
            identity = item.get("skill") or item.get("name") or item.get("key") or item.get("slug")
            name = _display_name(identity)
            modifier = _skill_modifier(item)
            if name and modifier is not None:
                rows.append({"name": name.title(), "modifier": modifier})
        return sorted(rows, key=lambda row: row["name"])
    return []


def _skill_modifier(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("modifier", "bonus", "value", "total", "score"):
            if key in value:
                return _skill_modifier(value[key])
        return None
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return f"{int(value):+d}"
    except (TypeError, ValueError):
        text_value = str(value).strip()
        return text_value if text_value else None


def _normalize_blocks(value: Any) -> list[dict[str, str]]:
    if not value:
        return []
    if isinstance(value, dict):
        value = [value]
    blocks: list[dict[str, str]] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("title") or "Feature")
                text_value = item.get("desc") or item.get("description") or item.get("text") or ""
                if isinstance(text_value, list):
                    text_value = "\n".join(str(part) for part in text_value)
                blocks.append({"name": name, "text": str(text_value)})
            elif item:
                blocks.append({"name": "Feature", "text": str(item)})
    elif isinstance(value, str):
        blocks.append({"name": "Feature", "text": value})
    return blocks



def _format_scalar(value: Any, default: str = "—") -> str:
    """Render a singular Open5e value without leaking nested dict syntax."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, dict):
        for key in ("value", "score", "total", "bonus", "modifier", "name", "display_name", "key"):
            if key in value and value[key] not in (None, ""):
                return _format_scalar(value[key], default)
        return default
    if isinstance(value, list):
        rendered = [_format_scalar(item, "") for item in value]
        return ", ".join(item for item in rendered if item) or default
    return str(value)


def _signed_modifier(value: Any, default: str = "—") -> str:
    if value is None or value == "":
        return default
    if isinstance(value, dict):
        for key in ("modifier", "bonus", "value", "total", "score"):
            if key in value:
                return _signed_modifier(value[key], default)
        return default
    try:
        return f"{int(value):+d}"
    except (TypeError, ValueError):
        text = str(value).strip()
        if text and text[0] not in "+-" and text.lstrip("-").isdigit():
            return f"{int(text):+d}"
        return text or default


def _normalize_named_values(value: Any) -> list[str]:
    """Flatten strings/reference objects used by resistance and immunity fields."""
    if not value:
        return []
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",")]
        return [part for part in parts if part]
    if isinstance(value, dict):
        for wrapper in ("data", "results", "items", "values"):
            if isinstance(value.get(wrapper), (dict, list)):
                return _normalize_named_values(value[wrapper])
        display = _display_name(value)
        if display:
            return [display]
        rows: list[str] = []
        for key, child in value.items():
            if key in {"as_string", "text", "description", "desc"}:
                continue
            child_values = _normalize_named_values(child)
            if child_values:
                rows.extend(child_values)
            elif child is True:
                rows.append(str(key).replace("_", " ").title())
        return rows
    if isinstance(value, list):
        rows: list[str] = []
        for child in value:
            rows.extend(_normalize_named_values(child))
        return rows
    return [str(value)]


def _resistance_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize both split and combined Open5e defense structures."""
    buckets: dict[str, list[str]] = {
        "Damage Vulnerabilities": [],
        "Damage Resistances": [],
        "Damage Immunities": [],
        "Condition Immunities": [],
    }

    def add(label: str, value: Any) -> None:
        if label not in buckets:
            return
        buckets[label].extend(_normalize_named_values(value))

    definitions = (
        ("Damage Vulnerabilities", ("damage_vulnerabilities", "vulnerabilities")),
        ("Damage Resistances", ("damage_resistances", "resistances")),
        ("Damage Immunities", ("damage_immunities", "immunities")),
        ("Condition Immunities", ("condition_immunities",)),
    )
    for label, keys in definitions:
        add(label, _first(data, *keys, default=None))

    combined = _first(data, "resistances_and_immunities", default=None)

    def classify_label(value: Any) -> str | None:
        text = _display_name(value).strip().casefold()
        if not text:
            return None
        if "vulnerab" in text:
            return "Damage Vulnerabilities"
        if "condition" in text and "immun" in text:
            return "Condition Immunities"
        if "resist" in text:
            return "Damage Resistances"
        if "immun" in text:
            return "Damage Immunities"
        return None

    def walk_combined(value: Any, inherited_label: str | None = None) -> None:
        if not value:
            return
        if isinstance(value, list):
            for child in value:
                walk_combined(child, inherited_label)
            return
        if isinstance(value, dict):
            row_label = classify_label(
                value.get("category")
                or value.get("type")
                or value.get("kind")
                or value.get("label")
                or value.get("name")
            ) or inherited_label

            handled = False
            aliases = {
                "damage_vulnerabilities": "Damage Vulnerabilities",
                "vulnerabilities": "Damage Vulnerabilities",
                "damage_resistances": "Damage Resistances",
                "resistances": "Damage Resistances",
                "damage_immunities": "Damage Immunities",
                "immunities": "Damage Immunities",
                "condition_immunities": "Condition Immunities",
            }
            for key, label in aliases.items():
                if key in value and value[key]:
                    add(label, value[key])
                    handled = True

            for wrapper in ("data", "results", "items", "values", "entries"):
                if wrapper in value and value[wrapper]:
                    walk_combined(value[wrapper], row_label)
                    handled = True

            if row_label:
                for key in ("value", "damage_type", "condition", "target", "types", "names"):
                    if key in value and value[key]:
                        add(row_label, value[key])
                        handled = True
                if not handled:
                    display = _display_name(value)
                    if display and classify_label(display) is None:
                        add(row_label, display)
            elif not handled:
                for key, child in value.items():
                    label = classify_label(key)
                    if label:
                        add(label, child)
                    elif isinstance(child, (dict, list)):
                        walk_combined(child, None)
            return
        if inherited_label:
            add(inherited_label, value)

    walk_combined(combined)

    rows: list[dict[str, Any]] = []
    for label in buckets:
        items: list[str] = []
        seen: set[str] = set()
        for item in buckets[label]:
            cleaned = str(item).strip()
            marker = cleaned.casefold()
            if cleaned and marker not in seen:
                seen.add(marker)
                items.append(cleaned.title() if cleaned.islower() else cleaned)
        if items:
            rows.append({"category": label, "items": items})
    return rows

def build_monster_card(entity: Entity) -> dict[str, Any]:
    data = entity.data_json or {}
    abilities = []
    save_modifiers = []
    for short, long in (("str", "strength"), ("dex", "dexterity"), ("con", "constitution"), ("int", "intelligence"), ("wis", "wisdom"), ("cha", "charisma")):
        score = _ability_score(data, short, long)
        base_modifier = ability_modifier(score)
        abilities.append({"label": short.upper(), "score": score if score is not None else "—", "modifier": base_modifier})
        save_modifiers.append({"label": short.upper(), "modifier": _saving_throw_value(data, short, long, base_modifier)})

    ac = _first(data, "armor_class", "ac", default="—")
    if isinstance(ac, list):
        ac = ", ".join(str(item.get("value") if isinstance(item, dict) else item) for item in ac)
    elif isinstance(ac, dict):
        ac = ac.get("value") or ac.get("base") or _display_name(ac) or str(ac)

    hp = _format_scalar(_first(data, "hit_points", "hp", default="—"))
    size = _display_name(_first(data, "size", default="Medium"), "Medium")
    creature_type = _display_name(_first(data, "type", "creature_type", default="Creature"), "Creature")
    subtype = _display_name(_first(data, "subtype"))
    alignment = _display_name(_first(data, "alignment", default="Unaligned"), "Unaligned")

    identity_badges = [
        descriptor_badge(size.title(), "size"),
        descriptor_badge(creature_type.title(), "type"),
    ]
    if subtype:
        identity_badges.append(descriptor_badge(subtype.title(), "subtype"))
    if alignment:
        identity_badges.append(descriptor_badge(alignment.title(), "alignment"))

    skills = _normalize_skill_bonuses(_first(data, "skills", "skill_bonuses", default={}))

    return {
        "identity_badges": identity_badges,
        "armor_class": ac,
        "armor_desc": _first(data, "armor_desc", "armor_description"),
        "hit_points": hp,
        "speed": _format_speed(_first(data, "speed", default="—")),
        "initiative_bonus": _signed_modifier(_first(data, "initiative_bonus", "initiative_modifier", "initiative", default=None)),
        "proficiency_bonus": _signed_modifier(_first(data, "proficiency_bonus", "proficiency", default=None)),
        "passive_perception": _format_scalar(_first(data, "passive_perception", "passive_wisdom", default=None)),
        "size": size.title(),
        "creature_type": creature_type.title(),
        "subtype": subtype.title() if subtype else "",
        "alignment": alignment.title(),
        "abilities": abilities,
        "saving_throw_modifiers": save_modifiers,
        "skill_bonuses": skills,
        "resistance_rows": _resistance_rows(data),
        "languages": _normalize_languages(_first(data, "languages", default=[])),
        "challenge_rating": _format_scalar(_first(data, "challenge_rating", "cr", default="—")),
        "xp": _format_scalar(_first(data, "xp", "experience_points", default=None)),
        "traits": _normalize_blocks(_first(data, "special_abilities", "traits", "features")),
        "actions": _normalize_blocks(_first(data, "actions")),
        "bonus_actions": _normalize_blocks(_first(data, "bonus_actions")),
        "reactions": _normalize_blocks(_first(data, "reactions")),
        "legendary_actions": _normalize_blocks(_first(data, "legendary_actions")),
        "description": _first(data, "desc", "description", default=entity.summary or ""),
    }



# v0.15 dedicated Magic Item and Species card normalization

def _rich_text(value: Any) -> str:
    """Flatten common Open5e prose wrappers without leaking Python objects."""
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n\n".join(part for part in (_rich_text(item) for item in value) if part)
    if isinstance(value, dict):
        for key in ("desc", "description", "text", "as_string", "value", "details", "content"):
            if value.get(key) not in (None, "", [], {}):
                return _rich_text(value[key])
        name = _display_name(value)
        return name.strip()
    return str(value).strip()


def _truth_label(value: Any) -> str:
    if isinstance(value, dict):
        text = _rich_text(value)
        return text or "Yes"
    if isinstance(value, bool):
        return "Required" if value else "Not required"
    if value in (None, "", False):
        return "Not required"
    text = str(value).strip()
    lowered = text.casefold()
    if lowered in {"false", "no", "none", "not required"}:
        return "Not required"
    if lowered in {"true", "yes", "required"}:
        return "Required"
    return text


def _summary_rows(*pairs: tuple[str, Any]) -> list[dict[str, str]]:
    rows=[]
    for label, value in pairs:
        if isinstance(value, dict) and "value" in value:
            rendered=str(value.get("value", ""))
            if rendered:
                rows.append({"label":label,"value":rendered,"tooltip":str(value.get("tooltip", ""))})
            continue
        rendered = _format_scalar(value, "")
        if rendered:
            rows.append({"label": label, "value": rendered, "tooltip": ""})
    return rows



# v0.22 display normalization
def _has_any_key(data: dict[str, Any], *keys: str) -> bool:
    if any(key in data for key in keys):
        return True
    for wrapper in ("weapon", "item", "equipment"):
        nested = data.get(wrapper)
        if isinstance(nested, dict) and any(key in nested for key in keys):
            return True
    return False

def _numeric_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        amount = value.get("value", value.get("amount", value.get("quantity", value.get("cost"))))
        unit = str(value.get("unit", value.get("coin", "gp"))).casefold()
        numeric = _numeric_value(amount)
        if numeric is None: return None
        return numeric * {"pp":10.0,"gp":1.0,"sp":0.1,"cp":0.01}.get(unit, 1.0)
    if isinstance(value, str):
        match = re.search(r"(-?\d+(?:\.\d+)?)\s*(pp|gp|sp|cp)?", value.strip(), re.I)
        if not match: return None
        numeric=float(match.group(1)); unit=(match.group(2) or "gp").casefold()
        return numeric * {"pp":10.0,"gp":1.0,"sp":0.1,"cp":0.01}[unit]
    return None

def _coin_number(value: float) -> str:
    if abs(value-round(value)) < 1e-9: return f"{int(round(value)):,}"
    return f"{value:,.4f}".rstrip("0").rstrip(".")

def format_cost(value: Any, *, present: bool = True) -> dict[str, str]:
    if not present: return {"value":"", "tooltip":""}
    gp=_numeric_value(value)
    if gp is None: return {"value":"Unknown", "tooltip":""}
    if gp == 0: return {"value":"0 GP", "tooltip":""}
    choices=(("PP",gp/10),("GP",gp),("SP",gp*10),("CP",gp*100))
    chosen=next(((coin,amount) for coin,amount in choices if abs(amount-round(amount))<1e-9 and amount>=1), choices[-1])
    tooltip="\n".join(f"{_coin_number(amount)} {coin}" for coin,amount in choices)
    return {"value":f"{_coin_number(chosen[1])} {chosen[0]}", "tooltip":tooltip}

def format_weight(value: Any, *, present: bool = True) -> str:
    if not present: return ""
    numeric=_numeric_value(value)
    if numeric is None: return "Unknown"
    return f"{numeric:.1f} lb."

def _normalize_weapon_properties(value: Any) -> list[dict[str, str]]:
    if isinstance(value, dict):
        for wrapper in ("data","results","items","properties"):
            if isinstance(value.get(wrapper), list): return _normalize_weapon_properties(value[wrapper])
        value=[value]
    if not isinstance(value, list):
        return [{"name":name.title(),"description":"","range":"","url":""} for name in _normalize_named_values(value)]
    rows=[]
    for item in value:
        if isinstance(item, str):
            rows.append({"name":item.title(),"description":"","range":"","url":""}); continue
        if not isinstance(item, dict): continue
        name=_display_name(item.get("name") or item.get("property") or item.get("key"))
        description=_rich_text(item.get("desc") or item.get("description") or item.get("text"))
        range_text=_format_weapon_range(item.get("range") or item.get("normal_range"), item.get("long_range"))
        url=str(item.get("permalink") or item.get("url") or item.get("link") or "")
        if name: rows.append({"name":name.title(),"description":description,"range":range_text,"url":url})
    return rows

def build_magic_item_card(entity: Entity) -> dict[str, Any]:
    data = entity.data_json or {}
    rarity = _display_name(_first(data, "rarity", "item_rarity", default=""))
    category = _display_name(_first(data, "type", "item_type", "category", "magic_item_type", default="Magic Item"), "Magic Item")
    subtype = _display_name(_first(data, "subtype", "item_subtype", "equipment_category", default=""))
    attunement_raw = _first(data, "requires_attunement", "attunement", "attunement_required", default=None)
    attunement = _truth_label(attunement_raw)
    badges=[]
    if rarity: badges.append(descriptor_badge(rarity.title(), "rarity"))
    if category: badges.append(descriptor_badge(category.title(), "item-type"))
    if subtype and subtype.casefold()!=category.casefold(): badges.append(descriptor_badge(subtype.title(), "subtype"))
    if attunement != "Not required": badges.append(descriptor_badge("Attunement", "attunement"))

    charges = _first(data, "charges", "maximum_charges", "max_charges", default=None)
    recharge = _rich_text(_first(data, "recharge", "charge_recovery", "recharge_description", default=None))
    value = _first(data, "cost", "value", "price", default=None)
    weight = _first(data, "weight", default=None)
    armor = _first(data, "armor", default={})
    armor_class = ""
    if isinstance(armor, dict):
        armor_class = _rich_text(armor.get("ac_display") or armor.get("armor_class") or armor.get("ac"))
    armor_class = armor_class or _rich_text(_first(data, "ac_display", "armor_class", "ac", default=None))

    properties = _normalize_blocks(_first(data, "properties", "traits", "features", "effects", default=[]))
    curses = _normalize_blocks(_first(data, "curses", "curse", default=[]))
    variants = _normalize_blocks(_first(data, "variants", "options", default=[]))
    description = _rich_text(_first(data, "desc", "description", "text", default=entity.summary or ""))

    return {
        "identity_badges": badges,
        "rarity": rarity.title() if rarity else "—",
        "item_type": category.title(),
        "subtype": subtype.title() if subtype else "",
        "attunement": attunement,
        "cost": format_cost(value, present=_has_any_key(data, "cost", "value", "price")),
        "weight": format_weight(weight, present=_has_any_key(data, "weight")),
        "armor_class": armor_class,
        "charges": _format_scalar(charges, "—"),
        "recharge": recharge,
        "summary_rows": _summary_rows(
            ("Rarity", rarity.title() if rarity else None),
            ("Item Type", category.title()),
            ("Subtype", subtype.title() if subtype else None),
            ("Attunement", attunement),
            ("Cost", format_cost(value, present=_has_any_key(data, "cost", "value", "price"))),
            ("Weight", format_weight(weight, present=_has_any_key(data, "weight"))),
            ("Armor Class", armor_class or None),
            ("Charges", charges),
            ("Recharge", recharge),
        ),
        "description": description,
        "properties": properties,
        "curses": curses,
        "variants": variants,
    }


def _ability_bonus_rows(value: Any) -> list[dict[str, str]]:
    rows=[]
    if isinstance(value, dict):
        for wrapper in ("data", "results", "items", "bonuses"):
            if isinstance(value.get(wrapper), (dict,list)):
                return _ability_bonus_rows(value[wrapper])
        for key, raw in value.items():
            if key in {"as_string", "text", "description"}: continue
            name=_display_name(raw.get("ability") if isinstance(raw,dict) else None) or str(key).replace("_"," ")
            amount=_signed_modifier(raw, "")
            if amount: rows.append({"name":name.title(),"value":amount})
    elif isinstance(value,list):
        for item in value:
            if not isinstance(item,dict): continue
            name=_display_name(item.get("ability") or item.get("name") or item.get("key"))
            amount=_signed_modifier(item, "")
            if name and amount: rows.append({"name":name.title(),"value":amount})
    return rows


def build_species_card(entity: Entity) -> dict[str, Any]:
    data=entity.data_json or {}
    size_raw=_first(data,"size","sizes",default=None)
    sizes=_normalize_named_values(size_raw)
    creature_type=_display_name(_first(data,"type","creature_type",default="Humanoid"),"Humanoid")
    subtype=_display_name(_first(data,"subtype","lineage","heritage",default=""))
    speed=_format_speed(_first(data,"speed","movement",default="—"))
    darkvision=_format_measurement(_first(data,"darkvision","darkvision_range",default=None),"feet")
    languages=_normalize_languages(_first(data,"languages",default=[]))
    ability_bonuses=_ability_bonus_rows(_first(data,"ability_score_increases","ability_scores","ability_bonuses","asi",default=[]))
    badges=[]
    for size in sizes[:3]: badges.append(descriptor_badge(size.title(),"size"))
    if creature_type: badges.append(descriptor_badge(creature_type.title(),"type"))
    if subtype: badges.append(descriptor_badge(subtype.title(),"subtype"))
    traits=_normalize_blocks(_first(data,"traits","features","species_traits","racial_traits",default=[]))
    lineages=_normalize_blocks(_first(data,"subraces","lineages","heritages","variants",default=[]))
    description=_rich_text(_first(data,"desc","description","text",default=entity.summary or ""))
    age=_rich_text(_first(data,"age",default=None))
    alignment=_rich_text(_first(data,"alignment",default=None))
    names=_rich_text(_first(data,"names","naming",default=None))
    return {
        "identity_badges":badges,
        "sizes":sizes,
        "creature_type":creature_type.title(),
        "subtype":subtype.title() if subtype else "",
        "speed":speed,
        "darkvision":darkvision if darkvision!="—" else "",
        "languages":languages,
        "ability_bonuses":ability_bonuses,
        "summary_rows":_summary_rows(
            ("Creature Type",creature_type.title()),
            ("Size",", ".join(sizes) if sizes else None),
            ("Darkvision",darkvision if darkvision!="—" else None),
        ),
        "description":description,
        "age":age,
        "alignment":alignment,
        "names":names,
        "traits":traits,
        "lineages":lineages,
    }


# v0.16 dedicated mundane Item card normalization
def build_item_card(entity: Entity) -> dict[str, Any]:
    data = entity.data_json or {}
    category = _display_name(_first(data, "category", "item_category", "type", "equipment_category", default="Item"), "Item")
    subtype = _display_name(_first(data, "subtype", "item_subtype", "weapon_category", "armor_category", default=""))
    cost = _first(data, "cost", "price", "value", default=None)
    weight = _first(data, "weight", default=None)
    quantity = _first(data, "quantity", "bundle_size", default=None)
    damage = _rich_text(_first(data, "damage", "damage_dice", default=None))
    damage_type = _display_name(_first(data, "damage_type", default=""))
    armor = _first(data, "armor", default={})
    armor_class = ""
    if isinstance(armor, dict):
        armor_class = _rich_text(armor.get("ac_display") or armor.get("armor_class") or armor.get("ac"))
    armor_class = armor_class or _rich_text(_first(data, "ac_display", "armor_class", "ac", default=None))
    properties = _normalize_named_values(_first(data, "properties", "weapon_properties", "tags", default=[]))
    badges = [descriptor_badge(category.title(), "item-type")]
    if subtype and subtype.casefold() != category.casefold():
        badges.append(descriptor_badge(subtype.title(), "subtype"))
    description = _rich_text(_first(data, "desc", "description", "text", default=entity.summary or ""))
    details = _normalize_blocks(_first(data, "traits", "features", "effects", "special", default=[]))
    return {
        "identity_badges": badges,
        "category": category.title(),
        "subtype": subtype.title() if subtype else "",
        "cost": format_cost(cost, present=_has_any_key(data, "cost", "price", "value")),
        "weight": format_weight(weight, present=_has_any_key(data, "weight")),
        "armor_class": armor_class,
        "properties": properties,
        "summary_rows": _summary_rows(
            ("Item Type", category.title()),
            ("Subtype", subtype.title() if subtype else None),
            ("Cost", format_cost(cost, present=_has_any_key(data, "cost", "price", "value"))),
            ("Weight", format_weight(weight, present=_has_any_key(data, "weight"))),
            ("Armor Class", armor_class or None),
            ("Damage", f"{damage} {damage_type}".strip() if damage or damage_type else None),
            ("Quantity", quantity),
        ),
        "description": description,
        "details": details,
    }


# v0.18 dedicated Weapon card normalization

def _weapon_value(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Read weapon fields from top-level or a nested ``weapon`` object."""
    value = _first(data, *keys, default=None)
    if value not in (None, "", [], {}):
        return value
    nested = data.get("weapon")
    if isinstance(nested, dict):
        return _first(nested, *keys, default=default)
    return default


def _format_weapon_range(value: Any, long_value: Any = None) -> str:
    if isinstance(value, dict):
        normal = value.get("normal") or value.get("value") or value.get("short") or value.get("range")
        long_range = value.get("long") or value.get("long_range") or value.get("maximum")
        unit = value.get("unit") or value.get("units") or "feet"
        if normal not in (None, "") and long_range not in (None, ""):
            return f"{normal}/{long_range} {unit}"
        if normal not in (None, ""):
            return f"{normal} {unit}"
        rendered = _rich_text(value)
        return rendered
    if value not in (None, "") and long_value not in (None, ""):
        return f"{value}/{long_value} feet"
    if value not in (None, ""):
        text = str(value).strip()
        return text if any(ch.isalpha() for ch in text) else f"{text} feet"
    return ""


def _format_weapon_damage(value: Any, damage_type: Any = None) -> str:
    if isinstance(value, dict):
        dice = value.get("dice") or value.get("damage_dice") or value.get("value") or value.get("amount")
        dtype = _display_name(value.get("type") or value.get("damage_type"))
        if dice or dtype:
            return " ".join(part for part in (str(dice).strip() if dice else "", dtype.title() if dtype else "") if part)
        return _rich_text(value)
    dice = _rich_text(value)
    dtype = _display_name(damage_type)
    return " ".join(part for part in (dice, dtype.title() if dtype else "") if part)


def build_weapon_card(entity: Entity) -> dict[str, Any]:
    data = entity.data_json or {}
    category = _display_name(_weapon_value(data, "category", "weapon_category", "type", default="Weapon"), "Weapon")
    weapon_range = _display_name(_weapon_value(data, "weapon_range", "range_type", "classification", default=""))
    damage_type = _display_name(_weapon_value(data, "damage_type", default=""))
    damage = _format_weapon_damage(
        _weapon_value(data, "damage", "damage_dice", "damage_die", default=None),
        damage_type,
    )
    versatile = _format_weapon_damage(
        _weapon_value(data, "versatile_damage", "two_handed_damage", "damage_two_handed", default=None),
        damage_type,
    )
    normal_range = _weapon_value(data, "range", "normal_range", "short_range", default=None)
    long_range = _weapon_value(data, "long_range", "maximum_range", default=None)
    range_text = _format_weapon_range(normal_range, long_range)
    reach = _weapon_value(data, "reach", default=None)
    if reach not in (None, ""):
        reach_text = _format_weapon_range(reach)
    else:
        reach_text = ""
    cost = _weapon_value(data, "cost", "price", "value", default=None)
    weight = _weapon_value(data, "weight", default=None)
    properties = _normalize_weapon_properties(_weapon_value(data, "properties", "weapon_properties", "property", "tags", default=[]))
    mastery = _display_name(_weapon_value(data, "mastery", "mastery_property", "weapon_mastery", default=""))
    ammunition = _rich_text(_weapon_value(data, "ammunition", "ammo", "ammunition_type", default=None))
    loading = _weapon_value(data, "loading", default=None)
    description = _rich_text(_weapon_value(data, "desc", "description", "text", default=entity.summary or ""))
    special = _normalize_blocks(_weapon_value(data, "special", "special_rules", "traits", "features", "effects", default=[]))

    badges = [descriptor_badge(category.title(), "weapon-category")]
    if weapon_range and weapon_range.casefold() != category.casefold():
        badges.append(descriptor_badge(weapon_range.title(), "weapon-range"))
    if damage_type:
        badges.append(descriptor_badge(damage_type.title(), "damage-type"))
    if mastery:
        badges.append(descriptor_badge(mastery.title(), "mastery"))

    primary_stats = [
        {"label": "Damage", "value": damage or "—", "kind": "damage"},
        {"label": "Cost", **format_cost(cost, present=_has_any_key(data, "cost", "price", "value")), "kind": "cost"},
        {"label": "Weight", "value": format_weight(weight, present=_has_any_key(data, "weight")), "tooltip": "", "kind": "weight"},
    ]
    summary_rows = _summary_rows(
        ("Category", category.title()),
        ("Range Type", weapon_range.title() if weapon_range else None),
        ("Damage Type", damage_type.title() if damage_type else None),
        ("Range", range_text or None),
        ("Reach", reach_text or None),
        ("Versatile Damage", versatile or None),
        ("Mastery", mastery.title() if mastery else None),
        ("Ammunition", ammunition or None),
        ("Loading", _truth_label(loading) if loading not in (None, "", False) else None),
    )
    return {
        "identity_badges": badges,
        "primary_stats": primary_stats,
        "summary_rows": summary_rows,
        "properties": properties,
        "mastery": mastery.title() if mastery else "",
        "description": description,
        "special": special,
    }
