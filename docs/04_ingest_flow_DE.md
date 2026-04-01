# Datei- und Inhaltsfluss

1. Quelle anlegen
2. Quelle read-only mounten
3. Scan starten
4. Dateiobjekte und Manifesteinträge erzeugen
5. Extraktion ausführen
6. Extraktion in kanonische Segmente übersetzen
7. Katalog aktualisieren
8. Suche bereitstellen
9. evidenzbasierte Antwort erzeugen
10. Audit-Ereignis schreiben

## Statusfelder
- seen
- registered
- fully_read
- partially_read
- unreadable
- indexed
- answerable

## Pflichtregel
Die Übersetzung von Roh-Extraktion zu kanonischen Segmenten ist ein eigener, prüfbarer Schritt.
