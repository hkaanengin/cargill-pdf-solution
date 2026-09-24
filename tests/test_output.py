"""`output_name()`, `repeated_upload()` and `package()`: what the user downloads.

R14 names each stamped file `PO<value>-<original>.pdf`. R15 packages by the
number **stamped**: one is a bare PDF, two or more a zip. Several uploaded
with one stamped is still a bare PDF, as the user confirmed on 2026-09-22.
R16 is withdrawn, so the zip holds PDFs and nothing else. R18 refuses a
filename uploaded twice in one batch, and R20 means a run with nothing stamped
offers no download at all.

The batch tests run real samples through `run()`, the call the app makes:
`repeated_upload`, then `lookup_po(index, *route_filename(name))`, then
`stamp_checked`, then `package`.
"""

from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

import pytest

from stamper import (
    Problem,
    load_workbook,
    lookup_po,
    output_name,
    package,
    repeated_upload,
    route_filename,
    run,
    verify,
)

NOW = datetime(2026, 9, 22, 14, 5, 9)


@pytest.fixture(scope="module")
def index(workbook_path):
    return load_workbook(workbook_path)


@pytest.fixture(scope="module")
def run_batch(index, sample_bytes):
    """Run filenames through `run()`, the whole per-file path.

    Returns `(download, problems)`. `problems` is `(filename, Problem)` for
    each refused file, in upload order.
    """

    def _run(filenames: list[str]):
        files = [(name, _bytes_for(name, sample_bytes)) for name in filenames]
        result = run(index, files, now=NOW)
        problems = [(o.filename, o.problem) for o in result.outcomes if not o.ok]
        return result.download, problems

    return _run


def _bytes_for(name, sample_bytes):
    # Unroutable names have no sample. Their bytes are never read.
    routed = route_filename(name)
    return sample_bytes(routed.key) if routed.family else b""


def zip_names(data: bytes) -> list[str]:
    with ZipFile(BytesIO(data)) as z:
        return z.namelist()


# --- R14: the name -------------------------------------------------------


@pytest.mark.parametrize(
    "filename, po, expected",
    [
        # Both of R14's own examples.
        ("SGM2026000010461.pdf", "4522142137", "PO4522142137-SGM2026000010461.pdf"),
        ("917023.pdf", "4522182195", "PO4522182195-917023.pdf"),
        ("SUB2026000019889.pdf", "4522207288", "PO4522207288-SUB2026000019889.pdf"),
    ],
)
def test_output_name_is_po_then_original(filename, po, expected):
    assert output_name(filename, po) == expected


def test_output_name_still_routes_back_to_nothing():
    # The prefix makes the delivered file unroutable, so feeding a delivered
    # file back in cannot silently resolve to a key.
    assert route_filename(output_name("917031.pdf", "4522207293")).family is None


# --- R18: a filename uploaded twice --------------------------------------


def test_first_upload_passes_and_is_recorded():
    seen: set[str] = set()
    assert repeated_upload("917031.pdf", seen) is None
    assert seen == {"917031.pdf"}


def test_second_upload_of_the_same_name_is_refused():
    seen: set[str] = set()
    repeated_upload("917031.pdf", seen)
    refused = repeated_upload("917031.pdf", seen)
    assert refused is not None
    assert refused.problem is Problem.REPEATED_UPLOAD
    assert refused.po is None
    assert refused.message


def test_different_names_are_not_repeats():
    seen: set[str] = set()
    assert repeated_upload("917031.pdf", seen) is None
    assert repeated_upload("917034.pdf", seen) is None


# --- R15, R16, R20: packaging ---------------------------------------------


def test_nothing_stamped_is_no_download():
    # R20: not an empty zip.
    assert package([]) is None


def test_one_stamped_is_a_bare_pdf():
    download = package([("PO1-917031.pdf", b"%PDF-1")], now=NOW)
    assert download.name == "PO1-917031.pdf"
    assert download.data == b"%PDF-1"
    assert download.mimetype == "application/pdf"


def test_two_stamped_is_a_zip_of_pdfs_only():
    files = [("PO1-917031.pdf", b"%PDF-a"), ("PO2-917034.pdf", b"%PDF-b")]
    download = package(files, now=NOW)
    assert download.mimetype == "application/zip"
    assert download.name == "stamped_20260922_140509.zip"
    # R16 withdrawn: no manifest, nothing but the PDFs, in upload order.
    assert zip_names(download.data) == ["PO1-917031.pdf", "PO2-917034.pdf"]
    with ZipFile(BytesIO(download.data)) as z:
        assert z.read("PO2-917034.pdf") == b"%PDF-b"


def test_colliding_output_names_are_a_caller_bug():
    with pytest.raises(ValueError):
        package([("PO1-917031.pdf", b"a"), ("PO1-917031.pdf", b"b")], now=NOW)


# --- The whole path, on real samples --------------------------------------


def test_single_upload_run_is_a_bare_stamped_pdf(run_batch):
    download, problems = run_batch(["SGM2026000010413.pdf"])
    assert problems == []
    assert download.name == "PO4522142137-SGM2026000010413.pdf"
    assert download.mimetype == "application/pdf"
    assert verify(download.data, "4522142137")


def test_multi_file_run_zips_the_stamped_and_reports_the_rest(run_batch):
    download, problems = run_batch(
        ["917031.pdf", "SGM2026000010415.pdf", "SUB2026000019889.pdf", "917031.pdf"]
    )
    assert download.mimetype == "application/zip"
    assert zip_names(download.data) == [
        "PO4522207293-917031.pdf",
        "PO4522207288-SUB2026000019889.pdf",
    ]
    assert problems == [
        ("SGM2026000010415.pdf", Problem.PO_BLANK),
        ("917031.pdf", Problem.REPEATED_UPLOAD),
    ]


def test_several_uploaded_one_stamped_is_a_bare_pdf(run_batch):
    # The case R15 left open, settled by the user 2026-09-22: stamped count
    # decides, not upload count.
    download, problems = run_batch(
        ["SGM2026000010415.pdf", "917035.pdf", "SGM2026000010416.pdf"]
    )
    assert len(problems) == 2
    assert download.name == "PO4522207291-917035.pdf"
    assert download.mimetype == "application/pdf"


def test_same_file_twice_alone_is_one_bare_pdf(run_batch):
    download, problems = run_batch(["917034.pdf", "917034.pdf"])
    assert download.mimetype == "application/pdf"
    assert problems == [("917034.pdf", Problem.REPEATED_UPLOAD)]


def test_all_failing_run_offers_no_download(run_batch):
    download, problems = run_batch(["SGM2026000010415.pdf", "notes.pdf"])
    assert download is None
    assert [p for _, p in problems] == [Problem.PO_BLANK, Problem.UNROUTABLE]


# --- Names as uploaded (R33) ----------------------------------------------


def test_a_near_miss_keeps_its_name_and_is_still_refused(index):
    # The app no longer sanitises names, so `(1)` reaches lookup untouched.
    # It is still not a key, so it is refused (Q11), not repaired.
    name = "SGM2026000011171 (1).pdf"
    routed = route_filename(name)
    assert routed.key == "SGM2026000011171 (1)"
    assert lookup_po(index, *routed).problem is Problem.NOT_IN_WORKBOOK
