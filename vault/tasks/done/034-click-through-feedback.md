---
area: web
priority: high
created: 2026-09-23
completed: 2026-09-23
---
# 034 — First click-through: manual download, adding PDFs, step navigation

Spec reference: **R29** (the download on click, back-and-forth between
steps) and **R32** (the PDF list adds, and duplicates are refused by name).
Raised by the user 2026-09-23 during the click-through for
[[029-wire-app-to-module]].

## Done when

- [x] Arriving at the results page downloads nothing. The download button
      is the only way to get the file
- [x] Choosing PDFs a second time adds to the list. A name already on it is
      skipped and named in an error on the page
- [x] The step list links to every step that has something to show, and
      visiting one keeps the workbook and the last run
- [x] The workbook step shows the loaded workbook when there is one, and
      offers to replace it rather than hiding behind a redirect
- [x] Tests updated. The old "download starts by itself" tests assert the
      opposite now
- [x] Each file on the list has a remove button (R32, added 2026-09-23)
- [x] The user's two list examples pass as tests (`tests/test_queue_js.py`)
- [x] The user has clicked through it: the user used the app end to end (workbook, PDFs, stamp, results, download) and said "looks good to me so far" on 2026-09-23. Further findings will come as new tasks

## Notes

**Built 2026-09-23. Two boxes wait on the user's browser**: the PDF list
adding, and the click-through.

- **No automatic download.** `POST /stamp` redirects to plain `/result`,
  and the `auto`/`ready` flag and the page's script are gone. The test now
  asserts that `result.html` has no `<script>` at all.
- **Navigation.** A `progress` context processor gives every template
  `has_source` and `has_run`. `base.html`'s `stepitem` macro makes a step a
  link when it is reachable and not the current page. The new `GET /excel`
  (`excel_page`) is step 1 whether a workbook is loaded or not. `GET /`
  still jumps to step 2 when a workbook is loaded, so reopening the app lands
  where the work is. "Replace workbook" and "Use a different workbook" now
  go to step 1 instead of `/reset`, so neither link loses anything by
  itself. `/reset` still exists, but nothing in the UI links to it now.
- **The PDF list adds** (R32). A `DataTransfer` in the page holds everything
  chosen so far. Each pick or drop is merged in by name, the file input is set
  to the merged list, and skipped names are shown in an alert above the list.
  This is browser-only, so pytest cannot reach it. The rendered script was
  syntax-checked with `node --check` in both languages. It is untested
  beyond that until the user tries it.
- **Remove button, added 2026-09-23 at the user's request.** The list rules
  moved out of the page into `static/queue.js`: `merge()` and `remove()`,
  plain functions over anything with a `.name`. The page keeps an array and
  rebuilds the file input from it after every change. `tests/test_queue_js.py`
  runs the user's two examples through node, and it is skipped if node is
  not installed. node is a dev tool like pytest and is not in the image. The
  Dockerfile now copies `static/`. The rows, buttons and file input are still
  checked by hand, but the rules no longer are.
- The suite has **458 passing**.
