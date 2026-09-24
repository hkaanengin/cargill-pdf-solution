---
area: web
priority: high
created: 2026-08-07
completed: 2026-09-16
---
# 002 — Upload multiple SGM PDFs, return a zip

## Problem

The web app handles one PDF per round trip. The CLI batches; the web app doesn't.
Anyone with a folder of receipts has to repeat the upload-download loop per file,
which is the main reason someone would still reach for the CLI.

## Done when

- [x] The stamp form accepts multiple PDFs (and ideally a drag-dropped folder)
- [x] All are stamped in memory and returned as a single zip
- [x] Per-file failures don't sink the batch — the zip arrives with a manifest
      listing what was skipped and why
- [x] Tested with a mixed batch: some valid, some unknown key, some non-PDF

## Notes

The manifest is where this task meets [[006-missing-key-handling]] — settle that
decision first so both paths report failures the same way, rather than inventing
a second convention here.

Memory is worth a thought: everything is held in RAM today, and a large batch of
PDFs held simultaneously is a different profile than one file. Probably fine at
realistic sizes; worth a sanity check, not a redesign.

## Promoted to high — 2026-09-08

The user described the expected product as: *"They will expect to upload pdfs
into the web site and receive/download stamped pdfs back."* Plural. Batch upload
isn't a convenience on top of the web app — it **is** the web app as the users
picture it. See [[decisions/0007-user-model-small-known-group]].

[[006-missing-key-handling]] is now settled, so the manifest convention is fixed:
skip the file, name it and its key in the report, don't sink the batch. Match
[[decisions/0006-skip-missing-keys-with-warning]] — the zip should carry a
manifest listing every skipped file, and the page should show the same warning.
That decision's rejected "report file" option effectively returns here as the
in-zip manifest, which is the right place for it.

## Built — 2026-09-16

`app.py`, `templates/stamp.html`, `templates/base.html`. The CLI was not touched.

### How it ended up working

- `request.files.getlist("pdf")` with `multiple` on the input. Drag-drop of a
  multi-file selection works through the same `dataTransfer.files` assignment
  that was already there.
- **One file and no skips returns a bare PDF; anything else returns a zip.** A
  single-file zip is a worse artifact than the PDF it contains, and a single file
  was the whole previous behaviour, so it is kept exactly.
- The zip always carries `MANIFEST.txt`: the source workbook and entry count,
  every stamped file with its Tescil No, then every skipped file with its reason.
- Skips are reported twice on purpose — as page warnings and in the manifest.
  Once the zip is downloaded the page is gone, so the zip has to explain itself.

### The non-obvious part: `send_file` swallows flash messages

The old handler returned the PDF straight from the POST. That works for one file,
but a batch has to report skips, and a download response never renders the page —
the flashes would surface on the *next* page load, attached to the wrong batch.

So the POST now stores the result bytes in `DOWNLOADS[sid]`, flashes the summary,
and redirects to `GET /stamp?ready=1`. That render shows the summary and kicks the
download. The `ready` flag is what makes it fire once rather than on every later
view of the page, and the result is kept (not popped) so the "download again" link
works if the browser blocked the automatic one.

One pending download per session; the next batch replaces it, and `/reset` and a
new Excel upload both clear it.

### Memory — the sanity check this task asked for

Held in RAM: every stamped PDF, plus the zip built from them, at once. Samples are
~100 KB, so a 200-file batch is ~40 MB of PDFs and roughly the same again in the
zip buffer. Fine. `MAX_CONTENT_LENGTH` went 25 MB → 200 MB to admit a real batch
at all, with a 413 handler that now says so in the UI instead of showing a raw
Werkzeug error page. That cap is the real bound on memory, and it is the knob to
turn if a batch ever gets refused.

### Tested

Flask test client, mixed batch of 2 valid + 1 unknown key + 1 `.txt`: zip holds
exactly the 2 stamped PDFs and the manifest, both skips are named with reasons on
the page and in the manifest, and both stamped PDFs contain their Tescil No when
read back with PyMuPDF. Also covered: all 4 samples in one batch, the single-file
path, an all-unstampable batch (refused with an explanation, no empty zip), and
re-clicking the download link.

Same-named uploads get `_2` suffixes rather than silently overwriting each other
inside the zip — cheap, and a folder drag from two directories would otherwise
lose a file.

### Left undone

A folder picker (`webkitdirectory`) was not added — it restricts the input to
folders only, and dropping a multi-file selection already covers the use.
