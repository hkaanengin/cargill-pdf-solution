"""A filename decides two things, and nothing else is consulted — R1-R5.

`route_filename()` is total: it never raises and never touches the disk. It
answers "which sheet, and under what key", and every failure it can express is
the single R5 one — `family is None`, no pattern matched. Everything else that
can go wrong with a name goes wrong later, in `lookup_po()`.

That split is the thing these tests are really protecting. `SGM2026…(1).pdf`
routes perfectly well and then finds nothing; if routing ever starts refusing
it, R18's near-miss case has quietly moved to the wrong layer.
"""

import builtins
import io
from pathlib import Path

import pytest

from stamper import Family, route_filename


# ---------------------------------------------------------------- the real ten

def test_every_sample_routes_to_the_family_its_shape_demands(sample_pdfs):
    """All ten inputs in samples/, by the rules R2-R4 state.

    Driven off the fixture rather than a hardcoded list, so a sample added to
    the directory is covered the moment it lands.
    """
    wrong = {}
    for stem, path in sample_pdfs.items():
        expected = Family.FATURA if stem[:3] in ("SGM", "SUB") else Family.DEKONT
        got = route_filename(path.name).family
        if got is not expected:
            wrong[stem] = f"expected {expected}, got {got}"
    assert not wrong, wrong


def test_every_sample_key_is_its_stem_verbatim(sample_pdfs):
    """R1: `.pdf` off, and nothing else done to the name."""
    keys = {stem: route_filename(path.name).key for stem, path in sample_pdfs.items()}
    assert keys == {stem: stem for stem in sample_pdfs}


# ------------------------------------------------------------------- the rules

@pytest.mark.parametrize(
    "name",
    [
        "SGM2026000010413.pdf",  # R2
        "SUB2026000019889.pdf",  # R3
        "SGM.pdf",               # the prefix is the whole rule; nothing follows it
    ],
)
def test_sgm_and_sub_route_to_fatura(name):
    assert route_filename(name).family is Family.FATURA


@pytest.mark.parametrize("key", ["1234", "91702", "917031"])
def test_digit_names_route_to_dekont_at_any_length(key):
    """R4 is explicit that 4, 5 and 6 digits are all legitimate keys."""
    assert route_filename(f"{key}.pdf") == (key, Family.DEKONT)


@pytest.mark.parametrize(
    "name",
    [
        "invoice.pdf",                  # no pattern at all
        "917031a.pdf",                  # digits, and then not
        "SG2026000010413.pdf",          # two letters of a three-letter prefix
        "sgm2026000010413.pdf",         # lower case — see the docstring below
        "DEKONT.pdf",                   # the sheet's name is not a filename rule
        ".pdf",                         # empty key
        "../x/SGM2026000010413.pdf",    # a folder part is not cut away
        "x\\SGM2026000010413.pdf",       # nor a Windows one
    ],
)
def test_unroutable_names_are_returned_as_unroutable(name):
    """R5: no sheet is chosen. The name is not guessed at, corrected or folded.

    `sgm…` is in here deliberately. Every key in the workbook is upper-case and
    the user has not said a lower-case name should be accepted, so it is left
    unroutable rather than quietly lower-cased — an assumption avoided, not an
    oversight. If a real file turns up in that shape, this is the test that
    should change, with the spec.
    """
    assert route_filename(name).family is None


def test_an_unroutable_name_still_carries_its_key():
    """R21 accounts for *every* input by name, including the ones R5 refuses."""
    assert route_filename("invoice.pdf").key == "invoice"


# ------------------------------------------- routing succeeds, lookup then fails

def test_the_near_miss_routes_and_is_not_repaired():
    """`SGM…(1).pdf` is an R18 exception, but it is not a *routing* one (Q11).

    It begins `SGM`, so it routes to FATURA and carries its key untouched — the
    ` (1)` included. Refusing it is `lookup_po()`'s job, because the sheet is
    what proves the key is absent.
    """
    assert route_filename("SGM2026000011171 (1).pdf") == (
        "SGM2026000011171 (1)",
        Family.FATURA,
    )


# ------------------------------------------------------- the name, and nothing else

def test_no_file_is_opened_to_route_a_name(monkeypatch, sample_pdfs):
    """R1: the filename is the key. No PDF is parsed, or even read.

    Every door to the filesystem is nailed shut for the duration, then the real
    ten are routed anyway — they exist on disk, so nothing but a genuine read
    would be caught by this.
    """

    def forbidden(*args, **kwargs):
        raise AssertionError("route_filename() touched the filesystem")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(io, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)

    for path in sample_pdfs.values():
        assert route_filename(path.name).family is not None


def test_routing_works_on_a_name_that_is_not_a_file():
    """The app is handed an upload's filename, not a path to anything."""
    assert route_filename("917031.pdf") == ("917031", Family.DEKONT)
