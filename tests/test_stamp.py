"""`stamp()` — `PO:<value>`, bold red 14pt, page 1, at the family's position.

Every test runs against all ten `samples/` inputs, so both layouts are
covered on every assertion: seven born-digital FATURA pages with a text layer,
and three two-page DEKONT scans with none (R12a, R28).

The stamp is found again by searching the output's text for it. That is the
same search `verify()` will make in 007 — here it is only the way to locate
what was drawn, not the check that decides delivery (R17).

What is **not** asserted: that the stamp covers nothing. Bounding boxes cannot
say — a DEKONT scan is built from full-width image strips and every FATURA has
a border drawn round the page, so both "overlap" the stamp on paper. Clearance
is asserted instead the way 017 measured it: by ink. Page 1 of the *input* is
rendered under the widest stamp the data can produce, and that area has to be
blank (`vault/decisions/0014-stamp-placement-per-family.md`).
"""

import pymupdf
import pytest

from stamper import (
    STAMP_POSITION,
    Family,
    route_filename,
    stamp,
    stamp_text,
)

# Every PO in the workbook is ten digits — the widest the stamp gets, which is
# what a clearance check wants to measure.
PO = "4522142137"

# The samples, split by family, as routing decides it. Listed rather than
# discovered so that a sample going missing fails here instead of shrinking
# the coverage quietly.
FATURA_SAMPLES = [
    "SGM2026000010413",
    "SGM2026000010414",
    "SGM2026000010415",
    "SGM2026000010416",
    "SGM2026000011171",
    "SUB2026000019889",
    "SUB2026000019890",
]
DEKONT_SAMPLES = ["917031", "917034", "917035"]
ALL_SAMPLES = FATURA_SAMPLES + DEKONT_SAMPLES

# 0xff0000 — how PyMuPDF reports the (1, 0, 0) the stamp is drawn in.
RED = 0xFF0000


def family_of(stem: str) -> Family:
    """The family as the app will pass it: from routing, never from the PDF (R1)."""
    family = route_filename(f"{stem}.pdf").family
    assert family is not None, f"{stem} no longer routes"
    return family


@pytest.fixture(scope="module")
def stamped(sample_bytes):
    """Each sample stamped once, opened, and kept for the module."""
    docs = {
        stem: pymupdf.open(stream=stamp(sample_bytes(stem), PO, family_of(stem)))
        for stem in ALL_SAMPLES
    }
    yield docs
    for doc in docs.values():
        doc.close()


def stamp_spans(page) -> list[dict]:
    """Every text span on the page carrying the stamp."""
    return [
        span
        for block in page.get_text("dict")["blocks"]
        if block["type"] == 0
        for line in block["lines"]
        for span in line["spans"]
        if span["text"].startswith("PO:")
    ]


def test_samples_route_as_listed():
    assert {family_of(s) for s in FATURA_SAMPLES} == {Family.FATURA}
    assert {family_of(s) for s in DEKONT_SAMPLES} == {Family.DEKONT}


@pytest.mark.parametrize("stem", ALL_SAMPLES)
def test_output_opens_with_every_page_kept(stem, stamped, sample_path):
    with pymupdf.open(sample_path(stem)) as original:
        assert stamped[stem].page_count == original.page_count


@pytest.mark.parametrize("stem", ALL_SAMPLES)
def test_stamp_reads_po_colon_value_on_one_line(stem, stamped):
    """R12: the prefix is part of the stamp. One span — nothing wrapped (R12a)."""
    spans = stamp_spans(stamped[stem][0])
    assert [s["text"] for s in spans] == [f"PO:{PO}"]
    assert stamp_text(PO) == f"PO:{PO}"


@pytest.mark.parametrize("stem", ALL_SAMPLES)
def test_stamp_is_bold_red_14pt(stem, stamped):
    """R12. Checked as rendered, not as requested."""
    (span,) = stamp_spans(stamped[stem][0])
    assert span["size"] == 14
    assert span["color"] == RED
    assert "Bold" in span["font"]


@pytest.mark.parametrize("stem", ALL_SAMPLES)
def test_stamp_sits_at_its_familys_baseline(stem, stamped):
    """R12a: FATURA (300, 45), DEKONT (220, 475) — the baseline, not the box."""
    (span,) = stamp_spans(stamped[stem][0])
    assert span["origin"] == pytest.approx(STAMP_POSITION[family_of(stem)])


def test_positions_are_the_settled_ones():
    """The two numbers in R12a. Changing either means changing the spec first."""
    assert STAMP_POSITION == {Family.FATURA: (300, 45), Family.DEKONT: (220, 475)}


@pytest.mark.parametrize("stem", DEKONT_SAMPLES)
def test_only_page_one_is_stamped(stem, stamped):
    """R28, against the three two-page DEKONT scans.

    Page 2 is a separate `TAHSİLAT MAKBUZU` receipt; a PO there would be on
    the wrong document.
    """
    doc = stamped[stem]
    assert doc.page_count == 2
    assert doc[0].search_for(f"PO:{PO}")
    assert not any(doc[i].search_for("PO:") for i in range(1, doc.page_count))


@pytest.mark.parametrize("stem", DEKONT_SAMPLES)
def test_scans_had_no_text_layer_to_begin_with(stem, sample_path):
    """What makes the DEKONT case real: the stamp is the only text on the page."""
    with pymupdf.open(sample_path(stem)) as original:
        assert original[0].get_text().strip() == ""


@pytest.mark.parametrize("stem", ALL_SAMPLES)
def test_stamp_lands_on_blank_page(stem, stamped, sample_path):
    """No ink under the stamp on the input's page 1 — 017's clearance, re-confirmed.

    Rendered in greyscale at 72 dpi over the stamp's own rectangle, grown by
    2pt so a stroke that just touches the edge still counts. 250 rather than
    255 leaves room for anti-aliasing noise, and nothing more.
    """
    (rect,) = stamped[stem][0].search_for(f"PO:{PO}")
    with pymupdf.open(sample_path(stem)) as original:
        pix = original[0].get_pixmap(
            clip=rect + (-2, -2, 2, 2), dpi=72, colorspace=pymupdf.csGRAY
        )
    assert min(pix.samples) >= 250, f"ink under the stamp on {stem}"


@pytest.mark.parametrize("stem", ["SGM2026000010413", "917031"])
def test_input_bytes_are_left_as_they_were(stem, sample_bytes):
    """R13: a copy comes back, and the input still equals the file on disk."""
    original = sample_bytes(stem)
    before = bytes(original)
    out = stamp(original, PO, family_of(stem))
    assert original == before
    assert out != original


@pytest.mark.parametrize("stem", ["SGM2026000010413", "917031"])
def test_does_not_rederive_family_from_the_pdf(stem, sample_bytes):
    """R1: the family passed in decides the position, whatever the document is.

    Deliberately the wrong one here — the app never does this, but it proves
    `stamp()` trusts routing rather than looking at the page.
    """
    wrong = Family.DEKONT if family_of(stem) is Family.FATURA else Family.FATURA
    with pymupdf.open(stream=stamp(sample_bytes(stem), PO, wrong)) as doc:
        (span,) = stamp_spans(doc[0])
    assert span["origin"] == pytest.approx(STAMP_POSITION[wrong])
