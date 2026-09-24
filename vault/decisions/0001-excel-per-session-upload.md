---
status: accepted
date: 2026-08-06
---
# 0001 — Excel is uploaded per session, never baked into the image

> **Still accepted — 2026-09-23.** The decision holds (R24 in [[spec]]).
> `load_tescil_map()` named below was deleted with `stamp_tescil.py`; the
> loader is now `stamper.load_workbook()`, which reads `PO` and still takes a
> path or a file-like object — [[019-tescil-to-po-rename]].

## Decision

The web app takes the Excel workbook as a **per-session upload**. It is not baked
into the Docker image, not read from disk, and never written out. The parsed
mapping is held in memory for the session and discarded.

This is why `app.py` is a two-step flow: upload Excel, then upload PDF.

## Why

- **The workbook is customer financial data.** Baking it into an image means it
  travels with every copy of that image, into every registry it's pushed to, and
  stays in layer history even if a later layer deletes it.
- **It goes stale.** One workbook per month; a baked-in image is wrong within
  weeks and needs a rebuild to fix.
- **It blocks multi-user.** Different users have different workbooks. A baked-in
  file makes the hosted version single-tenant by construction.

## Consequences

- Users re-upload each session. Accepted cost — it's one extra step.
- Requires session state, which is currently a module-level dict and is the
  project's main scaling blocker. See [[005-shared-session-state]].
- `load_tescil_map()` had to accept a file-like object as well as a path, so the
  CLI and the web app could share one parser.

## Revisit if

Users complain about re-uploading every session. The fix would be stored
workbooks per user — which means handling customer financial data at rest, a
much larger commitment than this decision avoided. Don't do it casually.
