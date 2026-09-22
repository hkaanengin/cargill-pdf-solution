"""`load_workbook()` — sheets by position, columns by header, every cell stripped.

Two kinds of test live here, and the split is deliberate.

**Against the real workbook** — the measured facts from
`vault/architecture/data-layout.md`. These are the numbers a new month's
workbook changes, and they are asserted anyway: they are what proves the loader
reads *this* data correctly, and a replaced workbook should fail loudly here
rather than quietly change what the app stamps.

**Against small synthetic workbooks** — the requirements themselves. R6/R7 are
only really tested by a workbook whose sheets are named wrongly, and R8 only by
one whose columns have moved. Neither can be shown with a file that happens to
be laid out correctly.
"""

import io

import openpyxl
import pytest

from stamper import Family, load_workbook

# Measured 2026-09-22 against `SUBASI FATURA-DEKONT AGUSTOS.xlsx`, and recorded
# in vault/architecture/data-layout.md.
DATA_ROWS = {Family.FATURA: 208, Family.DEKONT: 194}
PO_FILLED = {Family.FATURA: 90, Family.DEKONT: 81}
DUPLICATE_KEYS = {Family.FATURA: 0, Family.DEKONT: 26}

# FATURA row 127, the one PO stored as a string — with a trailing newline.
NEWLINE_PO_KEY = "SUB2026000021626"
NEWLINE_PO_VALUE = "4522320805"


@pytest.fixture(scope="module")
def index(workbook_path):
    """The real workbook, loaded once for the module."""
    return load_workbook(workbook_path)


# --- against the real workbook ------------------------------------------------


def test_both_families_are_indexed(index):
    assert set(index) == {Family.FATURA, Family.DEKONT}


@pytest.mark.parametrize("family", [Family.FATURA, Family.DEKONT])
def test_every_data_row_is_kept(index, family):
    """One list entry per row — including rows whose PO is blank.

    Counting entries rather than keys is the point: in DEKONT the two differ,
    and that difference is what R18's duplicate case is built on.
    """
    rows = sum(len(pos) for pos in index[family].values())
    assert rows == DATA_ROWS[family]


@pytest.mark.parametrize("family", [Family.FATURA, Family.DEKONT])
def test_blank_pos_are_kept_not_skipped(index, family):
    """Over half the rows have no PO, and they must survive the load.

    025 has to tell "key not in the sheet" from "key is there, PO is blank" —
    they are two different messages on the summary screen (R21). A loader that
    skipped blank rows would make them indistinguishable.
    """
    filled = sum(1 for pos in index[family].values() for po in pos if po)
    blank = sum(1 for pos in index[family].values() for po in pos if not po)
    assert filled == PO_FILLED[family]
    assert blank == DATA_ROWS[family] - PO_FILLED[family]


@pytest.mark.parametrize("family", [Family.FATURA, Family.DEKONT])
def test_duplicate_keys_survive_the_load(index, family):
    """26 DEKONT keys sit on two rows each. A flat dict would keep one.

    This is the reason the index is a list per key and the reason 024 comes
    before 025 — R18 cannot refuse a duplicate the loader has already thrown
    away.
    """
    duplicated = [key for key, pos in index[family].items() if len(pos) > 1]
    assert len(duplicated) == DUPLICATE_KEYS[family]


def test_the_six_conflicting_dekont_keys_keep_both_pos(index):
    """Six duplicated keys carry two *different* POs, with nothing to choose by.

    The rest of the 26 duplicate into a blank, or into two blanks. All 26 are
    R18 exceptions either way — but these six are the ones where guessing would
    put a wrong PO on a customs document.
    """
    conflicting = {
        key: pos
        for key, pos in index[Family.DEKONT].items()
        if len(pos) > 1 and all(pos) and len(set(pos)) > 1
    }
    assert len(conflicting) == 6


def test_keys_are_stripped(index):
    """27 FATURA keys carry trailing spaces; unstripped, none would be found."""
    for family in Family:
        for key in index[family]:
            assert key == key.strip(), f"{family}: {key!r}"
            assert key, f"{family}: empty key indexed"


def test_dekont_int_keys_come_back_as_strings(index):
    """DEKONT `Fatura No` is an `int` in the cell — `str()` before `.strip()`."""
    keys = list(index[Family.DEKONT])
    assert all(isinstance(key, str) for key in keys)
    assert all(key.isdigit() for key in keys)


def test_the_one_string_po_loses_its_trailing_newline(index):
    """FATURA row 127 holds `'4522320805\\n'`. `.rstrip(' ')` would not fix it.

    It matters past cosmetics: the PO goes into the stamp and into the output
    filename (R12, R14), and a newline in either is a defect.
    """
    assert index[Family.FATURA][NEWLINE_PO_KEY] == [NEWLINE_PO_VALUE]


def test_a_sample_pdf_resolves_to_its_po(index, sample_pdfs):
    """The end of R1-R8, on the real data: a filename stem finds its row."""
    assert index[Family.FATURA]["SGM2026000010413"] == ["4522142137"]
    assert index[Family.DEKONT]["917031"] == ["4522207293"]
    # ...and the two samples whose row exists with a blank PO — R18's
    # commonest exception, which 025 raises and this loader only records.
    assert index[Family.FATURA]["SGM2026000010415"] == [""]
    assert "SGM2026000010415" in sample_pdfs


def test_accepts_a_stream_and_reads_it_identically(workbook_path, index):
    """The app never has a path — the workbook arrives as an upload (R24)."""
    stream = io.BytesIO(workbook_path.read_bytes())
    assert load_workbook(stream) == index


def test_a_stream_someone_already_read_is_still_loaded(workbook_path, index):
    """A stream left at EOF is rewound rather than parsed from where it sat."""
    stream = io.BytesIO(workbook_path.read_bytes())
    stream.read()
    assert load_workbook(stream) == index


# --- against synthetic workbooks ----------------------------------------------


def _workbook(sheets) -> io.BytesIO:
    """Build an in-memory xlsx. `sheets` is [(title, [row, ...]), ...]."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for title, rows in sheets:
        ws = wb.create_sheet(title=title)
        for row in rows:
            ws.append(row)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def test_sheets_are_taken_by_position_whatever_they_are_called():
    """R6 and R7 together: position decides, and the name is never consulted.

    The titles here are deliberately wrong — the sheet at the FATURA position
    is called `DEKONT`. A loader that matched on names would index this
    backwards; one that gated on them would refuse the file. R7 says it does
    neither.
    """
    src = _workbook([
        ("PIVOT TABLE", []),
        ("DEKONT", [("Fatura No", "PO"), ("SGM1", "111")]),
        ("not a sheet name anyone chose", [("Fatura No", "PO"), ("222222", "333")]),
    ])
    index = load_workbook(src)
    assert index[Family.FATURA] == {"SGM1": ["111"]}
    assert index[Family.DEKONT] == {"222222": ["333"]}


def test_columns_are_found_by_header_not_by_letter():
    """R8. The two columns sit in different places in each sheet, and do in the
    real workbook too — `Fatura No` is column 3 in FATURA, column 5 in DEKONT.
    """
    src = _workbook([
        ("s1", []),
        ("s2", [("Tip", "Fatura No", "Tescil No", "PO"), ("x", "SGM1", "t", "111")]),
        ("s3", [("PO", "Dosya No", "Fatura No"), ("222", "d", "999999")]),
    ])
    index = load_workbook(src)
    assert index[Family.FATURA] == {"SGM1": ["111"]}
    assert index[Family.DEKONT] == {"999999": ["222"]}


def test_po_tarihi_is_not_mistaken_for_po():
    """`PO` is matched exactly. Both sheets carry a `PO Tarihi` beside it, and
    in DEKONT it is `PO TARIHI` — a prefix match would find the date column.
    """
    src = _workbook([
        ("s1", []),
        ("s2", [("Fatura No", "PO Tarihi", "PO"), ("SGM1", "2026-08-01", "111")]),
        ("s3", [("Fatura No", "PO TARIHI", "PO"), ("999999", "2026-08-02", "222")]),
    ])
    index = load_workbook(src)
    assert index[Family.FATURA] == {"SGM1": ["111"]}
    assert index[Family.DEKONT] == {"999999": ["222"]}


def test_headers_are_stripped_before_they_are_matched():
    src = _workbook([
        ("s1", []),
        ("s2", [("  Fatura No ", " PO  "), ("SGM1", "111")]),
        ("s3", [("Fatura No", "PO"), ("999999", "222")]),
    ])
    assert load_workbook(src)[Family.FATURA] == {"SGM1": ["111"]}


def test_rows_without_a_key_are_dropped():
    """Nothing can ever look them up. Blank rows under the data arrive so."""
    src = _workbook([
        ("s1", []),
        ("s2", [("Fatura No", "PO"), ("SGM1", "111"), (None, "222"), ("   ", "333")]),
        ("s3", [("Fatura No", "PO")]),
    ])
    index = load_workbook(src)
    assert index[Family.FATURA] == {"SGM1": ["111"]}
    assert index[Family.DEKONT] == {}


def test_a_missing_column_is_refused_by_position_not_by_name():
    """A workbook this loader cannot read says so. The message names the sheet
    by its position and family — never by the title it found there (R7).
    """
    src = _workbook([
        ("s1", []),
        ("s2", [("Fatura No", "Tescil No"), ("SGM1", "t")]),
        ("s3", [("Fatura No", "PO")]),
    ])
    with pytest.raises(ValueError) as caught:
        load_workbook(src)
    message = str(caught.value)
    assert "'PO'" in message
    assert "Sheet 2" in message and "FATURA" in message
    assert "s2" not in message
