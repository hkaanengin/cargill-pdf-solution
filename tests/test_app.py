"""`app.py` over Flask's test client: R29's walk, end to end, headless.

029 made the app thin, so what is tested here is the wiring, not the rules:
the workbook is parsed in memory, the batch goes to `run()` whole, the results
page renders the `Run` and survives a reload, and the download serves
`run.download`. The rules themselves are tested in the module's own files.

The click-through in a real browser is still 029's to do by hand. This file is
what keeps it from regressing afterwards.
"""

from io import BytesIO
import re
from zipfile import ZipFile

import pytest

import app as app_module
from app import app

STAMPED_FATURA = "SGM2026000010413"  # PO 4522142137
STAMPED_DEKONT = "917031"  # PO 4522207293
PO_BLANK = "SGM2026000010415"


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app_module.SOURCES.clear()
    app_module.DOWNLOADS.clear()
    with app.test_client() as c:
        # The assertions here are in English. Turkish is the default (R31) and
        # is tested in test_i18n.py.
        c.get("/lang/en")
        yield c


@pytest.fixture
def loaded(client, workbook_path):
    """A client that has done R29 step 2: the workbook is uploaded."""
    resp = client.post(
        "/excel",
        data={"excel": (BytesIO(workbook_path.read_bytes()), workbook_path.name)},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 302 and resp.location.endswith("/stamp")
    return client


def post_pdfs(client, files: list[tuple[str, bytes]]):
    return client.post(
        "/stamp",
        data={"pdf": [(BytesIO(data), name) for name, data in files]},
        content_type="multipart/form-data",
    )


# --- Steps 1-3: land, upload the workbook, get asked for PDFs -------------


def test_landing_asks_for_the_workbook(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b'name="excel"' in resp.data


def test_workbook_upload_is_parsed_in_memory_and_leads_to_the_pdf_step(loaded):
    (source,) = app_module.SOURCES.values()
    assert set(source["index"]) == set(app_module.stamper.Family)
    resp = loaded.get("/stamp")
    assert resp.status_code == 200
    assert b'name="pdf"' in resp.data


def test_unreadable_workbook_is_a_message_not_a_500(client):
    resp = client.post(
        "/excel",
        data={"excel": (BytesIO(b"not a workbook"), "book.xlsx")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Could not read that workbook".encode() in resp.data
    assert not app_module.SOURCES


def test_pdf_step_without_a_workbook_goes_back_to_step_1(client):
    resp = client.post("/stamp", data={}, content_type="multipart/form-data")
    assert resp.status_code == 302 and resp.location.endswith("/")


# --- Steps 4-6: stamp, then one screen with download and summary ----------


def test_stamp_redirects_to_results_which_offer_download_and_summary(loaded, sample_bytes):
    resp = post_pdfs(loaded, [
        (f"{STAMPED_FATURA}.pdf", sample_bytes(STAMPED_FATURA)),
        (f"{PO_BLANK}.pdf", sample_bytes(PO_BLANK)),
    ])
    assert resp.status_code == 302 and "/result" in resp.location

    page = loaded.get(resp.location)
    assert page.status_code == 200
    assert b"Stamped 1 of 2 files" in page.data
    assert f"{STAMPED_FATURA}.pdf".encode() in page.data
    assert f"{PO_BLANK}.pdf".encode() in page.data
    assert b"/download" in page.data


def test_results_page_survives_a_reload_and_never_downloads_by_itself(loaded, sample_bytes):
    resp = post_pdfs(loaded, [(f"{STAMPED_DEKONT}.pdf", sample_bytes(STAMPED_DEKONT))])
    assert resp.location.endswith("/result")  # no flag that could fire a download
    first = loaded.get(resp.location)
    reload = loaded.get("/result")
    for page in (first, reload):
        assert page.status_code == 200
        assert b"Stamped 1 of 1 file" in page.data
        assert b"window.location" not in page.data


def test_one_stamped_file_downloads_as_a_bare_pdf(loaded, sample_bytes):
    post_pdfs(loaded, [(f"{STAMPED_DEKONT}.pdf", sample_bytes(STAMPED_DEKONT))])
    resp = loaded.get("/download")
    assert resp.mimetype == "application/pdf"
    assert resp.data.startswith(b"%PDF")
    assert "4522207293" in resp.headers["Content-Disposition"]


def test_two_stamped_files_download_as_a_zip(loaded, sample_bytes):
    post_pdfs(loaded, [
        (f"{STAMPED_FATURA}.pdf", sample_bytes(STAMPED_FATURA)),
        (f"{STAMPED_DEKONT}.pdf", sample_bytes(STAMPED_DEKONT)),
    ])
    resp = loaded.get("/download")
    assert resp.mimetype == "application/zip"
    assert len(ZipFile(BytesIO(resp.data)).namelist()) == 2


def test_nothing_stamped_offers_no_download(loaded, sample_bytes):
    post_pdfs(loaded, [(f"{PO_BLANK}.pdf", sample_bytes(PO_BLANK))])
    page = loaded.get("/result")
    assert b"nothing to download" in page.data
    resp = loaded.get("/download")
    assert resp.status_code == 302


def test_a_non_pdf_upload_reaches_the_summary_rather_than_being_filtered(loaded, sample_bytes):
    post_pdfs(loaded, [
        (f"{STAMPED_DEKONT}.pdf", sample_bytes(STAMPED_DEKONT)),
        ("notes.docx", b"not a pdf"),
    ])
    page = loaded.get("/result")
    assert b"Stamped 1 of 2 files" in page.data
    assert b"notes.docx" in page.data


def test_a_refused_file_is_listed_under_the_name_it_was_uploaded_with(loaded, sample_bytes):
    # R33: `(1)` used to be listed as `_1`, a name the user never chose. The
    # near miss is still refused (R18, Q11); only the name shown changed.
    near_miss = f"{STAMPED_FATURA} (1).pdf"
    post_pdfs(loaded, [(near_miss, sample_bytes(STAMPED_FATURA))])
    run = next(iter(app_module.DOWNLOADS.values()))
    assert [o.filename for o in run.outcomes] == [near_miss]
    assert run.outcomes[0].problem is not None and run.download is None
    assert near_miss in loaded.get("/result").data.decode()


def test_a_name_with_a_folder_part_never_reaches_the_download(loaded, sample_bytes):
    # Browsers send a bare name, but a hand-made request need not. Without
    # `secure_filename()`, routing is what keeps a path out of the zip.
    post_pdfs(loaded, [
        (f"{STAMPED_DEKONT}.pdf", sample_bytes(STAMPED_DEKONT)),
        (f"../x/{STAMPED_FATURA}.pdf", sample_bytes(STAMPED_FATURA)),
    ])
    run = next(iter(app_module.DOWNLOADS.values()))
    assert run.stamped == 1
    assert "/" not in run.download.name and "\\" not in run.download.name


# --- Operational edges ----------------------------------------------------


def test_reset_clears_the_workbook_and_the_run(loaded, sample_bytes):
    post_pdfs(loaded, [(f"{STAMPED_DEKONT}.pdf", sample_bytes(STAMPED_DEKONT))])
    loaded.get("/reset")
    assert not app_module.SOURCES and not app_module.DOWNLOADS
    assert loaded.get("/result").status_code == 302


def test_over_the_upload_cap_is_a_message_not_a_crash(loaded):
    cap = app.config["MAX_CONTENT_LENGTH"]
    app.config["MAX_CONTENT_LENGTH"] = 1024
    try:
        resp = post_pdfs(loaded, [("big.pdf", b"x" * 4096)])
    finally:
        app.config["MAX_CONTENT_LENGTH"] = cap
    assert resp.status_code == 302 and resp.location.endswith("/stamp")


def test_uploads_over_500_kb_never_touch_disk(loaded, sample_bytes, monkeypatch):
    """R36. Werkzeug spools an upload over 500 KB to a temporary file unless
    the app says otherwise; a DEKONT scan is over that, so it would."""
    import werkzeug.formparser

    def no_disk(*_a, **_k):
        raise AssertionError("an upload was written to a temporary file")

    monkeypatch.setattr(werkzeug.formparser, "SpooledTemporaryFile", no_disk)
    monkeypatch.setattr(werkzeug.formparser, "TemporaryFile", no_disk, raising=False)
    data = sample_bytes(STAMPED_DEKONT)
    assert len(data) > 500 * 1024
    resp = post_pdfs(loaded, [(f"{STAMPED_DEKONT}.pdf", data)])
    assert resp.status_code == 302 and resp.location.endswith("/result")
    assert loaded.get("/download").status_code == 200


# --- Going back and forth between the steps (R29) -------------------------


def step_links(html: bytes) -> set[str]:
    """The steps the sidebar links to."""
    steps = html.split(b'<ol class="steps"', 1)[1].split(b"</ol>", 1)[0]
    return {href.decode() for href in re.findall(rb'href="([^"]+)"', steps)}


def test_before_a_workbook_no_step_links_anywhere(client):
    assert step_links(client.get("/").data) == set()


def test_with_a_workbook_the_first_two_steps_link(loaded):
    assert step_links(loaded.get("/stamp").data) == {"/excel"}
    assert step_links(loaded.get("/excel").data) == {"/stamp"}


def test_after_a_run_every_step_links_and_the_run_survives_visiting(loaded, sample_bytes):
    post_pdfs(loaded, [(f"{STAMPED_DEKONT}.pdf", sample_bytes(STAMPED_DEKONT))])
    assert step_links(loaded.get("/result").data) == {"/excel", "/stamp"}

    workbook_page = loaded.get("/excel")
    assert b"Continue to PDFs" in workbook_page.data
    assert b"This clears the results of the last run." in workbook_page.data
    loaded.get("/stamp")

    # Looking changed nothing: the workbook and the run are both still there.
    assert app_module.SOURCES and app_module.DOWNLOADS
    assert loaded.get("/result").status_code == 200
    assert loaded.get("/download").mimetype == "application/pdf"


def test_the_workbook_step_shows_the_loaded_workbook(loaded, workbook_path):
    html = loaded.get("/excel").data.decode()
    assert workbook_path.name in html  # exactly as uploaded, spaces and all (R33)
    assert "Load a different workbook" in html


def test_loading_a_different_workbook_clears_the_last_run(loaded, sample_bytes, workbook_path):
    post_pdfs(loaded, [(f"{STAMPED_DEKONT}.pdf", sample_bytes(STAMPED_DEKONT))])
    loaded.post(
        "/excel",
        data={"excel": (BytesIO(workbook_path.read_bytes()), workbook_path.name)},
        content_type="multipart/form-data",
    )
    assert loaded.get("/result").status_code == 302
