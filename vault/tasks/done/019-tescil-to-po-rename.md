---
area: cli
priority: medium
created: 2026-09-20
completed: 2026-09-23
---
# 019 — Retire "Tescil" from the codebase and the vault

Spec reference: **R11**, and the withdrawal of **R27** in [[spec]].

## Problem

`Tescil No` is no longer stamped and is no longer part of the product. The
project is still named after it everywhere:

- `stamp_tescil.py` — the command-line script's filename
- `load_tescil_map()` — the shared workbook parser, used by both entry points
- `VALUE_HEADER = "Tescil No"` and the module docstring
- `CLAUDE.md`'s summary, its data-gotchas section, and most of the vault

**This task also deletes `stamp_tescil.py` outright.** R27 was withdrawn on
2026-09-20: the web app is the only entry point, and the logic moves into a
module the tests import — [[decisions/0011-one-entry-point]]. That removes the
first two bullets above by deletion rather than by renaming.

Left alone this is the worst kind of stale memory: confident, specific, and
wrong. A future session reads "stamps a Tescil No" and believes it.

## Done when

- [x] `stamp_tescil.py` is deleted and the stamping logic lives in a module
      `app.py` imports
- [x] The parser and its docstrings name PO rather than Tescil
- [x] `CLAUDE.md` describes what the project actually does now
- [x] [[architecture/overview]] and [[architecture/data-layout]] match the spec
- [x] Superseded decisions carry a pointer to [[spec]] rather than being deleted —
      the reasoning stays, the claim about current behaviour goes

## Notes

Do this **with** the routing and PO work, not before it. Renaming a function on
one day and changing what it does on another means two passes over the same
lines and a window where the vault describes neither version.

`Tescil No` does not disappear from the *workbook* — it stays a column in both
sheets. What goes is its role as the value this project stamps. (Q1, which
concerned `Tescil No`, was closed on 2026-09-20: `PO` does not share its
cross-sheet behaviour.)

`sgm_folders/` is also now a misnomer — it holds `SUB` and digit-named files
too, and after R27's withdrawal it is a test fixture rather than an input
directory. Rename it here.

## Done — 2026-09-23

- **Code.** `stamp_tescil.py` deleted (nothing imported it after
  [[029-wire-app-to-module]]) and dropped from the Dockerfile's `COPY`. The
  parser was already `stamper.load_workbook()` reading `PO`; the one comment in
  `stamper.py` naming `load_tescil_map()` now calls it retired.
- **`sgm_folders/` → `samples/`.** Chosen to sit beside
  `samples_stamped_reference/`. Updated in `tests/conftest.py`, three test
  docstrings and `.gitignore`. The folder is git-ignored, so this was a plain
  `mv`. The deletion of `stamp_tescil.py` is left unstaged for the user.
- **Notes.** `CLAUDE.md` rewritten at the top and in *Data gotchas*, which
  still said `PO` was empty everywhere, that sheet names were checked, and that
  leading-zero keys were live. [[architecture/overview]] lost the CLI section
  and the automatic download. [[architecture/data-layout]], decisions 0001–0005
  and 0011, and open tasks 001, 004 and 009 got pointers. [[Home]] was
  condensed to current state. Done task files were left as written: they are
  history.
- **Acceptance criteria checked.** One mixed batch through the Flask test client
  with the real workbook: SGM, SUB, 6-digit and 5-digit (`14898`) stamped;
  missing key, blank PO, unroutable, near miss, duplicate key (`919290`,
  `15052`), already stamped, repeat and `.docx` each refused with its reason;
  zip of four, each carrying `PO:<value>` on page 1 only; several uploaded with
  one stamped gave a bare PDF; `samples/` unchanged by hash. Ticked in [[spec]].

### Found along the way

- **An unreadable workbook is already a message**, not a 500 — Q15's table in
  [[spec]] still said otherwise. Corrected. The message is the raw Python
  error and is not translated, which belongs to [[030-workbook-verification]].
- **A near-miss name is reported under its sanitised name.** `secure_filename()`
  turns `SGM2026000011171 (1).pdf` into `SGM2026000011171_1.pdf` before
  `run()` sees it, so the summary lists a name the user never uploaded, under
  *not in workbook*. It is still refused, so R18 holds. The user answered the
  same day: show the real name — R33, built in [[035-uploaded-names-verbatim]].
- **No 4-digit DEKONT key exists** in the workbook, so that acceptance
  criterion cannot be met with real data. It stays unticked.
- **The container was not built.** The Docker daemon was not running, so the
  Dockerfile edit is unverified — [[004-cloud-deployment]].
- **[[009-configurable-stamp-style]] lost its premise:** it adds flags to the
  CLI this task deleted. The user wants no CLI; closed unbuilt.
- `app.secret_key = "sgm-tescil-stamp"` was left alone. Moving it to the
  environment is [[003-auth-and-multi-user]]'s, and renaming it now would only
  log the user out.
