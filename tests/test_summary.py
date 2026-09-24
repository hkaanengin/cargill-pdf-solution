"""`run()`, `summarise()` and `templates/result.html`: the end of a run.

R21 asks for a summary that accounts for **every** input, grouped by outcome,
naming the PO each stamped file received. R19 says a refusal never stops the
batch, and R20 says a run with nothing stamped offers no download and says so.
R29 step 6 puts the summary and the download on one screen.

The template is rendered headless, through Flask's own Jinja environment, so
it is tested before 029 wires a route to it.
"""

from datetime import datetime

import pytest
from flask import render_template, session

from app import app
from stamper import (
    SUMMARY_ORDER,
    Outcome,
    Problem,
    Run,
    load_workbook,
    package,
    run,
    summarise,
    verify,
)

NOW = datetime(2026, 9, 23, 10, 0, 0)

# One file per outcome the samples can produce. The refused-before-stamping
# names carry no bytes: nothing reads them once lookup has said no.
STAMPED_FATURA = "SGM2026000010413.pdf"  # PO 4522142137
STAMPED_DEKONT = "917031.pdf"  # PO 4522207293
NOT_IN_WORKBOOK = "SGM2026000011171 (1).pdf"  # a near miss, as uploaded (R33)
PO_BLANK = "SGM2026000010415.pdf"
UNROUTABLE = "notes.pdf"
DUPLICATE_KEY = "919479.pdf"  # vault/tasks/done/020-duplicate-dekont-keys.md
ALREADY_STAMPED = "917034.pdf"  # fed the manually stamped reference
NOT_A_PDF = "SGM2026000010413.docx"  # routes and looks up; must never be opened


@pytest.fixture(scope="module")
def index(workbook_path):
    return load_workbook(workbook_path)


@pytest.fixture(scope="module")
def mixed(index, sample_bytes, already_stamped_bytes):
    """Every outcome, with refusals ahead of, between and after the stamps."""
    files = [
        (PO_BLANK, sample_bytes("SGM2026000010415")),
        (STAMPED_FATURA, sample_bytes("SGM2026000010413")),
        (UNROUTABLE, b""),
        (NOT_IN_WORKBOOK, b""),
        (DUPLICATE_KEY, b""),
        (ALREADY_STAMPED, already_stamped_bytes("917034")),
        (NOT_A_PDF, b"not a pdf"),
        (STAMPED_DEKONT, sample_bytes("917031")),
        (STAMPED_FATURA, sample_bytes("SGM2026000010413")),
    ]
    return run(index, files, now=NOW)


def render(result: Run) -> str:
    # In English, which the assertions below are written in. The Turkish
    # rendering is tested in test_i18n.py.
    with app.test_request_context():
        session["lang"] = "en"
        return render_template(
            "result.html", run=result, groups=summarise(result.outcomes)
        )


# --- run(): every input, one outcome, batch never stops (R19, R21) -------


def test_every_input_gets_exactly_one_outcome_in_upload_order(mixed):
    assert [o.filename for o in mixed.outcomes] == [
        PO_BLANK,
        STAMPED_FATURA,
        UNROUTABLE,
        NOT_IN_WORKBOOK,
        DUPLICATE_KEY,
        ALREADY_STAMPED,
        NOT_A_PDF,
        STAMPED_DEKONT,
        STAMPED_FATURA,
    ]
    assert [o.problem for o in mixed.outcomes] == [
        Problem.PO_BLANK,
        None,
        Problem.UNROUTABLE,
        Problem.NOT_IN_WORKBOOK,
        Problem.DUPLICATE_KEY,
        Problem.ALREADY_STAMPED,
        Problem.NOT_A_PDF,
        None,
        Problem.REPEATED_UPLOAD,
    ]


def test_refusals_do_not_stop_later_files_being_stamped(mixed):
    # R19: six refusals, a non-PDF among them, come before the DEKONT file, and it is still stamped.
    assert mixed.stamped == 2
    assert mixed.download.mimetype == "application/zip"


def test_a_stamped_outcome_names_its_po_and_its_delivered_file(mixed):
    stamped = [o for o in mixed.outcomes if o.ok]
    assert [(o.po, o.output, o.stamp) for o in stamped] == [
        ("4522142137", "PO4522142137-SGM2026000010413.pdf", "PO:4522142137"),
        ("4522207293", "PO4522207293-917031.pdf", "PO:4522207293"),
    ]
    assert all(o.message == "" for o in stamped)


def test_a_refused_outcome_has_a_reason_and_nothing_to_deliver(mixed):
    for o in mixed.outcomes:
        if not o.ok:
            assert o.po is None and o.output is None
            assert o.message


def test_the_download_holds_exactly_the_stamped_outcomes(index, sample_bytes):
    result = run(index, [(STAMPED_DEKONT, sample_bytes("917031"))], now=NOW)
    assert result.download.name == "PO4522207293-917031.pdf"
    assert verify(result.download.data, "4522207293")


def test_nothing_stamped_is_no_download(index, sample_bytes):
    # R20.
    result = run(index, [(PO_BLANK, sample_bytes("SGM2026000010415")), (UNROUTABLE, b"")])
    assert result.download is None
    assert result.stamped == 0
    assert len(result.outcomes) == 2


def test_a_non_pdf_alone_is_refused_not_raised(index):
    # Q16: the bytes would fail to open as a PDF. They are never opened.
    result = run(index, [(NOT_A_PDF, b"not a pdf")])
    assert [o.problem for o in result.outcomes] == [Problem.NOT_A_PDF]
    assert result.download is None


@pytest.mark.parametrize("name", ["917031.pdf", "917031.PDF", "917031.Pdf"])
def test_the_pdf_extension_ignores_case(index, sample_bytes, name):
    # Inference recorded in the spec's Q16 row: `.PDF` is a PDF.
    result = run(index, [(name, sample_bytes("917031"))])
    assert result.stamped == 1


@pytest.mark.parametrize("name", ["917031", "917031.pdf.docx", "917031.txt"])
def test_anything_else_is_not_a_pdf(index, name):
    result = run(index, [(name, b"")])
    assert result.outcomes[0].problem is Problem.NOT_A_PDF


# --- summarise(): R21's groups -------------------------------------------


def test_summary_order_covers_every_problem_once():
    assert SUMMARY_ORDER[0] is None
    assert SUMMARY_ORDER[1:3] == (Problem.NOT_IN_WORKBOOK, Problem.PO_BLANK)
    assert sorted(SUMMARY_ORDER[1:]) == sorted(Problem)
    assert len(set(SUMMARY_ORDER)) == len(SUMMARY_ORDER)


def test_groups_come_in_r21_order_and_skip_empty_ones(mixed):
    assert [key for key, _ in summarise(mixed.outcomes)] == [
        None,
        Problem.NOT_IN_WORKBOOK,
        Problem.PO_BLANK,
        Problem.UNROUTABLE,
        Problem.DUPLICATE_KEY,
        Problem.ALREADY_STAMPED,
        Problem.REPEATED_UPLOAD,
        Problem.NOT_A_PDF,
    ]


def test_every_outcome_lands_in_exactly_one_group(mixed):
    grouped = [o for _, group in summarise(mixed.outcomes) for o in group]
    # By identity: the same filename appears twice, as two outcomes.
    assert sorted(map(id, grouped)) == sorted(map(id, mixed.outcomes))


def test_a_group_keeps_upload_order(mixed):
    stamped = dict(summarise(mixed.outcomes))[None]
    assert [o.filename for o in stamped] == [STAMPED_FATURA, STAMPED_DEKONT]


# --- result.html: summary and download on one screen (R21, R29) ----------


def test_the_page_shows_the_download_and_every_file(mixed):
    html = render(mixed)
    assert mixed.download.name in html
    assert 'href="/download"' in html
    assert "Stamped 2 of 9 files" in html
    for o in mixed.outcomes:
        assert o.filename in html


def test_a_stamped_file_is_shown_with_its_po(mixed):
    html = render(mixed)
    assert f"{STAMPED_FATURA} → <b>PO:4522142137</b>" in html
    assert f"{STAMPED_DEKONT} → <b>PO:4522207293</b>" in html


def test_a_refused_file_is_shown_with_its_reason(mixed):
    html = render(mixed)
    for o in mixed.outcomes:
        if not o.ok:
            # Autoescaped, so compare against the escaped message.
            assert str(o.message).replace("'", "&#39;").replace('"', "&#34;") in html


@pytest.mark.parametrize("problem", list(Problem))
def test_every_problem_has_a_heading(problem):
    # A Problem added without a heading would render as a blank <h2>.
    result = Run([Outcome("x.pdf", None, None, problem, "a reason")], None)
    html = render(result)
    heading = html.split("<h2>", 1)[1].split("<span", 1)[0].strip()
    assert heading


def test_nothing_stamped_says_so_and_offers_no_download(index, sample_bytes):
    # R20: plainly, and with no download link.
    result = run(index, [(PO_BLANK, sample_bytes("SGM2026000010415"))])
    html = render(result)
    assert "Nothing was stamped" in html
    assert 'href="/download"' not in html
    assert "window.location" not in html


def test_the_download_never_starts_by_itself(mixed):
    # R29, 2026-09-23: the user clicks to download. Nothing on the page
    # navigates to /download on its own.
    html = render(mixed)
    assert "window.location" not in html
    assert "<script" not in html


def test_a_single_stamped_file_reads_in_the_singular():
    result = Run(
        [Outcome("917031.pdf", "1", "PO1-917031.pdf", None, "")],
        package([("PO1-917031.pdf", b"%PDF")]),
    )
    assert "Stamped 1 of 1 file<" in render(result)
