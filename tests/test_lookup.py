"""`lookup_po()` — the PO, or the named reason there isn't one.

Two kinds of test, split the same way `test_workbook.py` splits them.

**Against the real workbook** — the cases R18 exists for are all present in it:
two samples whose row carries a blank `PO`, 26 duplicated DEKONT keys, and 27
keys stored with trailing spaces. These are measured facts from
`vault/architecture/data-layout.md`, and a new month's workbook should fail
here loudly rather than quietly change what the app stamps.

**Against hand-built indexes** — `lookup_po()` takes an index, not a file, so
the requirements that the real workbook happens not to exercise are written as
a three-line dict. R18's duplicate rule is per *sheet*, and FATURA has no
duplicates today; only a built index can show the rule is not a DEKONT branch.
"""

import pytest

from stamper import Family, Lookup, Problem, load_workbook, lookup_po, route_filename

# Measured 2026-09-22 against `SUBASI FATURA-DEKONT AGUSTOS.xlsx`.

# The six DEKONT keys on two rows carrying two *different* POs, with nothing in
# either row to choose by — `vault/tasks/done/020-duplicate-dekont-keys.md`.
# These are the ones where guessing puts a wrong PO on a customs document.
CONFLICTING = ["919290", "919303", "919466", "919467", "919468", "919471"]
# A duplicate blank on both rows, and one with a PO on one row and a blank on
# the other. Both are still refused: the app never picks a row.
DUPLICATE_BOTH_BLANK = "919476"
DUPLICATE_ONE_BLANK = "919479"

# Stored as `'SGM2026000010589    '`. 27 FATURA keys carry trailing spaces, and
# the stem of an uploaded PDF never will.
TRAILING_SPACE_KEY = "SGM2026000010589"
TRAILING_SPACE_PO = "4522182196"

# The one PO held as a string, with a trailing newline in the cell.
NEWLINE_PO_KEY = "SUB2026000021626"
NEWLINE_PO_VALUE = "4522320805"

# Samples whose row exists with an empty `PO` — R18's commonest exception.
BLANK_PO_SAMPLES = ["SGM2026000010415", "SGM2026000010416"]


@pytest.fixture(scope="module")
def index(workbook_path):
    """The real workbook, loaded once for the module."""
    return load_workbook(workbook_path)


def resolve(index, filename: str) -> Lookup:
    """Route and look up in one call — how the app resolves a single upload.

    `lookup_po(index, *route_filename(name))` is the whole of it, and writing
    the tests through it is deliberate: it is the call site 029 will have, so a
    signature that stopped composing would fail here first.
    """
    return lookup_po(index, *route_filename(filename))


# --- a key that resolves ------------------------------------------------------


@pytest.mark.parametrize(
    "filename, po",
    [
        ("SGM2026000010413.pdf", "4522142137"),  # R2 — SGM, via FATURA
        ("SGM2026000011171.pdf", "4522207286"),
        ("SUB2026000019889.pdf", "4522207288"),  # R3 — SUB, via FATURA
        ("917031.pdf", "4522207293"),            # R4 — six digits, via DEKONT
        ("917035.pdf", "4522207291"),
    ],
)
def test_a_key_on_one_filled_row_returns_its_po(index, filename, po):
    """The end of R1-R8 and R11: a filename becomes the value to stamp."""
    assert resolve(index, filename) == Lookup(po, None, "")


def test_a_resolved_lookup_carries_no_reason(index):
    """`ok` and `problem` are the same fact. 026 stamps on one, 028 groups on
    the other, and they must never disagree."""
    found = resolve(index, "SGM2026000010413.pdf")
    assert found.ok
    assert found.problem is None
    assert found.message == ""


def test_the_string_po_arrives_without_its_trailing_newline(index):
    """R10 reaches past the loader: this value is stamped (R12) and goes into
    the output filename (R14), and a newline in either is a defect."""
    assert lookup_po(index, NEWLINE_PO_KEY, Family.FATURA).po == NEWLINE_PO_VALUE


def test_a_key_stored_with_trailing_spaces_is_found_by_the_clean_stem(index):
    """27 FATURA rows are stored padded. An uploaded PDF's stem never is, so
    without R10's `.strip()` on the *key* each one is reported as missing."""
    assert lookup_po(index, TRAILING_SPACE_KEY, Family.FATURA).po == TRAILING_SPACE_PO


# --- the key is not there -----------------------------------------------------


def test_a_key_the_sheet_does_not_have_is_named_against_the_workbook(index):
    found = resolve(index, "SGM2026000099999.pdf")
    assert found.po is None
    assert found.problem is Problem.NOT_IN_WORKBOOK
    assert "workbook" in found.message


def test_a_near_miss_is_refused_rather_than_repaired(index):
    """R18, Q11. `SGM2026000011171 (1)` routes to FATURA perfectly well and
    then fails as a key the sheet does not have — no normalisation is
    attempted, and the duplicate-download suffix is not stripped back off."""
    assert resolve(index, "SGM2026000011171.pdf").po == "4522207286"

    near_miss = resolve(index, "SGM2026000011171 (1).pdf")
    assert near_miss.po is None
    assert near_miss.problem is Problem.NOT_IN_WORKBOOK


def test_a_digit_key_of_the_wrong_length_is_simply_missing(index):
    """R4 makes any digit length routable, so `91703` routes to DEKONT and
    fails at lookup rather than being read as a truncated `917031`."""
    found = resolve(index, "91703.pdf")
    assert found.problem is Problem.NOT_IN_WORKBOOK


# --- the row is there, the PO is not ------------------------------------------


@pytest.mark.parametrize("key", BLANK_PO_SAMPLES)
def test_a_row_with_a_blank_po_says_so(index, key):
    """Over half the rows in this workbook have no PO, so this is the common
    path rather than an edge case."""
    found = resolve(index, f"{key}.pdf")
    assert found.po is None
    assert found.problem is Problem.PO_BLANK
    assert "empty" in found.message


def test_a_blank_po_is_not_reported_as_a_missing_key(index):
    """The distinction R21 puts in two separate groups: "your workbook has no
    such row" and "it has the row but nobody filled the PO in" send the user to
    two different places."""
    blank = resolve(index, "SGM2026000010415.pdf")
    missing = resolve(index, "SGM2026000099999.pdf")
    assert blank.problem is not missing.problem


# --- the key is on more than one row ------------------------------------------


@pytest.mark.parametrize("key", CONFLICTING)
def test_the_six_conflicting_dekont_keys_are_refused(index, key):
    """Two rows, two different POs, nothing to choose by. Returning either one
    stamps a wrong PO onto a document that looks perfectly normal — and R17
    would not catch it, because the stamp renders fine. The app never guesses."""
    found = resolve(index, f"{key}.pdf")
    assert found.po is None
    assert found.problem is Problem.DUPLICATE_KEY


def test_a_duplicate_blank_on_both_rows_reports_the_duplicate_not_the_blank(index):
    """This is why the check order in 020 is a requirement. 13 of the 26
    duplicated keys are blank on both rows, so a blank-first implementation
    passes every other duplicate test and still sends the user to look for a
    missing PO instead of a repeated row."""
    found = resolve(index, f"{DUPLICATE_BOTH_BLANK}.pdf")
    assert found.problem is Problem.DUPLICATE_KEY


def test_a_duplicate_with_one_filled_row_is_still_refused(index):
    """"Take the filled one" is a guess the user never authorised — 020. The
    second row exists, and nothing says the blank is the stale one."""
    found = resolve(index, f"{DUPLICATE_ONE_BLANK}.pdf")
    assert found.problem is Problem.DUPLICATE_KEY


def test_the_duplicate_message_names_it_as_a_workbook_problem(index):
    """R21. The fix is an edit to the spreadsheet; nothing about the PDF is
    wrong, and a message that does not say so sends the user to re-export it."""
    message = resolve(index, f"{CONFLICTING[0]}.pdf").message
    assert "workbook" in message
    assert "spreadsheet" in message and "not the PDF" in message
    assert "2 rows" in message


def test_the_duplicate_rule_is_per_sheet_not_a_dekont_branch():
    """FATURA has no duplicated keys in this workbook and nothing guarantees
    next month's — so the rule is written against the sheet that was routed to,
    whichever it is (020)."""
    built = {Family.FATURA: {"SGM1": ["111", "222"]}, Family.DEKONT: {}}
    found = lookup_po(built, "SGM1", Family.FATURA)
    assert found.po is None
    assert found.problem is Problem.DUPLICATE_KEY
    assert "FATURA" in found.message


def test_a_key_on_three_rows_counts_them():
    """Nothing caps a duplicate at two. The message reports what it found."""
    built = {Family.FATURA: {}, Family.DEKONT: {"999999": ["1", "2", "3"]}}
    assert "3 rows" in lookup_po(built, "999999", Family.DEKONT).message


# --- the filename routed nowhere ----------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "scan.pdf",                  # no pattern at all
        "sgm2026000010413.pdf",      # lower case — 023 leaves it unrouted
        "FATURA 917031.pdf",         # a digit key with something in front
        "917031 (1).pdf",            # no longer all digits
        ".pdf",                      # nothing to route
    ],
)
def test_an_unroutable_name_is_an_outcome_like_any_other(index, filename):
    """R5 joins R18 through the same value. 023 left open whether an unroutable
    name became the same kind of exception as a failed lookup; it does — one
    `Lookup`, a different `Problem` — because R21 reports both as "not stamped,
    and here is why" and nothing downstream needs to tell them apart."""
    found = resolve(index, filename)
    assert found.po is None
    assert found.problem is Problem.UNROUTABLE
    assert found.message


def test_an_unroutable_name_never_reaches_the_workbook(index):
    """No sheet was chosen, so there is nothing to look it up in. The reason
    has to be the name, not a claim about the workbook's contents."""
    assert "workbook" not in resolve(index, "scan.pdf").message


# --- invariants ---------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "SGM2026000010413.pdf", "SGM2026000010415.pdf", "919290.pdf", "scan.pdf",
        "", " ", "   .pdf", "SGM.pdf", "0.pdf", "٤٥٢٢.pdf", "SGM" + "9" * 400 + ".pdf",
        "SGM2026000010413.PDF", "SGM2026000010413", "../SGM2026000010413.pdf",
    ],
)
def test_nothing_raises_whatever_the_filename_is(index, filename):
    """R19 as a property, not a promise. One bad upload must never end the run,
    and a returned value cannot unwind a batch the way an uncaught raise can —
    which is why `lookup_po()` returns rather than raises."""
    found = resolve(index, filename)
    assert isinstance(found, Lookup)
    assert found.ok == (found.problem is None)


def test_an_empty_index_answers_rather_than_blowing_up():
    """A workbook whose sheets hold no data rows loads to an empty index. Every
    file then fails lookup and R20 stops the run — with a message, not a 500."""
    found = lookup_po({}, "SGM2026000010413", Family.FATURA)
    assert found.problem is Problem.NOT_IN_WORKBOOK


@pytest.mark.parametrize(
    "filename",
    ["SGM2026000099999.pdf", "SGM2026000010415.pdf", "919290.pdf", "scan.pdf"],
)
def test_every_refusal_carries_a_reason_the_user_can_read(index, filename):
    """R18: the user is told *which* file failed and *why*. The message is a
    fragment meant to follow the filename, so it opens lower case and does not
    end in a stop — 028 owns how it is finally shown."""
    found = resolve(index, filename)
    assert not found.ok
    assert found.message and found.message[0].islower()
    assert not found.message.endswith(".")


def test_every_sample_pdf_is_accounted_for(index, sample_pdfs):
    """R21 over the real inputs: ten files, every one either stamped with a PO
    or named with a reason. Eight resolve; the two blank-PO samples do not."""
    results = {stem: resolve(index, f"{stem}.pdf") for stem in sample_pdfs}
    assert len(results) == 10

    stamped = {stem for stem, found in results.items() if found.ok}
    refused = {stem: found.problem for stem, found in results.items() if not found.ok}
    assert len(stamped) == 8
    assert refused == {key: Problem.PO_BLANK for key in BLANK_PO_SAMPLES}
