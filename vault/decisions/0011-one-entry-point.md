---
status: accepted
date: 2026-09-20
---
# 0011 — One entry point: the web app, with the logic in an importable module

> **Carried out 2026-09-23.** `stamp_tescil.py` is deleted and `sgm_folders/`
> is renamed `samples/` — [[019-tescil-to-po-rename]].

## Decision

The **web app (`app.py`) is the only entry point.** `stamp_tescil.py` is
retired — R27 is withdrawn.

The stamping logic does **not** live inside the Flask request handlers. It goes
in a plain module that `app.py` imports and that tests import directly, with no
browser and no HTTP involved.

## Why

**Why the script goes.** The user was asked whether they run the project from a
terminal and answered that `stamp_tescil.py` existed only as a way to try things
locally — and that since `app.py` also runs locally, the script can go. Two
entry points obeying the same twenty-odd requirements is a standing cost: every
routing rule, every exception, every naming rule has to be implemented twice and
kept in agreement forever, and the spec had a requirement (R27) whose only job
was to insist they match.

**Why the logic still has to be importable.** The script was serving a real
purpose underneath the redundancy — exercising the logic without clicking
through a browser. Deleting it without replacing that would make the project
testable only by hand, which is the wrong trade for something whose worst
failure is a plausible-looking wrong document.

Putting the logic in a module keeps what was valuable and drops what was not.
Tests call `route_filename()`, `lookup_po()`, `stamp()` and so on directly;
`app.py` becomes thin — upload, call, render. An automated test suite is then
possible without a second user-facing surface to maintain.

*This split is an engineering choice, not a product requirement: the user asked
for one entry point and said nothing about internal structure.*

## Consequences

- `stamp_tescil.py` is deleted as part of [[019-tescil-to-po-rename]], alongside
  the renaming work rather than in a separate pass.
- R27 is withdrawn in [[spec]]; its ID is retired rather than reused.
- Every acceptance criterion in [[spec]] is now checked through the web app or
  through the module's tests. Nothing is verified by running a script.
- `sgm_folders/` stops being an input directory the app reads and becomes what
  it already is in practice: the local sample set that tests point at. Its name
  is a misnomer either way — see [[019-tescil-to-po-rename]].

## Revisit if

The user ever wants to stamp a folder of files without a browser — a scheduled
job, or a batch far too large to upload. The module split means that would be a
thin new front end over existing logic rather than a second implementation.
