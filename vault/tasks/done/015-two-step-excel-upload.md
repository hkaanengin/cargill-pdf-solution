---
area: web
created: 2026-08-06
completed: 2026-08-06
---
# 015 — Rework the web app to a two-step flow

## What it was

The first version baked the Excel workbook into the Docker image. This replaced
that with a per-session upload: **step 1** upload the Excel, **step 2** upload
the SGM PDF.

## Why it mattered

Baking in the workbook meant shipping customer financial data inside every copy
of the image — and it went stale monthly, and it made the hosted version
single-tenant by construction. Full reasoning in
[[0001-excel-per-session-upload]].

## Outcome

- Routes: `GET /` → `POST /excel` → `GET /stamp` → `POST /stamp`, plus `GET /reset`.
- Templates split into `base.html` / `excel.html` / `stamp.html` with a shared
  step indicator.
- Parsed mapping held server-side per session; the workbook itself is never
  stored.
- Full flow tested including reset, unknown key, and stamp-present assertions.

## Caveat carried forward

This is the change that *created* the session-state dependency —
[[005-shared-session-state]]. Worth it, but it's the direct cause.
