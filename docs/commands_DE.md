# Befehle

> Deutsch ist die Spiegelversion dieses Dokuments. Der englische Primärtext liegt in `commands.md`.

Dieses Repository zeigt einen kleinen öffentlichen Operator-Pfad, damit lokales Starten und Beenden leicht verständlich bleibt.

## Schnellster Einstieg

```bash
bash scripts/start_here.sh
```

Äquivalente Einstiegspunkte:

- PowerShell: `pwsh ./scripts/start_here.ps1`
- macOS: `./scripts/start_here.command`

Dieser Pfad führt Setup, Start und Health-Check in der erwarteten Reihenfolge aus.

## Direkter Runtime-Pfad für Linux/macOS

```bash
python3 run.py setup
python3 run.py up
python3 run.py check
python3 run.py status
python3 run.py down
```

## Browser-Control-Pfad

```bash
python3 run.py ui
```

## Standard-Befehlsfluss

```bash
bash scripts/setup.sh
bash scripts/up.sh
bash scripts/check.sh
bash scripts/logs.sh
bash scripts/down.sh
```

## Befehle

- `bash scripts/start_here.sh` — Einsteigerpfad, der Setup, Up und Check nacheinander ausführt
- `python3 run.py ui` — lokale Browser-Steuerfläche für Start, Suche und grounded Answer
- `bash scripts/setup.sh` — `.env` und lokale Verzeichnisse vorbereiten
- `bash scripts/up.sh` — den vollen Stack über den öffentlichen Wrapper starten
- `bash scripts/check.sh` — Health-Prüfungen für den laufenden Stack ausführen
- `bash scripts/logs.sh` — Compose-Logs verfolgen
- `bash scripts/pull.sh` — vorhandene Upstream-Images aktualisieren
- `bash scripts/down.sh` — den Stack sauber stoppen, ohne Daten zu löschen
- `bash scripts/restart.sh` — den Stack über die öffentlichen Wrapper neu starten
- `bash scripts/reset.sh` — destruktiver Reset für lokale Servicedaten sowie Derived-/Export-Storage

## Hinweise

- Linux-Shell-Wrapper rufen `python3 run.py ...` auf
- `down.sh` ist standardmäßig nicht destruktiv
- `reset.sh` ist der destruktive Pfad und sollte bewusst verwendet werden
