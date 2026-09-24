# Architecture overview

How the system works today. Update when the pipeline or components change.

See [[data-layout]] for Excel/PDF specifics, [[deployment]] for how it ships.

## Problem

For a customs document PDF, find its row in the uploaded Excel workbook and
print that row's **PO** onto page 1, then deliver the copy under a name that
carries the PO. The requirements are in [[spec]].

## Pipeline (per file)

1. Take an uploaded PDF, e.g. `SGM2026000010413.pdf` or `917031.pdf`.
2. Refuse it if it is not a `.pdf`, or if its name was already seen in this
   batch (R18).
3. The key is the filename exactly as uploaded, with only the extension cut
   (R1, R33); the app never sanitises names, and a folder part leaves a name
   unroutable. `SGM` and `SUB` names route to
   sheet 2 (FATURA), all-digit names to sheet 3 (DEKONT) (R2–R5).
4. Look the key up in that sheet's `Fatura No` column and read `PO` (R6–R10).
   A missing key, an empty `PO` or a key on more than one row is an exception.
5. Refuse a PDF that already carries a `PO:` stamp. Otherwise draw `PO:<value>`
   on page 1 at the family's position (R12, R12a, R28).
6. Check `PO:<value>` is in the output text, or withhold it (R17).
7. Name it `PO<value>-<original>.pdf` (R14). One stamped file downloads as a
   bare PDF, two or more as a zip (R15).

The key is the filename. There is no content parsing of the PDF at all — the text
layer is read only to verify the stamp and to spot an existing one. That keeps
the whole thing simple, and is why non-standard filenames are the main failure
mode.

## Components

### `stamper.py` — the logic, importable — added 2026-09-22

A flat module at the repo root. The per-file pieces are `route_filename()`,
`load_workbook()`, `lookup_po()`, `stamp_checked()` (which wraps `stamp()` and
`verify()`), `output_name()` and `repeated_upload()`. The batch functions are
`package()`, `run()` and `summarise()`. **`run(index, [(filename, bytes)])` is
the whole batch.** It returns one `Outcome` per input and the `Download`, and
never raises for any R18 case. `templates/result.html` renders a `Run`
([[028-summary-screen-and-run-flow]]). `app.py` and `tests/` both import it
([[029-wire-app-to-module]]).

Why it exists at all: [[decisions/0011-one-entry-point]]. Why it is one flat
file with pytest kept out of the image:
[[decisions/0012-module-shape-and-test-tooling]].

```bash
.venv/bin/python3 -m pytest        # the whole suite; pytest.ini finds tests/
```

The command-line script `stamp_tescil.py` was deleted on 2026-09-23
([[019-tescil-to-po-rename]]). The web app is the only entry point.

### `app.py` — Flask web app — rewritten 2026-09-23

Upload, call, render ([[029-wire-app-to-module]]). It holds no routing,
lookup, stamping or naming logic. That all lives in `stamper.py`. The workbook
is uploaded each session and parsed in memory, and nothing is written to disk.

| Route | Does |
|---|---|
| `GET /` | Step 1: upload the workbook (`templates/excel.html`) |
| `POST /excel` | `stamper.load_workbook(file.stream)`, stored in `SOURCES[sid]`. An unreadable file is a flash, not a 500 |
| `GET /stamp` | Step 2: choose PDFs (`templates/stamp.html`), with a link to the last run's results |
| `POST /stamp` | Every upload goes to `stamper.run()`. The `Run` is stored in `DOWNLOADS[sid]`, then redirect to `/result` |
| `GET /result` | Step 3: download button and summary on one screen (`templates/result.html`). Reachable again from the step list |
| `GET /download` | Serves `run.download`, only on the user's click (R29). Kept until the next run. If there is none (R20), it goes back with a flash |
| `GET /reset` | Clears the workbook and the run |
| `GET /lang/<tr\|en>?next=<path>` | Sets the session language (R31). `next` must be a path on this site |

**Why the POST redirects instead of returning the file.** A `send_file`
response never renders a page. Storing the `Run` and redirecting lets the
results page render and survive a reload, and the download waits for a click.

**The PDF list.** `static/queue.js` keeps the files chosen on the PDF step,
adds to them, refuses a name already on the list and gives each a remove
button (R32). The server's repeated-upload check stays as the backstop.

**Look and language.** `templates/base.html` is the Workbench shell (R30,
[[031-workbench-visual-style]]). Every string goes through `_()`, backed by
`i18n.py`: Turkish by default, English on a switch (R31,
[[decisions/0016-translations-as-a-dict]]). Per-file reasons are translated
from `Problem` plus `Outcome.details`, not from the English sentence.

- Templates extend `templates/base.html` (shared CSS + step list).
- Errors — wrong file type, unreadable workbook, no workbook loaded yet — flash
  a message and redirect to the correct step. An unreadable workbook is caught
  in `POST /excel`, so it is a message and not a 500.
- A file that cannot be stamped is not a flash. It is an `Outcome` with a
  `Problem`, listed on the results screen with its reason (R18, R21,
  [[decisions/0013-exceptions-as-returned-values]]). One bad file never sinks a
  batch, and a batch where *nothing* stamped has no download and says so (R20).
- `app.request_class` is `InMemoryRequest`. Every upload is parsed into a
  `BytesIO`, never Werkzeug's temporary file for bodies over 500 KB (R36).
- `MAX_CONTENT_LENGTH` is 100 MB (R34) (a batch, not a file), with a 413 handler that
  flashes the limit instead of showing Werkzeug's raw error page.
- `app.secret_key` comes from `SECRET_KEY` in the environment (R26), or a
  random key generated at start-up.

## Known structural limits

These are design constraints, not bugs:

- **`SOURCES` and `DOWNLOADS` are module-level dicts.** State resets on restart
  and is not shared across gunicorn workers. This is now *intended*:
  [[decisions/0008-single-user-session-scoped]] says one user, one session,
  nothing persists. **The whole design rests on running a single worker** — the
  Dockerfile pins `--workers 1` and that must not be raised. Two simultaneous
  users are not supported; if that changes, reopen
  [[005-shared-session-state]].
- **No TTL on either dict.** A session that is never reset holds its workbook, and
  its last batch of stamped PDFs, until the process restarts. Bounded in practice
  by one user and a 100 MB upload cap.
- **No auth.** Anyone reaching the port can use it. Postponed by the user on
  2026-09-23 — [[003-auth-and-multi-user]], R26.
- **One workbook at a time.** Uploading a different one replaces it. Fine under
  0008 — [[001-multi-workbook-support]] is near-dead as a result.
- **A4 assumed.** Coordinates are absolute points on page 1; a different page
  size puts the stamp in the wrong place silently. A long DEKONT line-item
  table could also reach the stamp — [[008-pdf-layout-robustness]].

## Environment

- Python venv at `.venv/`. Use `source .venv/bin/activate` or call
  `.venv/bin/python3` directly.
- Runtime dependencies: `openpyxl` (Excel), `pymupdf` / `fitz` (PDF), `flask`,
  `gunicorn`. Dev only: `pytest`.
