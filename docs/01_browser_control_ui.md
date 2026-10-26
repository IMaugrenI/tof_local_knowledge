# Local Knowledge browser UI – multiple pages

The existing local browser UI is launched with the same entry point:

```bash
python3 run.py ui
```

It is available only on `127.0.0.1:8785` by default. The historical URL `/` remains valid and now opens a guided **overview**. The original question page remains at `/frage-stellen`.

## Navigation

A shared top navigation bar (German/English, dark/light mode) links to five browser addresses:

| Area | Route | Purpose |
| --- | --- | --- |
| Übersicht / Overview | `/` or `/uebersicht` | Clear starting point, indexed-document count and links to next actions |
| Quellen & Index | `/quellen-index` | Inspect source status, select logical sources, manually index batches |
| Beleg prüfen | `/beleg-pruefen` | View an exact indexed segment, linked from search/answer results |
| Dokumente durchsuchen | `/dokumente-durchsuchen` | Search with source scope and open exact evidence |
| Frage stellen | `/frage-stellen` | Ask a grounded question and inspect its citations |

The active page is highlighted, and the URL changes on navigation, so browser back/forward and bookmarks work. Each route renders only its feature, while retaining the existing shared setup and status controls in the collapsible technical panel. The overview displays an indexed-document count from the existing read-only catalog status endpoint and guides the user to questions, searches, sources or evidence. Source-specific manual indexing and query scope/limit fields are folded into optional advanced areas on task pages. No extra server, Docker Compose file, SPA framework or second entry point is introduced.

### Cross-page actions

- Clicking **Textstelle ansehen** from a search or QA response navigates to `/beleg-pruefen?segment_id=...` and resolves the segment through the existing read-only evidence API.
- Clicking **Diese Quelle durchsuchen** on the sources page navigates to `/dokumente-durchsuchen?source_id=...` and pre-fills the existing source scope.
- Answer/search API requests, manual indexing, same-origin checks and local single-user limitations are unchanged.
- Theme and language preferences remain in the browser's existing local storage.

## Refreshing an already running UI

This UI is a local Python process, **not** a Docker container. After updating the repository, end only its foreground `python3 run.py ui` process with Ctrl+C, then launch it again with the same command. Leave the existing Compose stack running.

For acceptance, verify the overview and four task routes, one sample search with a viewable evidence segment, a sourced answer, and the negative no-evidence question. Do not repeat already accepted Docker and indexing tests.

Do not share screenshots with private document content, personal paths or secrets.

## Complete German / English UI text

The existing **English / Deutsch** toolbar button updates the whole five-page browser interface, including the navigation, captions, form accessibility labels, placeholders, source/index states, counts, help text, document evidence notices, QA uncertainty chips, no-evidence notices and the default mounted-source label. Selected language stays in the browser's existing local storage across all page URLs.

Dynamic results are rerendered in the new language when toggled. The app also localizes the **fixed German framing text** emitted by the existing QA API when it displays a sourced excerpt or a no-evidence response. This affects presentation only: the QA API response contract, original citations, document excerpts, source names and machine-readable diagnostics are deliberately preserved verbatim. A source document is **not silently translated**, and technical identifiers in expandable raw JSON remain unchanged.

To see changes after updating the repository, restart **only** the foreground Python UI process (`Ctrl+C` followed by `python3 run.py ui`). Do not rebuild or restart the existing Compose services.

## Usability revision after DOM's K-11 feedback

The previous four isolated pages lacked a clear beginning or progress context. The new default overview answers *What can I do?*, *Are my documents indexed?*, and *Where do I go next?*. It uses only the existing `/api/sources` read-only endpoint, and does not infer authentication or readiness from a mere document count. The four original routes and API contracts remain intact. Each task route has one short instruction and a way back, while scope/limit inputs and manual index tools are available only after opening **Advanced options**. The evidence page links back to Search when no passage is selected. Existing per-source search links and evidence deep links still function.

No additional service, database, external dependency, authentication layer, Compose start path, or persistent data change is introduced. The existing technical setup, check and emergency stop controls remain accessible in the collapsed technical panel. All new text appears in German and English.

## Eigene Dateien und Ordner freigeben (K-13)

Auf **Quellen & Index** gibt es zwei ausdrückliche Freigabewege:

1. **Dateien auswählen:** Der Browser erlaubt die Auswahl einzelner lokaler Dateien. Die UI kopiert diese über den lokalen Server in den Unterordner `Importierte_Dateien` innerhalb des bereits konfigurierten `LOCAL_SOURCE_ROOT_1`.
2. **Ordner verbinden:** Bei Browsern mit File System Access API wird der Benutzer durch den nativen Ordnerdialog um **Lesezugriff für genau diesen Ordner** gebeten. Der Browser kann den Ordner-Handle nach Freigabe lokal speichern. **Ordner erneut abgleichen** kopiert Inhalte nur nach einem weiteren ausdrücklichen Klick, niemals im Hintergrund. In Browsern ohne diese API funktioniert ein `webkitdirectory`-Ordnerimport; für den nächsten manuellen Abgleich muss der Benutzer den Ordner erneut auswählen.

Alle Auswahlwege liefern **lokale Kopien / Snapshots** an die unveränderte Docker-Quellenbindung. Sie sind **keine Live-Mounts** und erzeugen **keinen automatischen Watcher**. Die Originalordner werden weder modifiziert noch umbenannt, bewegt oder gelöscht. Die Benutzeroberfläche weist auf diese Grenze hin. Neue Kopien werden erst nach dem separaten Button **Importierte Dateien jetzt einlesen** durch den bestehenden Scan-/Extraktionspfad verarbeitet. Dieser manuelle UI-Auftrag ruft denselben bestehenden Batch-Endpunkt wiederholt mit begrenzter Chargenzahl auf (maximal 45 × 8 Dokumente); er zeigt die Anzahl der verarbeiteten Dokumente und meldet unvollständige Durchläufe. Der vorhandene technische Einzelchargen-Button bleibt erhalten. Keine automatische Hintergrundindexierung.

**Sicherheitsgrenzen:** Browser-Picker / ausdrückliche Benutzerfreigabe statt willkürlicher Hostpfadwahl; nur erlaubte Dateiendungen aus dem vorhandenen Extraktor; pro Datei max. 12 MiB, je Importanfrage höchstens vier Dateien und 16 MiB binäre Daten (Server-Payload streng begrenzt); keine absoluten Pfade, `..`, versteckte Namen oder Symbol-Links im Ziel; Importkopien erhalten `0600`. Berechtigung zu ursprünglich ausgewählten Ordnern liegt – wo unterstützt – ausschließlich im browserlokalen IndexedDB, nicht in der Docker-Konfiguration. Uploadaktion verlangt JSON, Same-Origin und den nicht-einfachen Header `X-ToF-UI-Action: source-import`. Die localhost-Portbindungen bleiben gleich.

**Einschränkung:** Gespiegelte Dateien bleiben bis zum nächsten bewussten Abgleich unverändert. Entfernte Quelldateien werden nicht automatisch aus Importkopien oder Index gelöscht. Große Dateien werden übersprungen; die UI meldet die Anzahl. Die voreingestellte Demoquelle kann weiterhin durch getrennte Quellen-Unterordner genutzt werden. Der automatisch angelegte Import-Unterordner der Demoquelle wird in `.gitignore` ausgeschlossen, damit private Dokumente nicht versehentlich committet werden. Bei anderen vom Betreiber gesetzten Quellenpfaden muss das externe Verzeichnis unabhängig geschützt werden.
