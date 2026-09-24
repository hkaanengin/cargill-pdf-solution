"""PO stamping for SGM, SUB and DEKONT customs documents.

The whole of the stamping logic, in one flat module. `app.py` imports it and
the tests import it directly — no Flask, no HTTP and no browser involved in
either case. See `vault/decisions/0011-one-entry-point.md` for why the logic
sits outside the request handlers, and `0012-module-shape-and-test-tooling.md`
for why it is one flat file rather than a package.

**Being filled in, bottom-up.** `route_filename()` (023), `load_workbook()`
(024), `lookup_po()` (025), `stamp()` (026) and `verify()` (007) are written,
which is the whole of the surface 022 declared. Naming and packaging the
output (027) sit on top of them, and `run()` with `summarise()` (028) put the
whole batch together. What is left is wiring `app.py` to it, 029. A task that
refines a signature records that in its own task file.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, NamedTuple
from zipfile import ZIP_DEFLATED, ZipFile

import openpyxl
import pymupdf


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
# duplicate before `lookup_po()` can refuse it. The `dict[str, str]` the
# retired `load_tescil_map()` returned could not: it silently kept the last row.
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
    # Only the extension is cut. `Path(name).stem` would also drop any folder
    # part, so `../x/SGM….pdf` would route as `SGM…` and stamp; cut this way,
    # its key keeps the `../x/` and is unroutable. The app passes names as
    # uploaded (R33), so this is what keeps a name from shaping a path.
    suffix = Path(name).suffix
    key = name[: -len(suffix)] if suffix else name

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


class Problem(StrEnum):
    """Why a file was not stamped — one member per group on the summary screen.

    R21 groups a run's outcomes, so a reason needs an identity to group on as
    well as a sentence to show. The member is the first and `Lookup.message` is
    the second; the values are slugs rather than prose, so that rewording a
    message can never quietly change a grouping.

    All nine of R18's exception cases are covered. Four are decided at
    lookup: R5's unroutable filename, which `route_filename()` detects and
    `lookup_po()` reports; a missing key; a duplicated key; and a blank `PO`.
    The near miss has no member of its own, because
    `SGM2026000011171 (1)` is simply a key the sheet does not have (Q11). Two
    are decided around the stamp by `stamp_checked()`: an input that already
    carries one, and a stamp that cannot be found after it is drawn. The last
    is decided across the batch by `repeated_upload()`: a filename already
    seen in this run. And before any of them, `not_a_pdf()` refuses a file
    whose name does not end `.pdf` (Q16).
    """

    UNROUTABLE = "unroutable"
    NOT_IN_WORKBOOK = "not-in-workbook"
    DUPLICATE_KEY = "duplicate-key"
    PO_BLANK = "po-blank"
    ALREADY_STAMPED = "already-stamped"
    STAMP_NOT_VERIFIED = "stamp-not-verified"
    REPEATED_UPLOAD = "repeated-upload"
    NOT_A_PDF = "not-a-pdf"


class Lookup(NamedTuple):
    """A PO to stamp, or the named reason there is none. Never both.

    Returned rather than raised, deliberately. R19 says one bad file never
    stops the rest of the batch, and a returned value cannot unwind anything —
    an exception can, the moment a caller forgets to catch it, and the caller
    here is a loop over whatever the user uploaded. `po` is `None` whenever
    `problem` is set, so there is nothing for a caller to stamp on a file the
    app has already refused.

    `problem` is what the summary screen groups on; `message` is what it shows
    (R21). The message is a fragment meant to follow the filename —
    "917031.pdf — on 2 rows of the DEKONT sheet…" — so it opens lower case and
    carries no final stop. How it is finally presented belongs to 028.
    """

    po: str | None
    problem: Problem | None
    message: str
    # The values the message was built from (`sheet`, `rows`), so the app can
    # say the same thing in another language (R31). Empty when there are none.
    details: dict | None = None

    @property
    def ok(self) -> bool:
        """True when there is a PO to stamp."""
        return self.problem is None


def lookup_po(index: PoIndex, key: str, sheet: Family | None) -> Lookup:
    """Return the PO for `key` in `sheet`, or the named reason it has none.

    Takes a `Routed` as it comes: `lookup_po(index, *route_filename(name))` is
    the whole of resolving one file, and `sheet=None` is R5's unroutable
    filename rather than a caller error. That answers the question 023 left
    open — an unroutable name and a failed lookup are the same kind of outcome,
    one value carrying a different `Problem`, because R21 reports them the same
    way and nothing downstream needs to tell them apart.

    The key must match exactly. No case folding, no trimming, no repair of a
    near miss: `SGM2026000011171 (1)` routes to FATURA and then fails here as a
    key the sheet does not have (R18, Q11).

    **The order of the three checks is the requirement, not an implementation
    detail** (020). A duplicated key is refused before its `PO` is looked at,
    because 13 of the 26 duplicated DEKONT keys are blank on both rows and 7 on
    one of them — reporting "the PO is empty" for a key that appears twice
    sends the user to look in the wrong place. And the rule is written per
    sheet, never as a DEKONT special case: FATURA has no duplicates in this
    workbook, and nothing guarantees next month's.

    Filled by 025-po-lookup-and-exceptions — R8, R18, R19, R21. Closes
    020-duplicate-dekont-keys.
    """
    if sheet is None:
        return Lookup(
            None,
            Problem.UNROUTABLE,
            "the filename is not an SGM…, SUB… or all-digit name, so there is "
            "no sheet to look it up in",
        )

    # Two `.get()`s rather than `index[sheet][key]`. A family missing from the
    # index can only be a hand-built one, and "not in the workbook" is still a
    # true answer for it; inside a request that is the difference between a
    # message and a 500.
    rows = index.get(sheet, {}).get(key, [])

    if len(rows) > 1:
        return Lookup(
            None,
            Problem.DUPLICATE_KEY,
            f"on {len(rows)} rows of the {sheet} sheet — a data-entry problem "
            f"in the workbook, so the fix is in the spreadsheet, not the PDF",
            {"sheet": str(sheet), "rows": len(rows)},
        )
    if not rows:
        return Lookup(
            None,
            Problem.NOT_IN_WORKBOOK,
            f"not in the {sheet} sheet of the uploaded workbook",
            {"sheet": str(sheet)},
        )
    if not rows[0]:
        return Lookup(
            None,
            Problem.PO_BLANK,
            f"found in the {sheet} sheet, but its PO cell is empty",
            {"sheet": str(sheet)},
        )
    return Lookup(rows[0], None, "")


# R12: the stamp's text and look. `helvetica-bold` is one of PDF's base-14
# fonts, so nothing is embedded and the scans with no text layer take it the
# same as the born-digital e-Faturas.
STAMP_PREFIX = "PO:"
STAMP_FONT = "helvetica-bold"
STAMP_SIZE = 14
STAMP_COLOR = (1, 0, 0)

# R12a: the baseline the stamp starts at, per family, in absolute points from
# the top-left of an A4 page. Measured against every clean sample in 017 and
# approved by the user — `vault/decisions/0014-stamp-placement-per-family.md`.
# FATURA sits in the free top band right of the logo; DEKONT in the mid-page
# band under the line-item table, clear of its header block.
STAMP_POSITION = {
    Family.FATURA: (300, 45),
    Family.DEKONT: (220, 475),
}


def stamp_text(po: str) -> str:
    """The literal stamp for `po` — what `stamp()` draws and `verify()` seeks."""
    return f"{STAMP_PREFIX}{po}"


def stamp(pdf_bytes: bytes, po: str, family: Family) -> bytes:
    """Return a copy of the PDF with `PO:<po>` drawn on its first page.

    Bold red, 14pt (R12), at the family's own position (R12a). Page 1 only,
    whatever the page count (R28) — page 2 of a DEKONT is a separate
    `TAHSİLAT MAKBUZU` receipt, not a continuation.

    Drawn with `insert_text`, never `insert_textbox` (R12a). A text box wraps
    what does not fit, and a wrapped last digit is exactly the defect in the
    manual process's `917034`: a document that looks stamped and carries the
    wrong PO. `insert_text` draws one line, so that cannot happen here.

    `po` is always a real value. `lookup_po()` refuses every blank and every
    duplicate before a caller gets this far, so there is no empty case to
    handle. Whether the text actually rendered is not checked here — that is
    `verify()`, which runs before anything is delivered (R17).

    Bytes in, bytes out: the source is never touched (R13), and nothing is
    written to disk (R23).

    Filled by 026-stamp-the-po — R11, R12, R12a, R28.
    """
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        doc[0].insert_text(
            STAMP_POSITION[family],
            stamp_text(po),
            fontname=STAMP_FONT,
            fontsize=STAMP_SIZE,
            color=STAMP_COLOR,
        )
        return doc.tobytes()


# Any `PO:` stamp, whoever drew it: `PO:` followed by a digit, with no letter
# straight before it. The manual process stamps in black or grey, in
# MinionPro, Arial or Tahoma, so style is no help. Only the text is. Matched
# case-sensitively, and a word like `DEPO:` does not count, because a Turkish
# document can contain one. None of the ten clean samples contains `po:` in
# any case.
_ANY_STAMP = re.compile(r"(?<!\w)PO:\s*\d")


def _page_text(page) -> str:
    """The page's text, clipped to the page, the way PyMuPDF reads it by default.

    The clipping matters. Text drawn off the page is not returned at all, and
    text that runs off an edge comes back cut short (`P`, not `PO:…`). So
    finding the whole stamp also shows it landed on the page. That catches
    the off-page coordinates 008 worries about, without a separate check.
    """
    return page.get_text()


def verify(pdf_bytes: bytes, po: str) -> bool:
    """Report whether `PO:<po>` is on the first page, whole and on one line.

    The prefixed form rather than the bare number (R17, Q10): it is what
    tells this app's stamp apart from a number that merely appears in the
    document. The match must stop at the last digit. Otherwise a stamp of
    `PO:45222072` would pass a check for `PO:452220729`, and so would the
    reverse. Extracted text keeps line breaks, so a stamp whose last digit
    wrapped fails. `917034`'s manual stamp is exactly that defect.

    Page 1 only, because that is the only page a stamp may be on (R28). A
    stamp that ended up anywhere else is as wrong as a missing one.

    Filled by 007-verify-stamp-after-write — R17.
    """
    wanted = re.compile(re.escape(stamp_text(po)) + r"(?!\d)")
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return bool(wanted.search(_page_text(doc[0])))


def already_stamped(pdf_bytes: bytes) -> bool:
    """Report whether the input already carries a `PO:` stamp, on any page.

    R18 refuses such a file rather than stamp it twice (Q9). The rule is any
    `PO:` followed by digits, not this file's PO. A stamp carrying a
    *different* PO is the worse case, since a second stamp would leave the
    document naming two POs.

    Every page is searched, not just page 1. A stamp is wrong anywhere, and
    this is looking for somebody else's mistake, which need not follow R28.

    Filled by 007-verify-stamp-after-write — R18. Split from `verify()`, which
    022 expected to serve both uses: the two questions differ in which PO they
    look for and in which pages they search.
    """
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return any(_ANY_STAMP.search(_page_text(page)) for page in doc)


class Stamped(NamedTuple):
    """A verified stamped copy, or the named reason there is none. Never both.

    Shaped like `Lookup` and for the same reason: returned rather than raised,
    so that one bad file cannot stop the batch (R19). `pdf` is `None` whenever
    `problem` is set. That is what "withheld" means (R18): there are no bytes
    a caller could deliver by mistake.
    """

    pdf: bytes | None
    problem: Problem | None
    message: str
    details: dict | None = None  # as on `Lookup`: `stamp`, for R31

    @property
    def ok(self) -> bool:
        """True when there is a verified PDF to deliver."""
        return self.problem is None


def stamp_checked(pdf_bytes: bytes, po: str, family: Family) -> Stamped:
    """Stamp a PDF, with R18's check before and R17's check after.

    This is the only way the app should call `stamp()`. Called bare,
    `stamp()` would stamp an already-stamped input and return a copy nobody
    has looked at.

    Filled by 007-verify-stamp-after-write — R17, R18, R19.
    """
    if already_stamped(pdf_bytes):
        return Stamped(
            None,
            Problem.ALREADY_STAMPED,
            "already carries a PO: stamp, so it was not stamped a second time",
        )
    out = stamp(pdf_bytes, po, family)
    if not verify(out, po):
        return Stamped(
            None,
            Problem.STAMP_NOT_VERIFIED,
            f"was stamped, but {stamp_text(po)} could not be found on page 1 "
            f"afterwards, so the file was withheld",
            {"stamp": stamp_text(po)},
        )
    return Stamped(out, None, "")


def output_name(filename: str, po: str) -> str:
    """The delivered name for a stamped file: `PO<po>-<original filename>` (R14).

    `SGM2026000010461.pdf` with PO `4522142137` becomes
    `PO4522142137-SGM2026000010461.pdf`. The original name is kept verbatim,
    extension included, so the key can still be read back out of it.

    Filled by 027-output-naming-and-packaging — R14.
    """
    return f"PO{po}-{filename}"


def not_a_pdf(filename: str) -> Lookup | None:
    """Refuse a file whose name does not end `.pdf`, or `None` if it does.

    R18, closing Q16: never expected, but if it happens the file is ignored
    and reported, and the batch goes on. Decided by the extension alone. The
    file is never opened to find out. Without this check,
    `SGM2026000010413.docx` routes, looks up, and then fails to open as a PDF,
    which loses the whole batch (R19). Case is ignored, so `.PDF` passes. That
    is what `app.py` already did, and it is marked as inference in the spec.

    Filled by 028-summary-screen-and-run-flow — R18, R19.
    """
    if filename.lower().endswith(".pdf"):
        return None
    return Lookup(None, Problem.NOT_A_PDF, "is not a PDF, so it was ignored")


def repeated_upload(filename: str, seen: set[str]) -> Lookup | None:
    """Refuse a filename already uploaded in this batch, or record it as seen.

    R18: the first copy goes on as normal, and every later copy is refused.
    Nothing is renamed. That is also what keeps output names unique. Name is
    `PO<po>-<filename>`, and one filename always gives one PO, so the only
    way two outputs could share a name is the same filename twice.

    Returned as a `Lookup`, so a repeat is grouped and shown exactly like a
    failed lookup (R21). Call it before `lookup_po()`, with the same filename
    the key is derived from. `seen` belongs to the caller and lasts one batch.

    Filled by 027-output-naming-and-packaging — R18. Replaces `app.py`'s
    `unique_name()`, which suffixed the copy with `_2` instead.
    """
    if filename in seen:
        return Lookup(
            None,
            Problem.REPEATED_UPLOAD,
            "was uploaded more than once in this batch; the first copy was "
            "processed and this one was not",
        )
    seen.add(filename)
    return None


class Download(NamedTuple):
    """What the user downloads at the end of a run: a name, bytes, a type."""

    name: str
    data: bytes
    mimetype: str


def package(stamped: list[tuple[str, bytes]], now: datetime | None = None) -> Download | None:
    """Package the run's stamped files for download, or `None` if there are none.

    `stamped` is `(output name, PDF bytes)` per file that passed
    `stamp_checked()`, in upload order. One file is a bare PDF, and two or
    more are a zip (R15). Only the stamped count matters. Several uploaded
    with only one stamped is still a bare PDF, as confirmed by the user on
    2026-09-22. The zip holds the PDFs and nothing else. There is no
    manifest (R16 withdrawn). It is named `stamped_<YYYYMMDD_HHMMSS>.zip`.

    Nothing stamped returns `None`, never an empty zip. R20 says that run
    offers no download, and 028 reports it.

    Two entries with one name raise `ValueError`. `repeated_upload()` makes
    that impossible for a correct caller. So it is a bug in the caller, not
    something a user can upload. `ZipFile` would otherwise write both entries
    and only warn.

    Filled by 027-output-naming-and-packaging — R15, R16, R20.
    """
    if not stamped:
        return None
    if len(stamped) == 1:
        name, data = stamped[0]
        return Download(name, data, "application/pdf")

    names = [name for name, _ in stamped]
    if len(set(names)) != len(names):
        raise ValueError(f"Two stamped files share an output name: {names}")

    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as z:
        for name, data in stamped:
            z.writestr(name, data)
    when = now or datetime.now()
    return Download(f"stamped_{when:%Y%m%d_%H%M%S}.zip", buf.getvalue(), "application/zip")


class Outcome(NamedTuple):
    """What happened to one uploaded file: one line of the summary screen (R21).

    `po` and `output` are set only when the file was stamped and delivered.
    `problem` and `message` are set only when it was not. Never both, the
    same contract as `Lookup` and `Stamped`, which it is built from.
    """

    filename: str
    po: str | None
    output: str | None
    problem: Problem | None
    message: str
    details: dict | None = None  # carried from `Lookup` / `Stamped`, for R31

    @property
    def ok(self) -> bool:
        """True when this file is in the download."""
        return self.problem is None

    @property
    def stamp(self) -> str:
        """The stamp it received, `PO:<po>`, which is how R21 names it."""
        return stamp_text(self.po) if self.po else ""


class Run(NamedTuple):
    """A whole batch: every input's outcome in upload order, and the download.

    `download is None` is R20: nothing was stamped, so nothing is offered.
    """

    outcomes: list[Outcome]
    download: Download | None

    @property
    def stamped(self) -> int:
        return sum(o.ok for o in self.outcomes)


def run(index: PoIndex, files: list[tuple[str, bytes]], now: datetime | None = None) -> Run:
    """Stamp a batch of `(filename, PDF bytes)`, one `Outcome` per input.

    The whole per-file path, in the order each check has to run:
    `not_a_pdf()` first, so nothing after it ever opens a file that is not a
    PDF, then `repeated_upload()`, so a repeat is refused before its key is
    looked up, then `lookup_po()`, then `stamp_checked()`, which is the only way
    `stamp()` is ever called. Every refusal is a returned value, so nothing in
    the loop can stop the batch (R19). Every input gets exactly one outcome,
    which is what lets the summary account for all of them (R21).

    `filename` is the name the key is derived from. The app passes it exactly
    as uploaded (R33).

    Filled by 028-summary-screen-and-run-flow — R18, R19, R20, R21.
    """
    seen: set[str] = set()
    outcomes: list[Outcome] = []
    stamped: list[tuple[str, bytes]] = []
    for filename, pdf_bytes in files:
        routed = route_filename(filename)
        lookup = (
            not_a_pdf(filename)
            or repeated_upload(filename, seen)
            or lookup_po(index, *routed)
        )
        if not lookup.ok:
            outcomes.append(
                Outcome(filename, None, None, lookup.problem, lookup.message, lookup.details)
            )
            continue
        result = stamp_checked(pdf_bytes, lookup.po, routed.family)
        if not result.ok:
            outcomes.append(
                Outcome(filename, None, None, result.problem, result.message, result.details)
            )
            continue
        output = output_name(filename, lookup.po)
        stamped.append((output, result.pdf))
        outcomes.append(Outcome(filename, lookup.po, output, None, ""))
    return Run(outcomes, package(stamped, now=now))


# The order R21 lists its groups in: stamped first, then the two reasons it
# names, then every other R18 reason. `None` is the stamped group.
SUMMARY_ORDER: tuple[Problem | None, ...] = (
    None,
    Problem.NOT_IN_WORKBOOK,
    Problem.PO_BLANK,
    *(p for p in Problem if p not in (Problem.NOT_IN_WORKBOOK, Problem.PO_BLANK)),
)


def summarise(outcomes: list[Outcome]) -> list[tuple[Problem | None, list[Outcome]]]:
    """Group a run's outcomes for the summary screen (R21), empty groups left out.

    Groups come in `SUMMARY_ORDER`. Within a group, files keep their upload
    order. Every outcome lands in exactly one group, because the key is its
    `problem` and `None` means stamped. Each R18 reason past the two R21
    names gets a group of its own, and each file in it still carries its own
    message.

    Filled by 028-summary-screen-and-run-flow — R21.
    """
    groups = {key: [o for o in outcomes if o.problem is key] for key in SUMMARY_ORDER}
    return [(key, group) for key, group in groups.items() if group]
