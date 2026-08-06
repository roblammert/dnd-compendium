from types import SimpleNamespace

from app.services import (
    build_alignment_card,
    build_background_card,
    build_class_card,
    build_condition_card,
    build_creature_type_card,
    build_damage_type_card,
    build_feat_card,
    build_game_system_card,
    build_item_card,
)


def entity(entity_type, data, name="Example"):
    return SimpleNamespace(entity_type=entity_type, data_json=data, summary="", name=name)


def labels(card):
    return {row["label"]: row["value"] for row in card["summary_rows"]}


def test_alignment_card_uses_axes_and_versioned_descriptions_only():
    card = build_alignment_card(entity("alignment", {
        "morality": "evil",
        "societal_attitude": "chaotic",
        "descriptions": [
            {"gamesystem": "5e-2014", "desc": "First description."},
            {"gamesystem": "5e-2024", "desc": "Second description."},
        ],
        "document": {"name": "Ignored document"},
        "key": "chaotic-evil",
    }, "Chaotic Evil"))
    assert labels(card) == {"Morality": "Evil", "Societal Attitude": "Chaotic"}
    assert [row["game_system"] for row in card["description_entries"]] == ["5e-2014", "5e-2024"]
    assert "Ignored document" not in str(card)


def test_background_and_feat_benefits_are_structured():
    data = {"benefits": [{"name": "Contacts", "desc": "You know useful people.", "detail": "+1"}]}
    background = build_background_card(entity("background", data))
    feat = build_feat_card(entity("feat", data))
    for card in (background, feat):
        assert card["detail_blocks_title"] == "Benefits"
        assert card["detail_blocks"][0] == {"name": "Contacts", "detail": "+1", "text": "You know useful people."}


def test_class_features_are_structured_after_description():
    card = build_class_card(entity("classe", {
        "description": "Class description.",
        "features": [{"name": "Second Wind", "desc": "Recover hit points.", "detail": "1/Rest"}],
    }))
    assert card["description"] == "Class description."
    assert card["detail_blocks_title"] == "Class Features"
    assert card["detail_blocks"][0]["name"] == "Second Wind"


def test_versioned_reference_cards_remove_key_box():
    payload = {"key": "example", "descriptions": [{"gamesystem": "5e-2024", "desc": "Description."}]}
    for builder, endpoint in (
        (build_condition_card, "condition"),
        (build_creature_type_card, "creaturetype"),
        (build_damage_type_card, "damagetype"),
    ):
        card = builder(entity(endpoint, payload))
        assert not any(row["label"] == "Key" for row in card["summary_rows"])
        assert card["description_entries"][0]["text"] == "Description."


def test_game_system_removes_key_and_item_adds_size():
    game = build_game_system_card(entity("gamesystem", {"key": "5e", "version": "2024"}))
    assert not any(row["label"] == "Key" for row in game["summary_rows"])
    item = build_item_card(entity("item", {"category": "gear", "size": {"name": "Large"}}))
    assert labels(item)["Size"] == "Large"
