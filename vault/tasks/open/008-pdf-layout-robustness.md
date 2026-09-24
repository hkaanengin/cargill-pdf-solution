---
area: cli
priority: medium
created: 2026-08-07
updated: 2026-09-22
---
# 008 — Handle non-A4 and multi-page PDFs

## Problem

Stamp coordinates are absolute and applied to page 0. Every sample is 1-page A4
(595 × 842 pt), so this has never been exercised. A differently-sized page puts
the stamp somewhere wrong — possibly off-page — **with no error**. Silent wrong
output is the worst failure mode this project has.

## Done when

- [ ] Page size is checked; non-A4 pages either scale the coordinate or refuse
- [ ] A defined rule for multi-page PDFs (first page? every page? refuse?)
- [ ] Anything refused is reported clearly, never silently skipped
- [ ] Tested with a deliberately non-A4 and a deliberately multi-page PDF

## Design notes

- Proportional scaling (fraction of page width/height rather than absolute
  points) would handle size variation automatically and is arguably the right
  representation regardless. It changes what
  [[decisions/0002-stamp-placement]] records — fractions, not points.
- Multi-page: **answered, and not by this task.** R28 says page 1 always, and
  [[017-dekont-stamp-placement]] found the reason it is not a simplification —
  page 2 of a DEKONT is a *different document* (a `TAHSİLAT MAKBUZU` receipt).
  Stamping it would put the PO on an unrelated page.
- Refusing loudly beats guessing on a customs document.

## Notes

Urgency depended on [[010-confirm-placement-across-layouts]] — **answered
2026-09-22, and the answer is "not urgent".** All ten clean samples are A4 and
unrotated, there are exactly two layouts, and *within* a family the layout does
not vary at all: measured clearance around the stamp is identical across all
seven FATURA files, August and September batches alike. These are fixed
templates. Absolute points are a deliberate, recorded choice
([[decisions/0014-stamp-placement-per-family]]), not an oversight to fix here.

## Inherited from 017 — 2026-09-22

One concrete layout risk was found while choosing the coordinates, and
deliberately **not** designed around:

**A DEKONT with a long line-item table grows into the stamp.** Its table grows
downward from `y≈400` toward a footer pinned at `y≈727`; the DEKONT stamp sits
at `y=475` with 80pt of clear space above it, so roughly five or more table rows
would reach it. All three DEKONT samples have a one-row table, so this has never
been seen.

It was left alone on purpose. Moving the stamp lower would trade a *measured*
position — one matching where the manual process already stamps — for an
unmeasured one, against a case that has never occurred. If it does occur the
options are a lower fixed `y`, or placing the DEKONT stamp relative to the table
rather than absolutely, which is a bigger change than this task currently
describes.

**Worth knowing:** this failure is not silent. R17 verification passes (the text
renders either way), but the stamp would be *drawn over the table* — visible to
anyone looking at the document. The silent-wrong-output concern above applies to
page size, not to this.
