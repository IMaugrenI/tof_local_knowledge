# Audit und Logging

## Trennung
- Audit Events = fachlich relevante Spuren
- Service Logs = technische Laufzeitlogs

## Auditpflichtfelder
- event_id
- timestamp
- actor_id
- action_type
- target_type
- target_id
- outcome
- correlation_id
- scope_ref

## Typische Events
- login_success
- source_created
- scan_started
- file_seen
- extraction_finished
- translation_finished
- search_executed
- answer_generated
- permission_denied

## Prinzip
Append-only. Keine stillen Überschreibungen fachlicher Auditspuren.
