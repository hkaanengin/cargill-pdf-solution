---
status: accepted
date: 2026-08-06
---
# 0003 — Never modify source PDFs in place

> **Still accepted — 2026-09-23.** Now R13 in [[spec]]. The command-line
> script and its `output/` directory are gone; the web app, the only entry
> point, stamps in memory and writes no PDF to disk. `sgm_folders/` is now
> `samples/`, the test inputs — [[019-tescil-to-po-rename]].

## Decision

Source PDFs in `sgm_folders/` are opened read-only. Stamped copies are written to
a separate `output/` directory. The web app goes further and writes nothing at
all — it stamps in memory and streams the result to the browser.

## Why

- **The sources are original customs documents.** There is no undo, and this is
  not a git repository, so an in-place mistake is unrecoverable.
- **Stamping is not idempotent.** Running twice in place would print the number
  on top of itself. With a separate output directory, re-running is always safe
  and is in fact the normal way to iterate on placement.
- Keeping originals clean made it cheap to re-test placement repeatedly while
  choosing coordinates.

## Consequences

- Output files are duplicates; disk usage is roughly double. Irrelevant at this
  scale.
- `output/` is disposable — safe to delete and regenerate at any time. It's in
  `.dockerignore` for that reason.

## Revisit if

Never, realistically. If bulk in-place stamping is ever genuinely wanted, it
should be an explicit opt-in flag with a loud confirmation, not the default.
