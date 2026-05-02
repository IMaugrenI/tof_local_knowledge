# Demo evidence screenshots

This page lists the public-safe screenshot evidence for the neutral `demo/source_1/` validation flow.

The README intentionally embeds only one screenshot to stay readable. The full evidence chain lives here and in `assets/screenshots/`.

## Screenshot set

1. [Healthcheck: all services OK](../assets/screenshots/knowledge-01-healthcheck.png)
2. [Scan: neutral demo source indexed](../assets/screenshots/knowledge-02-scan-demo-source.png)
3. [Extraction: citable segment created](../assets/screenshots/knowledge-03-extraction-citation.png)
4. [Search: vacation policy evidence found](../assets/screenshots/knowledge-04-search-vacation-policy.png)
5. [Grounded answer: vacation policy with citation](../assets/screenshots/knowledge-05-grounded-answer-vacation.png)
6. [No-evidence answer: private contract number rejected](../assets/screenshots/knowledge-06-no-evidence-contract-number.png)

## What the screenshots prove

- the local runtime starts and passes health checks
- the neutral demo source can be scanned
- demo documents can be extracted into citable segments
- search returns document references and citation labels
- grounded answers use retrieved evidence
- no-evidence questions do not produce invented private details

## Safety boundary

These screenshots use only neutral synthetic demo files from `demo/source_1/`.
They do not show private ToF/V7 runtime data, customer data, secrets, `.env` values, or real local logs.
