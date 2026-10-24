# Hier starten

Das ist der kürzeste sichere Weg vom frischen Klon bis zur ersten Antwort aus lokalen Dokumenten.

> English version: [START_HERE.md](START_HERE.md)

## Wofür dieses Produkt gedacht ist

Lege Dokumente auf deinem Rechner ab, durchsuche sie und stelle Fragen zu ihrem Inhalt.

Die wichtigste Regel ist einfach: **Antworten sollen auf sichtbaren Quellen beruhen.** Wenn deine Dokumente eine Antwort nicht tragen, soll ToF das sagen, statt etwas zu erfinden.

Beim ersten Start werden nur die mitgelieferten synthetischen Demo-Dokumente verwendet. Du musst für den Test keine privaten Dateien angeben.

## Was du brauchst

- Python 3.11+ (unter Windows über `py` oder `python`)
- Docker mit Docker Compose
- einen lokalen Browser
- genügend Speicherplatz für den Dokumentindex und ein optionales lokales KI-Modell

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

Der erste Start bereitet die lokale Umgebung vor, startet sie und prüft die wichtigen Teile.

Die lokale Oberfläche öffnest du mit:

```bash
python3 run.py ui
```

## Dein erstes sinnvolles Ergebnis

Nutze die mitgelieferten Demo-Dokumente und stelle eine der Beispielfragen aus `demo/questions.md`.

Ein erfolgreicher Ablauf bedeutet:

- du bekommst eine Antwort aus den Demo-Dokumenten
- die verwendeten Quellen werden sichtbar
- du kannst die passenden Fundstellen nachvollziehen
- eine Frage ohne ausreichende Grundlage bleibt sichtbar unbeantwortet

Du musst die interne Indexierung oder die einzelnen Dienste dafür nicht verstehen.

## Wenn nichts gefunden wird

Das ist nicht automatisch ein Fehler.

Versuche:

1. andere Suchbegriffe
2. zu prüfen, ob das Dokument bereits hinzugefügt wurde
3. die Frage enger zu formulieren

Wenn die lokale Umgebung selbst nicht erreichbar ist, öffne **Einrichtung & technische Details → Probleme finden**.

Im Terminal:

```bash
python3 run.py doctor
```

## Vor echten Dokumenten

Die Demo ist absichtlich künstlich. Bevor du private Dokumente hinzufügst, lies [SECURITY.md](SECURITY.md).

Die normale lokale Konfiguration bindet die erreichbaren Dienste standardmäßig nur an diesen Rechner. Veröffentliche keine privaten Dokumente, Screenshots, lokalen Pfade, Zugangsdaten oder Antworten mit sensiblen Informationen.

## Stoppen und später weitermachen

Stoppen:

```bash
python3 run.py down
```

Später:

```bash
python3 run.py up
python3 run.py ui
```

Dein lokaler Index und die Konfiguration bleiben auf diesem Rechner, solange du sie nicht selbst entfernst.

## Beispiel aus echter Nutzung

[docs/USER_JOURNEY_DE.md](docs/USER_JOURNEY_DE.md) zeigt einen kompletten Weg von der Frage über die Antwort bis zur Quelle und zusätzlich einen Fall ohne ausreichende Grundlage.

## Mehr Details

- [Einsteiger-Quickstart](docs/00_beginner_quickstart.md)
- [Demo-Ablauf](docs/01_demo_flow.md)
- [Validierungscheckliste](docs/02_demo_validation_checklist_DE.md)
- [Suche und Antworten](docs/05_search_qa_DE.md)
- [Technische Runtime](docs/11_runtime_stack.md)
- [Befehle](docs/commands.md)
