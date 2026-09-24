---
area: data
priority: low
created: 2026-08-07
---
# 001 — Support multiple workbooks / months

## Problem

Everything assumes one workbook — `SUBASI FATURA-DEKONT AGUSTOS.xlsx`, August.
Real use spans months, and hosted use spans months *and* users. A user with
September and August files currently has to upload one, stamp, reset, upload the
other.

## Done when

- [ ] More than one workbook can be loaded in a session at once
- [ ] A key present in two workbooks resolves predictably (defined rule, not luck)
- [ ] The UI shows which workbooks are loaded and how many entries each contributed
- [ ] CLI accepts multiple workbook paths

> **2026-09-23:** the CLI and `load_tescil_map()` below are gone. The loader
> is `stamper.load_workbook()`, which maps key → list of POs, and the "CLI
> accepts multiple workbook paths" line no longer applies.

## Design questions

- **Merge or keep separate?** Merging into one flat key→Tescil map is simplest
  and matches how lookup works today. It breaks if the same `Fatura No` appears
  in two months with different Tescil numbers — need to know whether that happens.
- **Collision rule.** Error out, prefer newest, or report both? Depends on the
  answer above.
- Does a month need to be a first-class concept, or is it just "more rows"?
  Leaning "just more rows" — nothing in the pipeline cares about dates.

## Notes

`load_tescil_map` already takes a path or file-like object, so calling it N times
and merging is a small change — the hard part is the collision rule, not the
plumbing. See [[architecture/data-layout]]. Interacts with
[[005-shared-session-state]]: more per-session data to hold.

## Mostly evaporated — 2026-09-16

[[decisions/0008-single-user-session-scoped]] means the workbook is uploaded by
the person stamping, every session. Someone who needs September uploads
September. The hosted-use-spans-months-and-users framing in the Problem section
above no longer applies — there are no users to span.

What survives is narrow: **one session that needs two months at once** — a batch
of PDFs straddling a month boundary. Unknown whether that happens; worth asking
before building. If it doesn't, this task should be deleted rather than kept
warm.

The collision rule is still the hard part, and still blocked on open question 4
(can the same `Fatura No` appear in two months?). Nothing about 0008 answers it.
