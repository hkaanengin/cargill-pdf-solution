---
area: cli
priority: medium
created: 2026-08-07
completed: 2026-09-08
---
# 006 — Decide how to handle keys missing from the Excel

**Resolved.** The user made the call on 2026-09-08: skip the file, warn by name.
Recorded as [[decisions/0006-skip-missing-keys-with-warning]].

## What was built

- **CLI** (`stamp_tescil.py`): skips collect into a list; each prints a `SKIP`
  line to **stderr** as it happens, and the run ends with a `WARNING:` block
  re-listing every skipped filename. Exit code 2 when anything was skipped.
  Warnings go to stderr so a redirected stdout log can't swallow them.
- **Web** (`app.py`): the missing-key flash changed from category `error` to
  `warn`, reworded to "Skipped X — 'key' was not found in <workbook>". A new
  `.flash.warn` amber style added in `templates/base.html`.

## Done when

- [x] Behaviour decided and recorded in `decisions/`
- [x] CLI implements it, including exit code
- [x] Web path matches the same rule
- [x] Tested with a PDF whose key is deliberately absent

## Verification

Ran the CLI over two real PDFs plus a copy renamed `SGM9999999999999.pdf`:
both real files stamped, the fake one skipped, end-of-run warning listed it,
exit code 2. Clean 4-file run still exits 0.

## What this did not settle

*Why* keys go missing — typo'd filename vs genuinely absent invoice row — is
still unknown, and both are handled identically on purpose. Was open question 5;
no longer blocking anything.

## Follow-on

The web app still handles one PDF per request, so "skip and continue" has nothing
to continue to. The rule only earns its keep once [[002-batch-upload-zip]] lands
— that's where a partial batch needs to report which files came back unstamped.
