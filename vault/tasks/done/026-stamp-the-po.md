---
area: code
priority: high
created: 2026-09-22
updated: 2026-09-22
completed: 2026-09-22
---
# 026 — Draw the stamp

Spec reference: **R11**, **R12**, **R12a**, **R13**, **R28**.

## Problem

Both current call sites stamp the wrong value at one global coordinate:
`page.insert_text((STAMP_X, STAMP_Y), tescil, …)` with `(240, 170)`. R11 changes
the value to `PO`, R12 changes the text to `PO:<value>`, and R12a says a single
coordinate is wrong in principle — the two document families have nothing in
common visually.

## 017 is done — the numbers are in

**Settled 2026-09-22**, closing [[spec]] Q5 —
[[decisions/0014-stamp-placement-per-family]], now in R12a. Nothing here is
waiting on anything:

| Family | Baseline `(x, y)` |
|---|---|
| `Family.FATURA` (`SGM`, `SUB`) | **`(300, 45)`** |
| `Family.DEKONT` (all-digit) | **`(220, 475)`** |

`PO:<value>`, `helvetica-bold`, **14pt — confirmed, not provisional**, red
`(1, 0, 0)`, page 1 always (R12, R28). Absolute points, top-left origin, A4.

**Two things 017 hands over beyond the numbers:**

- **Use `insert_text`, never `insert_textbox`** — this is in R12a now. A text
  box is what wrapped the final digit of `917034`'s PO onto a second line in
  the reference sample: a document that looks stamped and is wrong.
  `insert_text` cannot wrap, so the defect is designed out rather than caught.
- **The clearance baseline**, if a test wants to assert the stamp landed in
  free space rather than merely that it rendered. Around the widest stamp the
  data can produce (`PO:` + 10 digits = 102.7pt at 14pt bold), measured
  identical on every sample of a family: FATURA has 32pt below and 143pt left;
  DEKONT has 80pt above. Everything else is >200pt.

017 proved the placement works by stamping all eight stampable samples with a
throwaway prototype and looking at the renders. **That prototype was scratch and
is gone — `stamper.py` was not touched.** This task owes the real `stamp()`.

## The two families

From [[architecture/data-layout]] — the reason R12a exists:

- **FATURA-routed** (`SGM`, `SUB`): born-digital e-Fatura, one page, real text
  layer. Free space is `x≈165–595, y≈0–70`; the stamp goes in the top band,
  right of the logo.
- **DEKONT-routed** (all-digit): a **two-page scan**, 50–104 embedded images per
  page, **no text layer at all**. Free space is the full width between `y≈400`
  and `y≈726`; the stamp goes in the mid-page band under the line-item table.

A FATURA-position stamp on a DEKONT lands on its header block. That is the
failure 017 was opened to prevent. **Page 2 of a DEKONT is a different document
entirely** (a `TAHSİLAT MAKBUZU` receipt), so R28 is not a convenience — it
stops the PO landing on an unrelated page.

The family comes from [[023-filename-routing]]'s result — it is already known by
the time this is called, and must not be re-derived from the PDF's content (R1).

## Done when

- [x] The stamp reads `PO:<value>`, prefix included — it is part of the stamp,
      not decoration (R12)
- [x] Bold red at **14pt**, the size 017 confirmed (R12)
- [x] Position is chosen by family, from two named constants (R12a) — keyed by
      `Family`, which is already both the routed sheet and the layout
- [x] Drawn with `insert_text`, **not** `insert_textbox` (R12a)
- [x] **Page 1 only**, whatever the page count — asserted against the three
      two-page DEKONT samples (R28)
- [x] Works on a PDF with no text layer — the DEKONT scans have none
- [x] Input bytes are never mutated; the return is new bytes
      ([[decisions/0003-never-modify-originals]], R13)
- [x] A test stamps all ten `sgm_folders/` samples and each output opens cleanly
- [x] ~~[[decisions/0002-stamp-placement]] is rewritten for two families, or
      replaced~~ — **done by 017**:
      [[decisions/0014-stamp-placement-per-family]]

## Notes

The module takes and returns **bytes**, not paths. The app holds uploads in
memory and writes nothing to disk (R23), and tests read the samples themselves.

Absolute points are defensible while every sample is A4 595×842 — **said
explicitly and recorded** in [[decisions/0014-stamp-placement-per-family]], so
this task inherits the choice rather than making it. Page fractions are
[[008-pdf-layout-robustness]]'s question, not this one's.

`insert_text` returning without drawing is a real failure mode and is not
checked here — that is [[007-verify-stamp-after-write]] (R17), which runs after
this and before delivery.

## Built — 2026-09-22

`stamp()` in `stamper.py`, tested by `tests/test_stamp.py`. The suite went from
100 to **161 tests, all passing**.

- **Constants, as the task asked:** `STAMP_POSITION` (keyed by `Family`),
  `STAMP_PREFIX`, `STAMP_FONT`, `STAMP_SIZE`, `STAMP_COLOR`. The old
  `STAMP_X/STAMP_Y` in `stamp_tescil.py` are left alone. That file is deleted in
  [[019-tescil-to-po-rename]].
- **One addition not in the frame: `stamp_text(po)`.** It returns the literal
  `PO:<po>`. Drawing the stamp and searching for it (R17, Q10) both need the
  same string, so it is defined once. **[[007-verify-stamp-after-write]] should
  search for `stamp_text(po)`** and not build the string again.
- **`import pymupdf`, not `import fitz`.** PyMuPDF 1.28.2 warns that the
  `fitz` name is deprecated and will be removed. The package in
  `requirements.txt` is the same one.
- **Every sample is checked for all of it:** the text is `PO:<value>` on one
  line, Helvetica-Bold at 14pt in `0xff0000`, with its baseline exactly at the
  family's coordinate; the page count is unchanged; the input bytes are
  unchanged; there is no stamp on page 2 of any DEKONT. The DEKONT scans are
  also checked to have no text layer, so the no-text-layer case is really
  tested.
- **The spec's clearance criterion is re-confirmed in `stamper.py`, as it
  asked.** Bounding boxes cannot prove clearance. Each DEKONT page is
  full-width image strips, so image bboxes cross the stamp. Each FATURA has a
  page border drawing whose rectangle contains it. So the test does what 017
  did and looks at ink instead: it renders the *input's* page 1 in greyscale
  under the stamp's rectangle (grown by 2pt) and requires every pixel ≥250.
  **All ten samples come out 255, pure white.**
- **A test deliberately passes the wrong family** and checks that the position
  follows the argument. That proves `stamp()` trusts routing and never looks at
  the page to decide (R1).

Not done here, as the task said: nothing checks that `insert_text` actually
drew anything. That is still [[007-verify-stamp-after-write]]'s job.
