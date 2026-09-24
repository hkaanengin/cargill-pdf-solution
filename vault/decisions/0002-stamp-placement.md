---
status: superseded
date: 2026-08-06
superseded: 2026-09-20
superseded-by: 0014-stamp-placement-per-family
---
# 0002 — Stamp at (240, 170), bold red, 14pt

> ⚠️ **Superseded 2026-09-20. Do not implement from this file.**
> `(240, 170)` is withdrawn. The user confirmed that digit-named (DEKONT)
> documents need a different position from `SGM`/`SUB`, and that page 1 is
> stamped for every type — now **R12** and **R28** in [[spec]].
> Q8 has since settled the look as `PO:<value>`, bold red, 14pt (R12), and
> the per-family coordinates are in R12a and
> [[decisions/0014-stamp-placement-per-family]]. `stamp_tescil.py`, named
> below, was deleted on 2026-09-23.
> Everything here is kept as the record of how the original coordinate was
> reached. **The replacement landed 2026-09-22:**
> [[decisions/0014-stamp-placement-per-family]] — `(300, 45)` for FATURA and
> `(220, 475)` for DEKONT, measured against every clean sample. Colour, size
> and weight came back unchanged; only the position was wrong.

## Decision

The Tescil No is drawn at baseline **(x=240, y=170)** in **bold red at size 14**.
Constants live at the top of `stamp_tescil.py`: `STAMP_X`, `STAMP_Y`,
`FONT_SIZE`, `FONT`, `COLOR`.

## Why

- **The position** was chosen by rendering a sample PDF under a 50pt coordinate
  grid (`sample_grid_preview.png`) and picking empty space near the top of the
  document, where a registration number reads naturally and nothing is covered.
- **Red and bold** because the stamp must be obviously an addition, not part of
  the original document. Someone handling a customs receipt should be able to
  tell at a glance what was printed on and what came from the source.
- **14pt** is legible when printed without dominating the page.

## Consequences

- Coordinates are **absolute**, so they assume A4 (595 × 842 pt). A different
  page size puts the stamp in the wrong place with no error —
  [[008-pdf-layout-robustness]].
- Verified against 4 sample PDFs only, which may all share one layout —
  [[010-confirm-placement-across-layouts]].

## Revisit if

Real PDFs turn out to vary in layout, or a second document type appears.

**Both happened, on 2026-09-20.** A second document family arrived (two-page
DEKONT scans, no text layer) and its empty space is nowhere near an SGM's — the
measured human placement sits at y≈464–480 against the invoices' y≈38–47. A
stamp at `(240, 170)` would land on the DEKONT header block. This decision was
correct for what it could see and wrong for what it could not, which is why
[[010-confirm-placement-across-layouts]] existed.

**Replaced 2026-09-22** by [[decisions/0014-stamp-placement-per-family]]. One
note worth carrying forward: `(240, 170)` was not merely wrong for DEKONT, it
was wrong for the family it was chosen on — the ink map puts FATURA's free
space at `y≈0–70`, so `y=170` sat inside the recipient address block. One
sample and a 50pt grid was not enough to see that.
