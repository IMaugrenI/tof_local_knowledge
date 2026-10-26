# Local Knowledge browser UI – multiple pages

The existing local browser UI is launched with the same entry point:

```bash
python3 run.py ui
```

It is available only on `127.0.0.1:8785` by default. The historical URL `/` still opens the question page.

## Navigation

A shared top navigation bar (German/English, dark/light mode) links to four independent browser addresses:

| Area | Route | Purpose |
| --- | --- | --- |
| Quellen & Index | `/quellen-index` | Inspect source status, select logical sources, manually index batches |
| Beleg prüfen | `/beleg-pruefen` | View an exact indexed segment, linked from search/answer results |
| Dokumente durchsuchen | `/dokumente-durchsuchen` | Search with source scope and open exact evidence |
| Frage stellen | `/frage-stellen` | Ask a grounded question and inspect its citations |

The active page is highlighted, and the URL changes on navigation, so browser back/forward and bookmarks work. Each route renders only its feature, while retaining the existing shared setup and status controls in the collapsible technical panel. No extra server, Docker Compose file, SPA framework or second entry point is introduced.

### Cross-page actions

- Clicking **Textstelle ansehen** from a search or QA response navigates to `/beleg-pruefen?segment_id=...` and resolves the segment through the existing read-only evidence API.
- Clicking **Diese Quelle durchsuchen** on the sources page navigates to `/dokumente-durchsuchen?source_id=...` and pre-fills the existing source scope.
- Answer/search API requests, manual indexing, same-origin checks and local single-user limitations are unchanged.
- Theme and language preferences remain in the browser's existing local storage.

## Refreshing an already running UI

This UI is a local Python process, **not** a Docker container. After updating the repository, end only its foreground `python3 run.py ui` process with Ctrl+C, then launch it again with the same command. Leave the existing Compose stack running.

For acceptance, verify the four page routes, one sample search with a viewable evidence segment, a sourced answer, and the negative no-evidence question. Do not repeat already accepted Docker and indexing tests.

Do not share screenshots with private document content, personal paths or secrets.
