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
from tof_cli.knowledge.source_imports import import_selected_files
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
      margin-bottom: 20px;
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


        .simple-more { max-width: 1180px; margin: 0; }
    .simple-more > summary { padding: 7px 0 10px; color: var(--muted); font-size: .83rem; font-weight: 600; }
    .simple-more .page-nav { margin-top: 10px; }
    .simple-home { max-width: 1180px; margin: 0 auto; }
    .simple-home h1 { font-size: clamp(2rem, 5vw, 3.7rem); margin-bottom: 10px; }
    .simple-home .lead { margin-bottom: 14px; max-width: 750px; font-size: 1rem; }
    .simple-status { display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px 16px;
      color: var(--gold-bright); font-weight: 750; margin: 14px 0 24px; }
    .simple-status .muted { font-weight: 400; }
    .simple-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 18px; }
    .simple-card { border: 1px solid var(--border-strong); background: var(--surface);
      border-radius: 18px; padding: 24px; min-width: 0; }
    .simple-card h2 { font-size: 1.35rem; margin: 0 0 16px; }
    .simple-step { display: block; font-size: .75rem; font-weight: 800; color: var(--gold); margin-bottom: 8px; }
    .simple-dropzone { display: flex; flex-direction: column; gap: 10px; align-items: center;
      justify-content: center; text-align: center; min-height: 220px; padding: 22px 16px;
      border: 2px dashed var(--border-strong); border-radius: 15px; background: var(--surface-soft); }
    .simple-dropzone.drag-over { border-color: var(--gold-bright); background: var(--chip-bg); }
    .simple-buttons { display: flex; flex-wrap: wrap; gap: 9px; justify-content: center; }
    .simple-card .result { margin-top: 16px; }
    .simple-card textarea { min-height: 135px; }
    .chat-workspace { border: 1px solid var(--border-strong); border-radius: 18px;
      background: var(--surface); overflow: hidden; }
    .chat-toolbar { display: flex; justify-content: flex-end; padding: 9px 16px 0; }
    .chat-feed { display: flex; flex-direction: column; gap: 14px; padding: 22px;
      min-height: 280px; max-height: 52vh; overflow-y: auto; }
    .chat-message { border-radius: 16px; padding: 13px 16px; max-width: 82%;
      overflow-wrap: anywhere; line-height: 1.55; white-space: pre-wrap; }
    .chat-message--assistant { align-self: flex-start; background: var(--surface-soft);
      border: 1px solid var(--border); }
    .chat-message--user { align-self: flex-end; background: var(--chip-bg);
      border: 1px solid var(--border-strong); }
    .chat-message details { margin-top: 12px; white-space: normal; }
    .chat-source { display: flex; gap: 9px; align-items: center; flex-wrap: wrap;
      margin-top: 9px; overflow-wrap: anywhere; }
    .chat-attach { border-top: 1px solid var(--border); padding: 12px 18px 6px; }
    .chat-attach .simple-dropzone { flex-direction: row; min-height: 0; padding: 10px 12px;
      justify-content: space-between; gap: 10px; text-align: left; }
    .chat-attach .hint { margin: 8px 0; }
    .chat-composer { display: flex; align-items: end; gap: 12px;
      border-top: 1px solid var(--border); padding: 12px 18px; }
    .chat-composer textarea { min-height: 60px; flex: 1; resize: vertical; }
    .chat-composer button { flex-shrink: 0; }
    .chat-hint { font-size: .8rem; color: var(--muted); padding: 0 18px 14px; }
    .chat-evidence { margin: 0 18px 12px; padding: 14px; border: 1px solid var(--border);
      border-radius: 12px; overflow-wrap: anywhere; }
    @media (max-width: 650px) {
      .chat-message { max-width: 96%; }
      .chat-attach .simple-dropzone { flex-direction: column; align-items: stretch; }
      .chat-composer { flex-wrap: wrap; }
    }
    .simple-privacy { margin-top: 16px; color: var(--muted); font-size: .82rem; }
    @media (max-width: 830px) { .simple-grid { grid-template-columns: 1fr; } }
    .source-onboarding {
      border: 1px solid var(--border-strong); border-radius: 17px;
      padding: 23px; background: var(--surface);
      margin: 18px 0 22px;
    }
    .source-onboarding h3 { margin-bottom: 7px; }
    .source-onboarding .actions { margin: 14px 0; }
    .overview-hero { max-width: 850px; margin-bottom: 22px; }
    .overview-hero h1 { font-size: clamp(2.4rem, 5vw, 4.2rem); }
    .overview-hero .lead { max-width: 740px; }
    .overview-status {
      display: flex; align-items: center; justify-content: space-between;
      flex-wrap: wrap; gap: 12px; padding: 18px 20px;
      border: 1px solid var(--border-strong); border-radius: 16px;
      background: var(--chip-bg); margin: 20px 0 28px;
    }
    .overview-status strong { display: block; }
    .overview-status p { margin: 4px 0 0; color: var(--muted); font-size: .9rem; }
    .guide-grid {
      display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .guide-card {
      display: flex; flex-direction: column; gap: 12px;
      padding: 24px; min-height: 215px; border: 1px solid var(--border);
      border-radius: 18px; background: var(--surface);
      color: var(--text); text-decoration: none;
      transition: border-color .16s ease, transform .16s ease;
    }
    .guide-card:hover, .guide-card:focus-visible {
      border-color: var(--gold); transform: translateY(-2px);
    }
    .guide-card .step { color: var(--gold); font-weight: 800; font-size: .83rem; }
    .guide-card h2 { margin: 0; font-size: 1.4rem; }
    .guide-card p { margin: 0; color: var(--muted); font-size: .95rem; }
    .guide-card .forward { margin-top: auto; color: var(--gold-bright); font-weight: 750; }
    .page-intro {
      display: flex; justify-content: space-between; flex-wrap: wrap;
      gap: 18px; align-items: center; margin: 0 0 22px;
      border-bottom: 1px solid var(--border); padding-bottom: 22px;
    }
    .page-intro h1 { margin: 0 0 8px; font-size: clamp(1.8rem, 4vw, 3rem); }
    .page-intro p { margin: 0; max-width: 670px; color: var(--muted); }
    .page-intro a, .inline-link {
      color: var(--gold-bright); font-weight: 700; text-decoration: underline;
      text-underline-offset: 4px;
    }
    .advanced-options {
      border: 1px solid var(--border); border-radius: 12px;
      padding: 2px 12px 12px; margin: 10px 0;
    }
    .advanced-options summary { padding: 9px 2px; font-weight: 650; color: var(--muted); }
    .advanced-options summary::after { font-size: 1rem; }
    .advanced-options .options-row { margin-top: 8px; }
    .related-link { display: inline-flex; margin-top: 16px; }
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

    .section { padding-top: 18px; }

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
      .guide-grid { grid-template-columns: 1fr; }
    }

    @media (max-width: 560px) {
      .wrap { width: min(calc(100% - 26px),1180px); padding-top: 16px; }
      .topbar { flex-direction: column; }
      .page-nav { padding: 7px; gap: 5px; }
      .page-nav a { min-height: 44px; padding: 9px 12px; }
      .guide-card { min-height: 165px; }
      .page-intro { flex-direction: column; align-items: flex-start; }
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

    <details class="simple-more">
      <summary data-i18n="simpleMore">Weitere Funktionen</summary>
    <nav class="page-nav" aria-label="Navigation" data-i18n-aria-label="navigationLabel">
      <a href="/uebersicht" data-page-link="overview" data-i18n="navOverview">Übersicht</a>
      <a href="/frage-stellen" data-page-link="question" data-i18n="navAsk">Frage stellen</a>
      <a href="/dokumente-durchsuchen" data-page-link="search" data-i18n="navSearch">Dokumente durchsuchen</a>
      <a href="/quellen-index" data-page-link="sources" data-i18n="navSources">Quellen & Index</a>
      <a href="/beleg-pruefen" data-page-link="evidence" data-i18n="navEvidence">Beleg prüfen</a>
    </nav>
    </details>

    <main id="main-content">
      <div class="section">
        <!-- PAGE_START:overview -->
        <section class="simple-home" id="simple-home" aria-labelledby="simple-title">
          <p class="eyebrow" data-i18n="simpleEyebrow">DEIN WISSEN</p>
          <h1 id="simple-title" data-i18n="chatTitle">Frag deine Dokumente.</h1>
          <p class="lead" data-i18n="chatLead">Dateien hinzufügen, Fragen stellen und Antworten mit Quellen lesen – alles hier.</p>
          <div class="simple-status" aria-live="polite">
            <span id="overview-status-title" data-i18n="overviewLoading">Dokumentenstatus wird geladen …</span>
            <span id="overview-status-detail" class="muted" data-i18n="overviewLoadingHelp">Die lokalen Quellen werden geprüft.</span>
          </div>
          <section class="chat-workspace" aria-label="Dokumenten-Chat" data-i18n-aria-label="chatWorkspaceLabel">
            <div class="chat-toolbar"><button type="button" class="ghost" onclick="clearSimpleChat()" data-i18n="chatClear">Neuer Chat</button></div>
            <div id="qa-result" class="chat-feed" role="log" aria-live="polite" data-i18n-aria-label="chatHistoryLabel" aria-label="Unterhaltung">
              <div class="chat-message chat-message--assistant"><div class="chat-text" data-i18n="chatWelcome">Hallo! Füge Dokumente hinzu oder stelle direkt eine Frage zu deinen vorhandenen Dateien.</div></div>
            </div>
            <div class="chat-attach">
              <div id="simple-dropzone" class="simple-dropzone" role="group" aria-labelledby="simple-drop-label">
                <span id="simple-drop-label" data-i18n="chatDropText">Dateien hier ablegen</span>
                <div class="simple-buttons">
                  <button type="button" class="secondary" onclick="document.getElementById('source-files').click()" data-i18n="sourcePickFiles">Dateien auswählen</button>
                  <button type="button" class="ghost" onclick="chooseFolder()" data-i18n="simpleChooseFolder">Ordner auswählen</button>
                </div>
                <input type="file" multiple id="source-files" style="display:none" onchange="importSelectedFiles(this.files, false)">
                <input type="file" multiple webkitdirectory directory id="source-folder" style="display:none" onchange="importSelectedFiles(this.files, true)">
              </div>
              <p id="source-import-status" class="hint" role="status" aria-live="polite" data-i18n="simpleFilesHint">Nur ausgewählte Dateien werden lokal kopiert und eingelesen. Originale bleiben unverändert.</p>
              <progress id="source-import-progress" max="100" value="0" style="display:none;width:100%" aria-label="Dateiverarbeitung"></progress>
              <details id="source-import-errors" style="display:none"><summary data-i18n="simpleFailedFiles">Nicht verarbeitete Dateien</summary><ul id="source-import-error-list"></ul></details>
            </div>
            <div id="chat-evidence-panel" class="chat-evidence" role="status" hidden></div>
            <div class="chat-composer">
              <textarea id="qa-question" rows="2" data-i18n-aria-label="questionLabel" aria-label="Frage an deine Dokumente" data-i18n-placeholder="chatPlaceholder" placeholder="Frag etwas zu deinen Dokumenten …"></textarea>
              <input id="qa-scope" type="hidden" value="">
              <input id="qa-limit" type="hidden" value="5">
              <button id="qa-send-button" type="button" onclick="runAnswer()" data-i18n="chatSend">Senden</button>
            </div>
            <p class="chat-hint" data-i18n="chatHint">Enter sendet · Umschalt+Enter für eine neue Zeile. Jede Frage wird einzeln anhand deiner Dokumente geprüft; der Verlauf bleibt nur bis zum Neuladen sichtbar.</p>
          </section>
          <p class="simple-privacy" data-i18n="simplePrivacy">Deine ausgewählten Dateien bleiben auf diesem Computer. Es gibt keine automatische Ordnerüberwachung.</p>
        </section>
                <!-- PAGE_END:overview -->
        <!-- PAGE_START:question -->
        <div class="page-intro">
          <div><h1 data-i18n="navAsk">Frage stellen</h1>
          <p data-i18n="questionGuide">Gib deine Frage ein. Du siehst, welche Dokumente die Antwort belegen – oder dass Belege fehlen.</p></div>
          <a href="/uebersicht" data-i18n="backOverview">← Zur Übersicht</a>
        </div>

        <div class="answer-panel">
          <p class="eyebrow" data-i18n="answerEyebrow">FRAGE STELLEN</p>
          <h2 data-i18n="answerTitle">Was möchtest du aus deinen Dokumenten wissen?</h2>
          <div class="form-grid">
            <textarea id="qa-question" aria-label="Frage an deine Dokumente" data-i18n-aria-label="questionLabel" data-i18n-placeholder="questionPlaceholder" placeholder="Zum Beispiel: Was steht in meinen Unterlagen zur Urlaubsregelung?"></textarea>
            <details class="advanced-options">
              <summary data-i18n="optionalFilters">Erweiterte Optionen (optional)</summary>
              <div class="options-row">
              <input id="qa-scope" type="text" aria-label="Suche optional auf bestimmte Quellen begrenzen" data-i18n-aria-label="scopeLabel" data-i18n-placeholder="scopePlaceholder" placeholder="Optional: Suche auf bestimmte Quellen begrenzen">
              <input id="qa-limit" type="number" min="1" max="10" value="5" aria-label="Maximale Anzahl berücksichtigter Treffer" data-i18n-aria-label="qaLimitLabel">
              </div>
            </details>
            <button onclick="runAnswer()" data-i18n="runAnswer">Antwort aus meinen Dokumenten holen</button>
          </div>
          <div class="hint" data-i18n="answerHint">ToF sucht passende Stellen und zeigt die verwendeten Quellen zusammen mit der Antwort.</div>
          <div class="result" id="qa-result" role="status" aria-live="polite" data-i18n="noAnswerYet">Hier erscheint deine Antwort mit den dazugehörigen Quellen.</div>
        </div>

        <!-- PAGE_END:question -->
        <!-- PAGE_START:search -->
        <div class="page-intro">
          <div><h1 data-i18n="navSearch">Dokumente durchsuchen</h1>
          <p data-i18n="searchGuide">Suche nach einem Begriff. Öffne anschließend eine Fundstelle, um den Originaltext zu lesen.</p></div>
          <a href="/uebersicht" data-i18n="backOverview">← Zur Übersicht</a>
        </div>
        <div class="search-panel">
          <p class="eyebrow" data-i18n="searchEyebrow">DOKUMENTE DURCHSUCHEN</p>
          <h2 data-i18n="searchTitle">Finde passende Stellen direkt.</h2>
          <div class="form-grid">
            <input id="search-query" type="text" aria-label="Dokumente durchsuchen" data-i18n-aria-label="searchLabel" data-i18n-placeholder="searchPlaceholder" placeholder="Wonach möchtest du suchen?">
            <details class="advanced-options">
              <summary data-i18n="optionalFilters">Erweiterte Optionen (optional)</summary>
              <div class="options-row">
              <input id="search-scope" type="text" aria-label="Suche optional auf bestimmte Quellen begrenzen" data-i18n-aria-label="scopeLabel" data-i18n-placeholder="scopePlaceholder" placeholder="Optional: Suche auf bestimmte Quellen begrenzen">
              <input id="search-limit" type="number" min="1" max="20" value="5" aria-label="Maximale Anzahl Suchtreffer" data-i18n-aria-label="searchLimitLabel">
              </div>
            </details>
            <button class="secondary" onclick="runSearch()" data-i18n="runSearch">Dokumente durchsuchen</button>
          </div>
          <div class="hint" data-i18n="searchHint">Du bekommst die passendsten Fundstellen mit Dokument und Textausschnitt.</div>
          <div class="result" id="search-result" role="status" aria-live="polite" data-i18n="noSearchYet">Hier erscheinen passende Fundstellen aus deinen Dokumenten.</div>
        </div>

        <!-- PAGE_END:search -->
        <!-- PAGE_START:evidence -->
        <div class="page-intro">
          <div><h1 data-i18n="navEvidence">Beleg prüfen</h1>
          <p data-i18n="evidenceGuide">Hier erscheint eine Originaltextstelle, wenn du zuvor in der Suche oder Antwort auf „Textstelle ansehen“ geklickt hast.</p></div>
          <a href="/dokumente-durchsuchen" data-i18n="backSearch">← Zur Suche</a>
        </div>
        <section class="search-panel" aria-labelledby="evidence-title">
          <p class="eyebrow" data-i18n="evidenceEyebrow">BELEG PRÜFEN</p>
          <h2 id="evidence-title" data-i18n="evidenceTitle">Textstelle nachvollziehen</h2>
          <p class="hint" data-i18n="evidenceHint">Öffne einen Beleg aus Suche oder Antwort. Nur aktuell indexierte Fundstellen werden angezeigt.</p>
          <div class="result" id="evidence-result" aria-live="polite" data-i18n="evidenceEmpty">Wähle eine Fundstelle.</div>
          <a class="inline-link related-link" href="/dokumente-durchsuchen" data-i18n="findEvidence">Fundstelle suchen →</a>
        </section>

        <!-- PAGE_END:evidence -->
        <!-- PAGE_START:sources -->
        <div class="page-intro">
          <div><h1 data-i18n="navSources">Quellen & Index</h1>
          <p data-i18n="sourcesGuide">Prüfe zuerst, wie viele Dokumente schon bereitstehen. Nur bei Bedarf kannst du eine Quelle manuell indexieren.</p></div>
          <a href="/uebersicht" data-i18n="backOverview">← Zur Übersicht</a>
        </div>
        <section class="search-panel" aria-labelledby="sources-title">
          <p class="eyebrow" data-i18n="sourcesEyebrow">QUELLEN & INDEX</p>
          <h2 id="sources-title" data-i18n="sourcesTitle">Deine Quellen im Überblick</h2>
          <div class="hint" data-i18n="sourcesHint">Welche Dokumente bereits indexiert sind und welche noch Aufmerksamkeit brauchen.</div>
          <button class="secondary" onclick="refreshSources()" data-i18n="refreshSources">Quellen aktualisieren</button>
          <div class="result" id="source-result" aria-live="polite" data-i18n="sourcesEmpty">Hier erscheinen die erfassten Quellen und Indexstände.</div>
          <div class="source-onboarding">
            <h3 data-i18n="sourceAddTitle">Eigene Dokumente hinzufügen</h3>
            <p class="hint" data-i18n="sourceAddHelp">Wähle Dateien oder einen Ordner aus. ToF erstellt eine lokale Kopie im freigegebenen Dokumentenbereich. Originale werden nicht verändert.</p>
            <div class="actions">
              <button type="button" class="secondary" onclick="document.getElementById('source-files').click()" data-i18n="sourcePickFiles">Dateien auswählen</button>
              <button type="button" class="secondary" onclick="chooseFolder()" data-i18n="sourcePickFolder">Ordner verbinden</button>
              <button type="button" class="ghost" onclick="syncFolder()" data-i18n="sourceResyncFolder">Ordner erneut abgleichen</button>
            </div>
            <input type="file" multiple id="source-files" style="display:none" onchange="importSelectedFiles(this.files, false)">
            <input type="file" multiple webkitdirectory directory id="source-folder" style="display:none" onchange="importSelectedFiles(this.files, true)">
            <p class="hint" id="source-import-status" role="status" aria-live="polite" data-i18n="sourceIdle">Noch keine eigenen Dateien ausgewählt.</p>
            <button type="button" class="secondary" id="source-index-now" disabled onclick="indexImportedSource()" data-i18n="sourceIndexNow">Importierte Dateien jetzt einlesen</button>
            <p class="hint" data-i18n="sourcePrivacyHelp">Ordnerzugriff erfolgt nur mit deiner Freigabe. Abgleich und Indexierung starten ausschließlich auf Klick. Bei Browsern ohne dauerhafte Ordnerfreigabe den Ordner erneut auswählen.</p>
          </div>
          <details class="advanced-options" id="index-advanced">
          <summary data-i18n="manualIndexOptions">Dokumente manuell einlesen (optional)</summary>
          <label class="hint" for="index-source-select" data-i18n="indexSourceLabel">Zu indexierenden Quellenbereich auswählen</label>
          <select id="index-source-select" onchange="resetIndexCursor()" style="display:block;width:100%;padding:10px;margin:8px 0 12px"></select>
          <button class="secondary" type="button" onclick="loadSourceSpaces()" data-i18n="refreshSourceFolders">Quellenordner aktualisieren</button>
          <p class="hint" id="index-source-message" aria-live="polite"></p>
          <button class="secondary" id="index-batch-button" onclick="runIndexBatch()" data-i18n="indexBatch">Konfigurierte Quelle indexieren</button>
          <button class="secondary" onclick="resetIndexCursor()" data-i18n="indexReset">Dateidurchlauf neu beginnen</button>
          <p class="hint" data-i18n="indexMissingNote">Bei großen Quellen ist die Fehlbestandserkennung nur für vollständige Einzelscans verfügbar.</p>
          <div class="hint" id="index-batch-result" aria-live="polite" data-i18n="indexHint">Manuell: eine begrenzte Charge der konfigurierten, schreibgeschützten Quelle einlesen.</div>
          </details>
          <div class="hint" data-i18n="sourcesLocalOnly">Nur lokale Quellenübersicht. Es ist keine Mehrbenutzerfreigabe aktiv.</div>
        </section>

        <!-- PAGE_END:sources -->
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
              <div class="log"><pre id="log" data-i18n="uiStarted">ToF Knowledge ist bereit.</pre></div>
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
        simpleEyebrow: 'DEIN WISSEN',
        chatTitle: 'Frag deine Dokumente.',
        chatLead: 'Dateien hinzufügen, Fragen stellen und Antworten mit Quellen lesen – alles hier.',
        chatWorkspaceLabel: 'Dokumenten-Chat',
        chatHistoryLabel: 'Unterhaltung',
        chatWelcome: 'Hallo! Füge Dokumente hinzu oder stelle direkt eine Frage zu deinen vorhandenen Dateien.',
        chatDropText: 'Dateien hier ablegen',
        chatPlaceholder: 'Frag etwas zu deinen Dokumenten …',
        chatSend: 'Senden',
        chatSearching: 'Ich suche in deinen Dokumenten …',
        chatClear: 'Neuer Chat',
        chatImportBusy: 'Dateien werden verarbeitet. Bitte erst danach eine Frage stellen.',
        chatError: 'Die Antwort konnte nicht geladen werden. Bitte versuche es erneut.',
        chatHint: 'Enter sendet · Umschalt+Enter für eine neue Zeile. Jede Frage wird einzeln anhand deiner Dokumente geprüft; der Verlauf bleibt nur bis zum Neuladen sichtbar.',
        simpleTitle: 'Deine Dateien. Deine Antworten.',
        simpleLead: 'Dateien hinzufügen und direkt Fragen stellen. Den Rest übernimmt ToF.',
        simpleStepOne: '1 · DATEIEN',
        simpleStepTwo: '2 · FRAGEN',
        simpleFilesTitle: 'Dateien hinzufügen',
        simpleQuestionTitle: 'Was möchtest du wissen?',
        simpleDropText: 'Dateien hier hineinziehen',
        simpleDropOr: 'oder',
        simpleChooseFolder: 'Ordner auswählen',
        simpleFilesHint: 'Nur ausgewählte Dateien werden lokal kopiert und eingelesen. Originale bleiben unverändert.',
        simplePrivacy: 'Die Dateien bleiben lokal. Kein automatischer Zugriff auf deine anderen Ordner.',
        simpleMore: 'Weitere Funktionen',
        simpleAsk: 'Antwort finden',
        simpleEvidence: 'Quellen und Details',
        simpleNoEvidence: 'Dazu wurden keine ausreichenden Belege gefunden.',
        simpleFilesProcessing: 'Dateien werden eingelesen …',
        simpleFilesReady: 'Dateien bereit. Du kannst jetzt eine Frage stellen.',
        simpleFailedFiles: 'Nicht verarbeitete Dateien',
        sourceRejectedType: 'Dateityp nicht unterstützt',
        sourceRejectedSize: 'Datei größer als 12 MiB',
        sourceRejectedName: 'Ungültiger Dateiname oder Pfad',
        sourceRejectedLimit: 'Maximal 300 Dateien pro Auswahl',
        sourceAllRejected: 'Keine unterstützten Dateien ausgewählt. Details unten anzeigen.',
        sourceIndexNoText: 'Kein auslesbarer Text',
        sourceIndexProblem: 'Einlesen fehlgeschlagen',
        navigationLabel: 'Seitennavigation',
        sourceIndexNow: 'Importierte Dateien jetzt einlesen',
        sourceIndexProgress: 'Dokumente verarbeitet',
        sourceIndexDone: 'Einlesen abgeschlossen. Die Dokumente können jetzt durchsucht werden.',
        sourceIndexIncomplete: 'Einlesen teilweise abgeschlossen. Bitte offene Dokumente prüfen.',
        sourceAddTitle: 'Eigene Dokumente hinzufügen',
        sourceAddHelp: 'Wähle Dateien oder einen Ordner. ToF kopiert sie in den bereits freigegebenen Dokumentenbereich; deine Originaldateien bleiben unverändert.',
        sourcePickFiles: 'Dateien auswählen',
        sourcePickFolder: 'Ordner verbinden',
        sourceResyncFolder: 'Ordner erneut abgleichen',
        sourceIdle: 'Noch keine eigenen Dateien ausgewählt.',
        sourcePrivacyHelp: 'Ordner werden nur mit deiner Freigabe eingelesen. Abgleich und Indexierung erfolgen ausschließlich auf Klick. Falls dein Browser die Freigabe nicht speichern kann, wähle den Ordner erneut.',
        sourceImportRunning: 'Dateien werden lokal importiert …',
        sourceImportDone: 'Dateien lokal kopiert.',
        sourceImportFailed: 'Import fehlgeschlagen. Bitte unterstützte Dateien bis 12 MB auswählen.',
        sourceImportSkipped: 'Übersprungene Dateien',
        sourcePermissionDenied: 'Ordnerzugriff nicht erlaubt oder abgebrochen.',
        sourceNoConnectedFolder: 'Noch kein Ordner verbunden. Bitte zunächst einen Ordner auswählen.',
        sourceNotInSpaces: 'Importiert, aber der Quellenbereich ist nicht verfügbar. Quellenübersicht prüfen, bevor du indexierst.',
        sourceConnected: 'Ausgewählter Ordner',
        navOverview: 'Übersicht',
        overviewEyebrow: 'DEIN WISSEN IM ÜBERBLICK',
        overviewTitle: 'Was möchtest du heute tun?',
        overviewLead: 'Du kannst Fragen stellen, Dokumente durchsuchen und jede verwendete Textstelle prüfen. Hier findest du den richtigen Einstieg.',
        overviewLoading: 'Dokumentenstatus wird geladen …',
        overviewLoadingHelp: 'Die vorhandenen lokalen Quellen werden geprüft.',
        overviewManageSources: 'Quellen verwalten',
        overviewReady: 'Dokumente bereit',
        overviewReadyHelp: 'Dokumente indexiert. Du kannst jetzt fragen oder suchen.',
        overviewEmpty: 'Noch keine Dokumente indexiert',
        overviewEmptyHelp: 'Öffne Quellen & Index und lies eine Quelle manuell ein.',
        overviewUnavailable: 'Quellenstatus nicht erreichbar',
        overviewUnavailableHelp: 'Öffne Einrichtung & technische Details und prüfe den Dienstestatus.',
        overviewStepAsk: 'START · FRAGEN',
        overviewStepSearch: 'ALTERNATIV · SUCHEN',
        overviewStepSources: 'VORBEREITUNG · QUELLEN',
        overviewStepEvidence: 'DANACH · PRÜFEN',
        overviewAskHelp: 'Du hast eine konkrete Frage? Suche eine Antwort mit sichtbaren Quellen.',
        overviewSearchHelp: 'Du suchst eine Datei oder Textstelle? Durchsuche deine indexierten Dokumente.',
        overviewSourcesHelp: 'Sieh nach, welche Dokumente bereitstehen, oder starte die Indexierung manuell.',
        overviewEvidenceHelp: 'Öffne aus einer Antwort oder einem Suchtreffer die Originaltextstelle.',
        overviewOpenAsk: 'Zur Frage →',
        overviewOpenSearch: 'Zur Suche →',
        overviewOpenSources: 'Zu den Quellen →',
        overviewOpenEvidence: 'Zur Belegprüfung →',
        questionGuide: 'Gib deine Frage ein. Du siehst, welche Dokumente die Antwort belegen – oder dass Belege fehlen.',
        searchGuide: 'Suche nach einem Begriff. Öffne anschließend eine Fundstelle, um den Originaltext zu lesen.',
        evidenceGuide: 'Hier erscheint die Originaltextstelle, nachdem du in Suche oder Antwort auf „Textstelle ansehen“ geklickt hast.',
        sourcesGuide: 'Prüfe zuerst, welche Dokumente bereitstehen. Nur bei Bedarf kannst du eine Quelle manuell indexieren.',
        optionalFilters: 'Erweiterte Optionen (optional)',
        manualIndexOptions: 'Dokumente manuell einlesen (optional)',
        backOverview: '← Zur Übersicht',
        backSearch: '← Zur Suche',
        findEvidence: 'Fundstelle suchen →',
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
        evidenceFoundIntro: 'Gefundene Textstellen:',
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
        evidenceStatus: 'Belegstatus',
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
        simpleEyebrow: 'YOUR KNOWLEDGE',
        chatTitle: 'Ask your documents.',
        chatLead: 'Add files, ask questions and read sourced answers – all here.',
        chatWorkspaceLabel: 'Document chat',
        chatHistoryLabel: 'Conversation',
        chatWelcome: 'Hello! Add documents or ask a question about your existing files.',
        chatDropText: 'Drop files here',
        chatPlaceholder: 'Ask something about your documents …',
        chatSend: 'Send',
        chatSearching: 'Searching your documents …',
        chatClear: 'New chat',
        chatImportBusy: 'Files are being processed. Ask your question when they are ready.',
        chatError: 'The answer could not be loaded. Please try again.',
        chatHint: 'Enter to send · Shift+Enter for a new line. Each question is checked independently against your documents; the conversation display lasts until you reload.',
        simpleTitle: 'Your files. Your answers.',
        simpleLead: 'Add files and ask questions. ToF handles the rest.',
        simpleStepOne: '1 · FILES',
        simpleStepTwo: '2 · ASK',
        simpleFilesTitle: 'Add files',
        simpleQuestionTitle: 'What would you like to know?',
        simpleDropText: 'Drop files here',
        simpleDropOr: 'or',
        simpleChooseFolder: 'Choose folder',
        simpleFilesHint: 'Only selected files are copied and indexed locally. Originals stay unchanged.',
        simplePrivacy: 'Files remain local. No automatic access to your other folders.',
        simpleMore: 'More options',
        simpleAsk: 'Find answer',
        simpleEvidence: 'Sources and details',
        simpleNoEvidence: 'No sufficient evidence was found for this question.',
        simpleFilesProcessing: 'Indexing files …',
        simpleFilesReady: 'Files ready. You can ask a question now.',
        simpleFailedFiles: 'Files not processed',
        sourceRejectedType: 'Unsupported file type',
        sourceRejectedSize: 'File exceeds 12 MiB',
        sourceRejectedName: 'Invalid filename or path',
        sourceRejectedLimit: 'At most 300 files per selection',
        sourceAllRejected: 'No supported files selected. Open details below.',
        sourceIndexNoText: 'No extractable text',
        sourceIndexProblem: 'Could not index file',
        navigationLabel: 'Page navigation',
        sourceIndexNow: 'Index imported documents now',
        sourceIndexProgress: 'Documents processed',
        sourceIndexDone: 'Indexing complete. Your documents are now searchable.',
        sourceIndexIncomplete: 'Indexing only partially finished. Check pending documents.',
        sourceAddTitle: 'Add your own documents',
        sourceAddHelp: 'Select files or a folder. ToF copies them into the already approved document area; original files are unchanged.',
        sourcePickFiles: 'Select files',
        sourcePickFolder: 'Connect folder',
        sourceResyncFolder: 'Sync folder again',
        sourceIdle: 'No personal files selected yet.',
        sourcePrivacyHelp: 'Folders are read only with your permission. Sync and indexing happen only when clicked. If your browser cannot save the permission, select the folder again.',
        sourceImportRunning: 'Importing files locally …',
        sourceImportDone: 'Files copied locally.',
        sourceImportFailed: 'Import failed. Try supported files up to 12 MB each.',
        sourceImportSkipped: 'Files skipped',
        sourcePermissionDenied: 'Folder access denied or cancelled.',
        sourceNoConnectedFolder: 'No folder connected yet. Select a folder first.',
        sourceNotInSpaces: 'Imported, but this source is not available in the sources list. Check source settings before indexing.',
        sourceConnected: 'Selected folder',
        navOverview: 'Overview',
        overviewEyebrow: 'YOUR KNOWLEDGE AT A GLANCE',
        overviewTitle: 'What would you like to do?',
        overviewLead: 'Ask questions, search documents, and inspect the original passages behind each answer. Start here.',
        overviewLoading: 'Loading document status …',
        overviewLoadingHelp: 'Checking the existing local sources.',
        overviewManageSources: 'Manage sources',
        overviewReady: 'Documents ready',
        overviewReadyHelp: 'Documents indexed. You can ask a question or search.',
        overviewEmpty: 'No documents indexed yet',
        overviewEmptyHelp: 'Open Sources & Index and manually index a configured source.',
        overviewUnavailable: 'Source status unavailable',
        overviewUnavailableHelp: 'Open Setup & technical details and check the services.',
        overviewStepAsk: 'START · ASK',
        overviewStepSearch: 'ALTERNATIVE · SEARCH',
        overviewStepSources: 'PREPARE · SOURCES',
        overviewStepEvidence: 'THEN · VERIFY',
        overviewAskHelp: 'Have a specific question? Find an answer with visible evidence.',
        overviewSearchHelp: 'Looking for a file or passage? Search your indexed documents.',
        overviewSourcesHelp: 'See which documents are ready, or start indexing manually.',
        overviewEvidenceHelp: 'Open an original passage from a search result or answer.',
        overviewOpenAsk: 'Ask a question →',
        overviewOpenSearch: 'Search documents →',
        overviewOpenSources: 'View sources →',
        overviewOpenEvidence: 'Inspect evidence →',
        questionGuide: 'Enter a question. See which documents support an answer—or when evidence is missing.',
        searchGuide: 'Search for a term. Then open a match to read the original passage.',
        evidenceGuide: 'The original passage appears here after selecting “View excerpt” from search results or an answer.',
        sourcesGuide: 'First check which documents are ready. Only index a source manually if needed.',
        optionalFilters: 'Advanced options (optional)',
        manualIndexOptions: 'Index documents manually (optional)',
        backOverview: '← Back to overview',
        backSearch: '← Back to search',
        findEvidence: 'Find an excerpt →',
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
        evidenceFoundIntro: 'Document passages found:',
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
        evidenceStatus: 'Evidence status',
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
    let chatPendingReply = null;
    let chatBusy = false;
    let chatImportBusy = false;
    let chatImportBubble = null;
    let chatActiveQuestion = null;
    let chatGroundedQuestions = [];
    let lastIndexData = null;
    let lastEvidenceSegment = null;
    let lastOverviewData = null;
    let connectedFolderHandle = null;
    let folderFilesFallback = null;

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
        .replace('Verwendete Fundstellen:', t('evidenceUsedIntro'))
        .replace('Gefundene Textstellen:', t('evidenceFoundIntro'));
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
      if (lastAnswerData && !document.getElementById('simple-home')) renderAnswerResult(lastAnswerData);
      if (lastIndexData) renderIndexBatchResult(lastIndexData);
      if (lastOverviewData) renderOverviewStatus(lastOverviewData);
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
      const onChat = Boolean(document.getElementById('simple-home'));
      if (!onChat && window.location.pathname !== '/beleg-pruefen') {
        window.location.assign('/beleg-pruefen?segment_id=' + encodeURIComponent(segmentId));
        return;
      }
      const panel = document.getElementById(onChat ? 'chat-evidence-panel' : 'evidence-result');
      if (onChat) panel.hidden = false;
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
      if (data.error && !document.getElementById('simple-home')) {
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

      // Chat view is session-only. The existing QA API still evaluates each
      // question independently; no conversation memory is sent or invented.
      if (document.getElementById('simple-home')) {
        const bubble = chatPendingReply;
        if (!bubble) return;
        bubble.replaceChildren();
        const text = document.createElement('div');
        text.className = 'chat-text';
        const hasEvidence = !data.error && citations.length > 0 && evidenceRefs.length > 0;
        if (hasEvidence) {
          // An independent grounded question becomes the new topic anchor;
          // only explicit server-recognized follow-ups keep earlier context.
          const continues = data.evidence_signal &&
            data.evidence_signal.search_strategy === 'contextual_followup';
          if (!continues) chatGroundedQuestions = [];
          chatGroundedQuestions.push(chatActiveQuestion.slice(0, 500));
          if (chatGroundedQuestions.length > 4) {
            // Preserve the original grounded topic and the latest three turns.
            chatGroundedQuestions.splice(1, chatGroundedQuestions.length - 4);
          }
        } else {
          chatGroundedQuestions = [];
        }
        chatActiveQuestion = null;
        text.textContent = data.error ? t('chatError') :
          (hasEvidence ? answer : t('simpleNoEvidence'));
        bubble.appendChild(text);
        if (!data.error && hasEvidence) {
          const sources = document.createElement('details');
          const label = document.createElement('summary');
          label.textContent = t('simpleEvidence') + ' (' + evidenceRefs.length + ')';
          sources.appendChild(label);
          for (const ref of evidenceRefs) {
            const row = document.createElement('div');
            row.className = 'chat-source';
            const filename = document.createElement('span');
            filename.textContent = ref.relative_path || '';
            row.appendChild(filename);
            if (ref.segment_id && /^[A-Za-z0-9_-]{1,128}$/.test(ref.segment_id)) {
              const button = document.createElement('button');
              button.type = 'button';
              button.className = 'secondary';
              button.dataset.evidenceSegment = ref.segment_id;
              button.textContent = t('viewEvidence');
              row.appendChild(button);
            }
            sources.appendChild(row);
          }
          bubble.appendChild(sources);
          bindEvidenceButtons(bubble);
        }
        chatPendingReply = null;
        root.scrollTop = root.scrollHeight;
        return;
      }

      let html = `<div class=\"result-card\"><div class=\"answer-main\">${escapeHtml(answer)}</div><div class=\"muted\" style=\"margin-top:10px;\">${t('confidence')}: ${escapeHtml(confidence)}</div>`;
      if (signal) {
        html += '<div class="muted" style="margin-top:10px"><strong>'
          + t('evidenceSignal') + '</strong><br>'
          + t('evidenceStatus') + ': ' + escapeHtml(translatedCode('status', signal.status))
          + ' · ' + t('evidenceStrategy') + ': ' + escapeHtml(translatedCode('searchStrategy', signal.search_strategy))
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

    function renderOverviewStatus(data) {
      const title = document.getElementById('overview-status-title');
      const detail = document.getElementById('overview-status-detail');
      if (!title || !detail) return;
      if (!data || data.error) {
        title.textContent = t('overviewUnavailable');
        detail.textContent = t('overviewUnavailableHelp');
        return;
      }
      const indexed = (data.sources || [])
        .reduce((sum, source) => sum + Number(source.indexed || 0), 0);
      title.textContent = indexed > 0 ?
        indexed + ' · ' + t('overviewReady') : t('overviewEmpty');
      detail.textContent = indexed > 0 ?
        t('overviewReadyHelp') : t('overviewEmptyHelp');
    }

    async function refreshOverview() {
      if (!document.getElementById('overview-status-title')) return;
      try {
        const response = await fetch('/api/sources');
        const data = await response.json();
        lastOverviewData = response.ok ? data : {error: 'source_status_unavailable'};
      } catch (error) {
        lastOverviewData = {error: 'source_status_unavailable'};
      }
      renderOverviewStatus(lastOverviewData);
    }

    async function refreshSummary() {
      try {
        await fetch('/api/summary');
      } catch (error) {
        appendLog(t('issueService'));
      }
      await refreshOverview();
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

    // Folder handles are retained only by the browser, after the person has
    // approved access. The Python service never receives a host folder path.
    function folderStore() {
      return new Promise((resolve, reject) => {
        if (!window.indexedDB) { reject(new Error('storage_unavailable')); return; }
        const request = indexedDB.open('tof_knowledge_folder_permission', 1);
        request.onupgradeneeded = () => {
          request.result.createObjectStore('permissions');
        };
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
      });
    }

    async function saveFolderHandle(handle) {
      try {
        const db = await folderStore();
        await new Promise((resolve, reject) => {
          const tx = db.transaction('permissions', 'readwrite');
          tx.objectStore('permissions').put(handle, 'sourceFolder');
          tx.oncomplete = resolve;
          tx.onerror = () => reject(tx.error);
        });
        db.close();
      } catch (_) { /* Private browsing: session-only connection. */ }
    }

    async function restoreFolderHandle() {
      if (connectedFolderHandle) return connectedFolderHandle;
      try {
        const db = await folderStore();
        const handle = await new Promise((resolve, reject) => {
          const tx = db.transaction('permissions', 'readonly');
          const req = tx.objectStore('permissions').get('sourceFolder');
          req.onsuccess = () => resolve(req.result || null);
          req.onerror = () => reject(req.error);
        });
        db.close();
        if (handle && handle.kind === 'directory') connectedFolderHandle = handle;
      } catch (_) { /* Browser does not support persisted folder handles. */ }
      return connectedFolderHandle;
    }

    async function chooseFolder() {
      if (!window.showDirectoryPicker) {
        document.getElementById('source-folder').click();
        return;
      }
      try {
        connectedFolderHandle = await window.showDirectoryPicker({mode: 'read'});
        await saveFolderHandle(connectedFolderHandle);
        await syncFolder();
      } catch (_) {
        document.getElementById('source-import-status').textContent =
          t('sourcePermissionDenied');
      }
    }

    async function walkFolder(handle, prefix, output, state, depth = 0) {
      if (depth > 9 || state.scanned >= 300) { state.skipped += 1; return; }
      for await (const [name, entry] of handle.entries()) {
        if (state.scanned++ >= 300) { state.skipped += 1; break; }
        if (name.startsWith('.')) { state.skipped += 1; continue; }
        const rel = prefix + '/' + name;
        if (entry.kind === 'directory') {
          await walkFolder(entry, rel, output, state, depth + 1);
        } else if (entry.kind === 'file') {
          const file = await entry.getFile();
          output.push({file, name: rel});
        }
      }
    }

    async function syncFolder() {
      const output = document.getElementById('source-import-status');
      const handle = await restoreFolderHandle();
      if (!handle) {
        // File picker fallback for Firefox and non-Chromium browsers.
        document.getElementById('source-folder').click();
        return;
      }
      try {
        const permission = await handle.queryPermission({mode: 'read'});
        if (permission !== 'granted' &&
            await handle.requestPermission({mode: 'read'}) !== 'granted') {
          output.textContent = t('sourcePermissionDenied');
          return;
        }
        output.textContent = t('sourceImportRunning');
        const files = [];
        const state = {scanned: 0, skipped: 0};
        await walkFolder(handle, handle.name, files, state);
        await importSelectedFiles(files, true, state.skipped);
      } catch (_) {
        output.textContent = t('sourcePermissionDenied');
      }
    }

    function fileAsBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = reject;
        reader.onload = () => resolve(String(reader.result).split(',', 2)[1]);
        reader.readAsDataURL(file);
      });
    }

    function showImportFailures(paths) {
      const details = document.getElementById('source-import-errors');
      const list = document.getElementById('source-import-error-list');
      if (!details || !list) return;
      list.replaceChildren();
      const unique = [...new Set(paths.filter(x => typeof x === 'string' && x))].slice(0, 100);
      for (const path of unique) {
        const entry = document.createElement('li');
        entry.textContent = path; // Treat file paths as untrusted display text.
        list.appendChild(entry);
      }
      details.style.display = unique.length ? 'block' : 'none';
      details.open = unique.length > 0;
    }

    function showImportProgress(stage, done = 0, total = 0) {
      const bar = document.getElementById('source-import-progress');
      if (!bar) return;
      bar.style.display = stage === 'idle' ? 'none' : 'block';
      if (stage === 'index') {
        bar.removeAttribute('value'); // Unknown number of scan/index passes.
      } else {
        bar.value = total > 0 ? Math.min(100, Math.round(100 * done / total)) : 0;
      }
      bar.setAttribute('aria-label', stage === 'index' ? t('simpleFilesProcessing') :
        t('sourceImportRunning'));
    }

    async function importSelectedFiles(selection, isFolder, previousSkipped = 0) {
      const output = document.getElementById('source-import-status');
      const files = Array.from(selection || [], item =>
        item.file ? item : {file: item, name: isFolder ?
          (item.webkitRelativePath || item.name) : item.name});
      if (!files.length) { output.textContent = t('sourceIdle'); return; }
      const onChat = Boolean(document.getElementById('simple-home'));
      if (onChat && (chatImportBusy || chatBusy)) return;
      if (onChat) {
        chatImportBusy = true;
        chatGroundedQuestions = []; // New document set invalidates topic continuity.
        chatImportBubble = null;
        document.getElementById('qa-send-button').disabled = true;
      }
      const supported = /\.(txt|md|log|py|rst|ini|cfg|yaml|yml|json|htm|html|csv|eml|pdf|docx|xlsx)$/i;
      const candidates = [];
      const skippedDetails = [];
      for (const item of files) {
        const name = item.name;
        const parts = name.split('/');
        let reason = null;
        if (!supported.test(name)) reason = 'sourceRejectedType';
        else if (item.file.size > 12 * 1024 * 1024) reason = 'sourceRejectedSize';
        else if (name.length > 600 || parts.length > 12 ||
          name.includes(String.fromCharCode(92)) ||
          parts.some(part => !part || part.startsWith('.') ||
            part.includes(':') || Array.from(part).some(c => c.charCodeAt(0) < 32))) {
          reason = 'sourceRejectedName';
        } else if (candidates.length >= 300) reason = 'sourceRejectedLimit';
        if (reason) skippedDetails.push(name.slice(0, 180) + ' · ' + t(reason));
        else candidates.push(item);
      }
      showImportFailures(skippedDetails);
      let skipped = previousSkipped + files.length - candidates.length;
      let imported = 0;
      let sourceId = null;
      let failedBatchNames = [];
      output.textContent = t('sourceImportRunning') + ' (0/' + candidates.length + ')';
      showImportProgress('copy', 0, candidates.length);
      if (onChat) updateChatImportNotice(output.textContent);
      try {
        if (!candidates.length) {
          output.textContent = t('sourceAllRejected');
          return;
        }
        let batch = [];
        let bytes = 0;
        async function send() {
          if (!batch.length) return;
          const payload = [];
          failedBatchNames = batch.map(item => item.name);
          for (const item of batch) {
            payload.push({name: item.name, data: await fileAsBase64(item.file)});
          }
          const response = await fetch('/api/import-files', {
            method: 'POST',
            headers: {'Content-Type': 'application/json',
                      'X-ToF-UI-Action': 'source-import'},
            body: JSON.stringify({files: payload}),
          });
          const data = await response.json();
          if (!response.ok || data.status !== 'ok') {
            throw new Error(data.error || data.status || 'import_failed');
          }
          imported += data.copied || 0;
          sourceId = data.source_id;
          failedBatchNames = [];
          output.textContent = t('sourceImportRunning') + ' (' + imported + '/' + candidates.length + ')' +
            (skipped ? ' · ' + t('sourceImportSkipped') + ': ' + skipped : '');
          showImportProgress('copy', imported, candidates.length);
          if (onChat) updateChatImportNotice(output.textContent);
          batch = [];
          bytes = 0;
        }
        for (const item of candidates.slice(0, 300)) {
          if (batch.length >= 4 || bytes + item.file.size > 15 * 1024 * 1024) {
            await send();
          }
          batch.push(item);
          bytes += item.file.size;
        }
        await send();
        output.textContent = imported + ' · ' + t('sourceImportDone') +
          (skipped ? ' ' + t('sourceImportSkipped') + ': ' + skipped : '');
        if (imported && sourceId) {
          if (document.getElementById('simple-home')) {
            output.textContent = t('simpleFilesProcessing') + ' (' + imported + ')';
            showImportProgress('index');
            updateChatImportNotice(output.textContent);
            await indexImportedSource(sourceId, skippedDetails);
            return;
          }
          await loadSourceSpaces();
          const menu = document.getElementById('index-source-select');
          if ([...menu.options].some(opt => opt.value === sourceId)) {
            menu.value = sourceId;
            document.getElementById('source-index-now').disabled = false;
          } else {
            output.textContent = t('sourceNotInSpaces');
            document.getElementById('source-index-now').disabled = true;
          }
        }
      } catch (error) {
        output.textContent = t('sourceImportFailed') +
          (imported ? ' (' + imported + ' ' + t('sourceTotal') + ')' : '');
        showImportFailures([...skippedDetails, ...failedBatchNames.map(
          name => name.slice(0, 180) + ' · ' + t('sourceImportFailed'))]);
        showImportProgress('idle');
      } finally {
        if (onChat) {
          updateChatImportNotice(output.textContent);
          chatImportBusy = false;
          document.getElementById('qa-send-button').disabled = false;
        }
      }
    }

    async function indexImportedSource(selectedSource = null, skippedDetails = []) {
      const button = document.getElementById('source-index-now');
      const status = document.getElementById('source-import-status');
      const menu = document.getElementById('index-source-select');
      const source = selectedSource || (menu && menu.value);
      if (!source || (button && button.disabled)) return;
      if (button) button.disabled = true;
      let cursor = null;
      let processed = 0;
      let complete = false;
      const failedPaths = [];
      let stalled = 0;
      try {
        // Reuse the existing manual, bounded eight-document index endpoint.
        for (let batch = 0; batch < 45; batch++) {
          const response = await fetch('/api/index-batch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({space_id: source, cursor}),
          });
          const data = await response.json();
          if (!response.ok || !['ok', 'partial'].includes(data.status)) {
            throw new Error('index_failed');
          }
          const indexed = Number(data.indexed_this_pass || 0);
          processed += indexed;
          for (const item of (data.failed || [])) {
            if (item && typeof item.path === 'string') {
              const reason = item.detail === 'no_extractable_text' ?
                t('sourceIndexNoText') : t('sourceIndexProblem');
              failedPaths.push(item.path.slice(0, 180) + ' · ' + reason);
            }
          }
          status.textContent = t('sourceIndexProgress') + ': ' + processed;
          if (document.getElementById('simple-home')) updateChatImportNotice(status.textContent);
          // Failed files must not halt later scan pages. A new cursor is
          // forward progress even when that page extracted zero documents.
          // Repeated failures at an unchanged cursor still stop safely.
          const nextCursor = data.next_cursor || null;
          stalled = (indexed > 0 || (nextCursor && nextCursor !== cursor)) ?
            0 : stalled + 1;
          if (!data.page_has_more && !data.remaining_in_sample) {
            complete = true;
            break;
          }
          if (stalled >= 2) break;
          cursor = nextCursor;
        }
        const failures = new Set(failedPaths).size;
        status.textContent = (complete && !failures && !skippedDetails.length ?
          t('simpleFilesReady') : t('sourceIndexIncomplete')) + ' ' +
          t('sourceIndexProgress') + ': ' + processed +
          (failures ? ' · ' + t('failedCountLabel') + ': ' + failures : '') +
          (skippedDetails.length ? ' · ' + t('sourceImportSkipped') +
            ': ' + skippedDetails.length : '');
        showImportProgress('idle');
        showImportFailures([...skippedDetails, ...failedPaths]);
        if (document.getElementById('simple-home')) updateChatImportNotice(status.textContent);
        if (document.getElementById('source-result')) await refreshSources();
        await refreshOverview();
      } catch (_) {
        status.textContent = t('sourceIndexIncomplete') + ' ' +
          t('sourceIndexProgress') + ': ' + processed;
      } finally {
        showImportProgress('idle');
        if (document.getElementById('simple-home')) updateChatImportNotice(status.textContent);
        if (button) button.disabled = false;
      }
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

    function appendChatMessage(kind, message) {
      const thread = document.getElementById('qa-result');
      const bubble = document.createElement('div');
      bubble.className = 'chat-message chat-message--' + kind;
      const content = document.createElement('div');
      content.className = 'chat-text';
      content.textContent = message;
      bubble.appendChild(content);
      thread.appendChild(bubble);
      thread.scrollTop = thread.scrollHeight;
      return bubble;
    }

    function clearSimpleChat() {
      if (chatBusy || chatImportBusy || !document.getElementById('simple-home')) return;
      const feed = document.getElementById('qa-result');
      feed.replaceChildren();
      appendChatMessage('assistant', t('chatWelcome'));
      chatGroundedQuestions = [];
      chatActiveQuestion = null;
      chatImportBubble = null;
      chatPendingReply = null;
      lastAnswerData = null;
      const panel = document.getElementById('chat-evidence-panel');
      if (panel) { panel.replaceChildren(); panel.hidden = true; }
      document.getElementById('qa-question').focus();
    }

    function updateChatImportNotice(message) {
      if (!document.getElementById('simple-home')) return;
      // One live progress message rather than one message per indexing pass.
      if (!chatImportBubble) chatImportBubble = appendChatMessage('assistant', message);
      else chatImportBubble.children[0].textContent = message;
    }

    function initSimpleChat() {
      const question = document.getElementById('simple-home') &&
        document.getElementById('qa-question');
      if (!question) return;
      question.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
          event.preventDefault();
          runAnswer();
        }
      });
    }

    async function runAnswer() {
      const input = document.getElementById('qa-question');
      const question = input.value.trim();
      if (!question) { input.focus(); return; }
      const onChat = Boolean(document.getElementById('simple-home'));
      if (onChat && (chatBusy || chatImportBusy)) {
        if (chatImportBusy) {
          document.getElementById('source-import-status').textContent = t('chatImportBusy');
        }
        return;
      }
      const payload = {
        question,
        source_scope: parseScope(document.getElementById('qa-scope').value),
        limit: Number(document.getElementById('qa-limit').value || 5),
      };
      if (onChat && chatGroundedQuestions.length) {
        payload.recent_questions = chatGroundedQuestions.slice(0, 4);
      }
      if (onChat) {
        chatActiveQuestion = question;
        chatBusy = true;
        input.value = '';
        appendChatMessage('user', question);
        chatPendingReply = appendChatMessage('assistant', t('chatSearching'));
        document.getElementById('qa-send-button').disabled = true;
      }
      appendLog(t('runningAnswer'));
      try {
        const response = await fetch('/api/answer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok && !data.error) data.error = 'request_failed';
        renderAnswerResult(data);
        appendLog(t('answerFinished'));
      } catch (error) {
        renderAnswerResult({ error: 'request_failed' });
        appendLog(t('answerFailed'));
      } finally {
        if (onChat) {
          chatBusy = false;
          document.getElementById('qa-send-button').disabled = false;
          input.focus();
        }
      }
    }

    function initSimpleDropzone() {
      const zone = document.getElementById('simple-dropzone');
      if (!zone) return;
      for (const eventName of ['dragenter', 'dragover']) {
        zone.addEventListener(eventName, (event) => {
          event.preventDefault();
          zone.classList.add('drag-over');
        });
      }
      for (const eventName of ['dragleave', 'drop']) {
        zone.addEventListener(eventName, (event) => {
          event.preventDefault();
          zone.classList.remove('drag-over');
          if (eventName === 'drop' && event.dataTransfer && event.dataTransfer.files.length) {
            importSelectedFiles(event.dataTransfer.files, false);
          }
        });
      }
    }

    applyTheme();
    applyLanguage();
    document.getElementById('log').textContent = t('uiStarted');
    refreshSummary();
    initSimpleDropzone();
    initSimpleChat();
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
    "/": "overview",  # Existing root remains valid; now a guided landing page.
    "/uebersicht": "overview",
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
    for name in ("overview", "question", "search", "evidence", "sources"):
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
            if action == 'import-files':
                # Uploads always originate from an explicit browser file picker.
                # Non-simple action header blocks cross-origin form/CSRF posts.
                origin = self.headers.get("Origin", "")
                expected = f"http://{host}:{port}"
                if (origin and origin != expected or
                        self.headers.get("X-ToF-UI-Action") != "source-import" or
                        "application/json" not in self.headers.get("Content-Type", "").lower()):
                    self._send(403, "application/json; charset=utf-8",
                               _json_bytes({"error": "same_origin_action_required"}))
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 1 or length > 24 * 1024 * 1024:
                        raise ValueError("invalid_import_size")
                    raw = self.rfile.read(length)
                    if len(raw) != length:
                        raise ValueError("incomplete_import")
                    payload = json.loads(raw.decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError("invalid_import_request")
                    result = import_selected_files(payload.get("files"))
                except (ValueError, TypeError, UnicodeError):
                    self._send(400, "application/json; charset=utf-8",
                               _json_bytes({"error": "invalid_import_request"}))
                    return
                self._send(200, "application/json; charset=utf-8", _json_bytes(result))
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
