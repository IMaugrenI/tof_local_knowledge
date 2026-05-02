# Demo validation checklist

Use this checklist after `docs/01_demo_flow.md` and before publishing screenshots, a release note, or a public guide.

The goal is simple: prove that the safe demo works from a fresh local clone with neutral data only.

## Required local validation

Run this from a clean local checkout or a clean branch state.

```bash
git status --short
python3 run.py setup
python3 run.py up
python3 run.py check
python3 run.py status
```

The validation is acceptable only if:

- the stack starts without manual repair
- `check` reports the expected running services
- `status` does not show an obviously broken local state
- the configured source path points to `demo/source_1/`
- no private source folder is used for public screenshots

## Demo source validation

Confirm that the local source root points to the neutral demo folder.

Expected public demo source:

```text
demo/source_1/
```

Inside the running stack, the demo source should resolve as:

```text
/sources/source_1
```

Use a neutral source label such as:

```text
demo_source_1
```

Do not show absolute personal paths in screenshots. Crop or blur local path details if they appear.

## Search checks

Run at least these demo searches from `demo/questions.md`:

```text
vacation policy
citation labels
safe screenshots
resolved incident
```

A successful search screenshot should show at least:

- a source or document reference
- a relative path or neutral source name
- a segment or citation label
- preview text
- ranking or score information, if exposed by the UI or API

## Grounded-answer checks

Run at least these grounded questions:

```text
What does the demo say about vacation policy?
Why are demo screenshots safe to publish?
Which incident was resolved?
```

A successful grounded-answer screenshot should show or expose:

- answer text
- used documents
- citations or citation labels
- visible evidence linkage
- uncertainty or no-evidence behavior where relevant

## Negative test

Run this no-evidence question:

```text
What is the private customer contract number?
```

Expected behavior:

- the system should not invent a contract number
- the answer should clearly state that no supporting evidence was found
- no private-looking fake details should appear

## Screenshot acceptance checklist

Before committing screenshots, confirm:

- [ ] screenshot uses only `demo/source_1/` data
- [ ] no private ToF/V7 runtime data is visible
- [ ] no customer data is visible
- [ ] no `.env` values are visible
- [ ] no tokens, secrets, keys, or credentials are visible
- [ ] no private absolute local paths are visible
- [ ] no real logs are visible
- [ ] screenshot is from real local UI or real local API output
- [ ] screenshot is not a mock presented as real output
- [ ] result matches `demo/expected_results.md` closely enough

## Public release readiness

The repo is ready for a first public demo release only when:

- the safe demo source can be indexed from a fresh clone
- at least one search result with evidence is visible
- at least one grounded answer with citations is visible
- the negative no-evidence test behaves correctly
- screenshots are clean and public-safe
- the README links to the demo flow and validation checklist

Suggested release label after validation:

```text
v0.1.0-public-demo
```

Suggested release-note boundary:

```text
First public demo baseline for tof_local_knowledge.

Uses neutral demo data only. No private ToF/V7 runtime data, customer data, secrets, or real local logs are included.
```
