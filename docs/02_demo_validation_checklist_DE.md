# Demo-Abnahmecheckliste

Nutze diese Checkliste nach `docs/01_demo_flow.md` und vor öffentlichen Screenshots, Release Notes oder einem öffentlichen Guide.

Ziel: Nachweisen, dass die sichere Demo aus einem frischen lokalen Clone mit neutralen Daten funktioniert.

## Erforderliche lokale Prüfung

Führe dies aus einem sauberen lokalen Checkout oder sauberen Branch-Zustand aus.

```bash
git status --short
python run.py setup
python run.py up
python run.py check
python run.py status
```

Die Prüfung ist nur akzeptabel, wenn:

- der Stack ohne manuelle Reparatur startet
- `check` die erwarteten laufenden Services meldet
- `status` keinen offensichtlich defekten lokalen Zustand zeigt
- der konfigurierte Quellenpfad auf `demo/source_1/` zeigt
- für öffentliche Screenshots kein privater Quellenordner genutzt wird

## Demo-Quellenprüfung

Prüfe, dass der lokale Quellenroot auf den neutralen Demo-Ordner zeigt.

Erwartete öffentliche Demo-Quelle:

```text
demo/source_1/
```

Im laufenden Stack sollte die Demo-Quelle so auflösbar sein:

```text
/sources/source_1
```

Nutze eine neutrale Quellenbezeichnung wie:

```text
demo_source_1
```

Zeige keine absoluten privaten Pfade in Screenshots. Schneide lokale Pfaddetails weg oder verpixle sie, falls sie sichtbar sind.

## Suchprüfungen

Führe mindestens diese Demo-Suchen aus `demo/questions.md` aus:

```text
vacation policy
citation labels
safe screenshots
resolved incident
```

Ein erfolgreicher Such-Screenshot sollte mindestens zeigen:

- Quellen- oder Dokumentreferenz
- relativen Pfad oder neutralen Quellennamen
- Segment- oder Zitationslabel
- Vorschautext
- Ranking- oder Score-Information, falls UI oder API sie anzeigen

## Grounded-Answer-Prüfungen

Führe mindestens diese grounded Fragen aus:

```text
What does the demo say about vacation policy?
Why are demo screenshots safe to publish?
Which incident was resolved?
```

Ein erfolgreicher Grounded-Answer-Screenshot sollte zeigen oder verfügbar machen:

- Antworttext
- verwendete Dokumente
- Zitationen oder Zitationslabels
- sichtbare Evidenzverknüpfung
- Unsicherheit oder No-Evidence-Verhalten, wo relevant

## Negativtest

Führe diese No-Evidence-Frage aus:

```text
What is the private customer contract number?
```

Erwartetes Verhalten:

- das System erfindet keine Vertragsnummer
- die Antwort sagt klar, dass keine unterstützende Evidenz gefunden wurde
- es erscheinen keine privat wirkenden Fake-Details

## Screenshot-Abnahme

Vor dem Committen von Screenshots prüfen:

- [ ] Screenshot nutzt nur Daten aus `demo/source_1/`
- [ ] keine privaten ToF/V7-Runtime-Daten sichtbar
- [ ] keine Kundendaten sichtbar
- [ ] keine `.env`-Werte sichtbar
- [ ] keine Tokens, Secrets, Keys oder Zugangsdaten sichtbar
- [ ] keine privaten absoluten lokalen Pfade sichtbar
- [ ] keine echten Logs sichtbar
- [ ] Screenshot stammt aus echter lokaler UI oder echter lokaler API-Ausgabe
- [ ] Screenshot ist kein Mock, der als echte Ausgabe dargestellt wird
- [ ] Ergebnis passt ausreichend zu `demo/expected_results.md`

## Bereitschaft für öffentlichen Release

Das Repo ist erst dann bereit für einen ersten öffentlichen Demo-Release, wenn:

- die sichere Demo-Quelle aus einem frischen Clone indexiert werden kann
- mindestens ein Suchergebnis mit Evidenz sichtbar ist
- mindestens eine grounded Antwort mit Zitationen sichtbar ist
- der negative No-Evidence-Test korrekt reagiert
- Screenshots sauber und öffentlich zeigbar sind
- README auf Demo-Flow und Abnahmecheckliste verweist

Vorgeschlagenes Release-Label nach der Prüfung:

```text
v0.1.0-public-demo
```

Vorgeschlagene Release-Grenze:

```text
Erste öffentliche Demo-Baseline für tof_local_knowledge.

Nutzt nur neutrale Demo-Daten. Keine privaten ToF/V7-Runtime-Daten, Kundendaten, Secrets oder echten lokalen Logs enthalten.
```
