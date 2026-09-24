---
area: code
priority: high
created: 2026-09-22
completed: 2026-09-22
---
# 022 — The importable module, and something to test it with

Reference: **[[decisions/0011-one-entry-point]]**, and
**[[decisions/0012-module-shape-and-test-tooling]]** for the shape chosen.

No product requirement asks for this. It is the foundation 0011 calls for — the
logic lives outside the Flask handlers so tests can reach it without a browser,
and every task from [[023-filename-routing]] onwards adds to it. Built first so
the seven that follow have somewhere to land.

## Problem

There is no module and no test framework. `load_tescil_map()` lives in
`stamp_tescil.py`, which R27's withdrawal retires; `app.py` does its stamping
inline in a request handler. `requirements.txt` holds four runtime dependencies
and nothing else, so there is currently no way to assert anything about this
project except by clicking through it.

That is the wrong footing for a product whose worst failure — [[spec]], *Users
and context* — is a plausible-looking wrong document.

## Scope

**This task builds the frame, not the behaviour.** Function bodies can raise
`NotImplementedError`; the following tasks fill them. Nothing in `app.py`
changes here, and `stamp_tescil.py` is not yet deleted — that is
[[019-tescil-to-po-rename]], done last so there is never a window where neither
path works.

The surface to declare, named as [[decisions/0011-one-entry-point]] names it:

| Function | Filled by | Spec |
|---|---|---|
| `route_filename(name)` | [[023-filename-routing]] | R1–R5 |
| `load_workbook(src)` | [[024-workbook-access]] | R6–R10 |
| `lookup_po(index, key, sheet)` | [[025-po-lookup-and-exceptions]] | R8, R18 |
| `stamp(pdf_bytes, po, family)` | [[026-stamp-the-po]] | R11, R12, R12a, R28 |
| `verify(pdf_bytes, po)` | [[007-verify-stamp-after-write]] | R17 |

## Done when

- [x] `stamper.py` exists at the repo root, imports with no Flask present, and
      declares the surface above
- [x] `requirements-dev.txt` adds `pytest`; `requirements.txt` keeps its four
      runtime dependencies and gains nothing — the container image stays lean
- [x] `tests/conftest.py` exposes the real workbook and the ten
      `sgm_folders/` samples as fixtures, so no test hardcodes a path
- [x] `.venv/bin/python3 -m pytest` runs green on at least one real assertion
- [x] `app.py` and `stamp_tescil.py` are untouched

## Notes

The samples are fixtures, not inputs — 0011's last consequence. Tests point at
`sgm_folders/`; the app never reads a directory.

`samples_stamped_reference/` must **not** be wired in as an input fixture. It is
stamp-placement evidence and feeding it to the app is exactly the
already-stamped exception in R18 — [[decisions/0010-destamped-sample-pdfs]].

## What was built — 2026-09-22

Four files, 14 tests, `.venv/bin/python3 -m pytest` green in 0.14s.

- **`stamper.py`** — the five functions, each raising
  `NotImplementedError("<task that owes it>")`, each carrying the requirement
  IDs it has to satisfy in its docstring.
- **`requirements-dev.txt`** — `-r requirements.txt` plus `pytest>=8.0`.
  `requirements.txt` is byte-for-byte unchanged.
- **`tests/conftest.py`** — `repo_root`, `workbook_path`, `samples_dir`,
  `sample_pdfs` (stem → Path, discovered by glob rather than listed),
  `sample_path(stem)` and `sample_bytes(stem)`.
- **`tests/test_frame.py`** and **`tests/test_fixtures.py`** — the surface
  exists and imports without Flask; every filename shape has a sample; sheet 2
  is FATURA and sheet 3 is DEKONT; both sheets carry `Fatura No` and `PO`.

## Findings

**`.venv/` did not exist.** `CLAUDE.md` documents it and every command in the
project assumes it, but there was no virtualenv in the repo — `openpyxl` was
not importable from any interpreter on the machine. Created it (Python 3.13.2)
and installed both requirement files. Nothing was wrong with the documentation;
the directory was simply absent, which is what an untracked `.venv/` does when
a repo moves. Worth knowing for [[004-cloud-deployment]]: the only environment
this has ever run in is a developer's laptop.

**A fourth file was needed: `pytest.ini`.** `stamper.py` is a flat file at the
repo root, not an installed package, so `import stamper` from `tests/` does not
resolve on its own — pytest puts the *test* directory on `sys.path`, not the
root. `pytest.ini` sets `pythonpath = .` and `testpaths = tests`. Declarative,
and it beats a `sys.path` insertion at the top of `conftest.py`.

**The index shape is declared, and it is the thing 024 must honour.**

```python
SheetIndex = dict[str, list[str]]        # key -> every PO under it, one per row
PoIndex = dict[Family, SheetIndex]
```

The list is load-bearing and is the answer to the problem [[_index]] flagged
during the breakdown: a flat `dict[str, str]` — what `load_tescil_map()`
returns — silently keeps the last row, so [[025-po-lookup-and-exceptions]]
could never see the 26 duplicated DEKONT keys it has to refuse under R18.
Declaring it in the frame means 024 cannot accidentally rebuild the flat one.

**One `Family` enum serves as both the sheet selector and the stamp family.**
`route_filename()` returns it and `stamp()` takes it. That is not a shortcut —
R12a defines the two stamp positions *as* "FATURA-routed" and "DEKONT-routed"
documents, so the routed sheet and the page layout are the same distinction
wearing two names. Its members are the app's own vocabulary, never matched
against a sheet name in the workbook (R7). An engineering choice, not a
requirement; small enough to live here rather than in `decisions/`.

**No exception type was declared, deliberately.** R18 has seven exception cases
and each needs a reason that reaches the summary screen (R21). Designing that
hierarchy here would be designing [[025-po-lookup-and-exceptions]]'s work
ahead of it, against requirements this task has not read closely. `lookup_po()`
says in its docstring that the type is 025's to choose.

**`samples_stamped_reference/` is not exposed, and `conftest.py` says why.**
[[007-verify-stamp-after-write]] will want those six files — as the thing being
refused, under a fixture name that says so. Left out here so the suite is never
quietly reaching for them as inputs.

**One test asserts what the fixtures are, not what the app does.**
`test_workbook_sheets_sit_where_position_says` checks that sheet 2 is named
FATURA and sheet 3 DEKONT. That is not R7 creeping back in — the app still
never consults a name. The suite checks it once, here, precisely so that every
later test can trust position without looking.

**Checked 0012's consequence: the Dockerfile installs `-r requirements.txt`
only**, no glob, so `pytest` stays out of the image. But its
`COPY stamp_tescil.py app.py ./` does not mention `stamper.py` — noted in
[[029-wire-app-to-module]], which is where the container would otherwise break.
