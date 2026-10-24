# Hier starten

Das ist der kürzeste sichere Einstieg für neue Nutzer.

> English version: [START_HERE.md](START_HERE.md)

## Was dieses Tool macht

`tof_local_knowledge` indexiert lokale Dokumente, macht die gespeicherte Evidenz durchsuchbar und kann Fragen aus gefundenen Belegen beantworten, statt frei zu raten.

Für den ersten Lauf solltest du nur die synthetischen Demo-Dateien aus dem Repository verwenden.

## Voraussetzungen

- Python 3.11+
- Docker mit Docker Compose
- ein lokaler Browser
- genügend Speicherplatz für Postgres und optionale lokale Modellschichten

## Erster Start

### Linux

```bash
git clone https://github.com/IMaugrenI/tof_local_knowledge.git
cd tof_local_knowledge
bash scripts/start_here.sh
```

### Windows PowerShell

```powershell
git clone https://github.com/IMaugrenI/tof_local_knowledge.git
cd tof_local_knowledge
pwsh ./scripts/start_here.ps1
```

### macOS

```bash
git clone https://github.com/IMaugrenI/tof_local_knowledge.git
cd tof_local_knowledge
./scripts/start_here.command
```

Der Start-hier-Pfad führt Setup, Stack-Start und Health-Check aus.

## Prüfen, ob alles läuft

Linux/macOS:

```bash
python3 run.py check
```

Danach lokale UI öffnen:

```bash
python3 run.py ui
```

Die UI ist für lokale Nutzung auf `127.0.0.1:8785` gedacht.

## Sicherer erster Test

Bevor du private Dokumente verwendest, nutze die Demo:

- Quelldateien: `demo/source_1/`
- Beispielfragen: `demo/questions.md`
- erwartete Ergebnisformen: `demo/expected_results.md`

Folge [docs/01_demo_flow.md](docs/01_demo_flow.md).

Der Erfolgsweg ist:

```text
lokale Datei
  → Scan
  → Extraktion
  → zitierbares Segment
  → Suchtreffer
  → belegte Antwort
  → sichtbare Quelle
```

Wenn keine Evidenz vorhanden ist, soll das System diesen Zustand sichtbar lassen statt etwas zu erfinden.

## Befehle im Alltag

```bash
python3 run.py up
python3 run.py status
python3 run.py check
python3 run.py ui
python3 run.py down
```

Bei Problemen:

```bash
python3 run.py doctor
```

## Vor echten Dokumenten

Lies [SECURITY.md](SECURITY.md).

Nicht öffentlich posten:

- echte private Dokumente
- Screenshots echter Quellen
- Zugangsdaten oder `.env`-Werte
- private Pfade, Hostnamen oder Kundendaten

Für öffentliche Issues und Screenshots nur Demo-Daten verwenden.

## Was dieses Tool nicht ist

Es ist kein:

- Cloud-first Dokumentendienst
- Garant für immer korrekte Antworten
- Ersatz für professionelle oder rechtliche Prüfung
- Builder, der generierten Text automatisch zu Evidenz machen darf

## Mehr Details

- [Einsteiger-Quickstart](docs/00_beginner_quickstart.md)
- [Demo-Ablauf](docs/01_demo_flow.md)
- [Validierungscheckliste](docs/02_demo_validation_checklist_DE.md)
- [Suche und QA](docs/05_search_qa_DE.md)
- [Runtime](docs/11_runtime_stack.md)
- [Befehle](docs/commands.md)
