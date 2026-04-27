# Expected demo results

These notes describe the intended result shape for the neutral demo data.
Exact ranking, scores, IDs, and snippets can vary depending on the current index state and search implementation.

## Expected matches

| Question or query | Likely source file | Expected evidence theme |
| --- | --- | --- |
| `vacation policy` | `company_handbook.md` | Vacation requests and response timing |
| `citation labels` | `product_notes.md` or `incident_log_sample.csv` | Search results include document references and citation labels |
| `no-result answer` | `support_faq.md` | The system should avoid inventing missing facts |
| `safe screenshots` | `company_handbook.md`, `support_faq.md`, or `meeting_notes.md` | Public screenshots should use only synthetic demo data |
| `Which incident was resolved?` | `incident_log_sample.csv` | Demo incidents have status `resolved` |

## Expected search behavior

A successful search should return one or more hits with visible evidence fields, such as:

- document reference
- source identifier
- relative path
- segment or citation label
- preview text
- score or ranking information

## Expected grounded-answer behavior

A grounded answer should be based on retrieved evidence.
It should show or expose:

- answer text
- citations or citation labels
- used documents
- confidence or uncertainty information

## Expected no-evidence behavior

For questions that are not answered by the demo files, the system should return a clean no-evidence response.
It should not invent private contract numbers, real customer data, passwords, or hidden facts.

## Safety note

All demo files are synthetic and safe for public screenshots.
Do not replace them with private documents when preparing public README images, guides, PDFs, or Ko-fi product material.
