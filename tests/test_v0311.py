from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.character_rules_2024 import RULESET_SOURCE_KEY, RULESET_GAME_SYSTEM_KEY
from app.character_routes import _enforce_2024_rules
from app.character_services import entities_for_character, class_hit_die, class_save_proficiencies, class_skill_choice_count
from app.db import Base
from app.models import Character, Entity, User


def entity(pid, source, system, entity_type="class", name="Fighter", key="fighter", data=None):
    return Entity(public_id=pid, entity_type=entity_type, name=name, slug=key, canonical_key=key,
        source_kind="open5e", source_document=source, source_display_name=source,
        game_system_key=system, game_system_name=system, data_json=data or {})


def test_character_rules_are_forced_to_2024_and_old_choices_are_cleared():
    char = Character(public_id="chr_lock", user_id=1, name="Legacy", source_document="srd-2014",
        game_system_key="5e-2014", species_key="dwarf", class_key="fighter",
        selected_spells=["x"], selected_equipment=["y"], feats=["z"], ability_scores={})
    assert _enforce_2024_rules(char) is True
    assert char.source_document == RULESET_SOURCE_KEY
    assert char.game_system_key == RULESET_GAME_SYSTEM_KEY
    assert char.species_key is None and char.class_key is None
    assert char.selected_spells == [] and char.selected_equipment == [] and char.feats == []


def test_character_entity_queries_never_fall_back_to_2014():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(public_id="usr_lock", username="lock", display_name="Lock", password_hash="x", role="user")
        db.add(user); db.flush()
        db.add_all([
            entity("ent14", "srd-2014", "5e-2014"),
            entity("ent24", "srd-2024", "5e-2024"),
        ])
        char = Character(public_id="chr_q", user_id=user.id, name="Q", source_document="srd-2024", game_system_key="5e-2024", ability_scores={})
        db.add(char); db.commit()
        rows = entities_for_character(db, ["class"], char)
        assert [r.public_id for r in rows] == ["ent24"]


def test_builtin_2024_class_rules_fill_missing_open5e_fields():
    fighter = entity("f", "srd-2024", "5e-2024", data={})
    assert class_hit_die(fighter) == 10
    assert class_save_proficiencies(fighter) == ["str", "con"]
    assert class_skill_choice_count(fighter) == 2


def test_identity_step_has_no_source_selector():
    root = Path(__file__).parents[1]
    identity = (root / "app/templates/character_steps/identity.html").read_text()
    routes = (root / "app/character_routes.py").read_text()
    assert 'name="source_document"' not in identity
    assert "D&amp;D 2024 fifth-edition rules" in identity
    assert "source_document=RULESET_SOURCE_KEY" in routes
