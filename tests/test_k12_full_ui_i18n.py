"""K-12: full DE/EN localization of the existing multipage browser surface."""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from tof_cli.ui import app


def _catalog(source: str, locale: str) -> dict[str, str]:
    part = source.split("      " + locale + ": {", 1)[1].split("\n      },", 1)[0]
    return dict(re.findall(r"^        ([A-Za-z][A-Za-z0-9_]*): '([^']*)',?$", part, re.M))


def test_all_static_visible_and_accessible_keys_exist_in_both_languages():
    de = _catalog(app.HTML, "de")
    en = _catalog(app.HTML, "en")
    assert de.keys() == en.keys()
    assert len(de) >= 140
    assert all(value.strip() for value in de.values())
    assert all(value.strip() for value in en.values())
    marked = set(re.findall(r'data-i18n(?:-placeholder|-aria-label)?="([^"]+)"', app.HTML))
    assert marked.issubset(de)
    assert {"refreshSourceFolders", "qaLimitLabel", "searchLimitLabel",
            "navigationLabel", "evidenceStatus", "readOnlyExcerpt",
            "disabledLabel", "scannedLabel", "failedCountLabel"}.issubset(marked | set(de))


@pytest.mark.parametrize("route", [
    "/", "/frage-stellen", "/dokumente-durchsuchen",
    "/beleg-pruefen", "/quellen-index",
])
def test_each_page_keeps_language_theme_and_translatable_controls(route):
    html = app._render_page(route)
    assert 'id="language-toggle"' in html
    assert 'id="theme-toggle"' in html
    assert 'data-i18n-aria-label="navigationLabel"' in html
    assert 'navSources: \'Quellen & Index\'' in html
    assert 'navSources: \'Sources & Index\'' in html
    assert "element.setAttribute('aria-label', t(element.dataset.i18nAriaLabel))" in html
    assert "document.documentElement.lang = currentLanguage" in html


def test_small_labels_and_backend_status_texts_are_localized():
    text = app.HTML
    assert 'Refresh source folders</button>' not in text
    assert 'Quellenordner aktualisieren / Refresh source folders' not in text
    assert "t('readOnlyExcerpt')" in text and "t('characters')" in text
    assert "t('segmentLabel')" in text
    assert "t('disabledLabel')" in text
    assert "t('scannedLabel')" in text and "t('failedCountLabel')" in text
    assert "t('sourceDefaultLabel')" in text
    assert "translatedCode('uncertainty', code)" in text
    assert "translatedCode('searchStrategy', signal.search_strategy)" in text
    assert "translatedCode('status', signal.status)" in text
    assert "lastAnswerData = data" in text and "lastSearchData = data" in text
    assert "lastIndexData = { data, failed }" in text


@pytest.mark.skipif(not shutil.which("node"), reason="Node runtime not available")
def test_real_ui_javascript_switches_existing_qa_result_and_source_texts():
    """Execute the JS supplied to the browser with minimal built-in stubs.

    Source passages are not translated: only UI labels and the QA-owned
    German boilerplate are localized.
    """
    script = app.HTML.split("<script>", 1)[1].split("</script>", 1)[0]
    harness = r"""
const vm = require('vm');
const fs = require('fs');
const source = fs.readFileSync(0, 'utf8');
const elements = {};
for (const id of ['log', 'language-toggle', 'theme-toggle', 'next-step', 'qa-result']) {
  elements[id] = {
    textContent: '', innerHTML: '',
    querySelectorAll: () => [],
  };
}
const document = {
  documentElement: {lang: 'de'},
  body: {classList: {toggle: () => {}}},
  title: '',
  querySelectorAll: () => [],
  querySelector: () => ({textContent: 'Frage stellen'}),
  getElementById: (id) => elements[id] || null,
};
const storage = {getItem: () => 'de', setItem: () => {}};
const ctx = vm.createContext({
  document, localStorage: storage, fetch: async () => ({}),
  URLSearchParams, window: {location: {pathname: '/frage-stellen'}},
});
vm.runInContext(source, ctx, {timeout: 1500});
const answer = {
  answer_text: 'Belegbasierte Kurzantwort (Quellenauszüge, keine unabhängige Verifikation):' +
    '\\nStärkster Treffer aus company_handbook.md: Vacation requests are due two weeks early.' +
    '\\n\\nVerwendete Fundstellen:...',
  citations: ['demo:seg-1'], evidence_refs: [], used_documents: [],
  uncertainties: ['confidence_uncalibrated', 'limited_independent_sources'],
  evidence_signal: {status: 'single_document_matches', search_strategy: 'keywords',
                    matching_segments: 1, distinct_documents: 1},
  confidence: 0.45,
};
vm.runInContext('renderAnswerResult(answer)', vm.createContext({...ctx, answer}));
const before = elements['qa-result'].innerHTML;
vm.runInContext('toggleLanguage()', ctx);
const after = elements['qa-result'].innerHTML;
const negative = vm.runInContext(
  "localizeAnswerText('Keine belastbare Antwort gefunden. Eine breite Stichwortsuche lieferte nur ungeprüfte Treffer, keine ausreichenden Antwortbelege.')",
  ctx
);
const result = {
  beforeDe: before.includes('Belegbasierte Kurzantwort'),
  afterEn: after.includes('Evidence-based excerpt answer'),
  englishEvidenceStatus: after.includes('Evidence status'),
  englishUncertainty: after.includes('Limited independent sources'),
  unchangedSourceQuote: after.includes('Vacation requests are due two weeks early'),
  oldGermanGone: !after.includes('Stärkster Treffer aus'),
  noEvidenceEnglish: negative.includes('No reliable answer found'),
  englishLang: document.documentElement.lang === 'en',
};
process.stdout.write(JSON.stringify(result));
"""
    complete = subprocess.run(
        ["node", "-e", harness],
        input=script, text=True, capture_output=True, timeout=10,
    )
    assert complete.returncode == 0, complete.stderr
    checks = json.loads(complete.stdout)
    assert all(checks.values()), checks
