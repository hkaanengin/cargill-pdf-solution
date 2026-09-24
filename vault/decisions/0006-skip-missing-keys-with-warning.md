---
created: 2026-09-08
---
# 0006 — A key missing from the Excel skips the file, loudly

When a PDF's key has no matching `Fatura No` in the workbook, the file is **not
stamped** and the user is **warned by name**. The run continues.

- **CLI:** a `SKIP` line per file on **stderr**, then a `WARNING:` block at the
  end listing every skipped filename. Exit code **2** if anything was skipped,
  0 otherwise.
- **Web:** an amber `warn` flash naming the file and the key it looked for. No
  PDF is returned for that file.

## Why

The user's call, 2026-09-08, asked directly: *"it should skip it but gives out a
warning saying that X name was not found in the excel."*

Skipping keeps a run of many files from dying on one bad filename. The warning is
what makes skipping safe — the failure mode this guards against is a silent skip
inside a large batch, where unstamped files go out the door looking like the
stamped ones. So the skip is repeated at the end of the run rather than only at
the moment it happens: a single line 180 files back has scrolled away.

Warnings go to **stderr** so a redirected stdout log never swallows them, and the
non-zero exit code means a script wrapping the CLI can notice.

## Rejected

- **Hard error on the first missing key.** Impossible to miss, but one typo'd
  filename stops a 200-file run. Too brittle for a batch tool.
- **`output/_unstamped.txt` report file.** This was the leaning in
  [[006-missing-key-handling]] before the user's call. It leaves a durable
  artifact, but the user asked for a warning and nothing more; the end-of-run
  block plus exit code covers the same failure without adding a file to manage.
  Worth revisiting if runs ever get big enough that terminal output is not read
  — the web batch flow ([[002-batch-upload-zip]]) is where that will bite first.

## Not settled by this

*Why* a key goes missing — a typo'd filename vs a genuinely absent invoice row —
is still unknown, and the behaviour above is deliberately the same for both. If
the two ever need different handling, that is a new decision.
