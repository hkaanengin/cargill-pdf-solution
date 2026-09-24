---
area: web
priority: high
created: 2026-09-22
completed: 2026-09-23
---
# 028 — The summary screen, and the six-step run

Spec reference: **R19**, **R20**, **R21**, **R29**.

## Problem

Today's reporting is a list of amber `flash()` messages — one per skipped file,
plus a count. R21 asks for something different in kind: a **summary that
accounts for every input file, grouped by outcome**, sitting on the same screen
as the download.

The gap is not cosmetic. Flashes name only failures, so a user cannot tell a
stamped file from one that was never uploaded, and **no stamped file is ever
shown with the PO it received**. R21 requires `x.pdf → PO:123` per stamped file
— the only place the user can check the app's work before sending a customs
document.

## Why this screen carries more weight than it looks

R16 is withdrawn and R23 says nothing persists. **This screen is the only record
a run ever produces.** Close the tab and there is no trace of what happened —
accepted deliberately, and reopened as a parked discussion in
[[021-run-history]], which blocks nothing.

## The groups (R21)

Every input file appears in exactly one:

- **stamped** — each named with the PO it received, `x.pdf → PO:123`
- **key not in the workbook**
- **row found, `PO` blank** — over half of all rows, so this is the common path,
  not an edge case
- **every other R18 reason**, each with its own text: unroutable name (R5),
  duplicate key named as a *workbook* problem, already-stamped input, failed
  verification

## R29 — the run, in order

1. land → 2. upload workbook → 3. upload PDFs → 4. press **Stamp** → 5. app
stamps → 6. download **and** summary on one screen.

Steps 1–4 largely exist. Step 6 is the change: `app.py` redirects to
`/stamp?ready=1` and re-renders the *upload* page with flashes attached. That is
not the screen R29 describes.

## Done when

- [x] Every input file appears in exactly one group; the groups are those above
      (R21) — `summarise()`, `tests/test_summary.py`
- [x] Each stamped file is shown with its PO (R21) — `x.pdf → PO:123`
- [x] The summary and the download are on **one** screen (R29 step 6) —
      `templates/result.html` carries both. *Served by a route in 029.*
- [x] An exception never aborts the batch — every other file is still stamped
      and delivered (R19) — for every R18 case, including a non-PDF upload
      once Q16 was answered (see *Findings*)
- [x] A run where every input fails offers no download and says so plainly (R20)
- [ ] ~~The six steps of R29 walk in order, confirmed by clicking through~~ —
      **moved to [[029-wire-app-to-module]]**. Nothing is clickable until a
      route renders the page.
- [x] A mixed batch — stamped, missing key, blank PO, unroutable — renders
      correctly — rendered headless with all seven `Problem`s plus two stamps

## Notes

Keep the reason the POST redirects rather than returning the file
([[architecture/overview]], *Why the POST redirects*): a `send_file` response
renders no page, so the summary would arrive attached to the next request. The
redirect target changes from the upload page to a results page; the mechanism
stays.

`templates/base.html` styles `ok` / `warn` / `error` flashes. The summary is not
a flash — it is page content, and it should survive a reload rather than being
consumed once.

**`Problem` has seven members now, not six** — 027, 2026-09-22.
`REPEATED_UPLOAD` is the user's answer for the same filename uploaded twice.
It arrives as a `Lookup` from `repeated_upload()`, so it groups and renders
like the others.

## Findings — 2026-09-23

**Built headless, as the build order asks.** The task mixed module work with
app work: "confirmed by clicking through" needs a route, which is 029. The split
keeps [[decisions/0012-module-shape-and-test-tooling]]'s rule that the app
changes last. What exists:

- **`stamper.run(index, files, now=None) -> Run`.** `files` is
  `[(filename, bytes)]`. It gives back one `Outcome` per input in upload
  order, and the `Download` (or `None`, R20). This is the loop that lived in
  the `run_batch` test fixture, moved into the module; the fixture now calls
  `run()`, so the 027 batch tests pin it.
- **`Outcome`**: `filename`, `po`, `output`, `problem`, `message`, plus `.ok`
  and `.stamp` (`PO:<po>`). Same "never both" contract as `Lookup`.
- **`summarise(outcomes)`**: groups in `SUMMARY_ORDER`. That is stamped
  (`None`), then R21's two named reasons, then each other `Problem` in enum
  order. Empty groups are dropped. **Each other R18 reason gets its own
  group**, rather than one "other" bucket. R21 reads either way, and every
  line still carries its own message, so both readings are met.
- **`templates/result.html`**: headings keyed by `Problem` value, live in
  the template (presentation, not logic). A test fails if a `Problem` is added
  without a heading. The download auto-starts only when `auto` is passed. That
  is the old `?ready=1` mechanism, so a reload does not download again.
- `base.html` gained a third step, **3 · Results**, and the styles for groups.

**A non-PDF upload aborts the whole run.** Measured: `SGM2026000010413.docx`
routes to FATURA (the key is the stem, R1), looks up fine, and then
`already_stamped()` raises `FileDataError` inside `run()`. Every other file in
the batch is lost. Today's `app.py` avoids this by refusing non-`.pdf` names
up front with its own "not a PDF" reason, but no requirement asks for that. It
is not covered by the malformed-input non-goal either, which is about PDFs.
Raised as [[spec]] Q16.

**Q16 answered the same day and built.** The user said a non-PDF will never
arrive, and if one does, it is an exception, ignored and shown in the
summary. It is now an R18 case. `not_a_pdf()` checks the extension (case
ignored, which is the app's old behaviour and is marked as inference in the
spec). It runs first in `run()`, so a non-PDF is never opened. It adds
`Problem.NOT_A_PDF`, which renders under **Ignored: not a PDF**. The suite has
**290 passing**.

The `2 · SGM PDFs` step label and the `SGM Tescil Stamper` title are stale
(SUB and DEKONT are handled too). Left for [[019-tescil-to-po-rename]].
