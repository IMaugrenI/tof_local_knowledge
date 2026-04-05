# tof_local_knowledge

> Die englische Hauptfassung liegt in `README.md`.

On_prem lokales Wissenssystem fuer Dokumenten_Indexierung, Suche und belegte Antworten.

Ich habe dieses Repo gebaut, damit lokale Dateien zu durchsuchbarer Evidenz und zu Antworten mit sichtbarer Quellenbasis werden.

## start_here

```bash
bash scripts/setup.sh
bash scripts/up.sh
bash scripts/check.sh
```

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

## wichtige_dokumente

- `docs/00_product_scope.md`
- `docs/01_architecture.md`
- `docs/04_ingest_flow.md`
- `docs/05_search_qa.md`
- `docs/11_runtime_stack.md`
- `docs/12_first_run.md`
- `docs/commands.md`

## verwandte_oeffentliche_repos

- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — lokaler KI_Builder_Stack
- [`tof_showcase`](https://github.com/IMaugrenI/tof-showcase) — oeffentlicher Architektur_Einstieg
- [`tof_v7_public_frame`](https://github.com/IMaugrenI/tof-v7-public-frame) — reduzierter V7_Grenzrahmen
