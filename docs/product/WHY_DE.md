# Warum dieses Repository existiert

> Englisch ist der Primärtext dieses Repositories. Ein deutscher Klon liegt in `WHY_DE.md`.

## Problem

Viele "Knowledge"-Systeme antworten zu frei.
Sie wirken nützlich, verwischen aber oft die Grenze zwischen Quellmaterial, extrahiertem Inhalt, indexierten Datensätzen und generierten Antworten.

Für lokale und interne Dokumenträume ist das der falsche Trade-off.

## Gewählter Ansatz

Dieses Repository behandelt lokales Wissen als grounded system und nicht als freie Assistant-Hülle.

Die Hauptentscheidungen sind:

1. local-first / on-prem Betrieb
2. explizite Trennung zwischen Rohinput, Extraktion, Index und Antwortschichten
3. Antworten sollen auf gespeicherter Evidenz beruhen statt auf ungebundener Generierung

## Warum dieser Ansatz

Ich wollte ein Wissenssystem, in dem lokale Dateien lokal bleiben und in dem Antworten auf Evidenz zurückführbar sind.
Darum kollabiert dieses Repository Scanning, Extraktion, Indexierung und Antwortpfad nicht zu einer einzigen vagen Schicht.

Die Trennung ist bewusst:
Rohdateien sind nicht dasselbe wie extrahierte Blöcke,
extrahierte Blöcke sind nicht dasselbe wie durchsuchbare Segmente,
und durchsuchbare Segmente sind nicht dasselbe wie eine Antwort.

Diese Struktur existiert, um Mehrdeutigkeit zu reduzieren, das System besser prüfbar zu machen und den Antwortpfad ehrlich zu halten.

## Warum nicht die naheliegende Alternative

Ich wollte nicht:

- ein cloud-first Wissensprodukt
- ein System, das sich wie ein generischer Chatbot mit Dokumentgeschmack verhält
- versteckte Remote-Sync-Annahmen
- Antworten, die plausibel klingen, aber nicht stark geerdet sind

Diese Ansätze mögen einfacher wirken, schwächen aber das Vertrauen in das System.

## Trade-off

Dieses Design ist expliziter und strukturierter als ein leichteres Assistant-Style-Tool.
Das bedeutet mehr Pipeline-Denken, mehr Grenzen und weniger "Magie".

Ich akzeptiere diesen Trade-off, weil lokale Wissensarbeit Nachvollziehbarkeit stärker braucht als theatralische Flüssigkeit.

## Was ich als Nächstes verbessern würde

Wenn ich die öffentliche Darstellung überarbeite, würde ich die Designgründe noch direkter sichtbar machen:
warum grounded QA wichtig ist,
warum die Schichttrennung nicht verhandelbar ist,
und warum dieses Repo ein produktförmiges lokales Wissenssystem ist statt ein öffentlicher ToF-Runtime-Spiegel.
