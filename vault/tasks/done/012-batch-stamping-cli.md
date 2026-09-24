---
area: cli
created: 2026-08-06
completed: 2026-08-06
---
# 012 — Build the batch stamping CLI

## What it was

`stamp_tescil.py` — read the workbook, stamp every SGM PDF, write copies out.

## Outcome

- `load_tescil_map(workbook)` accepts a path **or** a file-like object. That dual
  signature is what later let the web app reuse the same parser unchanged.
- Stamp placement chosen by rendering a sample under a 50pt coordinate grid
  (`sample_grid_preview.png`) and picking empty space — [[0002-stamp-placement]].
- Output goes to `output/`; sources are never touched —
  [[0003-never-modify-originals]].
- Missing keys are skipped with a message rather than erroring. Whether that's
  the right call is still open — [[006-missing-key-handling]].
- Tested on all 4 sample PDFs; placement verified by eye.

## Caveat carried forward

"Verified" means 4 samples that may all share one layout, with absolute
coordinates that assume A4. Both are still open —
[[010-confirm-placement-across-layouts]], [[008-pdf-layout-robustness]].
