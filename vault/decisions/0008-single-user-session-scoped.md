---
created: 2026-09-16
---
# 0008 — One user, one session. Nothing outlives the session

Answers open question 6, which was gating [[005-shared-session-state]] and with
it the whole cloud track. It also narrows [[decisions/0007-user-model-small-known-group]].

The user's call, 2026-09-16, asked who uploads the workbook and answering neither
of the two options offered: *"Lets make this for one user only where only the
current session matter. In that session, we upload excel, then pdf file/s, then
we download files."*

## What this settles

- **The unit of use is a session, not a user.** One person, one browser, one
  sitting: upload the Excel, upload one or more PDFs, download the results.
- **Nothing is expected to persist.** No stored workbook, no history, no
  "which month is loaded". Closing the tab is allowed to lose everything.
- **The workbook is uploaded by whoever is stamping**, every session. This
  confirms [[decisions/0001-excel-per-session-upload]] rather than replacing it.
- **No concurrent users to reason about.** Two people at once is not a case the
  app has to be correct for today.
- **PDFs are plural.** Restated in the same sentence — see [[002-batch-upload-zip]].

## Why

The two options on the table both bought infrastructure the actual use doesn't
need. "Every user uploads it" meant Redis or an equivalent shared store before
anything could be hosted. "One maintainer loads it" meant a stored workbook, a
reload path, and a second role in auth.

Session-scoped single-user buys neither and deletes both. The in-process dict in
`app.py` — flagged in [[005-shared-session-state]] as wrong-the-moment-it's-hosted —
is *correct* under this model, provided the deployment runs a single worker. That
is a one-line gunicorn setting rather than a service dependency, and it turns the
next milestone from "stand up a session backend" into "deploy the container".

The cost is honest and worth naming: **a second simultaneous user is not
supported.** With one gunicorn worker they queue behind each other, and the
process holds both sessions' workbooks in RAM with no TTL. If real use ever turns
out to be two people stamping at the same time, [[005-shared-session-state]]
comes back — this decision is the reason it was closed, and reopening it is the
correct response, not a surprise.

## What it changes

| Task | Effect |
|---|---|
| [[005-shared-session-state]] | Closed. In-process state is the right answer under this model; single worker is the only requirement. |
| [[003-auth-and-multi-user]] | Reshaped: no accounts, no isolation. One shared gate in front of a hosted deployment, and `SECRET_KEY` out of source. |
| [[001-multi-workbook-support]] | Mostly evaporates: a user who needs September uploads September. Only worth doing if one session must span two months. |
| [[004-cloud-deployment]] | Unblocked and cheaper — single container, single worker, no session backend, no managed Redis. |
