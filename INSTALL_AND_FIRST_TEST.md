# Install and first test

This file is the shortest practical path for a fresh local download.

## 1. Get the repository

Clone it or download it from GitHub, then enter the repository folder.

```bash
git clone https://github.com/IMaugrenI/tof_local_knowledge.git
cd tof_local_knowledge
```

## 2. Use the easiest start path

### Linux

```bash
bash scripts/start_here.sh
```

### Windows PowerShell

```powershell
pwsh ./scripts/start_here.ps1
```

### macOS

```bash
./scripts/start_here.command
```

## 3. What should happen

The repository should:

1. prepare local setup
2. start the stack
3. check the main services

## 4. First real browser test

You can also open the local browser control path:

```bash
python run.py ui
```

Then do this:

1. start the stack if it is not already running
2. run one local search query
3. run one grounded question
4. open WebUI or the docs links only if needed

## 5. What counts as success

A good first test means:

- the stack comes up locally
- the browser UI opens
- search returns hits or a clean empty result
- grounded answer returns an answer or a clean no-result response
- the main local services answer without guessing or cloud dependency

## 6. If something fails

Run:

```bash
python run.py doctor
python run.py status
python run.py check
```

Then fix the first failing item before doing anything else.

## 7. Best first local test style

Start with a tiny local source set first.

Confirm that search and grounded answer work before moving to bigger or more important document spaces.
