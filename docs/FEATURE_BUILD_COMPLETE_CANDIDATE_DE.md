# Ausbauabschluss-Kandidat – Local Knowledge

**Status:** Implementierungsstand K1–K9 im bestehenden Repository, gemeinsame Abnahme noch ausstehend. GitHub-CI ist kein Zielsystem-/Runtime-Nachweis.

## Implementierter Funktionskörper

- Bestehender `compose.full.yml`-Stack mit Postgres, Katalog, Scan, Extraktion, Suche und QA
- Sicherer inkrementeller Index, begrenzte Dateichargen und Fortsetzung über große Quellenbestände
- Konkrete Quellen-, Index- und Fehlerstatus in der Browser-Steuerung
- Beleggestützte Suche/Antworten, exakte Segment-Fundstellen, deutschsprachiger Frage-Fallback
- K9: mehrere **logische Unterquellen innerhalb von LOCAL_SOURCE_ROOT_1**, mit eigener Quellkennung, gezielter manueller Indexierung und Suchfilter
- B8/K8-Verteilpaket-Kandidaten mit SHA-256 und vorhandenen Plattform-Startern, ohne öffentliche Release-Freigabe

## Bewusste Grenzen / Betreiberentscheidungen

- Lokaler Einzelbenutzerbetrieb; die Datenbank-Grants sind **keine** durchgesetzte Authentifizierung oder Quellen-ACL
- Keine beliebigen weiteren Host-Ordner über die Weboberfläche mounten. Für externe Wurzeln ist eine ausdrückliche Betreiberentscheidung samt Änderung des vorhandenen autoritativen Compose-Mounts nötig
- Dokumentquellen bleiben read-only; keine ungesicherte LAN-/Mehrbenutzerfreigabe
- Keine neuen Runtimes, keine automatische Kopplung an Builder, keine externen Cloud-Zwangsdienste
- GitHub-CI beweist **keine** reale Docker-Laufzeit auf Windows/macOS/Linux

## Nächste Phase: gemeinsame Abnahme beider Repositories

DOM prüft die zentrale Abnahmeliste nach Abschluss des Funktionsausbaus und trennt DEV-Code-/CI-Nachweise von tatsächlichen Zielsystemprüfungen. P0/P1 und P2 nach bestehendem Abnahmeverfahren bewerten; fehlende Nachweise und Betreiberentscheidungen separat festhalten. Anschließend GO/NO-GO und erst danach öffentliche Freigabe.

**Kein Release-GO vor der Betreiberentscheidung.**
