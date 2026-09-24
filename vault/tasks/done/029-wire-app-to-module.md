---
area: web
priority: high
created: 2026-09-22
completed: 2026-09-23
---
# 029 — Make `app.py` thin

Spec reference: **R29**, **R22**, **R23**, **R25**, and
**[[decisions/0011-one-entry-point]]**.

## Problem

`app.py` does the work itself: `stamp_bytes()` opens the PDF and calls
`insert_text`, the `POST /stamp` handler derives keys, looks them up, decides
what is skipped and builds the payload. Once 022–028 exist, every one of those
lines has a tested counterpart in `stamper.py` — and two implementations of the
same twenty-odd requirements is exactly the cost
[[decisions/0011-one-entry-point]] retired the CLI to avoid.

This task is the last of the implementation run: upload, call, render.

## Scope

`app.py` keeps what is genuinely web — routes, session id, uploads, flashes for
*operational* errors (wrong file type, no workbook loaded), the 200 MB cap and
its 413 handler, the download response. It keeps no routing rule, no header
matching, no coordinate, no exception policy.

Ordering is deliberate: this runs **after** 022–028 so there is never a window
where the app is half-wired and neither path works end to end.

## Done when

- [x] `app.py` imports `stamper` and contains no lookup, routing, stamping or
      naming logic of its own
- [x] `stamp_bytes()` and the inline key derivation are gone
- [x] `build_manifest()`, `build_zip()` and `unique_name()` are gone, and
      packaging is `stamper.package()` (moved here from
      [[027-output-naming-and-packaging]], which built the replacement without
      touching `app.py`)
- [x] The workbook upload calls `stamper.load_workbook(file.stream)` — parsed in
      memory, never written to disk (R23, R24)
- [x] The six steps of R29 walk end to end: the user used the app end to end (workbook, PDFs, stamp, results, download) and said "looks good to me so far" on 2026-09-23. Further findings will come as new tasks
- [x] `POST /stamp` calls `stamper.run()` and redirects to a results route that
      renders `templates/result.html` with `run`, `summarise(run.outcomes)` and
      `auto`. The page **survives a reload**: keep the `Run` in `DOWNLOADS[sid]`,
      not in flashes (from 028)
- [x] No import of `stamp_tescil` remains anywhere
- [x] `MAX_CONTENT_LENGTH`, the 413 handler and `/reset` still behave
- [x] `SOURCES` / `DOWNLOADS` stay module-level dicts — one user, one session,
      nothing persists (R22, R23,
      [[decisions/0008-single-user-session-scoped]]) — and the Dockerfile still
      pins `--workers 1` (R25)

## Notes

**Do not raise the worker count.** State lives in process memory; a second
worker breaks it. R25 is a requirement, and the `--workers 1` pin has still
never been verified in an actual build — that check belongs to
[[004-cloud-deployment]].

The error messages naming "FATURA sheet" and "Fatura No / Tescil No" in
`upload_excel()` are wrong twice over after R7 and R11: the sheet name is not
consulted at all and `Tescil No` is not read. Fix them here or in
[[019-tescil-to-po-rename]], but not in neither.

Once this lands, `stamp_tescil.py` has no importer and
[[019-tescil-to-po-rename]] can delete it.

**The Dockerfile does not copy `stamper.py`** — found while building
[[022-core-module-and-tests]]. Line 10 is
`COPY stamp_tescil.py app.py ./`, written when those two files were the whole
app. The moment `app.py` imports `stamper`, an image built from this Dockerfile
starts and dies on `ModuleNotFoundError`, and it will do it in the container
rather than on the laptop where the suite is green. Add `stamper.py` to that
COPY here, and drop `stamp_tescil.py` from it in
[[019-tescil-to-po-rename]]. (The `pip install -r requirements.txt` line is
correct as it stands — no glob, so pytest stays out of the image, which is what
[[decisions/0012-module-shape-and-test-tooling]] asked to be checked.)

**The per-file loop is already written, in a test** — 027, 2026-09-22.
`run_batch` in `tests/test_output.py` is the shape the handler should take:
`repeated_upload(name, seen) or lookup_po(index, *route_filename(name))`, then
`stamp_checked(...)`, then `output_name(...)`, and `package(stamped)` at the
end. `package()` returning `None` is R20's case: no download. Pass
`repeated_upload()` the **same** name the key is derived from, which is the
name after `secure_filename()`.

**`secure_filename()` strips path components**, so `../SGM2026000010413.pdf`
becomes a valid key. That is a repair Q11 would not make. Browsers send bare
basenames, so it should not happen from the upload form. Worth knowing, not
worth code, unless the user says otherwise.

**028 left the handler almost nothing to do** — 2026-09-23. `run()` is the
whole loop. `result.html` is the whole screen, already rendered in tests
(`tests/test_summary.py`, via `app.test_request_context()`). The handler reads
each upload into `(secure_filename(name), bytes)`, calls `run()`, stores the
`Run`, and redirects. `stamp.html`'s `pending` / `auto` block moves to the
results page.

**Non-PDF uploads are handled in the module now** ([[spec]] Q16, closed
2026-09-23). `run()` refuses them as `Problem.NOT_A_PDF` before anything opens
them. The app's own `"not a PDF"` check in `POST /stamp` is now a duplicate and
goes, like the rest of the loop. Pass every upload to `run()`, whatever its
extension. Filtering them out first would drop them from the summary, and
R21 requires every input to appear there.

**Built 2026-09-23 — only the click-through is left.** `app.py` is now
upload, call, render. `POST /stamp` passes every upload to `stamper.run()` as
`(secure_filename(name) or "unnamed", bytes)`, stores the `Run` in
`DOWNLOADS[sid]`, and redirects to `GET /result?ready=1`. `/result` renders
`result.html`. `ready` is set only on that redirect, so a reload does not
re-fire the download. `/download` serves `run.download` and redirects with a
flash when it is `None` (R20). `SOURCES[sid]` holds `{"filename", "index"}`.
`stamp.html` lost its `pending`/`auto` block and now links to the last run's
results.

Found and done along the way:

- **Dockerfile COPY now includes `stamper.py`.** `stamp_tescil.py` is still
  copied, and dropping it is [[019-tescil-to-po-rename]]'s job. Nothing imports
  it any more.
- **The wrong copy is fixed.** The FATURA-sheet and Tescil error message in
  `upload_excel()` is gone, together with the empty-mapping check it belonged
  to. An empty workbook now loads and shows "0 entries". That matches
  [[spec]] Q15's measured behaviour, and R20 still stops the run. The
  descriptions in `excel.html` and `stamp.html` also claimed Tescil and a
  manifest, and they now say PO and no manifest. The page title and the
  project name are still "Tescil", which is 019's.
- **An unreadable workbook is a flash, not a 500.** The existing broad
  `except` around the loader stays. That keeps Q15's `BadZipFile`/`IndexError`
  case off the error page without deciding anything Q15 asks. What the
  workbook *should* be checked for is still [[030-workbook-verification]].
- **`tests/test_app.py`, 12 tests over the Flask test client.** They cover
  R29's walk, reload survival, the bare-PDF and zip downloads, R20's missing
  download, a non-PDF reaching the summary, `/reset`, and the 413. The suite
  is at **302 passing**. These tests guard the wiring. They do not replace
  the click-through.
