from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "app/static/css/app.css").read_text()
REVIEW = (ROOT / "app/templates/character_steps/review.html").read_text()


def test_review_ability_rows_keep_modifier_inline():
    assert ".review-ability-row{grid-template-columns:auto 1fr auto" in CSS
    assert ".review-ability-row strong{justify-self:end" in CSS
    assert ".review-ability-row span{justify-self:end" in CSS


def test_completion_checkbox_is_compact_and_inside_status_panel():
    assert "review-completion-panel" in REVIEW
    assert "complete-toggle" in REVIEW
    assert ".review-completion-panel .complete-toggle input[type=checkbox]" in CSS
    assert "width:1rem!important" in CSS
    assert "max-width:260px" in CSS
