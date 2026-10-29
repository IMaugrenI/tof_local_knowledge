# Productization roadmap

## Goal

Turn `tof_local_knowledge` from a strong local stack repository into a local end-user product with a clear browser-led workflow.

## Product target

A user should be able to:

1. download the project
2. run the starter path
3. open a browser control surface
4. add or select source spaces
5. start indexing
6. see index state
7. ask a question
8. receive an answer with visible source references

## Phase 1 — browser control front door

Status: started.

Target:

- local browser control UI
- setup button
- start-stack button
- check button
- status button
- doctor button
- stop button
- clear next-step guidance

## Phase 2 — source and indexing UI

Target:

- source-root visibility in the browser
- add-source / choose-source workflow
- indexing controls
- visible indexing state
- visible source inventory
- clearer readiness messages

## Phase 3 — search and answer UI

Target:

- search field
- question field
- answer area
- visible source references
- simple explanation of where the answer came from
- no hidden jargon in the main user path

## Phase 4 — cross-platform polish

Target:

- same control path on Windows, Linux, and macOS
- friendlier messages around Docker and source paths
- clearer browser success state
- release-ready starter paths

## Phase 5 — release mode

Target:

- GitHub releases
- simple download package
- starter files per operating system
- short offline user guide inside the release package

## Definition of done for product V1

- normal users can control setup and startup from the browser
- normal users can add sources and see source state
- normal users can ask questions and see sourced answers
- the default path stays local-first
- the same basic path works across the three main supported operating systems


## One-screen chat milestone — current build track

Single acceptance source of truth: [ONE_SCREEN_MILESTONE_DE.md](ONE_SCREEN_MILESTONE_DE.md).

The everyday browser entry (`/`) now combines user-approved document
selection, bounded import/index batches, progress and per-file feedback,
document-grounded question/answer history, read-only evidence inspection, and
short contextual follow-ups. Existing technical routes stay under
**Weitere Funktionen**. No extra application server or second Compose stack.

The remaining **acceptance gate** is not a feature request:
1. Confirm the same source-candidate starter on the chosen real target system.
2. Confirm 1-file and mixed 5+-file imports, including failures and pagination.
3. Confirm sourced question + follow-up + unrelated topic + source inspection.
4. Confirm missing-evidence questions produce no claimed answer or citations.
5. Confirm source constraints, local-only network scope, stop/restart behavior,
   and no silent reading of unapproved directories.
6. Record what was actually verified on Linux/Windows/macOS separately.
7. Only after DOM's GO may the existing manual packaging workflow produce the
   install/test candidate; public product release remains a separate decision.

### Scope boundaries

- Model-generated ungrounded assertions are not part of the default product.
- A visible browser conversation is not persistent Memory.
- The repository currently enforces **single-user local operation**;
  multiuser ACLs are NOT ready just because role tables exist.
- Optional model services are neither mandatory nor automatically downloaded.
- CI is a development signal, not target runtime evidence.

This addendum supersedes the obsolete 'Phase 1: started' status text above;
the original phase descriptions remain historical product planning.
