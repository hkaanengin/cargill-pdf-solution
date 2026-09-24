---
area: data
priority: high
created: 2026-09-22
completed: 2026-09-22
---
# 024 — Read the workbook: by position, by header, stripped

Spec reference: **R6**, **R7**, **R8**, **R9**, **R10**.

## Problem

`load_tescil_map()` breaks four of these five requirements. It selects the sheet
**by name** (`wb["FATURA"]`, raising if absent) where R6/R7 say position and say
the name is not consulted at all; it reads only one sheet where two are needed;
it reads `Tescil No` (R11); and it returns a flat `dict[str, str]`.

## The flat dict is the important one

`mapping[str(key).strip()] = str(val).strip()` **silently overwrites** on a
repeated key. 26 DEKONT keys appear on two rows each and 6 of those pairs carry
different POs — so a flat dict keeps whichever row was read last and there is no
way, afterwards, to know a second row existed. [[025-po-lookup-and-exceptions]]
cannot implement R18's duplicate case on top of that structure.

**So the return value must preserve every matching row per key,** not one value
per key. That is this task's central design decision and the reason it comes
before 025.

## Scope

Given a workbook path or upload stream, return an index for both sheets. No
routing, no stamping, no exception policy — 025 decides what a key's rows
*mean*.

## Done when

- [x] Sheets are taken **by position** — sheet 2 FATURA, sheet 3 DEKONT (R6) —
      and the name is never read, matched on, or used to gate the run (R7)
- [x] `Fatura No` and `PO` are located **by header text** in row 1 (R8), not by
      letter — [[decisions/0004-match-columns-by-header]]
- [x] Opened with `data_only=True` (R9)
- [x] Every cell read as `str(cell).strip()` — never `cell.strip()`, because
      DEKONT keys are `int` and one FATURA `PO` is the string `'4522320805\n'`
      (R10)
- [x] The index preserves **all** rows per key, so duplicates survive to 025
- [x] Accepts a file-like object as well as a path — the app passes an upload
      stream and nothing is written to disk (R24)
- [x] Tests against the real workbook assert the measured counts from
      [[architecture/data-layout]]: 208 FATURA / 194 DEKONT data rows, `PO`
      filled in 90 / 81, and 26 duplicated DEKONT keys
- [x] A test asserts the trailing newline on FATURA row 127's `PO` is gone

## Notes

Over half of all rows have an empty `PO` — 118/208 and 113/194. Empty is
**normal data**, not corruption: the index records it as empty and 025 decides
it is an exception (R18). Do not skip those rows on load, or 025 cannot tell
"row absent" from "row present, PO blank" — two different messages on the
summary screen (R21).

`Tescil No` stays a column in the workbook; it simply stops being read.

---

## Done — 2026-09-22

`load_workbook()` is implemented in `stamper.py` with three helpers — `_text()`,
`_column()` and `_read_sheet()` — and `tests/test_workbook.py` covers it in 20
tests. The suite is **50 green**. The `load_workbook` case in
`tests/test_frame.py` was deleted, which is what that file's docstring says to
do when a stub is filled.

### The contract 025 inherits

`load_workbook()` returns `dict[Family, dict[str, list[str]]]` — the shape 022
declared, now filled. Three properties of it are decisions, not accidents, and
[[025-po-lookup-and-exceptions]] is built on all three:

- **A blank `PO` is carried as the empty string `''`, in the list, in order.**
  It is not dropped and it is not `None`. So `index[f][key] == ['']` means *the
  row is there and its PO is blank* (R18's commonest case, 118/208 and 113/194
  rows), while `key not in index[f]` means *no such row* (R18's other case).
  Those are two different messages on the summary screen (R21), and collapsing
  them here would make them indistinguishable there.
- **One list entry per row, always.** `len(pos) > 1` is R18's duplicate, with no
  further reading needed.
- **Every key is already stripped and non-empty.** A row whose `Fatura No` cell
  is empty is dropped at load — nothing could ever look it up — so 025 never
  has to think about a blank key.

### What the workbook turned out to hold

Measured while writing the tests, all against
`SUBASI FATURA-DEKONT AGUSTOS.xlsx`:

- **27 FATURA keys carry trailing spaces** — `'SGM2026000010589    '`. This was
  not previously written down anywhere. R10's `.strip()` is load-bearing on the
  **key**, not only on the value: without it, 27 of 208 FATURA rows are
  unfindable and every one of them would be reported as a missing key. Added to
  [[architecture/data-layout]].
- **The 26 duplicated DEKONT keys are not all the same problem.** Six carry two
  genuinely different POs, **seven** pair a PO with a blank, and **thirteen**
  are blank on both rows. All 26 are R18 exceptions regardless — the
  requirement is "matches more than one row", not "matches two different POs" —
  but 025 may want to say *why* differently, and the six are the ones where
  guessing would put a wrong PO on a customs document. The "6 of those pairs"
  in [[architecture/data-layout]] was right; it was only ever counting the
  conflicting ones.
- **`PO` must be matched exactly, never by prefix.** Both sheets carry a second
  column starting `PO` — `PO Tarihi` in FATURA, `PO TARIHI` in DEKONT — and in
  FATURA it sits *immediately after* `PO`. A `startswith` match is a plausible
  mistake that would stamp a date. There is a test for it.
- **The two sheets' columns really are in different places.** `Fatura No` is
  column 3 in FATURA and column 5 in DEKONT; `PO` is column 14 and column 12.
  R8 is not hypothetical — a by-letter loader cannot read both sheets.
- No key is `None` in either sheet, and no row is short. Both are guarded
  anyway; both are one line.

### Two choices worth naming

- **A missing `Fatura No` or `PO` column raises `ValueError`**, naming the
  sheet by **position and family** and listing the headers it did find — never
  by the title it read there, which R7 forbids. There is no requirement
  covering a workbook that lacks the columns: [[spec]] Q12 dropped malformed
  inputs from scope entirely, so this is not built *for*, it is simply what
  happens, and it happens legibly. Flagged as an implementation choice, **not**
  an inferred requirement. If the user wants a malformed workbook handled as a
  first-class case rather than an exception, that is a new requirement.
- **A file-like `src` is `seek(0)`-ed before it is opened.** An upload stream
  that something has already read would otherwise be parsed from wherever it
  was left. A workbook is a zip, so a stream that cannot seek could not be read
  at all — no guard is needed beyond `hasattr`. This exists for
  [[029-wire-app-to-module]]: the app's workbook never touches disk (R24), and
  the user restated on 2026-09-22 that the app reads the uploaded file and
  nothing else — no filename, no path, no sheet-name matching. Tested.

### Not done here, on purpose

No routing, no exception policy, no messages. `lookup_po()` still raises
`NotImplementedError`. 025 owns what a key's rows *mean* — including the
question inherited from [[023-filename-routing]], whether R5's unroutable name
becomes the same exception type as a failed lookup.
