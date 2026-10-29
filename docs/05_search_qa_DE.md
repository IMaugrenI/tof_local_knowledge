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


## K-18 – Begrenzter Mehrturn-Kontext mit Themenanker

Der Einseiten-Chat übergibt optional `recent_questions` mit höchstens **vier** zuvor belegten Benutzerfragen (je maximal 500 Zeichen). Nur Nutzerfragen sind zulässig; Antworten, Auszüge, Dateipfade und historische Zitationen werden nicht als Input-Kontext übertragen. Der erste belegte Themenanker bleibt bei weiteren Anschlussfragen erhalten; anschließend bleiben die neuesten drei Fragen als begrenzte Gesprächsreferenz vorhanden. Die QA verwendet davon ausschließlich den **frühesten Themenanker**, und auch nur bei ausdrücklich gekennzeichneten Anschlussformulierungen. Neue unabhängige Fragen übernehmen **keinen** früheren Kontext.

Die Auflösung ist weiterhin eine deterministische Keyword-/AND-Suche, keine echte semantische Konversation, keine Speicherung in Memory und kein LLM. Die bestehende Legacy-Option `previous_question` bleibt für ältere Clients erhalten. Treffer werden bei **jedem** Turn neu über den vorhandenen Suchdienst innerhalb des aktuellen Source Scope beschafft. Historische Aussagen oder Belege gelten niemals als Wahrheit für aktuelle Antworten. Breite OR-Treffer bleiben unsicher und nicht zitierfähig. Bei fehlenden Belegen, neuem Dateiimport oder „Neuer Chat“ wird der Kontext clientseitig verworfen.

Dieser Bauabschnitt ist ein sicherer Schritt in Richtung mehrturnfähige Bedienung, **kein** behauptetes vollständiges semantisches Gedächtnis. Weitergehende semantische Auflösung muss vor Umsetzung gesondert anhand der Understanding-/Memory-Verantwortungsgrenzen geprüft werden.


## K19–K21 – Sichere Chat-, Antwort- und Suchverbesserung

**K19 (Gesprächsintention):** Der bestehende, auf vier Benutzerfragen begrenzte Themenanker wird bei neuen Themenhinweisen wie „neuer Vertrag“ oder „another agreement“ nicht übernommen. Sehr lange oder inhaltlich uneindeutige, nur mit „und/and“ eingeleitete Fragen erhalten ebenfalls keine automatische Themenvererbung. Explizite kurze Nachfragen mit neuer Sachfrage bleiben möglich. Das ist eine heuristische Unterscheidung, **keine** semantische Intentionserkennung.

**K20 (Antwortdarstellung):** Das QA-Backend gibt bei belastbaren, nicht bloß breit gefundenen Treffern eine kurze, klar gekennzeichnete Sammlung von Original-Textauszügen aus **maximal drei unterschiedlichen Dokumenten** zurück (je Auszug höchstens 300 Zeichen). Zitatlabel, relativer Dateipfad und vollständige `citations`/`evidence_refs` bleiben erhalten. Die Oberfläche lokalisiert die eigene Überschrift Deutsch/Englisch. Es findet **keine freie Antwortsynthese** statt; Auszüge sind Suchhinweise und keine unabhängig verifizierten Tatsachen.

**K21 (Trefferpriorisierung):** Innerhalb der vom bestehenden, aktuellen, eingeschränkten Suchdienst gelieferten Treffer wird vor der Antwortbildung eine stabile lexikalische Nachordnung vorgenommen: Treffer mit mehreren tatsächlichen Wortübereinstimmungen im sichtbaren Auszug vor reinen Dateinamentreffern; bei Gleichstand bleibt die ursprüngliche Suchreihenfolge erhalten. Keine Änderung an Datenbank, Index oder dem erlaubten Quellen-Scope. Breite OR-Stichworttreffer werden nach wie vor **niemals** zu Antworten oder Zitationen hochgestuft. Dies ist **keine semantische Vektor-/Embedding-Suche**, obwohl pgvector/Ollama optional bereits im bestehenden Compose enthalten sind.

Grenzen: Die Relevanzprüfung bleibt lexikalisch und unkalibriert. Der nächste semantische Ausbau muss eine explizite Validierungsgrenze für Modelltexte sowie den unveränderten datenschutzkonformen lokalen Betrieb definieren, bevor ein Modell aus Evidenz neue Formulierungen ableitet.
