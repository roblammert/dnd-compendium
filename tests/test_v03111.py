from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_v03111_version_marker_was_present_in_release_history():
    assert '## v0.31.11' in (ROOT / 'RELEASE_NOTES.md').read_text()

def test_reopening_character_defaults_to_identity():
    routes=(ROOT/'app/character_routes.py').read_text()
    assert 'active = step if step in STEP_KEYS else "identity"' in routes
    assert 'row.current_step if row.current_step in STEP_KEYS' not in routes

def test_non_review_changes_invalidate_completion():
    routes=(ROOT/'app/character_routes.py').read_text()
    assert 'def _completion_fingerprint' in routes
    assert 'if step != "review" and _completion_fingerprint(row) != completion_before:' in routes
    assert 'row.is_complete = False' in routes

def test_review_page_is_simplified_and_completion_is_contained():
    html=(ROOT/'app/templates/character_steps/review.html').read_text()
    assert '<h3>Combat</h3>' not in html
    assert '<h3>Features &amp; Feats</h3>' not in html
    assert 'review-completion-panel' in html
    assert 'Mark character as complete' in html
    assert 'review-summary-grid' in html

def test_review_layout_has_responsive_guards():
    css=(ROOT/'app/static/css/app.css').read_text()
    assert '.review-summary-grid{display:grid' in css
    assert '.review-completion-panel{display:flex' in css
    assert '@media(max-width:760px)' in css
