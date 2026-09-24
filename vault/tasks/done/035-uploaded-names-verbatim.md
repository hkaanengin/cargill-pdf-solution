---
area: web
priority: medium
created: 2026-09-23
completed: 2026-09-23
---
# 035 — Show and use every uploaded name exactly as uploaded

Spec reference: **R33**, with **R1** and **R21**.

## Problem

`app.py` passes every upload through Werkzeug's `secure_filename()` before
`run()` sees it, and does the same to the workbook's name. So
`SGM2026000011171 (1).pdf` is listed on the summary screen as
`SGM2026000011171_1.pdf`, and `SUBASI FATURA-DEKONT AGUSTOS.xlsx` as
`SUBASI_FATURA-DEKONT_AGUSTOS.xlsx`. The user sees names they never uploaded.
Found during [[019-tescil-to-po-rename]].

## Done when

- [x] `app.py` no longer calls `secure_filename()` on a PDF or on the workbook
- [x] A near miss such as `SGM2026000011171 (1).pdf` is listed under that exact
      name, and is still refused (R18, Q11)
- [x] The loaded workbook is shown under its exact name
- [x] Tests that pinned the sanitised names are rewritten to pin the real ones

## Done — 2026-09-23

- `app.py` passes `f.filename` to `run()` and stores the workbook's
  `file.filename`, both untouched. `secure_filename()` is gone from the app.
- **Found while doing it: `secure_filename()` was also the only thing keeping
  a path out of the download.** `route_filename()` took the key with
  `Path(name).stem`, which drops any folder part, so a hand-made request
  naming `../x/SGM2026000010413.pdf` routed as `SGM2026000010413`, stamped, and
  went into the zip as `PO…-../x/SGM2026000010413.pdf`. Browsers never send a
  folder part, so no real user would hit it; a crafted request could.
- **Fixed by making R1 literal**, not by renaming anything: the key is now the
  name with only its extension cut. A name with a folder part (`/` or `\`)
  keeps it in its key and is unroutable (R5). No spec change was needed: R1
  already says the key is the filename with `.pdf` removed and nothing else
  done to it.
- Tests: the two `secure_filename()` tests in `test_output.py` became one that
  pins the near miss's real key; `test_summary.py`'s near-miss fixture is the
  real name; `test_app.py` checks the workbook name exactly, lists a refused
  near miss under its uploaded name, and keeps a folder-part name out of the
  download; `test_routing.py` has both kinds of folder part as unroutable.
  **461 passing.**
- R32's list in the browser already compared names as chosen, so the page and
  the server now agree on what "the same name" means.
