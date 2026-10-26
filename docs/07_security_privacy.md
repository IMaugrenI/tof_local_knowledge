# Sicherheit und Datenschutz

## Grundgrenzen
- Quellen read-only
- keine stillen Remote-Syncs
- keine Cloud-Pflicht
- keine ungefragten externen Modellaufrufe
- lokale Rechteprüfung
- Audit konfigurierbar

## Netzgrenzen
- Betrieb im LAN / internen Netz
- Tailscale höchstens optional für Admin-/Supportzugang
- nicht Kernbestandteil des Produkts

## Datenschutz
- Rohdaten bleiben lokal
- Querytexte können sensibel sein
- Audit daher minimal, standard oder detailed konfigurierbar

## K-10: Lokale Konfigurationsdatei schützen
- `python3 run.py setup` legt eine neue `.env` auf POSIX-Systemen mit Modus `0600` an, unabhängig von einer freizügigen Benutzer-`umask`.
- Vorhandene reguläre `.env`-Dateien werden beim regulären Aufruf von `ensure_env_file` auf `0600` eingeschränkt, **ohne ihren Inhalt zu überschreiben**.
- Symbolische Links und Nicht-Dateien werden bei der Einrichtungsroutine zurückgewiesen, damit nicht versehentlich fremde Dateien verändert werden.
- Für bereits laufende Installationen unmittelbar `chmod 600 .env` ausführen und mit `stat -c '%a' .env` bestätigen. Kein Container-Neustart erforderlich.
- Windows-Berechtigungen folgen dem Windows-ACL-Modell; `chmod` allein ersetzt dort keine Prüfung der ACLs.
- Niemals Zugangsdaten oder den Inhalt von `.env` in öffentlichen Berichten oder Screenshots veröffentlichen.
