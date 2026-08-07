from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.character_services import point_buy_total, proficiency_bonus, derive_character
from app.db import Base
from app.models import Character, Entity, User


def _entity(pid, entity_type, name, key, data):
    return Entity(
        public_id=pid, entity_type=entity_type, name=name, slug=key, canonical_key=key,
        source_kind="open5e", source_document="srd-2024", source_display_name="5e 2024 Rules",
        game_system_key="5e-2024", game_system_name="5th Edition 2024", data_json=data,
    )


def test_v031_level_proficiency_formula():
    assert [proficiency_bonus(level) for level in (1, 4, 5, 8, 9, 12, 13, 16, 17, 20)] == [2,2,3,3,4,4,5,5,6,6]


def test_v031_standard_array_is_27_point_buy():
    scores = dict(zip(("str","dex","con","int","wis","cha"), (15,14,13,12,10,8)))
    assert point_buy_total(scores) == 27


def test_v031_derivation_uses_class_species_and_equipment():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(public_id="usr_test", username="hero", display_name="Hero", password_hash="x", role="user")
        species = _entity("ent_species", "species", "Dwarf", "dwarf", {"speed": 25, "ability_score_increases": [{"ability":"Constitution","bonus":2}]})
        cls = _entity("ent_class", "class", "Fighter", "fighter", {"hit_die":"d10", "saving_throws":["Strength","Constitution"]})
        armor = _entity("ent_armor", "armor", "Chain Mail", "chain-mail", {"category":"Heavy Armor", "base_ac":16, "strength_requirement":13, "stealth_disadvantage":True})
        weapon = _entity("ent_weapon", "weapon", "Longsword", "longsword", {"damage_dice":"1d8", "damage_type":{"name":"Slashing"}, "properties":[]})
        db.add_all([user,species,cls,armor,weapon]); db.flush()
        char = Character(public_id="chr_test", user_id=user.id, name="Arden", source_document="srd-2024", game_system_key="5e-2024", level=1, species_key="dwarf", class_key="fighter", ability_scores={"str":15,"dex":12,"con":14,"int":10,"wis":10,"cha":8}, selected_equipment=[armor.public_id, weapon.public_id], skill_proficiencies=["Athletics"], save_proficiencies=[], currency={})
        db.add(char); db.commit()
        result = derive_character(db, char)
        assert result["scores"]["con"] == 14
        assert result["hp_max"] == 12
        assert result["armor_class"] == 16
        assert result["speed"] == 25
        assert result["stealth_disadvantage"] is True
        assert result["attacks"][0]["attack_bonus"] == 4
        assert next(row for row in result["skills"] if row["name"] == "Athletics")["modifier"] == 4


def test_v031_character_builder_navigation_and_pdf_template_present():
    root = Path(__file__).parents[1]
    tools_layout = (root / "app/templates/tools_layout.html").read_text()
    print_template = (root / "app/templates/character_print.html").read_text()
    routes = (root / "app/character_routes.py").read_text()
    assert 'href="/tools/character-builder"' in tools_layout
    assert print_template.count('class="print-page') >= 3
    assert "Attacks & Spellcasting" in print_template
    assert "Character Backstory" in print_template
    assert "Save DC" in print_template
    assert '@router.get("/{public_id}/pdf")' in routes
    assert "Depends(require_user)" in routes
