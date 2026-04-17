# Release checklist

Use this before calling a public release good enough for normal users.

## Basic repo checks

- README still matches the real start path
- `INSTALL_AND_FIRST_TEST.md` still matches the real start path
- `docs/00_beginner_quickstart.md` still matches the browser UI
- no private or local test data is committed

## Smoke path

- fresh local clone works
- `scripts/start_here.*` works on the intended platform
- stack starts
- browser UI opens
- local search works
- grounded answer works
- docs links open

## User-facing truth

- search results are readable enough
- grounded answers are readable enough
- raw JSON is not the only visible path
- the next-step hint still matches reality

## Final rule

If a normal first-time user still needs to guess how to start or how to run the first search, the release is not ready enough.
