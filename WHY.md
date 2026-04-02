# Why this repository exists

> English is the primary text in this repository. A German clone is available in `WHY_DE.md`.

## Problem

A lot of "knowledge" systems answer too freely.
They may look useful, but they often blur the line between source material, extracted content, indexed records, and generated answers.

For local and internal document spaces, that is the wrong trade-off.

## Chosen approach

This repository treats local knowledge as a grounded system, not as a free-form assistant shell.

The main decisions are:

1. local-first / on-prem operation
2. explicit separation between raw input, extraction, index, and answer layers
3. answers should be grounded in stored evidence instead of unconstrained generation

## Why this approach

I wanted a knowledge system where local files stay local and where answers can be traced back to evidence.
That is why the repository does not collapse scanning, extraction, indexing, and answering into one vague layer.

The separation is deliberate:
raw files are not the same thing as extracted blocks,
extracted blocks are not the same thing as searchable segments,
and searchable segments are not the same thing as an answer.

That structure exists to reduce ambiguity, make the system more inspectable, and keep the answer path honest.

## Why not the obvious alternative

I did not want:

- a cloud-first knowledge product
- a system that behaves like a generic chatbot with document flavor
- hidden remote sync assumptions
- answers that sound plausible without strong grounding

Those approaches may feel simpler, but they weaken trust in the system.

## Trade-off

This design is more explicit and more structured than a lighter assistant-style tool.
That means more pipeline thinking, more boundaries, and less "magic".

I accept that trade-off because local knowledge work needs traceability more than it needs theatrical fluency.

## What I would improve next

If I revised the public presentation, I would surface the design reasoning more directly:
why grounded QA matters,
why the layer split is non-negotiable,
and why this repo is a product-shaped local knowledge system rather than a public ToF runtime mirror.
