---
area: web
priority: low
created: 2026-08-07
---
# 003 — Auth and multi-user isolation

## Problem

There is no authentication. Anyone who can reach the port can upload a workbook
and stamp PDFs. That is fine on localhost and unacceptable hosted, because the
data involved is customer invoice and customs data.

Separately from login: right now "sessions" are just a cookie id with no identity
behind them. Multi-user means one user must never see another's workbook.

## Done when

- [ ] Unauthenticated requests to `/`, `/stamp`, `/excel`, `/reset` are rejected
- [ ] A user's uploaded workbook is reachable only by that user
- [ ] Sessions end — logout works, and idle sessions expire
- [ ] Secrets (session key, any provider creds) come from env, not source

## Open first

**Who are the users?** This is unresolved and it changes everything:

- *Internal to the company* → SSO / Google Workspace, small user count, trust is
  relatively high, probably no signup flow at all.
- *External customers* → real signup, password reset, per-tenant isolation,
  and a genuine data-protection obligation.

Don't start building until this is answered — see [[brainstorm/open-questions]].

## Notes

Depends on [[005-shared-session-state]]; identity has to live wherever sessions
live. Flask's `SECRET_KEY` must stop being anything hardcoded before this ships.

## Answered — 2026-09-08

**Who are the users:** a few known people, provisioned by hand. Not external
customers. Recorded in [[decisions/0007-user-model-small-known-group]].

This collapses the task to roughly a day:

- No signup, no email verification, no password reset, no billing.
- No per-tenant isolation. One shared deployment; sessions must not collide
  ([[005-shared-session-state]]), but that's correctness, not tenancy.
- Simplest thing that holds: a small fixed user list, or SSO if these users
  already share a Google/Microsoft account. Ask before picking.

Still required, and not softened by the small audience: HTTPS, login in front of
everything, and `SECRET_KEY` out of source and into env. The data is invoice and
customs numbers.

**One thing to settle first:** if the workbook ends up maintainer-uploaded rather
than per-user (open question 6 in [[open-questions]]), then this task also needs
a notion of *who may replace the workbook* — a second role, not just a login.

## Reshaped again — 2026-09-16

[[decisions/0008-single-user-session-scoped]]: one user, one session, nothing
persists. The "multi-user isolation" half of this task is now dead weight —
there is no second user to isolate from, and no stored workbook to control who
may replace. The question above about *who may replace the workbook* is answered:
whoever is in the session, because they uploaded it.

**What is left is small and still required before hosting:**

- [ ] One shared gate in front of everything (basic auth or a single shared
      password is enough for this audience) — the port must not be open to
      whoever finds it
- [x] `SECRET_KEY` from env, not the `"sgm-tescil-stamp"` literal in `app.py` — done 2026-09-23
- [ ] HTTPS, which most container platforms give for free
- [ ] An idle session timeout, so a forgotten tab doesn't hold a workbook in RAM

Dropped from the original list: per-user isolation, logout as a real feature,
accounts, roles. No longer depends on [[005-shared-session-state]] — that closed.

Priority is medium, not high: it gates [[004-cloud-deployment]] going public and
nothing else. It is also most of a day less work than it was this morning.

## Postponed — 2026-09-23

The user, on being asked how the gate should look: **"I dont need a password
gate, no one needs to login at the moment."** Priority dropped to low and
[[spec]] R26 amended: the gate no longer blocks hosting.

- **Done anyway, because it is part of R26 and not the gate:** `SECRET_KEY`
  comes from the environment. When it is unset the app makes a random one at
  start-up, which is safe here: a restart already drops every session (R23)
  and there is one worker (R25).
- **Postponed with the gate:** the idle-session timeout. The user answered the
  timeout question with R35 instead — they start and stop the app by hand for
  2–3 hours a day, and a stop ends every session.
- **Still required, and moved to [[004-cloud-deployment]]:** HTTPS.

**The risk this accepts:** while the app is up, anyone with the URL can upload
a workbook and stamp. Its exposure is bounded by R35. A free, no-code middle
ground if that changes: restrict the VM's ingress rule to the user's own IP in
the Oracle security list — [[decisions/0017-oracle-cloud-always-free-vm]].
