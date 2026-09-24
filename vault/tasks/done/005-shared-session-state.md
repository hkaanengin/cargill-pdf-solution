---
area: infra
priority: high
created: 2026-08-07
completed: 2026-09-16
---
# 005 — Replace in-process session state

**Closed 2026-09-16 without building anything — the user model removed the problem. See the bottom of this file.**

## Problem

`app.py` holds parsed Excel mappings in a module-level `SOURCES` dict, keyed by a
session-cookie id. That means:

- State is per-process. With >1 gunicorn worker, a user who uploads their Excel
  on worker A and their PDF on worker B is told "no source loaded". Intermittent
  and confusing, but fully deterministic.
- Any restart or redeploy silently drops every in-flight session.

Correct for local single-user, wrong the moment it's hosted.
See [[architecture/deployment]].

## Done when

- [ ] Session mappings survive a worker restart
- [ ] Two workers serve the same session correctly (test: upload Excel, then hit
      the PDF step repeatedly until both workers have handled a request)
- [ ] Sessions expire on a TTL rather than growing forever
- [ ] Local dev still works without extra infrastructure running

## Options

- **Redis** — obvious fit, TTL is built in, most platforms offer it managed.
  Adds a service dependency to local dev unless made optional.
- **Flask server-side session store** — less new infrastructure, but still needs
  a shared backend to be worth anything.
- **Re-upload the Excel with each PDF** — no state at all. Ugly UX, but worth
  considering; it would delete this entire problem class.
- **Pin to one worker** — stopgap only. Hides the bug, caps throughput at one
  request, still dies on restart.

## Notes

The no-state option deserves a real look before building Redis in — the app is
close to stateless already. Relates to [[001-multi-workbook-support]], which
changes what's held per session anyway.

## Reshaped by the user model — 2026-09-08

[[decisions/0007-user-model-small-known-group]] says the users upload PDFs and
get stamped PDFs back. It does **not** say they upload the workbook — that's
open question 6.

If the answer is "one maintainer loads the month's workbook, everyone else only
touches PDFs", this task changes shape entirely. The mapping stops being
per-session state and becomes **one shared server-side object**, loaded at
startup or on upload and read by every request. There would be no per-session
Excel to keep in sync across workers, and the "Options" list above is mostly
moot — no Redis, no session store, just a stored workbook plus a reload path.

That makes question 6 worth answering **before** any work starts here. The
stateless option ("re-upload the Excel with each PDF") and the shared-workbook
option both delete this problem; the per-session option is the only one that
needs the infrastructure.

## Closed — 2026-09-16

Open question 6 was answered in a way neither option anticipated:
[[decisions/0008-single-user-session-scoped]] — one user, one session, nothing
outlives it.

Under that model the module-level `SOURCES` dict is not a bug, it is the right
amount of machinery. The two failure modes this task was written about:

- *"State is per-process, >1 worker breaks it"* — solved by running **one**
  gunicorn worker. That is a flag in the Dockerfile's CMD, and it belongs to
  [[004-cloud-deployment]] now. It is the single thing that must be true for this
  closure to hold.
- *"A restart drops in-flight sessions"* — accepted. Nothing is supposed to
  outlive the session; the user re-uploads the workbook, which is one click.

The "Options" list above is moot. No Redis, no session store, no re-upload-per-PDF
compromise. The fourth option, "pin to one worker", was written off here as a
stopgap that hides the bug — under the new user model it is not a stopgap, it is
the design.

**What would reopen this:** two people stamping at the same time. Today they
queue behind a single worker and both workbooks sit in RAM with no TTL. That is a
capacity and memory question, not a correctness one, until it isn't. If real use
turns out to be concurrent, reopen this file rather than writing a new task — the
analysis above is still the analysis.

`DOWNLOADS` (added by [[002-batch-upload-zip]]) is a second dict with the same
lifetime and the same reasoning. It holds a whole batch of stamped PDFs, so it is
the heavier of the two — worth remembering if this ever is reopened.
