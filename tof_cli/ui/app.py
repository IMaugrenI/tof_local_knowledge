from __future__ import annotations

import io
import json
import re
import urllib.error
import urllib.request
import webbrowser
from contextlib import redirect_stdout
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import parse_qs, urlparse

from tof_cli.commands import check, doctor, down, setup, status, up
from tof_cli.knowledge.index_ops import index_configured_source
from tof_cli.knowledge.source_spaces import discover_source_spaces
from tof_cli.core.env_ops import read_env
from tof_cli.ui.service_ops import classify_error, configured_targets, parse_bounded_json


@dataclass(frozen=True)
class ActionSpec:
    label: str
    handler: Callable[..., int]
    kwargs: dict[str, object]
    safe_level: str


ACTIONS = {
    "setup": ActionSpec("Prepare local environment", setup.handle, {}, "SAFE"),
    "up": ActionSpec("Start local environment", up.handle, {"build": True}, "SAFE"),
    "check": ActionSpec("Check if everything is ready", check.handle, {}, "SAFE"),
    "status": ActionSpec("Show technical status", status.handle, {}, "SAFE"),
    "doctor": ActionSpec("Find problems", doctor.handle, {}, "SAFE"),
    "down": ActionSpec("Stop local environment", down.handle, {"remove_orphans": False}, "SAFE"),
}

LINKS = {
    "openwebui": {"label": "Open advanced workspace", "url": "http://127.0.0.1:3000"},
    "search_docs": {"label": "Technical search documentation", "url": "http://127.0.0.1:8105/docs"},
    "qa_docs": {"label": "Technical answer documentation", "url": "http://127.0.0.1:8106/docs"},
    "catalog_docs": {"label": "Technical source documentation", "url": "http://127.0.0.1:8102/docs"},
}

API_TARGETS = {
    "search": "http://127.0.0.1:8105/search",
    "answer": "http://127.0.0.1:8106/answer",
    "sources": "http://127.0.0.1:8102/sources/status",
}


HTML = """<!doctype html>
<html lang=\"de\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>tof_local_knowledge</title>
  <style>
    :root {
      --bg: #0d0d0c;
      --bg-soft: #13120f;
      --surface: #181612;
      --surface-soft: #211e18;
      --text: #f4f0e8;
      --muted: #aaa49a;
      --gold: #c69a52;
      --gold-bright: #e1b969;
      --border: rgba(244,240,232,.10);
      --border-strong: rgba(198,154,82,.34);
      --shadow: 0 24px 80px rgba(0,0,0,.30);
      --ok: #71c39b;
      --warn: #d8a85f;
      --danger: #cf7b72;
      --chip-bg: rgba(198,154,82,.08);
      --chip-text: #e1b969;
      --chip-border: rgba(198,154,82,.28);
      --warn-bg: rgba(216,168,95,.08);
      --warn-text: #e7c48a;
      --warn-border: rgba(216,168,95,.30);
      color-scheme: dark;
    }

    body:not(.dark) {
      --bg: #efe9df;
      --bg-soft: #f6f1e8;
      --surface: #fbf8f2;
      --surface-soft: #f1eadf;
      --text: #211d18;
      --muted: #6f675e;
      --gold: #9b7135;
      --gold-bright: #7f591f;
      --border: rgba(50,40,28,.12);
      --border-strong: rgba(155,113,53,.36);
      --shadow: 0 22px 60px rgba(52,41,28,.12);
      --chip-bg: rgba(155,113,53,.08);
      --chip-text: #76511d;
      --chip-border: rgba(155,113,53,.25);
      --warn-bg: rgba(164,111,35,.08);
      --warn-text: #7f5418;
      --warn-border: rgba(164,111,35,.26);
      color-scheme: light;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 82% 7%, rgba(198,154,82,.08), transparent 28rem),
        radial-gradient(circle at 7% 46%, rgba(198,154,82,.03), transparent 34rem),
        linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 52%, var(--bg) 100%);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      transition: background .18s ease, color .18s ease;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: .13;
      background-image:
        linear-gradient(rgba(255,255,255,.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.014) 1px, transparent 1px);
      background-size: 72px 72px;
      mask-image: linear-gradient(180deg, #000 0, transparent 80%);
      z-index: -1;
    }

    button, input, textarea, summary { font: inherit; }

    .skip-link {
      position: absolute;
      left: 16px;
      top: -64px;
      z-index: 20;
      padding: 10px 14px;
      border-radius: 10px;
      background: var(--gold);
      color: #17120d;
      font-weight: 750;
    }
    .skip-link:focus { top: 16px; }

    .wrap {
      width: min(calc(100% - 40px), 1180px);
      margin: 0 auto;
      padding: 26px 0 56px;
    }

    .topbar {
      min-height: 68px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 22px;
      margin-bottom: 58px;
    }

    .brand {
      display: inline-flex;
      align-items: center;
      gap: 13px;
    }

    .brand-mark { width: 38px; height: 38px; }
    .brand-mark svg { width: 100%; height: 100%; display: block; }
    .brand-copy { display: flex; flex-direction: column; gap: 2px; }
    .brand-name { font-size: .83rem; letter-spacing: .19em; font-weight: 800; }
    .product-name { color: var(--muted); font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; }

    .toolbar { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }

    button {
      min-height: 46px;
      border: 1px solid transparent;
      border-radius: 12px;
      padding: 0 17px;
      cursor: pointer;
      font-weight: 750;
      background: var(--gold);
      color: #17120d;
      transition: transform .16s ease, border-color .16s ease, background .16s ease, color .16s ease;
    }

    button:hover { transform: translateY(-1px); }
    button:focus-visible, summary:focus-visible, input:focus-visible, textarea:focus-visible {
      outline: 2px solid var(--gold-bright);
      outline-offset: 3px;
    }

    button.secondary {
      border-color: var(--border-strong);
      background: rgba(198,154,82,.06);
      color: var(--text);
    }

    button.ghost {
      border-color: var(--border);
      background: rgba(255,255,255,.018);
      color: var(--muted);
    }

    button.small { min-height: 38px; padding: 0 12px; font-size: .83rem; }

    .page-nav {
      display: flex;
      gap: 8px;
      align-items: center;
      padding: 9px;
      margin-bottom: 12px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: var(--surface);
      overflow-x: auto;
      scrollbar-width: thin;
    }

    .page-nav a {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex: 1 0 auto;
      min-height: 48px;
      padding: 10px 16px;
      border-radius: 12px;
      color: var(--muted);
      text-decoration: none;
      font-weight: 750;
      white-space: nowrap;
    }

    .page-nav a:hover, .page-nav a:focus-visible {
      color: var(--text);
      background: var(--surface-soft);
    }

    .page-nav a[aria-current="page"] {
      color: #17120d;
      background: var(--gold);
    }

    .page-nav a[aria-current="page"]:hover {
      color: #17120d;
      background: var(--gold-bright);
    }

    .hero {
      display: grid;
      grid-template-columns: minmax(0,1.05fr) minmax(340px,.95fr);
      gap: 60px;
      align-items: end;
      padding-bottom: 56px;
      border-bottom: 1px solid var(--border);
    }

    .eyebrow {
      margin: 0 0 16px;
      color: var(--gold);
      font-size: .76rem;
      letter-spacing: .18em;
      font-weight: 800;
    }

    h1,h2,h3,p { margin-top: 0; }
    h1 {
      margin-bottom: 22px;
      max-width: 760px;
      font-size: clamp(2.9rem, 6vw, 5.7rem);
      line-height: .97;
      letter-spacing: -.045em;
    }
    h2 { margin-bottom: 12px; font-size: clamp(1.7rem,3vw,2.6rem); letter-spacing: -.03em; }
    h3 { margin-bottom: 8px; }

    .lead { margin-bottom: 12px; color: #c6bfb4; font-size: clamp(1.04rem,1.65vw,1.23rem); line-height: 1.72; }
    body:not(.dark) .lead { color: #665e55; }
    .note, .muted, .hint { color: var(--muted); font-size: .88rem; }

    .hero-points { display: grid; border-top: 1px solid var(--border); }
    .hero-point {
      display: grid;
      grid-template-columns: 38px 1fr;
      gap: 14px;
      padding: 15px 0;
      border-bottom: 1px solid var(--border);
      color: var(--muted);
      font-size: .91rem;
    }
    .hero-point span { color: var(--gold); font-size: .76rem; letter-spacing: .1em; }

    .section { padding-top: 48px; }

    .answer-panel, .search-panel, details.tech-panel {
      border: 1px solid var(--border);
      border-radius: 22px;
      background: rgba(255,255,255,.014);
      box-shadow: var(--shadow);
    }

    .answer-panel {
      position: relative;
      overflow: hidden;
      padding: 30px;
      border-color: var(--border-strong);
      background:
        radial-gradient(circle at 88% 10%, rgba(198,154,82,.11), transparent 21rem),
        rgba(255,255,255,.014);
    }

    .answer-panel::before {
      content: "ASK";
      position: absolute;
      right: 22px;
      top: 18px;
      color: rgba(225,185,105,.16);
      font-size: .72rem;
      letter-spacing: .18em;
      font-weight: 800;
    }

    .search-panel { margin-top: 18px; padding: 24px; }

    .form-grid { display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 16px; }

    textarea, input[type=text], input[type=number] {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 13px;
      background: rgba(255,255,255,.018);
      color: var(--text);
    }

    textarea { min-height: 116px; resize: vertical; }
    input[type=number] { max-width: 120px; }

    .options-row {
      display: grid;
      grid-template-columns: minmax(0,1fr) 120px;
      gap: 10px;
    }

    .result {
      margin-top: 18px;
      min-height: 120px;
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      background: rgba(0,0,0,.10);
      color: var(--text);
    }

    .result-card {
      margin-top: 12px;
      padding: 15px;
      border: 1px solid var(--border);
      border-radius: 13px;
      background: rgba(255,255,255,.015);
    }
    .result-card:first-child { margin-top: 0; }
    .answer-main { font-size: 1.02rem; line-height: 1.65; white-space: pre-wrap; }
    .preview { margin-top: 8px; line-height: 1.5; white-space: pre-wrap; }

    .chip-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    .chip { background: var(--chip-bg); color: var(--chip-text); border: 1px solid var(--chip-border); border-radius: 999px; padding: 5px 10px; font-size: 12px; }
    .chip.warn { background: var(--warn-bg); color: var(--warn-text); border-color: var(--warn-border); }
    .meta-grid { display: grid; grid-template-columns: 1fr; gap: 6px; margin-top: 10px; }

    .status {
      margin-top: 18px;
      padding: 16px 18px;
      border-left: 2px solid var(--gold);
      background: rgba(198,154,82,.045);
      color: var(--muted);
    }

    details { margin-top: 12px; }
    details.tech-panel { margin-top: 38px; box-shadow: none; overflow: hidden; }
    summary { cursor: pointer; list-style: none; padding: 17px 19px; font-weight: 750; }
    summary::-webkit-details-marker { display: none; }
    summary::after { content: "+"; float: right; color: var(--gold); font-size: 1.2rem; }
    details[open] summary::after { content: "−"; }

    .tech-body { border-top: 1px solid var(--border); padding: 20px; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; }
    .subhead { margin: 22px 0 10px; font-size: .95rem; color: var(--muted); }

    .log {
      margin-top: 12px;
      min-height: 150px;
      max-height: 340px;
      overflow: auto;
      border: 1px solid rgba(255,255,255,.06);
      border-radius: 12px;
      background: #090a09;
      color: #c6d7c8;
      padding: 15px;
      font: 12px/1.6 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }

    pre { margin: 0; white-space: pre-wrap; word-break: break-word; }

    .footer {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      margin-top: 44px;
      padding-top: 18px;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: .79rem;
    }

    @media (max-width: 820px) {
      .hero { grid-template-columns: 1fr; gap: 32px; }
      .topbar { margin-bottom: 38px; align-items: flex-start; }
    }

    @media (max-width: 560px) {
      .wrap { width: min(calc(100% - 26px),1180px); padding-top: 16px; }
      .topbar { flex-direction: column; }
      .page-nav { padding: 7px; gap: 5px; }
      .page-nav a { min-height: 44px; padding: 9px 12px; }
      h1 { font-size: clamp(2.5rem,13vw,3.65rem); }
      .answer-panel, .search-panel { padding: 21px; }
      .options-row { grid-template-columns: 1fr; }
      input[type=number] { max-width: none; }
      .actions { flex-direction: column; }
      button { width: 100%; }
      .footer { flex-direction: column; }
    }

    @media (prefers-reduced-motion: reduce) {
      *,*::before,*::after { transition-duration: .001ms !important; animation-duration: .001ms !important; }
    }
  </style>
</head>
<body class="dark">
  <a class="skip-link" href="#main-content" data-i18n="skipLink">Zum Inhalt springen</a>
  <div class="wrap">
    <header class="topbar">
      <div class="brand" aria-label="ToF Systems Knowledge">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 64 64" fill="none">
            <g stroke="#e1b969" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M32 5.5C25.8 13.3 25.5 22.7 32 30.8C38.5 22.7 38.2 13.3 32 5.5Z"/>
              <path d="M31.6 30.1C23.1 20.8 12.4 22.4 5.8 31.8C13.4 40.5 23.7 41.2 31.8 32.5"/>
              <path d="M32.4 30.1C40.9 20.8 51.6 22.4 58.2 31.8C50.6 40.5 40.3 41.2 32.2 32.5"/>
              <path d="M32 33.2C25.7 41.4 26 50.8 32 58.5C38 50.8 38.3 41.4 32 33.2Z"/>
              <path d="M32 24.8L39.2 32L32 39.2L24.8 32L32 24.8Z"/>
              <path d="M19.7 29.1L15.2 33.2L23.2 39.1"/>
              <path d="M44.3 29.1L48.8 33.2L40.8 39.1"/>
            </g>
          </svg>
        </span>
        <span class="brand-copy">
          <span class="brand-name">TOF SYSTEMS</span>
          <span class="product-name">Knowledge</span>
        </span>
      </div>
      <div class="toolbar">
        <button class="ghost small" id="language-toggle" onclick="toggleLanguage()">English</button>
        <button class="ghost small" id="theme-toggle" onclick="toggleTheme()">Hell</button>
      </div>
    </header>

    <nav class="page-nav" aria-label="Navigation" data-i18n-aria-label="navigationLabel">
      <a href="/quellen-index" data-page-link="sources" data-i18n="navSources">Quellen & Index</a>
      <a href="/beleg-pruefen" data-page-link="evidence" data-i18n="navEvidence">Beleg prüfen</a>
      <a href="/dokumente-durchsuchen" data-page-link="search" data-i18n="navSearch">Dokumente durchsuchen</a>
      <a href="/frage-stellen" data-page-link="question" data-i18n="navAsk">Frage stellen</a>
    </nav>

    <main id="main-content">
      <div class="section">
        <!-- PAGE_START:question -->
        <section class="hero">
        <div>
          <p class="eyebrow" data-i18n="heroEyebrow">DEINE DOKUMENTE · DEINE QUELLEN</p>
          <h1 data-i18n="heroTitle">Frag deine Dokumente.</h1>
          <p class="lead" data-i18n="heroLead">Durchsuche deine lokalen Unterlagen oder stelle eine Frage. Antworten zeigen dir, auf welche Dokumente sie sich stützen.</p>
          <p class="note" data-i18n="heroNote">Deine Unterlagen und Anfragen bleiben auf diesem Computer.</p>
        </div>
        <div class="hero-points">
          <div class="hero-point"><span>01</span><div data-i18n="heroPointOne">Suche direkt in deinen eigenen Unterlagen.</div></div>
          <div class="hero-point"><span>02</span><div data-i18n="heroPointTwo">Antworten zeigen die verwendeten Quellen.</div></div>
          <div class="hero-point"><span>03</span><div data-i18n="heroPointThree">Wenn keine passende Grundlage gefunden wird, bleibt das sichtbar.</div></div>
        </div>
        </section>

        <div class="answer-panel">
          <p class="eyebrow" data-i18n="answerEyebrow">FRAGE STELLEN</p>
          <h2 data-i18n="answerTitle">Was möchtest du aus deinen Dokumenten wissen?</h2>
          <div class="form-grid">
            <textarea id="qa-question" aria-label="Frage an deine Dokumente" data-i18n-aria-label="questionLabel" data-i18n-placeholder="questionPlaceholder" placeholder="Zum Beispiel: Was steht in meinen Unterlagen zur Urlaubsregelung?"></textarea>
            <div class="options-row">
              <input id="qa-scope" type="text" aria-label="Suche optional auf bestimmte Quellen begrenzen" data-i18n-aria-label="scopeLabel" data-i18n-placeholder="scopePlaceholder" placeholder="Optional: Suche auf bestimmte Quellen begrenzen">
              <input id="qa-limit" type="number" min="1" max="10" value="5" aria-label="Maximale Anzahl berücksichtigter Treffer" data-i18n-aria-label="qaLimitLabel">
            </div>
            <button onclick="runAnswer()" data-i18n="runAnswer">Antwort aus meinen Dokumenten holen</button>
          </div>
          <div class="hint" data-i18n="answerHint">ToF sucht passende Stellen und zeigt die verwendeten Quellen zusammen mit der Antwort.</div>
          <div class="result" id="qa-result" role="status" aria-live="polite" data-i18n="noAnswerYet">Hier erscheint deine Antwort mit den dazugehörigen Quellen.</div>
        </div>

        <!-- PAGE_END:question -->
        <!-- PAGE_START:search -->
        <div class="search-panel">
          <p class="eyebrow" data-i18n="searchEyebrow">DOKUMENTE DURCHSUCHEN</p>
          <h2 data-i18n="searchTitle">Finde passende Stellen direkt.</h2>
          <div class="form-grid">
            <input id="search-query" type="text" aria-label="Dokumente durchsuchen" data-i18n-aria-label="searchLabel" data-i18n-placeholder="searchPlaceholder" placeholder="Wonach möchtest du suchen?">
            <div class="options-row">
              <input id="search-scope" type="text" aria-label="Suche optional auf bestimmte Quellen begrenzen" data-i18n-aria-label="scopeLabel" data-i18n-placeholder="scopePlaceholder" placeholder="Optional: Suche auf bestimmte Quellen begrenzen">
              <input id="search-limit" type="number" min="1" max="20" value="5" aria-label="Maximale Anzahl Suchtreffer" data-i18n-aria-label="searchLimitLabel">
            </div>
            <button class="secondary" onclick="runSearch()" data-i18n="runSearch">Dokumente durchsuchen</button>
          </div>
          <div class="hint" data-i18n="searchHint">Du bekommst die passendsten Fundstellen mit Dokument und Textausschnitt.</div>
          <div class="result" id="search-result" role="status" aria-live="polite" data-i18n="noSearchYet">Hier erscheinen passende Fundstellen aus deinen Dokumenten.</div>
        </div>

        <!-- PAGE_END:search -->
        <!-- PAGE_START:evidence -->
        <section class="search-panel" aria-labelledby="evidence-title">
          <p class="eyebrow" data-i18n="evidenceEyebrow">BELEG PRÜFEN</p>
          <h2 id="evidence-title" data-i18n="evidenceTitle">Textstelle nachvollziehen</h2>
          <p class="hint" data-i18n="evidenceHint">Öffne einen Beleg aus Suche oder Antwort. Nur aktuell indexierte Fundstellen werden angezeigt.</p>
          <div class="result" id="evidence-result" aria-live="polite" data-i18n="evidenceEmpty">Wähle eine Fundstelle.</div>
        </section>

        <!-- PAGE_END:evidence -->
        <!-- PAGE_START:sources -->
        <section class="search-panel" aria-labelledby="sources-title">
          <p class="eyebrow" data-i18n="sourcesEyebrow">QUELLEN & INDEX</p>
          <h2 id="sources-title" data-i18n="sourcesTitle">Deine Quellen im Überblick</h2>
          <div class="hint" data-i18n="sourcesHint">Welche Dokumente bereits indexiert sind und welche noch Aufmerksamkeit brauchen.</div>
          <button class="secondary" onclick="refreshSources()" data-i18n="refreshSources">Quellen aktualisieren</button>
          <label class="hint" for="index-source-select" data-i18n="indexSourceLabel">Zu indexierenden Quellenbereich auswählen</label>
          <select id="index-source-select" onchange="resetIndexCursor()" style="display:block;width:100%;padding:10px;margin:8px 0 12px"></select>
          <button class="secondary" type="button" onclick="loadSourceSpaces()" data-i18n="refreshSourceFolders">Quellenordner aktualisieren</button>
          <p class="hint" id="index-source-message" aria-live="polite"></p>
          <button class="secondary" id="index-batch-button" onclick="runIndexBatch()" data-i18n="indexBatch">Konfigurierte Quelle indexieren</button>
          <button class="secondary" onclick="resetIndexCursor()" data-i18n="indexReset">Dateidurchlauf neu beginnen</button>
          <p class="hint" data-i18n="indexMissingNote">Bei großen Quellen ist die Fehlbestandserkennung nur für vollständige Einzelscans verfügbar.</p>
          <div class="hint" id="index-batch-result" aria-live="polite" data-i18n="indexHint">Manuell: eine begrenzte Charge der konfigurierten, schreibgeschützten Quelle einlesen.</div>
          <div class="result" id="source-result" aria-live="polite" data-i18n="sourcesEmpty">Hier erscheinen die erfassten Quellen und Indexstände.</div>
          <div class="hint" data-i18n="sourcesLocalOnly">Nur lokale Quellenübersicht. Es ist keine Mehrbenutzerfreigabe aktiv.</div>
        </section>

        <!-- PAGE_END:sources -->
        <div class="status" id="next-step" role="status" aria-live="polite" data-i18n="nextStep">Wenn du ToF zum ersten Mal nutzt, öffne unten „Einrichtung & technische Details“ und starte dort die lokale Umgebung.</div>

        <details class="tech-panel">
          <summary data-i18n="techTitle">Einrichtung & technische Details</summary>
          <div class="tech-body">
            <div class="actions">
              <button class="secondary" onclick="runAction('setup')" data-i18n="setupButton">Einrichtung vorbereiten</button>
              <button class="secondary" onclick="runAction('up')" data-i18n="upButton">Lokale Umgebung starten</button>
              <button class="secondary" onclick="runAction('check')" data-i18n="checkButton">Prüfen, ob alles bereit ist</button>
              <button class="ghost" onclick="runAction('status')" data-i18n="statusButton">Technischen Status anzeigen</button>
              <button class="ghost" onclick="runAction('doctor')" data-i18n="doctorButton">Probleme finden</button>
              <button class="ghost" onclick="runAction('down')" data-i18n="downButton">Lokale Umgebung stoppen</button>
            </div>

            <p class="subhead" data-i18n="usefulLinks">Weitere technische Seiten</p>
            <div class="actions">
              <button class="ghost" onclick="openLink('openwebui')" data-i18n="openWebui">Erweiterte Arbeitsoberfläche öffnen</button>
              <button class="ghost" onclick="openLink('search_docs')" data-i18n="openSearchDocs">Technische Such-Dokumentation</button>
              <button class="ghost" onclick="openLink('qa_docs')" data-i18n="openQaDocs">Technische Antwort-Dokumentation</button>
              <button class="ghost" onclick="openLink('catalog_docs')" data-i18n="openCatalogDocs">Technische Quellen-Dokumentation</button>
            </div>

            <details>
              <summary data-i18n="activityLog">Technisches Protokoll</summary>
              <div class="log"><pre id="log">ToF Knowledge ist bereit.</pre></div>
            </details>
          </div>
        </details>
      </div>
    </main>

    <footer class="footer">
      <span>ToF Systems · Knowledge</span>
      <span data-i18n="footerText">Lokal arbeiten · Quellen sichtbar halten</span>
    </footer>
  </div>
  <script>
    const I18N = {
      de: {
        navigationLabel: 'Seitennavigation',
        qaLimitLabel: 'Maximale Anzahl berücksichtigter Treffer',
        searchLimitLabel: 'Maximale Anzahl Suchtreffer',
        refreshSourceFolders: 'Quellenordner aktualisieren',
        readOnlyExcerpt: 'Schreibgeschützter Textauszug · bis zu',
        characters: 'Zeichen',
        segmentLabel: 'Segment',
        disabledLabel: 'deaktiviert',
        sourceDefaultLabel: 'Alle eingebundenen Dokumente',
        searchHitLabel: 'Suchtreffer',
        unknownLabel: 'unbekannt',
        scannedLabel: 'eingelesen',
        failedCountLabel: 'fehlgeschlagen',
        noEvidenceBroadText: 'Keine belastbare Antwort gefunden. Eine breite Stichwortsuche lieferte nur ungeprüfte Treffer, keine ausreichenden Antwortbelege.',
        noEvidenceText: 'Keine belastbare Antwort gefunden. Es wurden keine passenden Fundstellen im erlaubten Scope gefunden.',
        answerExcerptIntro: 'Belegbasierte Kurzantwort (Quellenauszüge, keine unabhängige Verifikation):',
        strongestHitIntro: 'Stärkster Treffer aus',
        evidenceUsedIntro: 'Verwendete Fundstellen:',
        searchStrategy_original_question: 'Originalfrage',
        searchStrategy_keywords: 'Suchbegriffe',
        searchStrategy_keywords_variant: 'Suchbegriffe (Wortvariante)',
        searchStrategy_broad: 'Breite Stichwortsuche (nicht als Beleg verwendet)',
        searchStrategy_none: 'Kein Suchtreffer',
        status_no_evidence: 'Keine ausreichenden Belege',
        status_single_document_matches: 'Treffer aus einem Dokument',
        status_multiple_document_matches: 'Treffer aus mehreren Dokumenten',
        status_broad_keyword_matches: 'Breite Stichworttreffer (ungeprüft)',
        uncertainty_no_evidence: 'Keine ausreichenden Belege',
        uncertainty_broad_keyword_search: 'Nur breite Stichworttreffer',
        uncertainty_confidence_uncalibrated: 'Trefferwert ist keine geprüfte Wahrscheinlichkeit',
        uncertainty_limited_independent_sources: 'Nur wenige unabhängige Quellen',
        uncertainty_lexical_variant_not_semantically_verified: 'Wortvariante ohne eigenständige Bedeutungsprüfung',
        unverifiedCandidates: 'Nicht überprüfte Treffer',
        navSources: 'Quellen & Index',
        navEvidence: 'Beleg prüfen',
        navSearch: 'Dokumente durchsuchen',
        navAsk: 'Frage stellen',
        heroEyebrow: 'DEINE DOKUMENTE · DEINE QUELLEN',
        heroTitle: 'Frag deine Dokumente.',
        heroLead: 'Durchsuche deine lokalen Unterlagen oder stelle eine Frage. Antworten zeigen dir, auf welche Dokumente sie sich stützen.',
        heroPointOne: 'Suche direkt in deinen eigenen Unterlagen.',
        heroPointTwo: 'Antworten zeigen die verwendeten Quellen.',
        heroPointThree: 'Wenn keine passende Grundlage gefunden wird, bleibt das sichtbar.',
        answerEyebrow: 'FRAGE STELLEN',
        searchEyebrow: 'DOKUMENTE DURCHSUCHEN',
        techTitle: 'Einrichtung & technische Details',
        footerText: 'Lokal arbeiten · Quellen sichtbar halten',
        heroNote: 'Deine Unterlagen und Anfragen bleiben auf diesem Computer.',
        mainActions: 'Einrichtung',
        setupButton: 'Einrichtung vorbereiten',
        upButton: 'Lokale Umgebung starten',
        checkButton: 'Prüfen, ob alles bereit ist',
        statusButton: 'Technischen Status anzeigen',
        doctorButton: 'Probleme finden',
        downButton: 'Lokale Umgebung stoppen',
        usefulLinks: 'Weitere technische Seiten',
        openWebui: 'Erweiterte Arbeitsoberfläche öffnen',
        openSearchDocs: 'Technische Such-Dokumentation',
        openQaDocs: 'Technische Antwort-Dokumentation',
        openCatalogDocs: 'Technische Quellen-Dokumentation',
        nextStep: 'Wenn du ToF zum ersten Mal nutzt, öffne unten „Einrichtung & technische Details“ und starte dort die lokale Umgebung.',
        searchTitle: 'Finde passende Stellen direkt.',
        searchPlaceholder: 'Wonach möchtest du suchen?',
        scopePlaceholder: 'Optional: Suche auf bestimmte Quellen begrenzen',
        runSearch: 'Dokumente durchsuchen',
        searchHint: 'Du bekommst die passendsten Fundstellen mit Dokument und Textausschnitt.',
        noSearchYet: 'Hier erscheinen passende Fundstellen aus deinen Dokumenten.',
        answerTitle: 'Was möchtest du aus deinen Dokumenten wissen?',
        questionPlaceholder: 'Zum Beispiel: Was steht in meinen Unterlagen zur Urlaubsregelung?',
        runAnswer: 'Antwort aus meinen Dokumenten holen',
        answerHint: 'ToF sucht passende Stellen und zeigt die verwendeten Quellen zusammen mit der Antwort.',
        noAnswerYet: 'Hier erscheint deine Antwort mit den dazugehörigen Quellen.',
        activityLog: 'Technisches Protokoll',
        languageButton: 'English',
        skipLink: 'Zum Inhalt springen',
        questionLabel: 'Frage an deine Dokumente',
        searchLabel: 'Dokumente durchsuchen',
        scopeLabel: 'Suche optional auf bestimmte Quellen begrenzen',
        tryAgainHelp: 'Prüfe zuerst, ob die lokale Umgebung läuft. Wenn das Problem bleibt, öffne „Einrichtung & technische Details“ und wähle „Probleme finden“.',
        technicalError: 'Technische Details anzeigen',
        noHitsHelp: 'Versuche andere Suchbegriffe oder prüfe, ob die passenden Dokumente bereits eingelesen wurden.',
        themeButtonLight: 'Hell',
        themeButtonDark: 'Dunkel',
        searchFailed: 'Suche fehlgeschlagen',
        issueInvalid: 'Bitte prüfe die Eingabe und versuche es erneut.',
        issueService: 'Ein lokaler Dienst ist nicht erreichbar. Öffne Einrichtung & technische Details und wähle Probleme finden.',
        issueConfig: 'Die eingestellten lokalen Ports sind ungültig. Prüfe die .env-Konfiguration.',
        issueProcess: 'Die Anfrage konnte nicht verarbeitet werden. Technische Details sind unten verfügbar.',
        issueDetails: 'Technische Fehlerdetails',
        issuePending: 'Diese Quelle enthält noch nicht indexierte Dokumente. Die Indexierung kann über die vorhandene Schaltfläche fortgesetzt werden.',
        issueFailedDocs: 'Einige Dokumente konnten nicht indexiert werden. Details stehen im Indexierungsbericht.',
        noHits: 'Dazu wurde in deinen Dokumenten nichts Passendes gefunden.',
        query: 'Suche',
        returned: 'Gefunden',
        hits: 'Treffer',
        source: 'Quelle',
        document: 'Dokument',
        citation: 'Quelle',
        score: 'Übereinstimmung',
        rawSearch: 'Technische Suchdetails anzeigen',
        answerFailed: 'Die Antwort konnte nicht erstellt werden',
        noAnswerText: 'Keine Antwort zurückgegeben.',
        confidence: 'Heuristischer Trefferwert (keine Wahrscheinlichkeit)',
        uncertainties: 'Was noch unklar ist',
        citations: 'Verwendete Quellen',
        evidenceRefs: 'Nachvollziehbare Fundstellen',
        evidenceSignal: 'Suchbelege (keine Prüfung der Richtigkeit)',
        evidenceStrategy: 'Suchweg',
        evidenceSegments: 'Gefundene Textabschnitte',
        evidenceDocuments: 'Unterschiedliche Dokumente',
        evidenceCaution: 'Breite Stichwortsuche: Ergebnisse können nur einzelne Suchbegriffe enthalten.',
        viewEvidence: 'Textstelle ansehen',
        evidenceEyebrow: 'BELEG PRÜFEN',
        evidenceTitle: 'Textstelle nachvollziehen',
        evidenceHint: 'Öffne einen Beleg aus Suche oder Antwort. Nur aktuell indexierte Fundstellen werden angezeigt.',
        evidenceEmpty: 'Wähle eine Fundstelle.',
        evidenceUnavailable: 'Diese Fundstelle ist nicht mehr verfügbar oder wurde noch nicht indexiert.',
        usedDocuments: 'Verwendete Dokumente',
        searchQueries: 'Verwendete Suchbegriffe',
        rawAnswer: 'Technische Antwortdetails anzeigen',
        summaryRefreshed: 'Statushinweis aktualisiert.',
        runningAction: 'Führe Aktion aus',
        opening: 'Öffne',
        runningSearch: 'Lokale Suche läuft ...',
        searchFinished: 'Suche abgeschlossen.',
        runningAnswer: 'Antwort wird aus deinen Dokumenten erstellt ...',
        answerFinished: 'Antwort ist fertig.',
        uiStarted: 'ToF Knowledge ist bereit.',
        sourcesEyebrow: 'QUELLEN & INDEX',
        sourcesTitle: 'Deine Quellen im Überblick',
        sourcesHint: 'Welche Dokumente indexiert sind und wo noch Arbeit ansteht.',
        refreshSources: 'Quellen aktualisieren',
        sourcesEmpty: 'Hier erscheinen die erfassten Quellen und Indexstände.',
        sourcesLocalOnly: 'Lokale Einzelbenutzer-Ansicht. Keine aktive Mehrbenutzer-Berechtigung.',
        sourceUnavailable: 'Quellenstatus ist nicht erreichbar. Prüfe die lokale Umgebung.',
        indexBatch: 'Konfigurierte Quelle indexieren',
        indexSourceLabel: 'Quellenbereich innerhalb des eingestellten Dokumentenordners',
        indexSourceEmpty: 'Keine Quellenbereiche erreichbar. Dokumentenordner in der Einrichtung prüfen.',
        indexSourceNote: 'Unterordner werden als getrennte Quellen erfasst; es werden keine fremden Host-Ordner eingebunden.',
        indexHint: 'Nur auf Klick: eine begrenzte Charge der konfigurierten, schreibgeschützten Quelle einlesen.',
        indexFailed: 'Indexierung fehlgeschlagen:',
        indexSuccess: 'Indexiert in dieser Charge',
        indexAgain: 'Für weitere offene Dokumente erneut starten.',
        indexRunning: 'Indexierung läuft…',
        indexPage: 'Weitere Dateien folgen; nächste Charge fortsetzen.',
        indexFinished: 'Dateiliste bis zum Ende durchlaufen.',
        indexReset: 'Dateidurchlauf neu beginnen',
        indexMissingNote: 'Bei großen Quellen ist die Fehlbestandserkennung nur für vollständige Einzelscans verfügbar.',
        sourceNoData: 'Noch keine Quellen registriert.',
        sourceIndexed: 'Indexiert',
        sourcePending: 'Offen',
        sourceFailed: 'Fehlgeschlagen',
        sourceMissing: 'Fehlend',
        sourceTotal: 'Dokumente',
        sourceLastScan: 'Letzter Scan',
        selectSource: 'Diese Quelle durchsuchen',
      },
      en: {
        navigationLabel: 'Page navigation',
        qaLimitLabel: 'Maximum number of considered matches',
        searchLimitLabel: 'Maximum number of search results',
        refreshSourceFolders: 'Refresh source folders',
        readOnlyExcerpt: 'Read-only excerpt · up to',
        characters: 'characters',
        segmentLabel: 'Segment',
        disabledLabel: 'disabled',
        sourceDefaultLabel: 'All mounted documents',
        searchHitLabel: 'Search hit',
        unknownLabel: 'unknown',
        scannedLabel: 'scanned',
        failedCountLabel: 'failed',
        noEvidenceBroadText: 'No reliable answer found. A broad keyword search returned unverified matches, not sufficient evidence to answer.',
        noEvidenceText: 'No reliable answer found. No matching evidence was found within the permitted source scope.',
        answerExcerptIntro: 'Evidence-based excerpt answer (source passages, not independently verified):',
        strongestHitIntro: 'Strongest match from',
        evidenceUsedIntro: 'Evidence passages used:',
        searchStrategy_original_question: 'Original question',
        searchStrategy_keywords: 'Keywords',
        searchStrategy_keywords_variant: 'Keywords (word variant)',
        searchStrategy_broad: 'Broad keyword search (not used as evidence)',
        searchStrategy_none: 'No matching evidence',
        status_no_evidence: 'Insufficient evidence',
        status_single_document_matches: 'Matches from one document',
        status_multiple_document_matches: 'Matches from multiple documents',
        status_broad_keyword_matches: 'Broad keyword matches (unverified)',
        uncertainty_no_evidence: 'Insufficient evidence',
        uncertainty_broad_keyword_search: 'Broad keyword matches only',
        uncertainty_confidence_uncalibrated: 'Match score is not a calibrated probability',
        uncertainty_limited_independent_sources: 'Limited independent sources',
        uncertainty_lexical_variant_not_semantically_verified: 'Word variant without independent semantic verification',
        unverifiedCandidates: 'Unverified candidate matches',
        navSources: 'Sources & Index',
        navEvidence: 'Inspect evidence',
        navSearch: 'Search documents',
        navAsk: 'Ask a question',
        heroEyebrow: 'YOUR DOCUMENTS · YOUR SOURCES',
        heroTitle: 'Ask your documents.',
        heroLead: 'Search your local documents or ask a question. Answers show which documents they are based on.',
        heroPointOne: 'Search directly across your own documents.',
        heroPointTwo: 'Answers show the sources they used.',
        heroPointThree: 'If there is not enough evidence, that stays visible.',
        answerEyebrow: 'ASK A QUESTION',
        searchEyebrow: 'SEARCH DOCUMENTS',
        techTitle: 'Setup & technical details',
        footerText: 'Work locally · keep sources visible',
        heroNote: 'Your documents and questions stay on this computer.',
        mainActions: 'Setup',
        setupButton: 'Prepare setup',
        upButton: 'Start local environment',
        checkButton: 'Check if everything is ready',
        statusButton: 'Show technical status',
        doctorButton: 'Find problems',
        downButton: 'Stop local environment',
        usefulLinks: 'More technical pages',
        openWebui: 'Open advanced workspace',
        openSearchDocs: 'Technical search documentation',
        openQaDocs: 'Technical answer documentation',
        openCatalogDocs: 'Technical source documentation',
        nextStep: 'If this is your first time using ToF, open “Setup & technical details” below and start the local environment there.',
        searchTitle: 'Find matching passages directly.',
        searchPlaceholder: 'What would you like to find?',
        scopePlaceholder: 'Optional: limit the search to specific sources',
        runSearch: 'Search documents',
        searchHint: 'You will see the best matching passages with their document and text excerpt.',
        noSearchYet: 'Matching passages from your documents will appear here.',
        answerTitle: 'What would you like to know from your documents?',
        questionPlaceholder: 'For example: What do my documents say about the vacation policy?',
        runAnswer: 'Answer from my documents',
        answerHint: 'ToF finds matching passages and shows the sources together with the answer.',
        noAnswerYet: 'Your answer and its sources will appear here.',
        activityLog: 'Technical log',
        languageButton: 'Deutsch',
        skipLink: 'Skip to content',
        questionLabel: 'Question for your documents',
        searchLabel: 'Search documents',
        scopeLabel: 'Optionally limit the search to specific sources',
        tryAgainHelp: 'First check that the local environment is running. If the problem remains, open “Setup & technical details” and choose “Find problems”.',
        technicalError: 'Show technical details',
        noHitsHelp: 'Try different search words or check whether the relevant documents have already been added.',
        themeButtonLight: 'Light',
        themeButtonDark: 'Dark',
        searchFailed: 'Search failed',
        issueInvalid: 'Check your input and try again.',
        issueService: 'A local service is unavailable. Open Setup & technical details and choose Find problems.',
        issueConfig: 'The configured local ports are invalid. Check your .env configuration.',
        issueProcess: 'The request could not be processed. Technical details remain available below.',
        issueDetails: 'Technical error details',
        issuePending: 'Some documents in this source have not been indexed. Continue indexing using the existing button.',
        issueFailedDocs: 'Some documents could not be indexed. See the indexing report for details.',
        noHits: 'Nothing relevant was found in your documents.',
        query: 'Search',
        returned: 'Found',
        hits: 'hit(s)',
        source: 'Source',
        document: 'Document',
        citation: 'Source',
        score: 'Match',
        rawSearch: 'Show technical search details',
        answerFailed: 'The answer could not be created',
        noAnswerText: 'No answer text returned.',
        confidence: 'Heuristic match score (not a probability)',
        uncertainties: 'What is still unclear',
        citations: 'Sources used',
        evidenceRefs: 'Traceable evidence references',
        evidenceSignal: 'Retrieved evidence (not factual verification)',
        evidenceStrategy: 'Search method',
        evidenceSegments: 'Matching excerpts',
        evidenceDocuments: 'Distinct documents',
        evidenceCaution: 'Broad keyword search: results may match only one search term.',
        viewEvidence: 'View excerpt',
        evidenceEyebrow: 'INSPECT EVIDENCE',
        evidenceTitle: 'Trace an excerpt',
        evidenceHint: 'Open an excerpt from a search or answer. Only current indexed evidence is shown.',
        evidenceEmpty: 'Choose an evidence reference.',
        evidenceUnavailable: 'This excerpt is unavailable or no longer indexed.',
        usedDocuments: 'Used documents',
        searchQueries: 'Search terms used',
        rawAnswer: 'Show technical answer details',
        summaryRefreshed: 'Summary refreshed.',
        runningAction: 'Running action',
        opening: 'Opening',
        runningSearch: 'Running local search ...',
        searchFinished: 'Search finished.',
        runningAnswer: 'Building an answer from your documents ...',
        answerFinished: 'Answer is ready.',
        uiStarted: 'ToF Knowledge is ready.',
        sourcesEyebrow: 'SOURCES & INDEX',
        sourcesTitle: 'Your sources at a glance',
        sourcesHint: 'See which documents are indexed and which still need attention.',
        refreshSources: 'Refresh sources',
        sourcesEmpty: 'Registered sources and index status will appear here.',
        sourcesLocalOnly: 'Local single-user view only. Multi-user permissions are not active.',
        sourceUnavailable: 'Source status is not reachable. Check the local environment.',
        indexBatch: 'Index configured source',
        indexSourceLabel: 'Source space inside the configured document folder',
        indexSourceEmpty: 'No source spaces available. Check the configured document folder.',
        indexSourceNote: 'Subfolders are separate logical sources; external host folders are never mounted automatically.',
        indexHint: 'Only on click: scan a bounded batch from the configured read-only source.',
        indexFailed: 'Indexing failed:',
        indexSuccess: 'Indexed in this batch',
        indexAgain: 'Run again for any remaining pending documents.',
        indexRunning: 'Indexing in progress…',
        indexPage: 'More files remain; continue with the next batch.',
        indexFinished: 'Reached the end of the file list.',
        indexReset: 'Start scanning from beginning',
        indexMissingNote: 'For large sources, missing-file reconciliation requires a complete single-pass scan.',
        sourceNoData: 'No sources registered yet.',
        sourceIndexed: 'Indexed',
        sourcePending: 'Pending',
        sourceFailed: 'Failed',
        sourceMissing: 'Missing',
        sourceTotal: 'Documents',
        sourceLastScan: 'Last scan',
        selectSource: 'Search this source',
      },
    };

    let currentLanguage = localStorage.getItem('tof_local_knowledge_language') === 'en' ? 'en' : 'de';
    let currentTheme = localStorage.getItem('tof_local_knowledge_theme') || 'dark';
    let indexCursor = null;
    let availableSourceSpaces = [];
    let lastSearchData = null;
    let lastAnswerData = null;
    let lastIndexData = null;
    let lastEvidenceSegment = null;

    function t(key) {
      return (I18N[currentLanguage] && I18N[currentLanguage][key]) || I18N.de[key] || key;
    }

    function translatedCode(prefix, code) {
      const key = prefix + '_' + String(code || '');
      return (I18N[currentLanguage] && I18N[currentLanguage][key]) ||
        I18N.de[key] || String(code || t('unknownLabel'));
    }

    function localizeAnswerText(raw) {
      const value = String(raw || '');
      if (value.startsWith('Keine belastbare Antwort gefunden. Eine breite Stichwortsuche')) {
        return t('noEvidenceBroadText');
      }
      if (value.startsWith('Keine belastbare Antwort gefunden. Es wurden keine passenden Fundstellen')) {
        return t('noEvidenceText');
      }
      if (!value.startsWith('Belegbasierte Kurzantwort (Quellenauszüge, keine unabhängige Verifikation):')) {
        // User-authored document excerpts and arbitrary backend messages must
        // never be machine-translated or silently rewritten.
        return value;
      }
      return value
        .replace('Belegbasierte Kurzantwort (Quellenauszüge, keine unabhängige Verifikation):',
                 t('answerExcerptIntro'))
        .replace('Stärkster Treffer aus ', t('strongestHitIntro') + ' ')
        .replace('Verwendete Fundstellen:', t('evidenceUsedIntro'));
    }

    function applyLanguage() {
      document.documentElement.lang = currentLanguage;
      document.querySelectorAll('[data-i18n]').forEach((element) => {
        element.textContent = t(element.dataset.i18n);
      });
      document.querySelectorAll('[data-i18n-placeholder]').forEach((element) => {
        element.placeholder = t(element.dataset.i18nPlaceholder);
      });
      document.querySelectorAll('[data-i18n-aria-label]').forEach((element) => {
        element.setAttribute('aria-label', t(element.dataset.i18nAriaLabel));
      });
      const active = document.querySelector('.page-nav a[aria-current="page"]');
      document.title = 'ToF Knowledge · ' + (active ? active.textContent : t('navAsk'));
      if (lastSearchData) renderSearchResult(lastSearchData);
      if (lastAnswerData) renderAnswerResult(lastAnswerData);
      if (lastIndexData) renderIndexBatchResult(lastIndexData);
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
      if (document.getElementById('source-result')) {
        loadSourceSpaces().then(refreshSources);
      }
      if (lastEvidenceSegment && document.getElementById('evidence-result')) {
        inspectEvidence(lastEvidenceSegment);
      }
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

    function bindEvidenceButtons(root) {
      root.querySelectorAll('button[data-evidence-segment]').forEach(button => {
        button.addEventListener('click', () => inspectEvidence(button.dataset.evidenceSegment));
      });
    }

    async function inspectEvidence(segmentId) {
      if (!/^[A-Za-z0-9_-]{1,128}$/.test(segmentId)) return;
      if (window.location.pathname !== '/beleg-pruefen') {
        window.location.assign('/beleg-pruefen?segment_id=' + encodeURIComponent(segmentId));
        return;
      }
      const panel = document.getElementById('evidence-result');
      lastEvidenceSegment = segmentId;
      panel.textContent = t('evidenceEmpty');
      try {
        const query = new URLSearchParams({segment_id: segmentId});
        const response = await fetch('/api/evidence?' + query.toString());
        const data = await response.json();
        if (!response.ok || !data.evidence) {
          panel.textContent = t('evidenceUnavailable');
          return;
        }
        panel.replaceChildren();
        const e = data.evidence;
        const heading = document.createElement('strong');
        heading.textContent = e.citation_label + ' · ' + e.relative_path;
        const detail = document.createElement('p');
        detail.className = 'muted';
        detail.textContent = e.source_id + ' · ' + e.document_id + ' · ' + e.segment_id;
        const excerpt = document.createElement('pre');
        excerpt.className = 'preview';
        excerpt.style.whiteSpace = 'pre-wrap';
        excerpt.textContent = e.excerpt || '';
        const note = document.createElement('p');
        note.className = 'muted';
        note.textContent = t('readOnlyExcerpt') + ' ' + data.truncated_to_chars + ' ' + t('characters') + '.';
        panel.append(heading, detail, excerpt, note);
        panel.scrollIntoView({behavior: 'smooth', block: 'nearest'});
      } catch (error) {
        panel.textContent = t('evidenceUnavailable');
      }
    }

    function friendlyIssue(error) {
      const code = String(error || '');
      if (code === 'service_unavailable' || code === 'source_status_unavailable'
          || code === 'request_failed') return t('issueService');
      if (code === 'invalid_configuration' || code.startsWith('invalid_local_port'))
        return t('issueConfig');
      if (code === 'invalid_request' || code.startsWith('http_error_4')
          || code === 'same_origin_json_required') return t('issueInvalid');
      return t('issueProcess');
    }

    function errorMarkup(data, title) {
      return '<div class="result-card"><strong>' + escapeHtml(title) + '</strong>'
        + '<p class="muted">' + escapeHtml(friendlyIssue(data.error)) + '</p>'
        + '<details><summary>' + escapeHtml(t('issueDetails')) + '</summary><pre>'
        + escapeHtml(JSON.stringify(data, null, 2)) + '</pre></details></div>';
    }

    function renderSearchResult(data) {
      lastSearchData = data;
      const root = document.getElementById('search-result');
      if (data.error) {
        root.innerHTML = errorMarkup(data, t('searchFailed'));
        return;
      }
      const hits = data.results || data.hits || [];
      if (!hits.length) {
        root.innerHTML = `<div class=\"muted\">${t('noHits')}</div>`;
        return;
      }
      let html = `<div class=\"muted\">${t('query')}: ${escapeHtml(data.query || '')} · ${t('returned')} ${hits.length} ${t('hits')}.</div>`;
      for (const hit of hits) {
        const title = hit.relative_path || hit.title || hit.document_title || hit.document_id || t('searchHitLabel');
        const preview = hit.preview_text || hit.snippet || hit.text || hit.chunk_text || '';
        html += `<div class=\"result-card\"><strong>${escapeHtml(title)}</strong>`;
        html += '<div class=\"meta-grid\">';
        if (hit.source_id) html += `<div class=\"muted\">${t('source')}: ${escapeHtml(hit.source_id)}</div>`;
        if (hit.document_id) html += `<div class=\"muted\">${t('document')}: ${escapeHtml(hit.document_id)}</div>`;
        if (hit.citation_label) html += `<div class=\"muted\">${t('citation')}: ${escapeHtml(hit.citation_label)}</div>`;
        if (hit.score !== undefined && hit.score !== null) html += `<div class=\"muted\">${t('score')}: ${escapeHtml(hit.score)}</div>`;
        html += '</div>';
        if (preview) html += `<div class=\"preview\">${escapeHtml(preview)}</div>`;
        if (hit.segment_id) html += `<button class=\"secondary\" type=\"button\" data-evidence-segment=\"${escapeHtml(hit.segment_id)}\">${t('viewEvidence')}</button>`;
        html += `</div>`;
      }
      html += `<details><summary>${t('rawSearch')}</summary><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre></details>`;
      root.innerHTML = html;
      bindEvidenceButtons(root);
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
      lastAnswerData = data;
      const root = document.getElementById('qa-result');
      if (data.error) {
        root.innerHTML = errorMarkup(data, t('answerFailed'));
        return;
      }
      const answer = localizeAnswerText(data.answer_text || data.answer || t('noAnswerText'));
      const confidence = data.confidence ?? t('unknownLabel');
      const citations = asList(data.citations);
      const evidenceRefs = asList(data.evidence_refs);
      const usedDocuments = asList(data.used_documents);
      const uncertainties = asList(data.uncertainties);
      const searchQueries = asList(data.search_queries);
      const signal = data.evidence_signal || null;

      let html = `<div class=\"result-card\"><div class=\"answer-main\">${escapeHtml(answer)}</div><div class=\"muted\" style=\"margin-top:10px;\">${t('confidence')}: ${escapeHtml(confidence)}</div>`;
      if (signal) {
        html += '<div class="muted" style="margin-top:10px"><strong>'
          + t('evidenceSignal') + '</strong><br>'
          + t('evidenceStrategy') + ': ' + escapeHtml(translatedCode('searchStrategy', signal.search_strategy))
          + ' · ' + t('evidenceSegments') + ': ' + escapeHtml(signal.matching_segments || 0)
          + ' · ' + t('evidenceDocuments') + ': ' + escapeHtml(signal.distinct_documents || 0)
          + '</div>';
        if (signal.unverified_candidates) {
          html += '<div class="muted">' + t('unverifiedCandidates') + ': ' +
            escapeHtml(signal.unverified_candidates) + '</div>';
        }
        if (signal.status === 'broad_keyword_matches' || signal.search_strategy === 'broad') {
          html += '<div class="muted" style="margin-top:10px">'
            + t('evidenceCaution') + '</div>';
        }
      }
      if (uncertainties.length) {
        html += `<div style=\"margin-top:10px;\"><strong>${t('uncertainties')}</strong>${renderChips(uncertainties.map(code => translatedCode('uncertainty', code)), 'warn')}</div>`;
      }
      html += '</div>';

      if (citations.length) {
        html += `<div class=\"result-card\"><strong>${t('citations')}</strong>`;
        for (const citation of citations) {
          html += renderCitation(citation);
        }
        html += `</div>`;
      }
      if (evidenceRefs.length) {
        html += '<div class="result-card"><strong>' + t('evidenceRefs') + '</strong>';
        for (const ref of evidenceRefs) {
          html += '<div class="meta-grid" style="margin-top:8px">';
          html += '<div class="muted">' + escapeHtml(ref.relative_path || '') + '</div>';
          html += '<div class="muted">' + escapeHtml(ref.citation_label || '') + '</div>';
          html += '<div class="muted">' + t('segmentLabel') + ': ' + escapeHtml(ref.segment_id || '') + '</div>';
          if (ref.segment_id) html += '<button class="secondary" type="button" data-evidence-segment="' + escapeHtml(ref.segment_id) + '">' + t('viewEvidence') + '</button>';
          html += '</div>';
        }
        html += '</div>';
      }
      if (usedDocuments.length) {
        html += `<div class=\"result-card\"><strong>${t('usedDocuments')}</strong>${renderChips(usedDocuments)}</div>`;
      }
      if (searchQueries.length) {
        html += `<div class=\"result-card\"><strong>${t('searchQueries')}</strong>${renderChips(searchQueries)}</div>`;
      }
      html += `<details><summary>${t('rawAnswer')}</summary><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre></details>`;
      root.innerHTML = html;
      bindEvidenceButtons(root);
    }

    async function refreshSummary() {
      await fetch('/api/summary');
      document.getElementById('next-step').textContent = t('nextStep');
      appendLog(t('summaryRefreshed'));
    }

    async function runAction(action) {
      const actionLabels = {
        setup: 'setupButton', up: 'upButton', check: 'checkButton',
        status: 'statusButton', doctor: 'doctorButton', down: 'downButton',
      };
      appendLog(`${t('runningAction')}: ${t(actionLabels[action] || action)} ...`);
      const response = await fetch(`/api/${action}`, { method: 'POST' });
      const data = await response.json();
      appendLog(JSON.stringify(data, null, 2));
      await refreshSummary();
    }

    async function openLink(name) {
      const linkLabels = {
        openwebui: 'openWebui', search_docs: 'openSearchDocs',
        qa_docs: 'openQaDocs', catalog_docs: 'openCatalogDocs',
      };
      appendLog(`${t('opening')}: ${t(linkLabels[name] || name)} ...`);
      const response = await fetch(`/api/open/${name}`, { method: 'POST' });
      const data = await response.json();
      appendLog(JSON.stringify(data, null, 2));
    }

    async function loadSourceSpaces() {
      const menu = document.getElementById('index-source-select');
      const status = document.getElementById('index-source-message');
      const current = menu.value;
      try {
        const response = await fetch('/api/source-spaces');
        const data = await response.json();
        availableSourceSpaces = data.spaces || [];
        menu.replaceChildren();
        availableSourceSpaces.forEach(space => {
          if (!space.available) return;
          const option = document.createElement('option');
          option.value = space.id;
          option.textContent = (space.label === 'All mounted documents' ?
            t('sourceDefaultLabel') : space.label) + ' (' + space.id + ')';
          menu.appendChild(option);
        });
        if ([...menu.options].some(option => option.value === current)) menu.value = current;
        status.textContent = menu.options.length ? t('indexSourceNote') : t('indexSourceEmpty');
        document.getElementById('index-batch-button').disabled = !menu.options.length;
      } catch (error) {
        status.textContent = t('indexSourceEmpty');
        document.getElementById('index-batch-button').disabled = true;
      }
    }

    function resetIndexCursor() {
      indexCursor = null;
      lastIndexData = null;
      document.getElementById('index-batch-result').textContent = t('indexHint');
    }

    function renderIndexBatchResult(outcome) {
      const result = document.getElementById('index-batch-result');
      if (outcome.failed) {
        const data = outcome.data;
        result.textContent = t('indexFailed') + ' ' +
          friendlyIssue(data.error || data.detail);
        return;
      }
      const data = outcome.data;
      result.textContent = t('indexSuccess') + ': ' + (data.indexed_this_pass || 0) +
        ' / ' + (data.files_scanned || 0) + ' ' + t('scannedLabel') + '. ' +
        (data.failed || []).length + ' ' + t('failedCountLabel') + '. ' +
        (data.page_has_more ? t('indexPage') : t('indexFinished'));
    }

    async function runIndexBatch() {
      const button = document.getElementById('index-batch-button');
      const result = document.getElementById('index-batch-result');
      button.disabled = true;
      result.textContent = t('indexRunning');
      try {
        const response = await fetch('/api/index-batch', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            cursor: indexCursor,
            space_id: document.getElementById('index-source-select').value,
          }),
        });
        const data = await response.json();
        const failed = !response.ok || data.status === 'error';
        lastIndexData = { data, failed };
        renderIndexBatchResult(lastIndexData);
        if (!failed) {
          indexCursor = data.next_cursor || null;
          await refreshSources();
        }
      } catch (error) {
        result.textContent = t('indexFailed') + ' ' + String(error);
      } finally {
        button.disabled = false;
      }
    }

    async function refreshSources() {
      const root = document.getElementById('source-result');
      root.textContent = t('sourcesEmpty');
      try {
        const response = await fetch('/api/sources');
        const data = await response.json();
        if (!response.ok || data.error) {
          root.textContent = t('sourceUnavailable');
          return;
        }
        const sources = data.sources || [];
        if (!sources.length) {
          root.textContent = t('sourceNoData');
          return;
        }
        root.replaceChildren();
        for (const source of sources) {
          const panel = document.createElement('div');
          panel.className = 'result-card';
          const title = document.createElement('strong');
          const matchingSpace = availableSourceSpaces.find(space => space.id === source.source_id);
          const label = matchingSpace ? matchingSpace.label : (source.display_name || source.source_id);
          title.textContent = (label === 'All mounted documents' ?
            t('sourceDefaultLabel') : label)
            + (source.enabled ? '' : ' (' + t('disabledLabel') + ')');
          const stats = document.createElement('div');
          stats.className = 'muted';
          const number = value => Number(value || 0);
          stats.textContent = t('sourceTotal') + ': ' + number(source.documents_total)
            + ' · ' + t('sourceIndexed') + ': ' + number(source.indexed)
            + ' · ' + t('sourcePending') + ': ' + number(source.pending)
            + ' · ' + t('sourceFailed') + ': ' + number(source.failed)
            + ' · ' + t('sourceMissing') + ': ' + number(source.missing);
          const scan = document.createElement('div');
          scan.className = 'muted';
          scan.textContent = t('sourceLastScan') + ': '
            + (source.last_scan_at ? new Date(source.last_scan_at).toLocaleString() : '—');
          const select = document.createElement('button');
          select.className = 'secondary';
          select.type = 'button';
          select.style.marginTop = '10px';
          select.textContent = t('selectSource');
          select.disabled = !source.enabled;
          select.addEventListener('click', () => {
            window.location.assign('/dokumente-durchsuchen?source_id=' +
              encodeURIComponent(source.source_id));
          });
          panel.append(title, stats, scan, select);
          if (number(source.pending) > 0) {
            const reminder = document.createElement('p');
            reminder.className = 'hint';
            reminder.textContent = t('issuePending');
            panel.appendChild(reminder);
          }
          if (number(source.failed) > 0) {
            const failure = document.createElement('p');
            failure.className = 'hint';
            failure.textContent = t('issueFailedDocs');
            panel.appendChild(failure);
          }
          root.appendChild(panel);
        }
      } catch (error) {
        root.textContent = t('sourceUnavailable');
      }
    }

    async function runSearch() {
      const payload = {
        query: document.getElementById('search-query').value,
        source_scope: parseScope(document.getElementById('search-scope').value),
        limit: Number(document.getElementById('search-limit').value || 5),
      };
      appendLog(t('runningSearch'));
      try {
        const response = await fetch('/api/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        renderSearchResult(data);
        appendLog(t('searchFinished'));
      } catch (error) {
        renderSearchResult({ error: 'request_failed', details: String(error) });
        appendLog(t('searchFailed') + ': ' + String(error));
      }
    }

    async function runAnswer() {
      const payload = {
        question: document.getElementById('qa-question').value,
        source_scope: parseScope(document.getElementById('qa-scope').value),
        limit: Number(document.getElementById('qa-limit').value || 5),
      };
      appendLog(t('runningAnswer'));
      try {
        const response = await fetch('/api/answer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        renderAnswerResult(data);
        appendLog(t('answerFinished'));
      } catch (error) {
        renderAnswerResult({ error: 'request_failed', details: String(error) });
        appendLog(t('answerFailed') + ': ' + String(error));
      }
    }

    applyTheme();
    applyLanguage();
    document.getElementById('log').textContent = t('uiStarted');
    refreshSummary();
    const params = new URLSearchParams(window.location.search);
    const sourceId = params.get('source_id');
    if (sourceId && sourceId.length <= 64) {
      const scope = document.getElementById('search-scope') ||
        document.getElementById('qa-scope');
      if (scope) scope.value = sourceId;
    }
    if (document.getElementById('source-result')) {
      loadSourceSpaces().then(refreshSources);
    }
    if (document.getElementById('evidence-result')) {
      const segmentId = params.get('segment_id');
      if (segmentId) inspectEvidence(segmentId);
    }
  </script>
</body>
</html>
"""


PAGE_ROUTES = {
    "/": "question",  # Keep the documented root URL working.
    "/frage-stellen": "question",
    "/dokumente-durchsuchen": "search",
    "/beleg-pruefen": "evidence",
    "/quellen-index": "sources",
}


def _render_page(path: str) -> str:
    """Render one navigable page with the shared header, footer and scripts.

    Page markers only control presentation. Backend search/QA/source security
    remains enforced by the existing API handlers.
    """
    page = PAGE_ROUTES[path]
    html = HTML
    for name in ("question", "search", "evidence", "sources"):
        start = f"<!-- PAGE_START:{name} -->"
        end = f"<!-- PAGE_END:{name} -->"
        pattern = re.escape(start) + r"(.*?)" + re.escape(end)
        html, count = re.subn(
            pattern,
            lambda match, selected=(name == page): match.group(1) if selected else "",
            html,
            count=1,
            flags=re.DOTALL,
        )
        if count != 1:
            raise RuntimeError(f"Missing UI page markers: {name}")
    marker = f'data-page-link="{page}"'
    if html.count(marker) != 1:
        raise RuntimeError(f"Missing UI navigation link: {page}")
    return html.replace(marker, f'aria-current="page" {marker}', 1)


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


def _configured_api_targets() -> dict[str, str]:
    return configured_targets(read_env())


def _configured_links() -> dict[str, dict[str, str]]:
    targets = _configured_api_targets()
    return {
        name: {"label": item["label"], "url": targets[name]}
        for name, item in LINKS.items()
    }


def _open_link(name: str) -> dict[str, object]:
    try:
        link = _configured_links()[name]
    except ValueError as exc:
        return {"opened": None, "error": classify_error(str(exc))}
    webbrowser.open(link["url"])
    return {"opened": link["url"], "label": link["label"]}


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    return parse_bounded_json(handler.rfile, handler.headers.get("Content-Length", ""))


def _evidence_lookup(segment_id: str) -> dict[str, object]:
    # This is a source viewer in the existing local single-user application.
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", segment_id):
        return {"error": "invalid_segment_id"}
    env = read_env()
    if env.get("BIND_HOST", "127.0.0.1") not in {"localhost", "127.0.0.1", "::1"}:
        return {"error": "local_only"}
    try:
        endpoint = _configured_api_targets()["evidence"]
    except ValueError:
        return {"error": "invalid_configuration"}
    return _get_json(f"{endpoint}/{segment_id}")


def _configured_target(name: str) -> str | None:
    try:
        return _configured_api_targets()[name]
    except ValueError:
        return None


def _get_json(url: str) -> dict[str, object]:
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        return {"error": "service_unavailable" if exc.code >= 500 else "invalid_request",
                "details": f"upstream_http_{exc.code}"}
    except (urllib.error.URLError, OSError, TimeoutError):
        return {"error": "service_unavailable"}
    except (ValueError, UnicodeError):
        return {"error": "processing_error"}


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
        return {"error": "invalid_request" if 400 <= exc.code < 500 else "processing_error",
                "details": f"upstream_http_{exc.code}"}
    except (urllib.error.URLError, OSError, TimeoutError):
        return {"error": "service_unavailable"}
    except (ValueError, UnicodeError):
        return {"error": "processing_error"}


def _ports_valid() -> bool:
    try:
        _configured_api_targets()
    except ValueError:
        return False
    return True


def _summary_payload() -> dict[str, object]:
    return {
        "next_step": "Prepare the local environment once, then ask questions or search your documents from this page.",
        "actions": [
            {"name": key, "label": spec.label, "safe_level": spec.safe_level}
            for key, spec in ACTIONS.items()
        ],
        "links": _configured_links() if _ports_valid() else {},
        "configuration_error": None if _ports_valid() else "invalid_configuration",
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
            if parsed.path in PAGE_ROUTES:
                self._send(200, "text/html; charset=utf-8",
                           _render_page(parsed.path).encode("utf-8"))
                return
            if parsed.path == "/api/summary":
                self._send(200, "application/json; charset=utf-8", _json_bytes(_summary_payload()))
                return
            if parsed.path == "/api/evidence":
                params = parse_qs(parsed.query)
                segment_id = params.get("segment_id", [""])[0]
                response = _evidence_lookup(segment_id)
                code = 400 if response.get("error") == "invalid_segment_id" else (503 if response.get("error") else 200)
                self._send(code, "application/json; charset=utf-8", _json_bytes(response))
                return
            if parsed.path == "/api/source-spaces":
                result = discover_source_spaces(read_env())
                self._send(200, "application/json; charset=utf-8", _json_bytes(result))
                return
            if parsed.path == "/api/sources":
                target = _configured_target("sources")
                report = _get_json(target) if target else {"error": "invalid_configuration"}
                code = 503 if report.get("error") else 200
                self._send(code, "application/json; charset=utf-8", _json_bytes(report))
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
            if action == 'index-batch':
                # JSON-only and same-origin: never allow a cross-site form to
                # trigger processing, even on a loopback-bound local server.
                origin = self.headers.get('Origin', '')
                expected = f"http://{host}:{port}"
                if (origin and origin != expected) or 'application/json' not in self.headers.get('Content-Type', ''):
                    self._send(403, "application/json; charset=utf-8",
                               _json_bytes({"error": "same_origin_json_required"}))
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 0 or length > 4096:
                        raise ValueError("invalid_request_size")
                    body = json.loads(self.rfile.read(length) or b"{}")
                    if not isinstance(body, dict):
                        raise ValueError("invalid_request_body")
                    cursor = body.get("cursor")
                    space_id = body.get("space_id")
                    if space_id is not None and (
                        not isinstance(space_id, str) or len(space_id) > 64
                    ):
                        raise ValueError("invalid_space_id")
                    if cursor is not None and not isinstance(cursor, str):
                        raise ValueError("invalid_scan_cursor")
                except (ValueError, TypeError):
                    self._send(400, "application/json; charset=utf-8",
                               _json_bytes({"error": "invalid_index_request"}))
                    return
                self._send(200, "application/json; charset=utf-8",
                           _json_bytes(index_configured_source(start_after=cursor, space_id=space_id)))
                return
            if action in {'search', 'answer'}:
                origin = self.headers.get("Origin", "")
                expected = f"http://{host}:{port}"
                content_type = self.headers.get("Content-Type", "").lower()
                if (origin and origin != expected) or 'application/json' not in content_type:
                    self._send(403, "application/json; charset=utf-8",
                               _json_bytes({"error": "same_origin_json_required"}))
                    return
                try:
                    payload = _read_json_body(self)
                except ValueError as exc:
                    self._send(400, "application/json; charset=utf-8",
                               _json_bytes({"error": "invalid_request", "details": str(exc)}))
                    return
                target = _configured_target(action)
                result = _post_json(target, payload) if target else {"error": "invalid_configuration"}
                error = result.get("error")
                status_code = 400 if error == "invalid_request" else (503 if error else 200)
                self._send(status_code, "application/json; charset=utf-8", _json_bytes(result))
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
