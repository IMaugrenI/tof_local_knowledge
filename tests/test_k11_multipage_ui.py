"""K-11: independent Knowledge navigation pages without a new web runtime."""
from __future__ import annotations

import pytest

from tof_cli.ui import app


PAGES = {
    "/uebersicht": ("overview", 'id="overview-status-title"'),
    "/frage-stellen": ("question", 'id="qa-question"'),
    "/dokumente-durchsuchen": ("search", 'id="search-query"'),
    "/beleg-pruefen": ("evidence", 'id="evidence-result"'),
    "/quellen-index": ("sources", 'id="source-result"'),
}


@pytest.mark.parametrize(("path", "page", "feature"), [
    (route, label, field) for route, (label, field) in PAGES.items()
])
def test_each_browser_route_has_one_active_page_and_only_its_feature(path, page, feature):
    html = app._render_page(path)
    assert '<nav class="page-nav"' in html
    nav = html.split('<nav class="page-nav"', 1)[1].split("</nav>", 1)[0]
    assert nav.count('aria-current="page"') == 1
    assert f'aria-current="page" data-page-link="{page}"' in html
    assert feature in html
    assert 'class="tech-panel"' in html  # Original start/status controls retained.
    assert 'id="log"' in html
    for other_route, (other_page, other_feature) in PAGES.items():
        assert f'href="{other_route}"' in html
        if other_page != page:
            assert other_feature not in html
    assert '<!-- PAGE_START:' not in html
    assert '<!-- PAGE_END:' not in html


def test_old_root_url_becomes_guided_overview_without_losing_question_route():
    assert app._render_page("/") == app._render_page("/uebersicht")
    assert 'id="qa-question"' in app._render_page("/frage-stellen")
    assert 'id="qa-question"' not in app._render_page("/")


def test_unknown_route_is_not_served_as_a_valid_page():
    with pytest.raises(KeyError):
        app._render_page("/missing")
    assert "/api/search" not in app.PAGE_ROUTES
    assert "/api/index-batch" not in app.PAGE_ROUTES


def test_evidence_buttons_open_deep_link_and_source_selection_opens_search():
    script = app.HTML
    assert "window.location.assign('/beleg-pruefen?segment_id=' +" in script
    assert "encodeURIComponent(segmentId)" in script
    assert "if (segmentId) inspectEvidence(segmentId)" in script
    assert "window.location.assign('/dokumente-durchsuchen?source_id=' +" in script
    assert "encodeURIComponent(source.source_id)" in script
    assert "if (scope) scope.value = sourceId" in script
    assert "if (document.getElementById('source-result'))" in script
    # Old cross-page assumptions would throw now that pages have separate DOMs.
    assert "document.getElementById('search-scope').value = data.source_id" not in script
    assert "document.getElementById('qa-scope').value = data.source_id" not in script


def test_navigation_has_existing_locale_theme_and_responsive_layout():
    html = app._render_page("/quellen-index")
    assert "navSources: 'Quellen & Index'" in html
    assert "navEvidence: 'Beleg prüfen'" in html
    assert "navSearch: 'Dokumente durchsuchen'" in html
    assert "navAsk: 'Frage stellen'" in html
    assert "navSources: 'Sources & Index'" in html
    assert 'page-nav a[aria-current="page"]' in html
    assert ".page-nav { padding: 7px; gap: 5px; }" in html
    assert 'id="language-toggle"' in html
    assert 'id="theme-toggle"' in html
