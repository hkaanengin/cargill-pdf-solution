---
area: data
priority: low
created: 2026-09-22
---
# 030 — Verify the uploaded workbook, in two phases *(discussion)*

Spec reference: **Q15**. Serves R29 (what the user sees at upload) and touches
R7, R18, R20.

**Parked by the user on 2026-09-22 — "I don't want to do this at the moment,
let's discuss this in a later time."** Nothing here is to be built until that
discussion happens. It is recorded so the shape is not re-derived from scratch,
the same way [[021-run-history]] is parked.

## The direction, as given

Verification happens in **two phases**, and they are different in kind:

| | Phase 1 | Phase 2 |
|---|---|---|
| Nature | **Blocking** | **Non-blocking** |
| Purpose | Critical defects that actually stop the process | A status report on the workbook |
| When | Before a run starts | Shown to the user, run continues |
| Example given | Sheets 2 and 3 do not exist | Duplicated `Fatura No` in sheet 2 or 3 |

## Where things stand today

[[024-workbook-access]] checks three structural things — a header row exists,
and `Fatura No` and `PO` are present — and nothing else. Measured 2026-09-22:

| Upload | Today |
|---|---|
| Fewer than three sheets | uncaught `IndexError` |
| Not an xlsx, or corrupt | uncaught `BadZipFile` |
| Sheets in the wrong order | loads, backwards |
| Empty sheets, no data rows | loads, empty index |
| Last month's workbook | loads |

The first two are squarely phase 1 as described. In the web app they are
currently a 500 rather than a message, which is the one concrete hole.

## What the discussion has to settle

- **Which defects are phase 1.** "Sheets 2 and 3 not existing" is the stated
  example; not an xlsx, and corrupt, behave the same way and probably belong
  with it. Missing `Fatura No` / `PO` columns already raise — are they phase 1
  too, or is raising enough?
- **What phase 2 reports, and where.** R29 describes six steps and the summary
  screen (R21) comes at the *end*. A workbook report belongs at upload time,
  which is a new place for information to appear. Does R29 gain a step?
- **Phase 2 and R18 are not the same check.** R18 refuses a duplicated key for
  an uploaded file that hits one. A workbook-level report would surface all 26
  duplicated DEKONT keys at upload, including those no uploaded PDF touches —
  6 conflicting, 7 one-blank, 13 both-blank. Which is meant?
- **Whether a swap check is wanted, and in which phase.** FATURA keys are 100%
  non-digit and DEKONT keys 100% digit, so a reordered workbook is detectable
  from the data alone without reading a sheet title — R7 stays intact. It could
  block (phase 1) or merely report (phase 2).
- **How this sits with Q12.** Malformed inputs were dropped from scope entirely
  on 2026-09-20. Phase 1 partly reopens that, deliberately. The spec should say
  so rather than leave the two in silent contradiction.

## Not urgent, and why

Correctness is not at risk. A workbook of the wrong shape makes every lookup
fail, so R20 stops the run and produces no download — the failure is loud, not
silent. What is missing is an accurate *reason*, and a web app that answers a
bad upload with a message instead of a stack trace.

## Done when

Not yet a build task. It becomes one when the discussion settles phases 1 and
2, at which point Q15 closes into requirements and this file gets a real
*Done when*.
