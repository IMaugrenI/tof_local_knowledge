# Browser control UI

`tof_local_knowledge` now includes a simple local browser control UI.

## Start it

```bash
python run.py ui
```

By default this starts a local server on `127.0.0.1:8785` and opens the browser.

## What it is for

This UI is a simple front door for normal users who do not want to begin with raw terminal commands.

It currently exposes large buttons for:

- prepare local setup
- start stack
- check services
- show runtime status
- run doctor
- stop stack

## What it is not

This is not yet the full search or source-management interface.

It is a safe local control surface for the main runtime steps.

## Suggested user path

1. prepare local setup
2. start stack
3. check services
4. show runtime status
5. continue into the actual knowledge workflow
