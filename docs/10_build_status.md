# Build-Status — öffentlicher Quellcode

**Stand:** 25. Oktober 2026 · Hauptentwicklungsstand mit K1; K2 in Arbeit.

Diese Übersicht beschreibt den im Repository vorhandenen Code. Sie ist **kein Nachweis eines auf einem Zielrechner laufenden Systems**.

## Implementiert im Quellcode

- Offizieller Python-Startweg über `run.py`, `tof_cli` und `compose.full.yml`; optionale Ollama-/Open-WebUI-Profile.
- PostgreSQL-Tabellen für Quellen, Dokumente, Segmente, Extraktionsereignisse, Benutzer-/Rollendatensätze und Scan-Manifeste.
- Quellenscan mit Fingerprintvergleich, dokumentierten Scan-Zählern, unveränderten Erfolgszuständen sowie `pending`/`missing`-Kennzeichnung.
- Datei-Extraktion aus mehreren unterstützten Formaten, Segmentübersetzung und Datenbankpersistenz.
- PostgreSQL-Volltextsuche, belegbasierte Kurzantworten, Keyword-Fallback und Kennzeichnung unkalibrierter Confidence-Werte.
- Lokale Browseroberfläche und Gesundheits-/Diagnosebefehle.

## Wichtige K1-Korrekturen

1. Wiederholter Scan setzt unveränderte, erfolgreich extrahierte Dokumente nicht erneut auf `pending`.
2. Vollständige Scans markieren nicht mehr vorhandene Dokumente als `missing`. Abgebrochene bzw. durch Limit verkürzte Scans führen keine Lösch-/Fehlbestands-Reconciliation durch. Ausgeblendete Hidden-Dateien werden dabei nicht irrtümlich als fehlend bewertet.
3. Die Suche liefert Segmente nur für `extraction_status = 'done'` und aktivierte Quellen zurück. Alte, fehlende oder in Bearbeitung befindliche Dokumente werden nicht als aktuelle Fundstellen präsentiert.
4. Fehlgeschlagene Extraktionsversuche löschen vorhandene Segmente nicht. Diese bleiben als Wiederherstellungsgrundlage erhalten, sind aber aufgrund des Dokumentstatus nicht mehr durchsuchbar.
5. Ein explizites `document_id` muss zur angefragten Quelle und Datei gehören. Extraktionswarnungen werden als valides JSON gespeichert.

## K2: geführte lokale Indexierung

- Die bestehende Browseroberfläche kann nun eine ausdrücklich gestartete, begrenzte Scan-/Extraktionscharge für die bereits über `LOCAL_SOURCE_ROOT_1` eingebundene Quelle auslösen.
- Keine freie Host-Pfadwahl über diese Aktion: Containerpfad `/sources/source_1`, Quellkennung `LOCAL_SOURCE_ID_1` (Standard `demo_source_1`).
- Pro Aufruf höchstens 100 gescannte und acht extrahierte Dokumente. Erneute Aufrufe bearbeiten weitere neu/geänderte/pending Dokumente; neue Dateien gehen vor fehlerhaften Wiederholungen.
- Scanner und Extraktion verwenden beim UPSERT den tatsächlich vorhandenen Primärschlüssel `document_id` statt einen in der bestehenden Schema-Definition nicht vorhandenen Unique-Key `(source_id, relative_path)`.
- Für eine echte Mehrbenutzerfreigabe fehlt weiterhin eine wirksame Identitäts-/Quellenberechtigungsprüfung. Hier wurde kein Mehrbenutzermodus eingeführt.

## Grenzen / noch nicht freigegeben

- **Keine echte Mehrbenutzer-/Quellen-ACL-Freigabe.** Nutzer- und Grant-Tabellen allein sind keine aktive Berechtigungsprüfung. Der aktuelle Codepfad der Suche und der QA akzeptiert einen vom Client angegebenen `source_scope` als Filter, **nicht** als autorisierte Identität. Keine öffentliche oder ungesicherte LAN-Freigabe; die Standard-Konfiguration bindet lokale Ports an `127.0.0.1`.
- Keine behauptete automatische Integration mit Local Builder oder der privaten ToF-Runtime.
- Keine unabhängig kalibrierte Antwortwahrscheinlichkeit. `confidence` ist ein Kompatibilitäts-/Heuristikwert, markiert durch `confidence_uncalibrated`.
- Ausbauschritte wie serverseitig validierte Benutzerrechte, verbesserte Quellen-/Indexansichten, echte Antwortsynthese und größere Datenmengen benötigen eigene Architekturentscheidungen und spätere Arbeit.
- Die GitHub-CI prüft Python, gezielte Tests und Compose-Konfiguration. Sie ersetzt keine reale Betriebsbestätigung.

## Orientierung

- [README](../README.md)
- [K1-Ausbauauftrag](https://github.com/IMaugrenI/tof_local_knowledge/issues/15)
- [Runtime-Dokumentation](11_runtime_stack.md)


## K19–K21 – Gesprächsintention, Quellenauszüge und lexikalische Relevanz

Die GitHub-Entwicklung ergänzt den bestehenden lokalen QA-Pfad um konservative Themenwechsel-Erkennung, kurze mehrdokumentige Textauszüge mit sichtbaren Quellen und eine stabile textbezogene Nachordnung bereits freigegebener Suchtreffer. Erweiterungen sind ohne neue Services oder konkurrierende Runtime integriert. **Nicht enthalten** sind echte semantische Suche, frei formulierte LLM-Synthese, dauerhaftes Gesprächsgedächtnis, serverseitige Mehrbenutzer-ACLs oder eine Betriebsfreigabe auf einem Zielsystem. GitHub-CI und gezielte Tests sind Entwicklungsnachweise; die Runtime-Abnahme wird bis zum vereinbarten Meilenstein gesammelt.
