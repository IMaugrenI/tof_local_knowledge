# Rollen und Rechte

## Rollen
- system_admin
- source_admin
- knowledge_user
- auditor
- service_account

## Scope-Modell
Rechte werden nicht nur über Rollen, sondern über Scopes vergeben:
- source_scope
- path_scope
- action_scope

## Grundregeln
- fail-closed
- keine Treffer außerhalb erlaubter Scopes
- keine QA-Antwort aus verbotenen Quellen
- Audit kann getrennt von Inhaltsfreigabe sein

## Minimale Aktionen
- source:create
- source:read
- scan:run
- document:read
- search:run
- answer:run
- audit:read
