"""K7 checks for configured local endpoints, bounded requests and UI guidance."""
from __future__ import annotations

import io
import json

import pytest

from tof_cli.ui import app
from tof_cli.ui.service_ops import (
    MAX_JSON_BYTES,
    classify_error,
    configured_targets,
    parse_bounded_json,
)


def test_configured_targets_reuse_existing_local_ports():
    config = {
        "SEARCH_API_PORT": "8115", "QA_API_PORT": "8116",
        "CATALOG_API_PORT": "8112", "OPENWEBUI_PORT": "3111",
    }
    routes = configured_targets(config)
    assert routes["search"] == "http://127.0.0.1:8115/search"
    assert routes["answer"] == "http://127.0.0.1:8116/answer"
    assert routes["sources"] == "http://127.0.0.1:8112/sources/status"
    assert routes["evidence"] == "http://127.0.0.1:8115/evidence"
    assert routes["openwebui"] == "http://127.0.0.1:3111"
    assert routes["qa_docs"] == "http://127.0.0.1:8116/docs"


@pytest.mark.parametrize("bad", ["0", "65536", "foo", "8105/evil", "1.1", "", "１２３４"])
def test_port_validation_fails_closed(bad):
    with pytest.raises(ValueError):
        configured_targets({"SEARCH_API_PORT": bad})


def test_ui_target_selection_uses_env_not_hardcoded_routes(monkeypatch):
    monkeypatch.setattr(app, "read_env", lambda: {"QA_API_PORT": "9222"})
    assert app._configured_target("answer") == "http://127.0.0.1:9222/answer"
    assert app._configured_links()["qa_docs"]["url"] == "http://127.0.0.1:9222/docs"


def test_invalid_configuration_prevents_browser_navigation(monkeypatch):
    monkeypatch.setattr(app, "read_env", lambda: {"OPENWEBUI_PORT": "foo"})
    opened = []
    monkeypatch.setattr(app.webbrowser, "open", lambda url: opened.append(url))
    assert app._open_link("openwebui")["error"] == "invalid_configuration"
    assert opened == []


def test_bounded_json_requires_full_object_and_valid_utf8():
    payload = json.dumps({"query": "Übersicht"}).encode("utf-8")
    assert parse_bounded_json(io.BytesIO(payload), str(len(payload))) == {"query": "Übersicht"}
    for raw in [b"{", b"[]", b"null", b"\xff"]:
        with pytest.raises(ValueError):
            parse_bounded_json(io.BytesIO(raw), str(len(raw)))
    with pytest.raises(ValueError):
        parse_bounded_json(io.BytesIO(b"{}"), str(MAX_JSON_BYTES + 1))
    with pytest.raises(ValueError):
        parse_bounded_json(io.BytesIO(b"{}"), "-1")
    with pytest.raises(ValueError):
        parse_bounded_json(io.BytesIO(b"{}"), "not-a-number")
    with pytest.raises(ValueError):
        parse_bounded_json(io.BytesIO(b"{}"), "3")


def test_categories_are_stable_and_user_facing():
    assert classify_error("service_unavailable") == "service_unavailable"
    assert classify_error("invalid_json") == "invalid_request"
    assert classify_error("invalid_local_port:QA_API_PORT") == "invalid_configuration"
    assert classify_error("upstream_error") == "processing_error"
    assert "friendlyIssue" in app.HTML
    assert "errorMarkup(data, t('searchFailed'))" in app.HTML
    assert "errorMarkup(data, t('answerFailed'))" in app.HTML


def test_existing_api_result_contract_and_scope_unchanged(monkeypatch):
    monkeypatch.setattr(app, "read_env", lambda: {"SEARCH_API_PORT": "8105"})
    assert app._configured_target("search") == "http://127.0.0.1:8105/search"
    assert "source_scope: parseScope" in app.HTML
    assert "issuePending" in app.HTML and "issueFailedDocs" in app.HTML
