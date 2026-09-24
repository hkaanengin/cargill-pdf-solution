---
area: web
priority: high
created: 2026-09-23
completed: 2026-09-23
---
# 033 — Turkish by default, English on a switch

Spec reference: **R31**. How: [[decisions/0016-translations-as-a-dict]].

## Done when

- [x] Every page opens in Turkish. A TR / EN switch in the sidebar changes it
      for the session
- [x] Flashes, summary headings and each file's reason are translated too
- [x] Data is untouched: file names, POs, sheet names, column headers, and the
      `PO:` stamp itself
- [x] A test fails if a template string or a `Problem` has no Turkish entry
- [x] The existing English assertions still pass with the language set to EN
- [x] **The user has reviewed the Turkish in `i18n.py`**. The user said "Turkish seems right" on 2026-09-23. Strings added afterwards, for [[034-click-through-feedback]], follow the same style and have not been reviewed separately

## Notes

The error text in "could not read that workbook: …" comes from openpyxl or
zipfile and stays in English. It is technical detail after a Turkish sentence
that already says what went wrong. Translating library exceptions is not
worth it unless the user says otherwise.

**Built 2026-09-23. It waits on the user reviewing the Turkish.**

- **`i18n.py`** holds `TR` (English → Turkish, about 60 strings, grouped by
  page) and `REASONS_TR` (one per `Problem`). `translate()` and `reason()` are
  the only functions.
- **`app.py`** adds `current_language()` (session `lang`, default `tr`), a
  `_()` helper, a context processor that gives templates `_`, `lang` and
  `reason`, and `GET /lang/<code>?next=<path>`. `next` must be a path on this
  site: `//host` and absolute URLs go to `/` instead, which prevents an open
  redirect.
- **`stamper.py`** gained a `details` field on `Lookup`, `Stamped` and
  `Outcome`, defaulting to `None` so every existing constructor still works.
  It carries `sheet`, `rows` or `stamp`, the values each English message was
  built from. The English `message` is unchanged, and the tests pin it.
- **The templates** wrap every string in `_()`. The JS counts on the PDF step
  come from a `tojson` dict, so the browser never builds English.
  `<html lang>` follows the choice, which also makes CSS uppercase `i` → `İ`
  correctly in the group headings.
- **Tests.** `test_app.py` and `test_summary.py` now set EN, because their
  assertions are English. The new `test_i18n.py` pulls every `_()` literal
  out of the templates (by regex) and `app.py` (by `ast`) and requires a
  Turkish entry for each. It also checks that each Turkish string keeps the
  same `{placeholders}`, that the default is TR, that the switch works,
  that the open redirect is closed, and it runs a full ten-sample walk in
  Turkish. The suite has **433 passing**.
- **The Dockerfile COPY now includes `i18n.py`.**
- **Wording choices to review.** "Workbook" is translated as *Excel
  dosyası*, not *çalışma kitabı*, on the inference that users call it that.
  The product name "PO Stamper" is left untranslated.
