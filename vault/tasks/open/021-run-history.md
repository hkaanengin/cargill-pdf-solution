---
area: web
priority: low
created: 2026-09-20
---
# 021 — Should a run leave a trace the user can come back to?

Spec reference: **R16** (withdrawn), **R23**, and the *No persistence* non-goal
in [[spec]].

**Status: a discussion, not a build.** Opened at the user's request 2026-09-20 so
the idea is not lost. Explicitly **not** a priority — the instruction was "our
priority is now to get the web app running, with or without storing trace."
Nothing here blocks anything.

## The problem it would solve

Two decisions combine into a gap neither of them intended:

- **R16 was withdrawn** — there is no manifest, no report file. The zip holds
  stamped PDFs only.
- **R23 says nothing persists** between sessions, by design.

So the summary screen (R21) is the *only* account of what a run did, and it dies
with the browser tab. Open a zip a week later, wonder why a file is missing, and
the only way to find out is to re-run the whole batch — assuming the same
workbook is still to hand, which R24 does not guarantee either.

Neither decision is wrong. The gap is a consequence of both being right.

## Why this is not a small feature

It runs straight into the two load-bearing decisions of the project:

- **[[decisions/0008-single-user-session-scoped]]** — no persistence, no
  database, no session backend. This is what keeps the app a single process
  with state in memory.
- **R25** — exactly one gunicorn worker, *because* state lives in process
  memory.

Any store that outlives a session reopens both. That does not make it a bad
idea; it makes it a change to the project's shape rather than an addition to it,
and it should be decided as one.

## Questions to settle before anything is built

- **What is actually wanted** — a list of past runs in the app? A downloadable
  report at the time of the run? An emailed copy? These have very different
  costs; the emailed or downloaded version does not touch R23 at all.
- **How long does it need to live?** A session, a day, forever.
- **What goes in it** — the summary as shown, or the stamped files too? Storing
  customs documents is a different proposition from storing a list of filenames.
- **Does it survive a restart?** In-memory history dies with the process and may
  still be worth having; on-disk history reopens 0008.

## Worth noting

The cheapest version that solves the stated problem may not be persistence at
all: **let the user download the summary** from the screen where it is already
shown. That keeps R23 intact, needs no store, no schema and no migration, and
puts the record in the same folder as the zip it describes — which is where
someone looking for it a week later would actually look.

That is a suggestion for the discussion, not a decision. The user has not asked
for it and it is not assumed.

## Done when

- [ ] The user says what they want to be able to look back at, and for how long
- [ ] The answer is weighed against [[decisions/0008-single-user-session-scoped]]
      and R25 — explicitly, whichever way it goes
- [ ] It becomes a requirement in [[spec]], or an explicit non-goal
