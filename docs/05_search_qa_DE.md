# Suche und QA

## MVP-Suche
- Postgres Full Text Search
- strukturierte Filter
- Segmenttreffer statt nur Dokumenttreffer

## QA-Regeln
- QA arbeitet nur auf Trefferpool
- Antwort nur mit Zitationen
- bei schwacher Evidenz: Unsicherheit explizit
- keine freie Antwort ohne Quellenbezug

## Antwortpaket
- answer_text
- confidence
- citations[]
- used_documents[]
- uncertainties[]
- query_id
- correlation_id

## Später optional
- pgvector
- lokales Reranking
- Ollama für Formulierung

## K-08: Konservative Evidenzgrenze (P1-Korrektur)

Die lokale QA darf **Treffer einer breiten OR-Stichwortsuche nicht automatisch als Antwortbelege** behandeln. OR kann einzelne, voneinander unabhängige Wörter in unpassenden Dokumenten finden. Gibt es nur solche Treffer, wird deshalb **keine belegte Antwort** erzeugt: `confidence = 0`, `citations = []`, `used_documents = []`, `evidence_refs = []`, `evidence_signal.status = no_evidence`. Zur Diagnose bleiben die versuchten `search_queries` erhalten; `evidence_signal.unverified_candidates` zählt die nicht als Beleg zugelassenen OR-Treffer. `uncertainties` enthält `no_evidence` und `broad_keyword_search`.

Bereits belegte direkte Treffer und strengere Keyword-Fallbacks bleiben nutzbar. **Grenze:** Ein reiner Texttreffer ist noch keine semantische Verifikation jeder Sachbehauptung. Auch positive Antworten bestehen weiterhin aus belegten Auszügen mit ausdrücklicher Unsicherheitskennzeichnung, nicht aus einer unabhängigen Faktenprüfung. Keine externe KI, kein neues Modell und keine weitere Runtime-Komponente erforderlich.

## K-09: Gezielt behobene Demo-Abruflücken

Die vorhandene PostgreSQL-Textsuche berücksichtigt zusätzlich zum extrahierten Segmenttext den in Wörter zerlegten **relativen Dateinamen**. Dadurch findet die Suche mit `resolved incident` den Status `resolved` in `incident_log_sample.csv`; der Quellen-Scope, der Extraktionsstatus und die stabile Trefferreihenfolge bleiben unverändert.

Bei strikten QA-Keyword-Suchen wird bei Bedarf eine **eng begrenzte Wortformvariante** (`publish` → `public`) ausprobiert; alle anderen relevanten Suchwörter bleiben verpflichtend (AND). Der Treffer erhält `search_strategy = keywords_variant` sowie `uncertainties += lexical_variant_not_semantically_verified`. **Breite OR-Treffer bleiben ausschließlich diagnostisch und dürfen weiterhin keine Quellenzitate erzeugen.** Diese konservative Reparatur deckt die reproduzierten Demo-Abweichungen ab, ersetzt jedoch keine unabhängige semantische Antwortprüfung.


## K-16 – Quellengebundene Nachfragen im Dokumenten-Chat

Die Chat-Startseite darf nach einer erfolgreich belegten Antwort die **unmittelbar vorherige Benutzerfrage** (maximal 500 Zeichen) als optionales Feld `previous_question` an `/api/answer` weiterreichen. Der Server verwendet sie ausschließlich bei expliziten Anschlussformulierungen (z. B. „Und welche Frist gilt dafür?“) für eine **deterministische, begrenzte AND-Stichwortsuche** mit dem vorherigen Thema. Er übernimmt weder vorherige Antworttexte noch frühere Fundstellen als Beweise. Die Suche verwendet unverändert den aktuellen Quellen-Scope und die aktive Index-/Berechtigungsgrenze.

Fehlt eine belastbar belegte vorherige Antwort, ist der Verlauf gelöscht oder wurden neue Dateien importiert, wird kein Gesprächskontext weitergegeben. Eine unabhängige neue Frage wird nicht mit alten Themen vermischt. Breite OR-Treffer bleiben weiterhin ausschließlich diagnostisch ohne Zitate. Bei einem positiven Kontexttreffer meldet `uncertainties` die zusätzliche Grenze `contextual_keyword_match_not_semantically_verified`; `evidence_signal.search_strategy` heißt `contextual_followup`.

**Keine semantische Gesprächs-Memory:** Das Verfahren ist kein LLM-basiertes Schlussfolgern aus einer ganzen Unterhaltung und keine persistente Gedächtnisspeicherung. Jede Antwort bleibt dokumentengestützt und fordert bei nicht belegbaren Anfragen Zurückhaltung. Die gesamte sichtbare Unterhaltung existiert nur im Browser bis zum Neuladen und kann mit „Neuer Chat“ gelöscht werden.
