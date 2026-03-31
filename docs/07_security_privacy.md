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
