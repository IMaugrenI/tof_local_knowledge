# tof_local_knowledge

> Die englische Hauptfassung liegt in `README.md`.

On_prem lokales Wissenssystem fuer Dokumenten_Indexierung, Suche und belegte Antworten.

Ich habe dieses Repo gebaut, damit lokale Dateien zu durchsuchbarer Evidenz und zu Antworten mit sichtbarer Quellenbasis werden.

## start_here

Primaerer Runtime_Einstieg:

```bash
python run.py setup
python run.py up
python run.py check
```

Weitere Runtime_Befehle:

```bash
python run.py status
python run.py doctor
python run.py down
```

Linux Komfort_Wrapper existieren weiter, sind aber jetzt nur noch duenne Huelle um `python run.py ...`.

## was_dieses_repo_macht

1. es registriert und scannt lokale Quellen
2. es extrahiert Inhalte aus gaengigen Dokumentenformaten
3. es uebersetzt rohe Extraktionsbloecke in zitierbare Segmente
4. es speichert durchsuchbare Datensaetze in Postgres
5. es beantwortet Fragen aus Suchtreffern statt aus freiem Raten
6. es kann optional lokale Ollama_ und Open_WebUI Ebenen nutzen

## was_bereits_funktioniert

1. Quellen_Scan in Postgres_gestuetzte Dokumentensaetze
2. Extraktionshelfer fuer txt, md, json, html, csv, eml, pdf, docx und xlsx
3. kanonische zitierbare Segmente
4. full_text Suche ueber gespeicherte Segmente
5. grounded QA Endpoint

## was_dieses_repo_zeigt

1. hands_on Arbeit mit Linux, Docker und Postgres
2. evidence_first Dokumenten_Workflows
3. klare Trennung zwischen Rohinput, Index und Antwort_Ebenen
4. produktorientiertes Denken fuer lokale Wissensraeume
5. praktische Dokumentations_ und Runtime_Disziplin

## grenze

1. das ist nicht das Builder_Repo
2. das ist kein cloud_first Produkt
3. das ist kein verstecktes Remote_Sync System
4. dieses Repo konzentriert sich auf lokale oder interne Dokumentenraeume

## zentrale_runtime_dateien

- `run.py`
- `tof_cli/`
- `compose.full.yml`
- `.env.example`
- `docs/13_python_cli_runtime.md`
- `docs/11_runtime_stack.md`
- `docs/commands.md`

## legacy_shell_wrapper

- `scripts/setup.sh`
- `scripts/up.sh`
- `scripts/check.sh`
- `scripts/down.sh`
- `scripts/status.sh`
- `scripts/doctor.sh`

## verwandte_oeffentliche_repos

- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — lokaler KI_Builder_Stack
- [`tof_showcase`](https://github.com/IMaugrenI/tof-showcase) — oeffentlicher Architektur_Einstieg
- [`tof_v7_public_frame`](https://github.com/IMaugrenI/tof-v7-public-frame) — reduzierter V7_Grenzrahmen
