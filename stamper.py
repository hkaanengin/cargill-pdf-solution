"""PO stamping for SGM, SUB and DEKONT customs documents.

The whole of the stamping logic, in one flat module. `app.py` imports it and
the tests import it directly — no Flask, no HTTP and no browser involved in
either case. See `vault/decisions/0011-one-entry-point.md` for why the logic
sits outside the request handlers, and `0012-module-shape-and-test-tooling.md`
for why it is one flat file rather than a package.

**Being filled in, bottom-up.** `route_filename()` (023) and
`load_workbook()` (024) are written. The rest still raise
`NotImplementedError`, each naming the task that owes it and the requirements
in `vault/spec.md` it has to satisfy. Signatures are the shape expected today —
an implementing task refines one if its requirement turns out to say otherwise,
and records that in its own task file.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, NamedTuple

import openpyxl


class Family(StrEnum):
    """A document family, which is also the sheet its key is looked up in.

    The spec ties the two together: R2/R3 route `SGM` and `SUB` names to the
    FATURA sheet, R4 routes all-digit names to DEKONT, and R12a defines the
    stamp position in exactly those terms — "FATURA-routed documents ... and
    DEKONT-routed documents". One value therefore answers both questions, which
    is why `route_filename()` returns it and `stamp()` takes it.

    The sheets are reached **by position** — FATURA is sheet 2, DEKONT is
    sheet 3 — and the name found there is never consulted (R6, R7). These
    members are the app's own vocabulary, not a lookup key into the workbook.
    """

    FATURA = "FATURA"
    DEKONT = "DEKONT"


# key -> every PO found under it, one entry per matching row.
#
# The list is load-bearing. R18 makes a key that matches more than one row an
# exception, and the workbook has 26 such keys in DEKONT (6 of them with
# genuinely different POs) — so the index has to be able to *represent* the
# duplicate before `lookup_po()` can refuse it. The `dict[str, str]` that
# `load_tescil_map()` returns cannot: it silently keeps the last row.
SheetIndex = dict[str, list[str]]
PoIndex = dict[Family, SheetIndex]


class Routed(NamedTuple):
    """What a filename turned out to be: its lookup key, and its family.

    Both halves come out of the same reading of the name, so they are returned
    together — R1 (the key is the stem, verbatim) is then implemented in
    exactly one place. `family is None` is R5: the name matches no pattern and
    no sheet can be chosen for it.

    The key is filled in either way. An unroutable file still has to be named
    on the summary screen (R21), and its key is what the user typed.
    """

    key: str
    family: Family | None


def route_filename(name: str) -> Routed:
    """Return the lookup key for a PDF filename, and the family it belongs to.

    The key is the filename with its extension removed and **nothing else done
    to it** (R1) — no case folding, no trimming of suffixes, no repair of a
    near miss. PDF content is never opened or parsed to obtain it.

    `SGM` and `SUB` prefixes are FATURA (R2, R3); a key that is all digits, of
    any length, is DEKONT (R4). Anything else is unroutable, `family=None`
    (R5).

    Routing and lookup fail differently, and the split matters:
    `SGM2026000011171 (1).pdf` routes *successfully* to FATURA and then fails
    in `lookup_po()`, because its key is not in the sheet. Only a name matching
    none of R2-R4 is unroutable here.

    Case is significant. Every key in the workbook is upper-case, and the user
    has never said a lower-case `sgm…` should be accepted, so it is left
    unroutable rather than quietly folded — the same refusal to repair a near
    miss that R18 makes for lookup.
    """
    key = Path(name).stem

    if key.startswith(("SGM", "SUB")):
        return Routed(key, Family.FATURA)
    if key.isdigit():
        return Routed(key, Family.DEKONT)
    return Routed(key, None)


# The headers R8 locates the two columns by. Matched **exactly**, after
# stripping — not by prefix. Both sheets also carry a `PO Tarihi` / `PO TARIHI`
# column, and a `startswith` would find that one first in DEKONT.
KEY_HEADER = "Fatura No"
VALUE_HEADER = "PO"

# R6, as a zero-based index: "sheet 2 is FATURA, sheet 3 is DEKONT", counting
# from 1. Sheet 1 is the empty `PIVOT TABLE`. The name found at the position is
# never read (R7) — not to match on, not to gate the run, and not in an error
# message.
SHEET_POSITION = {Family.FATURA: 1, Family.DEKONT: 2}


def _text(cell: object) -> str:
    """Every cell arrives through here: `str()` first, then `.strip()` (R10).

    Both halves are load-bearing and each has a real case in this workbook.
    `str()` first, because DEKONT keys come back as `int` and `.strip()` on an
    int raises. `.strip()` bare, because 27 FATURA keys carry trailing spaces
    and one FATURA `PO` is `'4522320805\n'` — a newline `.rstrip(' ')` would
    leave in place.

    `None` becomes `''`. An empty `PO` is normal data — over half the rows —
    and the empty string is how it is carried to `lookup_po()`, which decides
    it is an R18 exception. It is not skipped here, or 025 could not tell a
    blank `PO` from an absent row.
    """
    return "" if cell is None else str(cell).strip()


def _column(header: list[str], wanted: str, family: Family) -> int:
    """The index of `wanted` in the header row — by text, never by letter (R8).

    The workbook is hand-maintained and column order shifts, and it already
    differs between the two sheets: `Fatura No` is the 3rd column in FATURA and
    the 5th in DEKONT. See `vault/decisions/0004-match-columns-by-header.md`.
    """
    try:
        return header.index(wanted)
    except ValueError:
        raise ValueError(
            f"Sheet {SHEET_POSITION[family] + 1} ({family}) has no {wanted!r} "
            f"column. Headers found: {header}"
        ) from None


def _read_sheet(sheet, family: Family) -> SheetIndex:
    """Index one sheet as key -> every PO found under it, one entry per row."""
    rows = sheet.iter_rows(values_only=True)
    try:
        header = [_text(cell) for cell in next(rows)]
    except StopIteration:
        raise ValueError(
            f"Sheet {SHEET_POSITION[family] + 1} ({family}) is empty."
        ) from None

    key_i = _column(header, KEY_HEADER, family)
    po_i = _column(header, VALUE_HEADER, family)

    index: SheetIndex = {}
    for row in rows:
        key = _text(row[key_i]) if key_i < len(row) else ""
        if not key:
            # No key, so nothing could ever look this row up. Trailing blank
            # rows below the data arrive this way.
            continue
        po = _text(row[po_i]) if po_i < len(row) else ""
        index.setdefault(key, []).append(po)
    return index


def load_workbook(src: str | Path | BinaryIO) -> PoIndex:
    """Read the uploaded workbook into a per-family key -> POs index.

    `src` is a file-like object in the app and a path in the tests. The stream
    is the real case: the workbook is uploaded every session (R24) and is never
    written to disk, so nothing here ever sees a filename. The path form exists
    so the suite can point at the copy in the repo.

    Sheets by position, never by name (R6, R7); `Fatura No` and `PO` located by
    header text, never by column letter (R8); `data_only=True` (R9); every cell
    `str()`-ed before it is `.strip()`ed (R10).

    The value is a **list per key**, not a single PO. A key on two rows keeps
    both, so `lookup_po()` can refuse it under R18 — 26 DEKONT keys need this.

    Filled by 024-workbook-access — R6-R10.
    """
    if hasattr(src, "seek"):
        # An upload stream someone has already read would otherwise be parsed
        # from wherever it was left. A workbook is a zip, so a stream that
        # cannot seek could not be read at all.
        src.seek(0)

    workbook = openpyxl.load_workbook(src, data_only=True, read_only=True)
    try:
        return {
            family: _read_sheet(workbook.worksheets[position], family)
            for family, position in SHEET_POSITION.items()
        }
    finally:
        workbook.close()


def lookup_po(index: PoIndex, key: str, sheet: Family) -> str:
    """Return the PO for `key` in `sheet`, or raise the reason it has none.

    The key must match exactly — no normalisation, no near-miss repair (R18).
    Absent key, blank PO and a key matching more than one row are all
    exceptions, each reported with its own reason (R18, R21).

    Filled by 025-po-lookup-and-exceptions — R8, R18. The exception type and
    how a reason reaches the summary screen are 025's to design; nothing is
    declared here so that it is designed once, against the requirement.
    """
    raise NotImplementedError("025-po-lookup-and-exceptions")


def stamp(pdf_bytes: bytes, po: str, family: Family) -> bytes:
    """Return a copy of the PDF with `PO:<po>` drawn on its first page.

    Bold red, 14pt to start from (R12), positioned per family because the two
    layouts look nothing alike (R12a) — the coordinates are settled in
    017-dekont-stamp-placement against the real samples. Page 1 only, whatever
    the page count; DEKONT scans run to two pages (R28).

    Bytes in, bytes out: the source is never touched (R13).

    Filled by 026-stamp-the-po — R11, R12, R12a, R28.
    """
    raise NotImplementedError("026-stamp-the-po")


def verify(pdf_bytes: bytes, po: str) -> bool:
    """Report whether the literal `PO:<po>` is present in the PDF's text.

    Searching for the prefixed form rather than the bare number is deliberate:
    it is what distinguishes this app's stamp from a number that merely happens
    to appear in the document (R17, Q10). Used twice — on the output before it
    is delivered (R17), and on the input to refuse one that is already stamped
    (R18).

    A failure withholds the file; it does not deliver it with a warning (R18).

    Filled by 007-verify-stamp-after-write — R17, R18.
    """
    raise NotImplementedError("007-verify-stamp-after-write")
