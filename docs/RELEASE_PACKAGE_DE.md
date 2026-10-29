# ToF Local Knowledge – Offline-Anleitung zum Quellpaket

**Pakettyp:** Quellpaket-Kandidat für Windows, Linux und macOS; **keine native Installation, kein freigegebener Produkt-Release**. Die Abnahme erfolgt erst nach abgeschlossenem Ausbau.

## Voraussetzungen

- Docker mit Docker Compose auf dem Zielrechner
- Python 3.11 oder neuer
- Windows: PowerShell 7 (`pwsh`), Linux/macOS: Bash
- Genügend lokaler Speicher für Container und Dokumentindex (optionale KI-Modelle benötigen weiteren Speicher)

Das ZIP enthält vorhandene Repository-Dateien und Startskripte. Es installiert Docker/Python nicht automatisch.

## Paket prüfen und entpacken

Das heruntergeladene ZIP hat das Format `tof_local_knowledge-source-candidate-<commit>.zip`.
Die Datei `CHECKSUMS.sha256` enthält den erwarteten SHA-256-Hash.

- Linux: im Downloadverzeichnis `sha256sum -c CHECKSUMS.sha256`
- macOS: `shasum -a 256 <zip-dateiname>` und mit `CHECKSUMS.sha256` vergleichen
- Windows: `Get-FileHash .\<zip-dateiname> -Algorithm SHA256` und vergleichen

Entpacke das ZIP und wechsle in den Ordner `tof_local_knowledge`.

## Erster Start: vorhandener Weg

Windows PowerShell 7:

```powershell
pwsh ./scripts/start_here.ps1
```

Linux:

```bash
bash scripts/start_here.sh
```

macOS:

```bash
bash scripts/start_here.command
```

Der vorhandene Ablauf verwendet weiterhin `run.py` und die im Repository definierten Docker-Compose-Dateien. **Nicht** parallel eigene Compose-Instanzen starten.

## Browser-Steuerung und Hilfe

Vom entpackten Projektordner aus:

```bash
python run.py ui
```

Unter Linux/macOS heißt der Python-Befehl häufig `python3`. Danach mitgelieferte Demoquelle nutzen, Indexierung starten, suchen und die angezeigten Belegstellen prüfen.

Bei einem Problem: `python run.py doctor` (gegebenenfalls `python3`). Weitere Hilfe: `START_HERE_DE.md` und `INSTALL_AND_FIRST_TEST.md`.

## Grenzen

Das Paket ist **kein Installer**, keine Bestätigung von Windows-/macOS-/Linux-Runtime-Funktion und keine Produktfreigabe. Es startet beim Entpacken nichts, enthält keine persönlichen lokalen Einstellungen oder private Dokumente und veröffentlicht nichts über GitHub Releases. Die vollständige Abnahme und spätere Release-Freigabe bleiben ausdrücklich ausstehend.


## Gemeinsamer Test-Meilenstein: Ein-Seiten-Chat

Nach Freigabe des Ausbaustands durch DOM wird **einmal** ein Quellpaket über
den vorhandenen manuellen GitHub-Actions-Workflow `Source distribution candidate`
oder das bestehende `scripts/build_source_candidate.py` erstellt. Dieser
Schritt ändert weder laufende Container noch produktive Dokumente. Das Paket
ist weiter ein Quellpaket, kein nativer Installer.

Der normale Bedienweg nach dem bestehenden Start ist
`http://127.0.0.1:8785/`. Dort werden freigegebene Dateien oder Ordner
ausgewählt, automatisch in den konfigurierten Quellenbereich kopiert,
indexiert und anschließend mit dem Dokumenten-Chat befragt. Fortschritt,
abgelehnte Dateien und belegende Textstellen bleiben auf dieser Seite sichtbar.
Die Fachseiten dienen nur der Diagnose und erweiterten Bedienung.

**Einmalige Betreiber-Abnahme mit neutralen Dateien:** Eine Datei,
mindestens fünf gemischte Dateien einschließlich einer absichtlich
unlesbaren/ungültigen, Fortschritt bis zur Abschlussmeldung, danach
dokumentengestützte Antwort und zwei Anschlussfragen, eine unbelegte Frage,
anschließend „Neuer Chat“. Originaldateien müssen unverändert bleiben.
Fehlerhafte Dateien dürfen erfolgreiche nicht blockieren. Diese Prüfung ist
bis zum Test-Meilenstein **offen** und darf nicht durch GitHub-CI als bestanden
bezeichnet werden.

Bei einem Fehler zuerst auf der Chat-Startseite den sichtbaren Status prüfen;
weiterführende Diagnose über „Weitere Funktionen“. Keine zweite App starten,
kein paralleles Compose-Projekt erzeugen und keine lokalen privaten Dokumente
in einen öffentlichen GitHub-Report kopieren.
