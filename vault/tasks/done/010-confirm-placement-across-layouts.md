---
area: data
priority: high
created: 2026-08-07
updated: 2026-09-22
completed: 2026-09-22
---
# 010 — Confirm stamp placement on real, varied PDFs

## Problem

Placement at (x=240, y=170) was chosen off `sample_grid_preview.png` and verified
on **4 sample PDFs** — which may all share one layout. If any real SGM PDF puts
content there, the stamp lands on top of existing text and may be unreadable.

*(That coordinate is withdrawn as of 2026-09-20 — see Unblocked below. The
concern it describes is unchanged and now applies to whatever R12 replaces it
with.)*

This is cheap to check and expensive to get wrong: a misplaced stamp on a customs
document is a real-world problem, not a cosmetic one.

## Done when

- [x] A larger, more varied set of real SGM PDFs has been stamped and eyeballed
      — all ten clean samples, both layout families
- [x] Confirmed the stamp never overlaps existing content — measured, not just
      eyeballed
- [x] Any layout variants found are documented in [[architecture/data-layout]]
- [x] If placement must change, [[decisions/0002-stamp-placement]] is updated
      with the new rationale — it was **replaced**:
      [[decisions/0014-stamp-placement-per-family]]

## How

Run the CLI over everything available, then open the `output/` files. Nothing
clever needed — this is a look-at-it task. Regenerate the grid preview against a
differently-shaped PDF if one turns up.

## Notes

Distinct from [[008-pdf-layout-robustness]]: that one is about *code* handling
odd page sizes, this is about validating the *current* coordinate against real
documents. This one should happen first — it tells us whether 008 is urgent.

## Unblocked — 2026-09-20

New sample PDFs arrived: `sgm_folders/` now holds **ten** clean inputs, six of
them new, across two genuinely different layouts (born-digital e-Fatura and
two-page DEKONT scans). That is the material this task was waiting for.

The premise has also changed. This task was written to validate *one* global
coordinate. There is no longer one: R12 makes position per-document-type and the
old `(240, 170)` is withdrawn. So this is now the validation half of
[[017-dekont-stamp-placement]] — 017 chooses the two positions, this task
confirms they cover nothing on every available layout. **Do them together.**

Note the sharpened scope: `SUB` files turn out to share the e-Fatura layout with
`SGM`, so the two families are *FATURA-routed* and *DEKONT-routed*, not three
separate ones. Still worth eyeballing a `SUB` explicitly — 164 of the 208 FATURA
rows are `SUB`, so it is the common case, not the exotic one.

Reference material: `samples_stamped_reference/` holds the same six files as
delivered, showing where a human placed the stamp —
[[decisions/0010-destamped-sample-pdfs]].


---

## Closed — 2026-09-22

Done in one pass with [[017-dekont-stamp-placement]], the way [[_index]] said it
should be: 017 chose the two coordinates, this task is the evidence that they
cover nothing. Full method and figures live in **017**; only what this task
specifically asked is recorded here.

**The answer is no, the stamp never overlaps** — on any of the ten clean
samples, in either family. That was established two ways rather than one:

- **Measured.** Each family's free space was computed as the *union* of the ink
  on every sample in it, so a coordinate is only clear if it is clear on all of
  them. Clearance around the widest possible stamp is ≥32pt on FATURA and ≥80pt
  on DEKONT in the tightest direction.
- **Looked at.** All eight stampable samples were rendered and viewed. The two
  remaining files have a blank `PO` and were refused, not stamped (R18).

### The layout question this task was really asking

It was opened because four samples "may all share one layout", and they did.
What the ten now show:

- **There are exactly two layouts, and they line up with the two routing
  families** — so `Family` is both the sheet a file is looked up in and the
  layout it is stamped on. Nothing in the data argues for a third.
- **Within a family the layout does not vary at all.** The FATURA clearance
  figures are *identical* across all seven files, August batch and September
  batch, `SGM` and `SUB` alike. These are fixed templates, not hand-made
  documents, which is why one absolute coordinate per family is defensible.
- `SUB` shares the e-Fatura layout with `SGM`, as the 2026-09-20 note predicted
  — confirmed by eye on `SUB2026000019890`, the one whose reference stamp used
  a different font and so might have hinted at a different origin. It does not.

### What stays open

Nothing here. The one layout risk found is a DEKONT whose line-item table grows
down into the stamp band — never observed, and logged on
[[008-pdf-layout-robustness]] rather than fixed by guesswork. `sample_grid_preview.png`
is stale and is left that way: the ink-map method in 017 replaces it and covers
both families, which a single-sample grid image cannot.