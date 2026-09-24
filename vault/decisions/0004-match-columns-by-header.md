---
status: accepted
date: 2026-08-06
---
# 0004 — Match Excel columns by header text, not by letter

> **Still accepted — 2026-09-23.** Now R8 in [[spec]]. The columns matched are
> `Fatura No` and `PO`, by `stamper.load_workbook()`; `Tescil No` is no longer
> read. The match must be exact, because both sheets also carry a `PO Tarihi`
> column — [[architecture/data-layout]].

## Decision

`load_tescil_map()` finds `Fatura No` and `Tescil No` by reading row 1 and
matching **header text**. Column letters (C and F today) are documented in
[[architecture/data-layout]] for humans but nothing in the code depends on them.

## Why

- **The workbook is maintained by hand, monthly.** Someone inserting a column in
  September would silently shift every letter-based index. The failure wouldn't
  be an error — it would be stamping the wrong value onto a customs document.
- Header text is the stable identifier here; position is not.
- A missing header raises `ValueError` immediately, which is a loud, obvious
  failure at load time rather than wrong output at stamp time.

## Consequences

- Renaming a header breaks the load — deliberately. Loud beats silent.
- Matching is exact and case-sensitive, which is also why the sheet name gotcha
  (`FATURA`, not `Fatura`) matters. Both are documented in
  [[architecture/data-layout]].

## Related

Same principle drove `.strip()` on every string cell — `Tescil No` values carry
trailing whitespace, and an unstripped value stamps fine but compares unequal.
