from __future__ import annotations


def health_targets(env: dict[str, str]) -> list[tuple[str, str]]:
    return [
        ("auth_api", f"http://127.0.0.1:{env.get('AUTH_API_PORT', '8101')}/health"),
        ("catalog_api", f"http://127.0.0.1:{env.get('CATALOG_API_PORT', '8102')}/health"),
        ("ingest_api", f"http://127.0.0.1:{env.get('INGEST_API_PORT', '8103')}/health"),
        ("extractor_api", f"http://127.0.0.1:{env.get('EXTRACTOR_API_PORT', '8104')}/health"),
        ("search_api", f"http://127.0.0.1:{env.get('SEARCH_API_PORT', '8105')}/health"),
        ("qa_api", f"http://127.0.0.1:{env.get('QA_API_PORT', '8106')}/health"),
    ]
