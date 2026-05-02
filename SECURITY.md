# Security policy

`tof_local_knowledge` is a local-first knowledge stack for scanning, extracting, searching, and answering from local document sources.

Because the project deals with local files and document metadata, public reports and screenshots must avoid private data.

## Please do not post private data

When opening issues, discussions, pull requests, or public screenshots, do not include:

- private documents
- customer data
- real contracts, invoices, logs, emails, or support material
- private local paths
- `.env` values
- passwords, tokens, API keys, or database credentials
- private Docker hostnames or service names
- real source folder names that reveal internal systems
- screenshots of non-demo local sources

Use the synthetic demo files in `demo/source_1/` when possible.

## Safe reproduction pattern

For public bug reports, prefer:

1. a fresh clone
2. the neutral demo source from `demo/source_1/`
3. `python3 run.py setup`
4. `python3 run.py up`
5. `python3 run.py check`
6. a minimal command, screenshot, or error message with private data removed

## Reporting security issues

If you believe you found a security issue, avoid posting sensitive details publicly.

Use GitHub security reporting when available, or open a minimal public issue that asks for a private security channel without disclosing documents, paths, secrets, hostnames, or internal infrastructure details.

## Project boundary

This project is designed to:

- run locally
- scan explicitly mounted source folders
- store local metadata and citable segments
- search indexed local content
- answer from retrieved evidence
- provide a local browser UI

This project is not designed to:

- upload private documents to a cloud service by default
- silently sync local folders
- act as a public document hosting service
- bypass file permissions
- replace legal, compliance, or security review for private datasets

## Screenshot rule

Public screenshots should use only neutral demo data.

Before publishing a screenshot, confirm that it does not show private paths, real source names, customer names, secrets, `.env` values, logs, or private document content.
