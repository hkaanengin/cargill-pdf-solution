---
area: cli
priority: high
created: 2026-09-20
updated: 2026-09-22
completed: 2026-09-22
---
# 017 — Where does the stamp belong, per document type?

Spec reference: **R12**, **R28**, open question **Q5** in [[spec]].

## Problem

`(240, 170)` was chosen by rendering *one SGM sample* under a 50pt coordinate
grid and picking empty space near the top ([[decisions/0002-stamp-placement]]).
The spec then stamped three document types through that single constant.

That is now known to be wrong, and the coordinate is withdrawn.

## What the user settled — 2026-09-20

- **Position is per document type.** Digit-named (DEKONT) documents have a
  different layout from `SGM`/`SUB` and need a different position. Now R12.
- **Page 1 is stamped, for every type.** DEKONT scans are two pages; only the
  first is stamped. Now R28.

What is still open is the *exact* coordinate for each of the two families.

## Findings — 2026-09-20

The six new samples arrived **already stamped** by whatever process does this
today (almost certainly a person in Acrobat). Originals are preserved in
`samples_stamped_reference/`; the copies in `sgm_folders/` have been de-stamped
— [[decisions/0010-destamped-sample-pdfs]].

That makes them the first real evidence of where a human chooses to put this
stamp. Measured origins (PyMuPDF baseline, top-left origin, A4 595 × 842):

| Sample | Family | Origin | Font | Size | Colour |
|---|---|---|---|---|---|
| `SGM2026000011171` | FATURA | (310.2, 37.9) | ArialMT | 10.8 | `#666666` |
| `SUB2026000019889` | FATURA | (316.8, 46.4) | ArialMT | 10.8 | `#666666` |
| `SUB2026000019890` | FATURA | (294.0, 47.1) | Tahoma | 7.8 | `#666666` |
| `917031` | DEKONT | (242.6, 479.9) | MinionPro | 12.0 | `#000000` |
| `917034` | DEKONT | (231.2, 463.7) | MinionPro | 12.0 | `#000000` |
| `917035` | DEKONT | (217.9, 478.0) | MinionPro | 12.0 | `#000000` |

Read across the two families:

- **FATURA family clusters at x≈294–317, y≈38–47** — the top whitespace band
  above the letterhead, right of centre. Confirms the user's instinct that this
  family wants a near-top position, and lands nowhere near the withdrawn
  `y=170`.
- **DEKONT family clusters at x≈218–243, y≈464–480** — the empty mid-page band
  between the line-item table and the footer totals. A stamp at the FATURA
  position would land **on the DEKONT's header block**, which is exactly the
  failure this task was opened to prevent.
- **Positions vary by up to 23pt within a family**, because they were placed by
  hand. These are evidence for choosing a fixed coordinate, not values to copy.
- All three DEKONT stamps are on **page 1**, consistent with R28.

### The stamp text is `PO:<value>`, not the bare value

Every sample reads `PO:4522207286`. That is a real difference from anything the
spec has ever said and is raised separately as Q8, along with colour and size —
the current process uses grey 7.8–10.8pt on invoices and black 12pt on DEKONTs,
none of which is the "obviously an addition" red the original rationale wanted.

### One reference sample is defective

`917034` reads `PO:452220729` with the final `0` wrapped onto the next line —
a text box one character too narrow. `search_for("4522207290")` finds nothing.
It looks stamped and is wrong, which is precisely the R17 failure mode, found
in production output. Useful as a regression fixture; see
[[007-verify-stamp-after-write]].

## Done when

- [x] A fixed position is chosen for the **FATURA family** (`SGM`, `SUB`) that
      covers nothing on that layout — **`(300, 45)`**
- [x] A fixed position is chosen for the **DEKONT family** (digit-named) that
      covers nothing on that layout — **`(220, 475)`**
- [x] Both are verified by stamping the clean samples in `sgm_folders/` and
      eyeballing the rendered result — 5 FATURA-family and 3 DEKONT-family files
      are available
- [x] The DEKONT check confirms page 1 only (R28)
- [x] [[decisions/0002-stamp-placement]] is rewritten to cover both families, or
      replaced — **replaced** by [[decisions/0014-stamp-placement-per-family]]
- [x] Q8 is resolved or explicitly deferred — a position without a size is not
      implementable — **already closed 2026-09-20** into R12; this task confirmed
      14pt rather than changing it

## Notes

Whether the chosen coordinates should be absolute points or page fractions
depends on [[008-pdf-layout-robustness]]; every sample so far is A4, so absolute
is defensible for now, but say so explicitly rather than by omission.

## Related

[[010-confirm-placement-across-layouts]] is unblocked by the same material and
should be done alongside this. [[009-configurable-stamp-style]] becomes more
attractive now that there are provably two styles.


---

## Settled — 2026-09-22

**FATURA `(300, 45)`, DEKONT `(220, 475)`**, baseline, absolute points, 14pt
helvetica-bold red, page 1 only. Written up as
[[decisions/0014-stamp-placement-per-family]] and into [[spec]] R12a; **Q5 is
closed**. [[010-confirm-placement-across-layouts]] was done in the same pass and
closed with it, as [[_index]] said it should be.

### How the numbers were reached

Not by eye, and not off the stale grid preview. Page 1 of all ten clean samples
was rendered at 1px/pt greyscale, reduced to an ink map on a 5pt grid
(ink = any pixel below gray 235, which tolerates scan speckle), then **unioned
per family** — so a candidate only survives if it is clear on *every* sample of
that family.

| Family | Free space in the union | Human places it at |
|---|---|---|
| FATURA | `x≈165–595`, `y≈0–70` | `x≈294–317`, `y≈38–47` |
| DEKONT | full width, `y≈400–726` | `x≈218–243`, `y≈464–480` |

Both chosen points sit inside their family's free space **and** on top of where
the manual process already stamps. There was no tension between the two, so no
reason to depart from existing practice.

Measured clearance around the widest stamp the data can produce (`PO:` plus a
10-digit PO = 102.7pt at 14pt bold), identical on every sample of a family
because both layouts are fixed templates:

| Family | above | below | left | right |
|---|---|---|---|---|
| FATURA | >200pt | 32pt | 143pt | >200pt |
| DEKONT | 80pt | >200pt | >200pt | >200pt |

All eight stampable samples were then stamped with a throwaway prototype, using
real POs pulled through the already-built `route_filename` → `lookup_po` path,
and the rendered pages were looked at. Nothing is covered on either layout. Two
of the ten have a blank `PO` and were refused rather than stamped — the R18 path
behaving correctly, unprompted.

### Findings

- **`(240, 170)` was wrong for FATURA too**, not just for DEKONT. The ink map
  puts FATURA's free space at `y≈0–70`; `y=170` sits inside the recipient
  address block. One sample under a 50pt grid could not see that.
- **`insert_text`, never `insert_textbox`** — carried into R12a as a
  requirement. A text box is what wrapped `917034`'s final digit onto a second
  line in the reference sample. `insert_text` cannot wrap, so the defect this
  task found in the manual process is designed out rather than checked for.
  R17 still catches it if it ever recurs by another route.
- **The DEKONT band can close, and nothing here prevents it.** Its line-item
  table grows downward from `y≈400` toward a footer pinned at `y≈727` on all
  three samples. Every sample has a one-row table, leaving 80pt of clear space
  above the stamp; a DEKONT with roughly five or more rows would reach it. Not
  observed in any sample and **not guessed at** — recorded on
  [[008-pdf-layout-robustness]], which is where layout variance lives. Placing
  the stamp lower to pre-empt it was considered and rejected: it would trade a
  measured position for an unmeasured one against a case that has never
  occurred.
- **FATURA carries no equivalent risk.** Its stamp is above the entire document
  body in a header band that is fixed template across all seven samples,
  including the four from the August batch.
- **Page 2 of a DEKONT is a different document** — a `TAHSİLAT MAKBUZU`
  receipt, not a continuation of page 1. R28's "page 1 only" is not a
  simplification; stamping page 2 would put the PO on an unrelated document.
  Now in [[architecture/data-layout]].
- **Absolute points, chosen deliberately.** The task asked for this to be said
  rather than left to omission: every sample is A4 and unrotated, page
  fractions would buy nothing today and would obscure the measurements above,
  and a non-A4 page remains [[008-pdf-layout-robustness]]'s problem.

### Confirmed by the user — 2026-09-22

The user asked to see the stamps before the numbers were treated as settled,
was shown every stamped sample in both families, and **approved them**:
"looks good to me". Position and 14pt bold red are both confirmed. The proof
sheet is https://claude.ai/artifact/BhZADA5bXawBGFbauYGjrf — eight samples, each crop switchable between clean input, app
stamp and hand-placed stamp at identical geometry, so anything covered would
jump.

**This is what closes the task properly.** 017's "Done when" asked for the
samples to be stamped and eyeballed; the person who owns the output did the
eyeballing, which is better than the session doing it alone.

### What this leaves for [[026-stamp-the-po]]

The two coordinates become constants keyed by `Family`. 026 owes the real
`stamp()`; the prototype lived in the scratchpad and **nothing in `stamper.py`
was touched by this task**. Two things it inherits: `insert_text` is a
requirement now, and the clearance figures above are the regression baseline if
a test ever wants to assert the stamp landed in free space.