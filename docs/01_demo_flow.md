# Safe demo flow

This guide prepares `tof_local_knowledge` for trustworthy public screenshots.
It uses only neutral demo data from this repository.

Do not create a PDF, product guide, or public screenshot set before this flow has been validated with a fresh local run.

## Goal

Show the real knowledge chain:

```text
local source -> scan/index -> extracted segments -> search hits/evidence -> grounded answer
```

## Safety rules

- Do not use private documents.
- Do not use customer data.
- Do not use real logs.
- Do not show secrets, tokens, `.env` values, or private local paths.
- Do not present generated or fake screenshots as real UI output.
- Artificial images are acceptable only as banners, diagrams, or explanatory visuals.
- Trustworthy screenshots must be captured from the real local UI or real local API output.

## Demo data

Neutral demo files live in:

```text
demo/source_1/
```

Supporting demo notes live in:

```text
demo/questions.md
demo/expected_results.md
```

## Step 1 — start from a clean local clone

```bash
git clone https://github.com/IMaugrenI/tof_local_knowledge.git
cd tof_local_knowledge
```

If you are testing this branch before merge:

```bash
git checkout docs/demo-validation-checklist
```

## Step 2 — point the local source root to the demo folder

Copy `.env.example` to `.env` if it does not already exist:

```bash
cp .env.example .env
```

Then set the first local source root to the absolute path of the demo folder.

Example on Linux or macOS:

```bash
LOCAL_SOURCE_ROOT_1=/absolute/path/to/tof_local_knowledge/demo/source_1
```

Example on Windows PowerShell syntax inside `.env` should still be a normal path value, for example:

```text
LOCAL_SOURCE_ROOT_1=C:\Users\demo\tof_local_knowledge\demo\source_1
```

Use your real local path, but avoid showing personal path details in public screenshots.

## Step 3 — start the stack

Use the beginner path for your operating system.

Linux:

```bash
bash scripts/start_here.sh
```

Windows PowerShell:

```powershell
pwsh ./scripts/start_here.ps1
```

macOS:

```bash
./scripts/start_here.command
```

Alternative Linux/macOS browser-first path:

```bash
python3 run.py ui
```

## Step 4 — scan or index the demo source

Use the local browser UI or the API docs to scan the mounted demo source.

The intended demo source should resolve inside the container as:

```text
/sources/source_1
```

Use a safe source identifier such as:

```text
demo_source_1
```

## Step 5 — extract citable segments

After scanning, extract the demo files so the system creates citable segments.
A good demo should show at least one document with extracted segment output and citation labels.

## Step 6 — run local search

Use queries from `demo/questions.md`, for example:

```text
vacation policy
safe screenshots
citation labels
```

Expected result shape:

- source or document reference
- relative path
- segment or citation label
- preview text
- score or ranking information

## Step 7 — ask a grounded question

Use a grounded question from `demo/questions.md`, for example:

```text
What does the demo say about vacation policy?
```

Expected result shape:

- answer text
- citations or citation labels
- used documents
- confidence or uncertainty information

## Step 8 — test the no-evidence path

Ask:

```text
What is the private customer contract number?
```

Expected behavior: the system should return a clean no-evidence response instead of inventing a private contract number.

## Step 9 — only now capture screenshots

Capture screenshots only after the real demo flow works.

Recommended screenshot list:

1. browser UI start screen
2. service check success
3. demo source state
4. scan or indexing result
5. extracted segments or citation labels
6. search result with evidence
7. grounded answer with citations
8. no-evidence response

## Final release rule

If a first-time user still has to guess how to run the first safe demo search, the repo is not ready for product screenshots or a paid guide.
