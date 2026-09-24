---
area: data
created: 2026-08-06
completed: 2026-08-06
---
# 011 — Explore the data, confirm the approach is viable

## What it was

Before writing anything, establish that the Excel → PDF mapping actually exists
and that stamping is technically possible.

## Outcome

- Confirmed `Fatura No` → `Tescil No` mapping lives in the `FATURA` sheet, and
  that the SGM filename is the join key. Documented in [[data-layout]].
- Confirmed sample PDFs are A4 with a real text layer — **no OCR needed**, which
  is what made the whole thing a small project rather than a large one.
- Found the three data gotchas that still matter: trailing whitespace on
  `Tescil No`, the uppercase `FATURA` sheet name, and needing `data_only=True`.
- Set up `.venv/` with `openpyxl` and `pymupdf`.

## What it produced

Feasibility confirmed and [[0004-match-columns-by-header]] decided — column
order in a hand-maintained monthly workbook can't be trusted.
