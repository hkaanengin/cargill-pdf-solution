"""`verify()`, `already_stamped()` and `stamp_checked()`, the checks around the stamp.

R17 says nothing is delivered until `PO:<value>` has been found in the output.
R18 says an input that already carries a `PO:` stamp is refused. Both are
tested against real documents where possible.

- **The ten clean samples** must all pass. Stamped, each verifies; unstamped,
  none reads as already stamped. The FATURA ones have a text layer, so a false
  positive there is possible, which is why they are tested.
- **The six manually stamped originals** in `samples_stamped_reference/` must
  all be refused. `917034` is also the regression fixture for R17: its manual
  stamp reads `PO:452220729` with the final `0` wrapped onto the next line,
  so the whole PO is not on the page.
- **A deliberately bad coordinate** stands in for a stamp that silently
  failed to render. Off the page, PyMuPDF draws it where nobody can see it and
  reports no error, which is the failure R17 exists for.
"""

import pymupdf
import pytest

import stamper
from stamper import (
    Family,
    Problem,
    already_stamped,
    route_filename,
    stamp,
    stamp_checked,
    verify,
)

PO = "4522142137"

CLEAN_SAMPLES = [
    "917031",
    "917034",
    "917035",
    "SGM2026000010413",
    "SGM2026000010414",
    "SGM2026000010415",
    "SGM2026000010416",
    "SGM2026000011171",
    "SUB2026000019889",
    "SUB2026000019890",
]

# The manually stamped originals and the PO each should carry. That is the
# PO from the workbook for that key, measured 2026-09-22.
REFERENCE_POS = {
    "917031": "4522207293",
    "917034": "4522207290",
    "917035": "4522207291",
    "SGM2026000011171": "4522207286",
    "SUB2026000019889": "4522207288",
    "SUB2026000019890": "4522207290",
}


def family_of(stem: str) -> Family:
    family = route_filename(f"{stem}.pdf").family
    assert family is not None, f"{stem} no longer routes"
    return family


def with_text(pdf_bytes: bytes, text: str, at=(100, 100), page: int = 0) -> bytes:
    """A copy with `text` drawn somewhere, as a stand-in for anyone's stamp."""
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        doc[page].insert_text(at, text, fontsize=11)
        return doc.tobytes()


# --- verify() -------------------------------------------------------------


@pytest.mark.parametrize("stem", CLEAN_SAMPLES)
def test_every_stamped_sample_verifies(stem, sample_bytes):
    assert verify(stamp(sample_bytes(stem), PO, family_of(stem)), PO)


@pytest.mark.parametrize("stem", CLEAN_SAMPLES)
def test_an_unstamped_sample_does_not_verify(stem, sample_bytes):
    assert not verify(sample_bytes(stem), PO)


def test_wrapped_last_digit_fails_verification(already_stamped_bytes):
    """R17's real case: `917034` as the manual process delivered it.

    The stamp is on the page, but as `PO:452220729` on one line and `0` on the
    next. It is the correct PO with a digit missing, and it must not pass.
    """
    assert not verify(already_stamped_bytes("917034"), REFERENCE_POS["917034"])


@pytest.mark.parametrize("stem", ["917031", "917035", "SUB2026000019889"])
def test_whole_manual_stamps_do_verify(stem, already_stamped_bytes):
    """The same search on the manual stamps that are *not* broken. It is not
    `917034`'s font or layout that fails, only the missing digit."""
    assert verify(already_stamped_bytes(stem), REFERENCE_POS[stem])


def test_bare_number_is_not_a_stamp(sample_bytes):
    """Q10: the prefix is what makes it the app's stamp."""
    assert not verify(with_text(sample_bytes("SGM2026000010413"), PO), PO)


@pytest.mark.parametrize(
    "drawn",
    [f"PO:{PO}7", f"PO:{PO[:-1]}"],
    ids=["one-digit-too-many", "one-digit-short"],
)
def test_a_different_po_does_not_verify(drawn, sample_bytes):
    """The match stops at the last digit: a longer or shorter PO is another PO."""
    assert not verify(with_text(sample_bytes("917031"), drawn), PO)


def test_a_stamp_on_page_two_does_not_verify(sample_bytes):
    """R28: page 1 is the only right place. Found on page 2, it is still wrong."""
    assert not verify(with_text(sample_bytes("917031"), f"PO:{PO}", page=1), PO)


@pytest.mark.parametrize(
    "at",
    [(300, 2000), (-500, 475), (590, 475)],
    ids=["below-the-page", "left-of-the-page", "running-off-the-right-edge"],
)
def test_a_stamp_off_the_page_does_not_verify(at, sample_bytes):
    """Drawn, but not where anyone can see it, so it has not landed."""
    assert not verify(with_text(sample_bytes("917031"), f"PO:{PO}", at=at), PO)


# --- already_stamped() ----------------------------------------------------


@pytest.mark.parametrize("stem", CLEAN_SAMPLES)
def test_no_clean_sample_reads_as_already_stamped(stem, sample_bytes):
    """Especially the seven FATURA ones, which have a text layer to misread."""
    assert not already_stamped(sample_bytes(stem))


@pytest.mark.parametrize("stem", sorted(REFERENCE_POS))
def test_every_manually_stamped_original_is_caught(stem, already_stamped_bytes):
    """Black or grey, MinionPro, Arial or Tahoma, and one of them wrapped. The
    style varies, and only the text is checked."""
    assert already_stamped(already_stamped_bytes(stem))


@pytest.mark.parametrize("stem", CLEAN_SAMPLES)
def test_our_own_output_reads_as_stamped(stem, sample_bytes):
    """So a file downloaded and uploaded again is refused, not stamped twice."""
    assert already_stamped(stamp(sample_bytes(stem), PO, family_of(stem)))


def test_a_stamp_on_any_page_counts(sample_bytes):
    """Someone else's mistake need not be on page 1."""
    assert already_stamped(with_text(sample_bytes("917031"), "PO:4522207293", page=1))


@pytest.mark.parametrize(
    "text, stamped",
    [
        ("PO: 4522207293", True),
        ("DEPO:12", False),
        ("PO:", False),
        ("po:4522207293", False),
    ],
    ids=["space-after-colon", "word-ending-in-po", "prefix-alone", "lower-case"],
)
def test_what_counts_as_a_stamp(text, stamped, sample_bytes):
    """`PO:` then a digit, with no letter just before it. Case matters."""
    assert already_stamped(with_text(sample_bytes("SGM2026000010413"), text)) is stamped


# --- stamp_checked() ------------------------------------------------------


@pytest.mark.parametrize("stem", CLEAN_SAMPLES)
def test_a_clean_sample_comes_back_stamped_and_verified(stem, sample_bytes):
    result = stamp_checked(sample_bytes(stem), PO, family_of(stem))
    assert result.ok
    assert result.problem is None
    assert verify(result.pdf, PO)


@pytest.mark.parametrize("stem", sorted(REFERENCE_POS))
def test_an_already_stamped_input_is_withheld(stem, already_stamped_bytes):
    """R18: refused, not stamped twice, and no bytes to deliver by mistake."""
    result = stamp_checked(already_stamped_bytes(stem), PO, family_of(stem))
    assert not result.ok
    assert result.problem is Problem.ALREADY_STAMPED
    assert result.pdf is None
    assert result.message


@pytest.mark.parametrize("family", list(Family))
def test_a_stamp_that_did_not_land_is_withheld(family, sample_bytes, monkeypatch):
    """R17 end to end: move the stamp off the page and it must not be delivered.

    `stamp()` raises nothing here. PyMuPDF draws off the page without
    complaint, so only the verification after it notices.
    """
    monkeypatch.setitem(stamper.STAMP_POSITION, family, (300, 2000))
    stem = "SGM2026000010413" if family is Family.FATURA else "917031"
    result = stamp_checked(sample_bytes(stem), PO, family)
    assert result.problem is Problem.STAMP_NOT_VERIFIED
    assert result.pdf is None
    assert f"PO:{PO}" in result.message


def test_one_withheld_file_does_not_stop_the_next(sample_bytes, already_stamped_bytes):
    """R19: nothing is raised, so a loop over a batch carries on by itself."""
    results = [
        stamp_checked(already_stamped_bytes("917031"), PO, Family.DEKONT),
        stamp_checked(sample_bytes("917031"), PO, Family.DEKONT),
    ]
    assert [r.ok for r in results] == [False, True]
