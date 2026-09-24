---
area: web
created: 2026-08-06
completed: 2026-08-06
---
# 013 — Build the Flask web app

## What it was

A browser front end so stamping doesn't require the command line: upload an SGM
PDF, get the stamped PDF back.

## Outcome

- `app.py` — stamps **entirely in memory**. Nothing is written to disk at any
  point, which keeps customer documents out of the server's filesystem.
- Reuses `load_tescil_map()` from the CLI rather than duplicating the parser.
- Tested: successful stamp, unknown key, non-PDF upload, and asserting the
  stamped text is actually present in the returned file.

## Known limit shipped with it

State lives in a module-level `SOURCES` dict keyed by session cookie. Correct for
one user on localhost, and the project's main blocker for hosting —
[[005-shared-session-state]]. This was a deliberate "good enough for now", not an
oversight.
