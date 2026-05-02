from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
import webbrowser
from contextlib import redirect_stdout
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import urlparse

from tof_cli.commands import check, doctor, down, setup, status, up


@dataclass(frozen=True)
class ActionSpec:
    label: str
    handler: Callable[..., int]
    kwargs: dict[str, object]
    safe_level: str


ACTIONS = {
    "setup": ActionSpec("Prepare local setup", setup.handle, {}, "SAFE"),
    "up": ActionSpec("Start stack", up.handle, {"build": True}, "SAFE"),
    "check": ActionSpec("Check services", check.handle, {}, "SAFE"),
    "status": ActionSpec("Show runtime status", status.handle, {}, "SAFE"),
    "doctor": ActionSpec("Run doctor", doctor.handle, {}, "SAFE"),
    "down": ActionSpec("Stop stack", down.handle, {"remove_orphans": False}, "SAFE"),
}

LINKS = {
    "openwebui": {"label": "Open WebUI", "url": "http://127.0.0.1:3000"},
    "search_docs": {"label": "Open search API docs", "url": "http://127.0.0.1:8105/docs"},
    "qa_docs": {"label": "Open QA API docs", "url": "http://127.0.0.1:8106/docs"},
    "catalog_docs": {"label": "Open catalog API docs", "url": "http://127.0.0.1:8102/docs"},
}

API_TARGETS = {
    "search": "http://127.0.0.1:8105/search",
    "answer": "http://127.0.0.1:8106/answer",
}


HTML = """<!doctype html>
<html lang=\"de\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>tof_local_knowledge</title>
  <style>
    :root {
      --bg: #f5f7fb;
      --surface: #ffffff;
      --surface-soft: #f8fafc;
      --text: #18212f;
      --muted: #6b7280;
      --border: #e5e7eb;
      --shadow: rgba(0,0,0,0.06);
      --primary: #1f6feb;
      --secondary: #0f766e;
      --ghost-bg: #e5e7eb;
      --ghost-text: #111827;
      --status-bg: #ecfeff;
      --status-border: #a5f3fc;
      --status-text: #164e63;
      --log-bg: #111827;
      --log-text: #d1fae5;
      --chip-bg: #eef2ff;
      --chip-text: #3730a3;
      --chip-border: #c7d2fe;
      --warn-bg: #fff7ed;
      --warn-text: #9a3412;
      --warn-border: #fed7aa;
    }
    body.dark {
      --bg: #0b1120;
      --surface: #111827;
      --surface-soft: #1f2937;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --border: #374151;
      --shadow: rgba(0,0,0,0.35);
      --primary: #3b82f6;
      --secondary: #14b8a6;
      --ghost-bg: #253041;
      --ghost-text: #e5e7eb;
      --status-bg: #082f49;
      --status-border: #0e7490;
      --status-text: #cffafe;
      --log-bg: #020617;
      --log-text: #bbf7d0;
      --chip-bg: #312e81;
      --chip-text: #e0e7ff;
      --chip-border: #6366f1;
      --warn-bg: #431407;
      --warn-text: #fed7aa;
      --warn-border: #9a3412;
    }
    body { font-family: Arial, sans-serif; margin: 0; background: var(--bg); color: var(--text); transition: background 0.2s ease, color 0.2s ease; }
    .wrap { max-width: 1080px; margin: 0 auto; padding: 24px; }
    .hero, .panel { background: var(--surface); border-radius: 16px; padding: 24px; box-shadow: 0 8px 30px var(--shadow); border: 1px solid var(--border); }
    .panel { margin-top: 20px; }
    .hero-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
    .toolbar { display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-end; }
    .lead { color: var(--muted); line-height: 1.5; }
    .note { color: var(--muted); font-size: 14px; }
    .actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-top: 18px; }
    button { border: 0; border-radius: 12px; padding: 14px 16px; font-size: 15px; cursor: pointer; background: var(--primary); color: white; }
    button.secondary { background: var(--secondary); }
    button.ghost { background: var(--ghost-bg); color: var(--ghost-text); }
    button.small { padding: 10px 12px; font-size: 14px; }
    .status { margin-top: 18px; background: var(--status-bg); border: 1px solid var(--status-border); color: var(--status-text); border-radius: 14px; padding: 16px; }
    .log, .result { margin-top: 18px; background: var(--log-bg); color: var(--log-text); border-radius: 14px; padding: 16px; min-height: 220px; }
    .result { background: var(--surface); color: var(--text); min-height: 140px; border: 1px solid var(--border); }
    .result-card { border: 1px solid var(--border); border-radius: 12px; padding: 14px; margin-top: 12px; background: var(--surface-soft); }
    .result-card:first-child { margin-top: 0; }
    .muted { color: var(--muted); font-size: 14px; }
    .answer-main { font-size: 16px; line-height: 1.5; white-space: pre-wrap; }
    .preview { margin-top: 8px; line-height: 1.45; white-space: pre-wrap; }
    .chip-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    .chip { background: var(--chip-bg); color: var(--chip-text); border: 1px solid var(--chip-border); border-radius: 999px; padding: 4px 10px; font-size: 12px; }
    .chip.warn { background: var(--warn-bg); color: var(--warn-text); border-color: var(--warn-border); }
    .meta-grid { display: grid; grid-template-columns: 1fr; gap: 6px; margin-top: 10px; }
    pre { margin: 0; white-space: pre-wrap; word-break: break-word; }
    h1 { margin-top: 0; }
    textarea, input[type=text], input[type=number] { width: 100%; box-sizing: border-box; border: 1px solid var(--border); border-radius: 8px; padding: 10px; font: inherit; background: var(--surface); color: var(--text); }
    textarea { min-height: 90px; resize: vertical; }
    .form-grid { display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 14px; }
    .hint { color: var(--muted); font-size: 14px; margin-top: 10px; }
    .two-col { display: grid; grid-template-columns: 1fr; gap: 20px; }
    details { margin-top: 12px; }
    summary { cursor: pointer; }
    @media (min-width: 1100px) { .two-col { grid-template-columns: 1fr 1fr; } }
    @media (max-width: 720px) { .hero-top { flex-direction: column; } .toolbar { justify-content: flex-start; } }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <div class=\"hero-top\">
        <div>
          <h1>tof_local_knowledge</h1>
          <p class=\"lead\" data-i18n=\"heroLead\">Lokale Steueroberfläche für den Knowledge-Stack. Starte den Stack, öffne die wichtigsten Seiten, suche in lokalen Quellen und stelle beleggebundene Fragen.</p>
          <p class=\"note\" data-i18n=\"heroNote\">Diese UI läuft lokal. Such- und Antwortanfragen bleiben auf deinem lokalen Stack.</p>
        </div>
        <div class=\"toolbar\">
          <button class=\"ghost small\" id=\"language-toggle\" onclick=\"toggleLanguage()\">English</button>
          <button class=\"ghost small\" id=\"theme-toggle\" onclick=\"toggleTheme()\">Dunkel</button>
        </div>
      </div>
    </div>

    <div class=\"panel\">
      <h2 data-i18n=\"mainActions\">Hauptaktionen</h2>
      <div class=\"actions\">
        <button onclick=\"runAction('setup')\" data-i18n=\"setupButton\">1. Lokales Setup vorbereiten</button>
        <button class=\"secondary\" onclick=\"runAction('up')\" data-i18n=\"upButton\">2. Stack starten</button>
        <button onclick=\"runAction('check')\" data-i18n=\"checkButton\">3. Services prüfen</button>
        <button class=\"ghost\" onclick=\"runAction('status')\" data-i18n=\"statusButton\">Runtime-Status anzeigen</button>
        <button class=\"ghost\" onclick=\"runAction('doctor')\" data-i18n=\"doctorButton\">Doctor ausführen</button>
        <button onclick=\"runAction('down')\" data-i18n=\"downButton\">Stack stoppen</button>
      </div>
      <h3 style=\"margin-top:22px;\" data-i18n=\"usefulLinks\">Nützliche Links</h3>
      <div class=\"actions\">
        <button class=\"ghost\" onclick=\"openLink('openwebui')\" data-i18n=\"openWebui\">Open WebUI öffnen</button>
        <button class=\"ghost\" onclick=\"openLink('search_docs')\" data-i18n=\"openSearchDocs\">Search-API-Doku öffnen</button>
        <button class=\"ghost\" onclick=\"openLink('qa_docs')\" data-i18n=\"openQaDocs\">QA-API-Doku öffnen</button>
        <button class=\"ghost\" onclick=\"openLink('catalog_docs')\" data-i18n=\"openCatalogDocs\">Catalog-API-Doku öffnen</button>
      </div>
      <div class=\"status\" id=\"next-step\" data-i18n=\"nextStep\">Empfohlene Reihenfolge: Setup vorbereiten, Stack starten, Services prüfen, danach Suche oder beleggebundene Antwort nutzen.</div>
    </div>

    <div class=\"two-col\">
      <div class=\"panel\">
        <h2 data-i18n=\"searchTitle\">Lokale Knowledge Base durchsuchen</h2>
        <div class=\"form-grid\">
          <input id=\"search-query\" type=\"text\" data-i18n-placeholder=\"searchPlaceholder\" placeholder=\"Suchbegriffe eingeben\">
          <input id=\"search-scope\" type=\"text\" data-i18n-placeholder=\"scopePlaceholder\" placeholder=\"Optionale Source-IDs, durch Komma getrennt\">
          <input id=\"search-limit\" type=\"number\" min=\"1\" max=\"20\" value=\"5\">
          <button class=\"secondary\" onclick=\"runSearch()\" data-i18n=\"runSearch\">Suche ausführen</button>
        </div>
        <div class=\"hint\" data-i18n=\"searchHint\">Die Suche nutzt lokal den laufenden `POST /search` Endpunkt.</div>
        <div class=\"result\" id=\"search-result\" data-i18n=\"noSearchYet\">Noch keine Suche ausgeführt.</div>
      </div>

      <div class=\"panel\">
        <h2 data-i18n=\"answerTitle\">Beleggebundene Frage stellen</h2>
        <div class=\"form-grid\">
          <textarea id=\"qa-question\" data-i18n-placeholder=\"questionPlaceholder\" placeholder=\"Stelle eine Frage zu deinen indexierten lokalen Quellen\"></textarea>
          <input id=\"qa-scope\" type=\"text\" data-i18n-placeholder=\"scopePlaceholder\" placeholder=\"Optionale Source-IDs, durch Komma getrennt\">
          <input id=\"qa-limit\" type=\"number\" min=\"1\" max=\"10\" value=\"5\">
          <button class=\"secondary\" onclick=\"runAnswer()\" data-i18n=\"runAnswer\">Beleggebundene Antwort holen</button>
        </div>
        <div class=\"hint\" data-i18n=\"answerHint\">Fragen nutzen lokal den laufenden `POST /answer` Endpunkt.</div>
        <div class=\"result\" id=\"qa-result\" data-i18n=\"noAnswerYet\">Noch keine beleggebundene Antwort ausgeführt.</div>
      </div>
    </div>

    <div class=\"panel\">
      <h2 data-i18n=\"activityLog\">Aktivitätslog</h2>
      <div class=\"log\"><pre id=\"log\">tof_local_knowledge UI wird gestartet...</pre></div>
    </div>
  </div>
  <script>
    const I18N = {
      de: {
        heroLead: 'Lokale Steueroberfläche für den Knowledge-Stack. Starte den Stack, öffne die wichtigsten Seiten, suche in lokalen Quellen und stelle beleggebundene Fragen.',
        heroNote: 'Diese UI läuft lokal. Such- und Antwortanfragen bleiben auf deinem lokalen Stack.',
        mainActions: 'Hauptaktionen',
        setupButton: '1. Lokales Setup vorbereiten',
        upButton: '2. Stack starten',
        checkButton: '3. Services prüfen',
        statusButton: 'Runtime-Status anzeigen',
        doctorButton: 'Doctor ausführen',
        downButton: 'Stack stoppen',
        usefulLinks: 'Nützliche Links',
        openWebui: 'Open WebUI öffnen',
        openSearchDocs: 'Search-API-Doku öffnen',
        openQaDocs: 'QA-API-Doku öffnen',
        openCatalogDocs: 'Catalog-API-Doku öffnen',
        nextStep: 'Empfohlene Reihenfolge: Setup vorbereiten, Stack starten, Services prüfen, danach Suche oder beleggebundene Antwort nutzen.',
        searchTitle: 'Lokale Knowledge Base durchsuchen',
        searchPlaceholder: 'Suchbegriffe eingeben',
        scopePlaceholder: 'Optionale Source-IDs, durch Komma getrennt',
        runSearch: 'Suche ausführen',
        searchHint: 'Die Suche nutzt lokal den laufenden `POST /search` Endpunkt.',
        noSearchYet: 'Noch keine Suche ausgeführt.',
        answerTitle: 'Beleggebundene Frage stellen',
        questionPlaceholder: 'Stelle eine Frage zu deinen indexierten lokalen Quellen',
        runAnswer: 'Beleggebundene Antwort holen',
        answerHint: 'Fragen nutzen lokal den laufenden `POST /answer` Endpunkt.',
        noAnswerYet: 'Noch keine beleggebundene Antwort ausgeführt.',
        activityLog: 'Aktivitätslog',
        languageButton: 'English',
        themeButtonLight: 'Hell',
        themeButtonDark: 'Dunkel',
        searchFailed: 'Suche fehlgeschlagen',
        noHits: 'Keine Suchtreffer zurückgegeben.',
        query: 'Query',
        returned: 'Zurückgegeben',
        hits: 'Treffer',
        source: 'Quelle',
        document: 'Dokument',
        citation: 'Zitat',
        score: 'Score',
        rawSearch: 'Rohe Suchantwort anzeigen',
        answerFailed: 'Beleggebundene Antwort fehlgeschlagen',
        noAnswerText: 'Keine Antwort zurückgegeben.',
        confidence: 'Konfidenz',
        uncertainties: 'Unsicherheiten',
        citations: 'Zitate',
        usedDocuments: 'Verwendete Dokumente',
        searchQueries: 'Suchanfragen',
        rawAnswer: 'Rohe Antwortdaten anzeigen',
        summaryRefreshed: 'Statushinweis aktualisiert.',
        runningAction: 'Führe Aktion aus',
        opening: 'Öffne',
        runningSearch: 'Lokale Suche läuft ...',
        searchFinished: 'Suche abgeschlossen.',
        runningAnswer: 'Beleggebundene Antwort läuft ...',
        answerFinished: 'Beleggebundene Antwort abgeschlossen.',
        uiStarted: 'tof_local_knowledge UI wird gestartet...',
      },
      en: {
        heroLead: 'A simple local control surface for the knowledge stack. Start the stack, open the main pages, search local sources, and ask grounded questions.',
        heroNote: 'This UI is local-only. Search and answer requests stay on your local stack.',
        mainActions: 'Main actions',
        setupButton: '1. Prepare local setup',
        upButton: '2. Start stack',
        checkButton: '3. Check services',
        statusButton: 'Show runtime status',
        doctorButton: 'Run doctor',
        downButton: 'Stop stack',
        usefulLinks: 'Useful links',
        openWebui: 'Open WebUI',
        openSearchDocs: 'Open search API docs',
        openQaDocs: 'Open QA API docs',
        openCatalogDocs: 'Open catalog API docs',
        nextStep: 'Recommended order: prepare local setup, start stack, check services, then use search or grounded answer in this browser page.',
        searchTitle: 'Search the local knowledge base',
        searchPlaceholder: 'Type search words here',
        scopePlaceholder: 'Optional source IDs, comma separated',
        runSearch: 'Run search',
        searchHint: 'Search uses the local `POST /search` endpoint of the running stack.',
        noSearchYet: 'No search run yet.',
        answerTitle: 'Ask a grounded question',
        questionPlaceholder: 'Ask a question about your indexed local sources',
        runAnswer: 'Get grounded answer',
        answerHint: 'Questions use the local `POST /answer` endpoint of the running stack.',
        noAnswerYet: 'No grounded answer run yet.',
        activityLog: 'Activity log',
        languageButton: 'Deutsch',
        themeButtonLight: 'Light',
        themeButtonDark: 'Dark',
        searchFailed: 'Search failed',
        noHits: 'No search hits returned.',
        query: 'Query',
        returned: 'Returned',
        hits: 'hit(s)',
        source: 'Source',
        document: 'Document',
        citation: 'Citation',
        score: 'Score',
        rawSearch: 'Show raw search response',
        answerFailed: 'Grounded answer failed',
        noAnswerText: 'No answer text returned.',
        confidence: 'Confidence',
        uncertainties: 'Uncertainties',
        citations: 'Citations',
        usedDocuments: 'Used documents',
        searchQueries: 'Search queries',
        rawAnswer: 'Show raw grounded-answer response',
        summaryRefreshed: 'Summary refreshed.',
        runningAction: 'Running action',
        opening: 'Opening',
        runningSearch: 'Running local search ...',
        searchFinished: 'Search finished.',
        runningAnswer: 'Running grounded answer ...',
        answerFinished: 'Grounded answer finished.',
        uiStarted: 'Starting tof_local_knowledge UI...',
      },
    };

    let currentLanguage = localStorage.getItem('tof_local_knowledge_language') || 'de';
    let currentTheme = localStorage.getItem('tof_local_knowledge_theme') || 'light';

    function t(key) {
      return (I18N[currentLanguage] && I18N[currentLanguage][key]) || I18N.de[key] || key;
    }

    function applyLanguage() {
      document.documentElement.lang = currentLanguage;
      document.querySelectorAll('[data-i18n]').forEach((element) => {
        element.textContent = t(element.dataset.i18n);
      });
      document.querySelectorAll('[data-i18n-placeholder]').forEach((element) => {
        element.placeholder = t(element.dataset.i18nPlaceholder);
      });
      document.getElementById('language-toggle').textContent = t('languageButton');
      document.getElementById('theme-toggle').textContent = currentTheme === 'dark' ? t('themeButtonLight') : t('themeButtonDark');
      localStorage.setItem('tof_local_knowledge_language', currentLanguage);
    }

    function applyTheme() {
      document.body.classList.toggle('dark', currentTheme === 'dark');
      document.getElementById('theme-toggle').textContent = currentTheme === 'dark' ? t('themeButtonLight') : t('themeButtonDark');
      localStorage.setItem('tof_local_knowledge_theme', currentTheme);
    }

    function toggleLanguage() {
      currentLanguage = currentLanguage === 'de' ? 'en' : 'de';
      applyLanguage();
    }

    function toggleTheme() {
      currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
      applyTheme();
    }

    function appendLog(text) {
      const log = document.getElementById('log');
      log.textContent = `[${new Date().toLocaleTimeString()}] ${text}\n\n` + log.textContent;
    }

    function escapeHtml(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;');
    }

    function parseScope(value) {
      if (!value || !value.trim()) return [];
      return value.split(',').map(v => v.trim()).filter(Boolean);
    }

    function asList(value) {
      if (!value) return [];
      return Array.isArray(value) ? value : [value];
    }

    function renderChips(items, cssClass = '') {
      const list = asList(items).filter(item => item !== null && item !== undefined && String(item).trim() !== '');
      if (!list.length) return '';
      return `<div class=\"chip-list\">${list.map(item => `<span class=\"chip ${cssClass}\">${escapeHtml(item)}</span>`).join('')}</div>`;
    }

    function renderSearchResult(data) {
      const root = document.getElementById('search-result');
      if (data.error) {
        root.innerHTML = `<div class=\"result-card\"><strong>${t('searchFailed')}</strong><div class=\"muted\">${escapeHtml(data.details || data.error)}</div></div>`;
        return;
      }
      const hits = data.results || data.hits || [];
      if (!hits.length) {
        root.innerHTML = `<div class=\"muted\">${t('noHits')}</div>`;
        return;
      }
      let html = `<div class=\"muted\">${t('query')}: ${escapeHtml(data.query || '')} · ${t('returned')} ${hits.length} ${t('hits')}.</div>`;
      for (const hit of hits) {
        const title = hit.relative_path || hit.title || hit.document_title || hit.document_id || 'Search hit';
        const preview = hit.preview_text || hit.snippet || hit.text || hit.chunk_text || '';
        html += `<div class=\"result-card\"><strong>${escapeHtml(title)}</strong>`;
        html += '<div class=\"meta-grid\">';
        if (hit.source_id) html += `<div class=\"muted\">${t('source')}: ${escapeHtml(hit.source_id)}</div>`;
        if (hit.document_id) html += `<div class=\"muted\">${t('document')}: ${escapeHtml(hit.document_id)}</div>`;
        if (hit.citation_label) html += `<div class=\"muted\">${t('citation')}: ${escapeHtml(hit.citation_label)}</div>`;
        if (hit.score !== undefined && hit.score !== null) html += `<div class=\"muted\">${t('score')}: ${escapeHtml(hit.score)}</div>`;
        html += '</div>';
        if (preview) html += `<div class=\"preview\">${escapeHtml(preview)}</div>`;
        html += `</div>`;
      }
      html += `<details><summary>${t('rawSearch')}</summary><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre></details>`;
      root.innerHTML = html;
    }

    function renderCitation(citation) {
      if (typeof citation === 'string') {
        return `<div style=\"margin-top:10px;\"><strong>${escapeHtml(citation)}</strong></div>`;
      }
      const title = citation.title || citation.citation_label || citation.source_id || citation.document_id || t('citation');
      let html = `<div style=\"margin-top:10px;\"><strong>${escapeHtml(title)}</strong>`;
      if (citation.relative_path) html += `<div class=\"muted\">${escapeHtml(citation.relative_path)}</div>`;
      if (citation.snippet || citation.preview_text) html += `<div class=\"muted\" style=\"margin-top:4px;\">${escapeHtml(citation.snippet || citation.preview_text)}</div>`;
      html += '</div>';
      return html;
    }

    function renderAnswerResult(data) {
      const root = document.getElementById('qa-result');
      if (data.error) {
        root.innerHTML = `<div class=\"result-card\"><strong>${t('answerFailed')}</strong><div class=\"muted\">${escapeHtml(data.details || data.error)}</div></div>`;
        return;
      }
      const answer = data.answer_text || data.answer || t('noAnswerText');
      const confidence = data.confidence ?? 'unknown';
      const citations = asList(data.citations);
      const usedDocuments = asList(data.used_documents);
      const uncertainties = asList(data.uncertainties);
      const searchQueries = asList(data.search_queries);

      let html = `<div class=\"result-card\"><div class=\"answer-main\">${escapeHtml(answer)}</div><div class=\"muted\" style=\"margin-top:10px;\">${t('confidence')}: ${escapeHtml(confidence)}</div>`;
      if (uncertainties.length) {
        html += `<div style=\"margin-top:10px;\"><strong>${t('uncertainties')}</strong>${renderChips(uncertainties, 'warn')}</div>`;
      }
      html += '</div>';

      if (citations.length) {
        html += `<div class=\"result-card\"><strong>${t('citations')}</strong>`;
        for (const citation of citations) {
          html += renderCitation(citation);
        }
        html += `</div>`;
      }
      if (usedDocuments.length) {
        html += `<div class=\"result-card\"><strong>${t('usedDocuments')}</strong>${renderChips(usedDocuments)}</div>`;
      }
      if (searchQueries.length) {
        html += `<div class=\"result-card\"><strong>${t('searchQueries')}</strong>${renderChips(searchQueries)}</div>`;
      }
      html += `<details><summary>${t('rawAnswer')}</summary><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre></details>`;
      root.innerHTML = html;
    }

    async function refreshSummary() {
      await fetch('/api/summary');
      document.getElementById('next-step').textContent = t('nextStep');
      appendLog(t('summaryRefreshed'));
    }

    async function runAction(action) {
      appendLog(`${t('runningAction')}: ${action} ...`);
      const response = await fetch(`/api/${action}`, { method: 'POST' });
      const data = await response.json();
      appendLog(JSON.stringify(data, null, 2));
      await refreshSummary();
    }

    async function openLink(name) {
      appendLog(`${t('opening')}: ${name} ...`);
      const response = await fetch(`/api/open/${name}`, { method: 'POST' });
      const data = await response.json();
      appendLog(JSON.stringify(data, null, 2));
    }

    async function runSearch() {
      const payload = {
        query: document.getElementById('search-query').value,
        source_scope: parseScope(document.getElementById('search-scope').value),
        limit: Number(document.getElementById('search-limit').value || 5),
      };
      appendLog(t('runningSearch'));
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      renderSearchResult(data);
      appendLog(t('searchFinished'));
    }

    async function runAnswer() {
      const payload = {
        question: document.getElementById('qa-question').value,
        source_scope: parseScope(document.getElementById('qa-scope').value),
        limit: Number(document.getElementById('qa-limit').value || 5),
      };
      appendLog(t('runningAnswer'));
      const response = await fetch('/api/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      renderAnswerResult(data);
      appendLog(t('answerFinished'));
    }

    applyTheme();
    applyLanguage();
    document.getElementById('log').textContent = t('uiStarted');
    refreshSummary();
  </script>
</body>
</html>
"""


def _run_action(name: str) -> dict[str, object]:
    spec = ACTIONS[name]
    namespace = type("Args", (), spec.kwargs)()
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = spec.handler(namespace)
    output = buffer.getvalue().strip()
    return {
        "action": name,
        "label": spec.label,
        "safe_level": spec.safe_level,
        "exit_code": int(code or 0),
        "output": output,
    }


def _open_link(name: str) -> dict[str, object]:
    link = LINKS[name]
    webbrowser.open(link["url"])
    return {"opened": link["url"], "label": link["label"]}


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    return json.loads(raw.decode("utf-8")) if raw else {}


def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return {"error": f"http_error_{exc.code}", "details": body or str(exc)}
    except Exception as exc:
        return {"error": "request_failed", "details": str(exc)}


def _summary_payload() -> dict[str, object]:
    return {
        "next_step": "Recommended order: prepare local setup, start stack, check services, then use search or grounded answer in this browser page.",
        "actions": [
            {"name": key, "label": spec.label, "safe_level": spec.safe_level}
            for key, spec in ACTIONS.items()
        ],
        "links": LINKS,
    }


def _json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, indent=2).encode("utf-8")


def run_ui(host: str = "127.0.0.1", port: int = 8785, open_browser: bool = True) -> int:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, content_type: str, body: bytes) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send(200, "text/html; charset=utf-8", HTML.encode("utf-8"))
                return
            if parsed.path == "/api/summary":
                self._send(200, "application/json; charset=utf-8", _json_bytes(_summary_payload()))
                return
            self._send(404, "application/json; charset=utf-8", _json_bytes({"error": "not found"}))

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            action = parsed.path.removeprefix('/api/')
            if action in ACTIONS:
                self._send(200, "application/json; charset=utf-8", _json_bytes(_run_action(action)))
                return
            if action.startswith('open/'):
                name = action.removeprefix('open/')
                if name in LINKS:
                    self._send(200, "application/json; charset=utf-8", _json_bytes(_open_link(name)))
                    return
            if action == 'search':
                payload = _read_json_body(self)
                self._send(200, "application/json; charset=utf-8", _json_bytes(_post_json(API_TARGETS['search'], payload)))
                return
            if action == 'answer':
                payload = _read_json_body(self)
                self._send(200, "application/json; charset=utf-8", _json_bytes(_post_json(API_TARGETS['answer'], payload)))
                return
            self._send(404, "application/json; charset=utf-8", _json_bytes({"error": "not found"}))

        def log_message(self, fmt: str, *args: object) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(json.dumps({"ui_url": url, "message": "tof_local_knowledge UI is running"}, indent=2))
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
