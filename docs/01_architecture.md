# Architektur

## Fachliche Kette
1. Quelle sehen
2. Quelle scannen
3. Dateiobjekt registrieren
4. Inhalt extrahieren
5. Extraktion übersetzen/normalisieren
6. Dokumentsegmente katalogisieren
7. suchen
8. evidenzbasiert antworten

## Technische Dienste
- postgres
- auth_api
- catalog_api
- ingest_api
- extractor_api
- search_api
- qa_api
- optional ollama
- optional open_webui

## Architekturprinzipien
- Docker-first
- Postgres-only
- klare Servicegrenzen
- API-/Vertragsdenken
- fail-closed
- append-only Auditdenken
- gelesen ist nicht nur gesehen
- Antwort nur mit Beleg oder Unsicherheit
- Open WebUI nur als UI, nicht als Wahrheitsschicht

## Wichtige Kante
Die QA-Schicht darf nie direkt gegen Rohdateien antworten. Sie muss gegen Katalog, Segmente und Fundstellen arbeiten.
