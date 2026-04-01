# File and Content Flow

1. create source
2. mount source as read-only
3. start scan
4. create file objects and manifest entries
5. run extraction
6. translate extraction into canonical segments
7. update catalog
8. expose search
9. produce grounded answer
10. write audit event

## Status fields
- seen
- registered
- fully_read
- partially_read
- unreadable
- indexed
- answerable

## Required rule
The translation from raw extraction to canonical segments is its own explicit and testable step.
