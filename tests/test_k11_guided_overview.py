"""K-11 usability: guided overview, task isolation and preserved capabilities."""
from __future__ import annotations

import re

import pytest

from tof_cli.ui import app


def test_navigation_uses_clear_entry_and_same_four_existing_features():
    overview = app._render_page("/")
    nav = overview.split('<nav class="page-nav"', 1)[1].split('</nav>', 1)[0]
    assert nav.count('<a href=') == 5
    assert 'aria-current="page" data-page-link="overview"' in nav
    for route in ("/uebersicht", "/frage-stellen", "/dokumente-durchsuchen",
                  "/quellen-index", "/beleg-pruefen"):
        assert f'href="{route}"' in nav
    assert "http://127.0.0.1:8785" not in nav


def test_overview_shows_readable_steps_and_only_readonly_status():
    html = app._render_page("/")
    assert 'data-i18n="overviewTitle"' in html
    assert 'id="overview-status-title"' in html
    assert 'id="overview-status-detail"' in html
    assert html.count('class="guide-card"') == 4
    assert '/api/sources' in html  # existing read-only catalog query
    assert "await refreshOverview()" in html
    assert 'id="index-batch-button"' not in html
    assert 'id="qa-question"' not in html
    assert 'id="search-query"' not in html


@pytest.mark.parametrize(("route", "advanced", "feature"), [
    ("/frage-stellen", "optionalFilters", 'id="qa-question"'),
    ("/dokumente-durchsuchen", "optionalFilters", 'id="search-query"'),
    ("/quellen-index", "manualIndexOptions", 'id="source-result"'),
])
def test_task_pages_show_primary_action_and_hide_advanced_settings_by_default(
    route, advanced, feature
):
    html = app._render_page(route)
    assert feature in html
    assert 'class="page-intro"' in html
    assert f'<summary data-i18n="{advanced}">' in html
    assert ('<details class="advanced-options">' in html or
            '<details class="advanced-options" id="index-advanced">' in html)
    assert '<details class="advanced-options" open' not in html
    assert 'id="log"' in html  # original technical panel kept
    if route == "/quellen-index":
        assert html.index('id="source-result"') < html.index('id="index-batch-button"')


def test_evidence_page_explains_how_to_get_there():
    html = app._render_page("/beleg-pruefen")
    assert 'data-i18n="evidenceGuide"' in html
    assert 'data-i18n="findEvidence"' in html
    assert 'href="/dokumente-durchsuchen"' in html
    assert "if (segmentId) inspectEvidence(segmentId)" in html


def test_localized_ux_strings_complete_on_all_pages():
    src = app.HTML
    catalog_de = src.split("      de: {", 1)[1].split("\n      },", 1)[0]
    catalog_en = src.split("      en: {", 1)[1].split("\n      },", 1)[0]
    def keys(text):
        return set(re.findall(r"^        (\w+): ", text, re.MULTILINE))
    assert keys(catalog_de) == keys(catalog_en)
    needed = {"navOverview", "overviewTitle", "overviewReady", "overviewEmpty",
              "overviewUnavailable", "overviewManageSources", "questionGuide",
              "searchGuide", "sourcesGuide", "evidenceGuide", "optionalFilters",
              "manualIndexOptions", "backOverview", "backSearch"}
    assert needed <= keys(catalog_de)
    assert 'lastOverviewData = response.ok ? data' in src
    assert "Number(source.indexed || 0)" in src


def test_existing_api_paths_and_local_port_unchanged():
    assert "/api/index-batch" in app.HTML
    assert "/api/answer" in app.HTML
    assert "/api/search" in app.HTML
    assert app.run_ui.__defaults__[:2] == ("127.0.0.1", 8785)
