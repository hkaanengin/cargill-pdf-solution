"""R31: Turkish by default, English on a switch, nothing left untranslated.

A string with no Turkish entry falls back to English without an error, which
is the right behaviour inside a request and exactly why it needs a test. A
user who reads only Turkish would not report a stray English label. They
would just not understand it.
"""

import ast
import re
import string
from io import BytesIO
from pathlib import Path

import pytest

import app as app_module
import i18n
from app import app
from stamper import Outcome, Problem

REPO = Path(__file__).resolve().parent.parent
# `_("…")` or `_('…')` in a template. Every call puts its literal first.
TEMPLATE_CALL = re.compile(r"""\b_\(\s*(["'])(.+?)\1""")


def template_strings() -> set[str]:
    found = set()
    for path in (REPO / "templates").glob("*.html"):
        found |= {m.group(2) for m in TEMPLATE_CALL.finditer(path.read_text())}
    return found


def app_strings() -> set[str]:
    """Every literal passed to `_()` in app.py, implicit concatenation joined."""
    tree = ast.parse((REPO / "app.py").read_text())
    return {
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == "_"
        and node.args and isinstance(node.args[0], ast.Constant)
    }


def fields(s: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(s) if name}


# --- The catalogue is complete and consistent ----------------------------


def test_the_extractors_find_the_strings():
    # Guards the two tests below from passing because they found nothing.
    assert "Stamped {n} of {total} files" in template_strings()
    assert "Stamped {n} of {total} file" in template_strings()
    assert "That upload is over the {limit} MB limit. Send the PDFs in smaller batches." in app_strings()


@pytest.mark.parametrize("text", sorted(template_strings() | app_strings()))
def test_every_shown_string_has_turkish(text):
    assert text in i18n.TR, f"No Turkish for {text!r} in i18n.TR"


@pytest.mark.parametrize("text", sorted(i18n.TR))
def test_turkish_keeps_the_same_placeholders(text):
    assert fields(i18n.TR[text]) == fields(text)


@pytest.mark.parametrize("problem", list(Problem))
def test_every_reason_has_turkish(problem):
    assert problem in i18n.REASONS_TR


def test_a_reason_is_built_from_its_details():
    o = Outcome("919479.pdf", None, None, Problem.DUPLICATE_KEY, "english", {"sheet": "DEKONT", "rows": 2})
    tr = i18n.reason(o, "tr")
    assert "DEKONT" in tr and "2 satırda" in tr
    assert i18n.reason(o, "en") == "english"


def test_a_reason_missing_a_detail_falls_back_to_english_not_a_500():
    o = Outcome("x.pdf", None, None, Problem.PO_BLANK, "english", None)
    assert i18n.reason(o, "tr") == "english"


# --- The app speaks Turkish until told otherwise -------------------------


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app_module.SOURCES.clear()
    app_module.DOWNLOADS.clear()
    with app.test_client() as c:
        yield c


def test_the_first_page_is_turkish(client):
    html = client.get("/").get_data(as_text=True)
    assert '<html lang="tr">' in html
    assert "Excel dosyasını buraya bırakın veya seçin" in html
    assert "Drop the Excel workbook" not in html


def test_the_switch_changes_language_and_returns_to_the_page(client):
    resp = client.get("/lang/en?next=/")
    assert resp.status_code == 302 and resp.location.endswith("/")
    html = client.get("/").get_data(as_text=True)
    assert '<html lang="en">' in html and "Drop the Excel workbook" in html
    client.get("/lang/tr?next=/")
    assert '<html lang="tr">' in client.get("/").get_data(as_text=True)


@pytest.mark.parametrize("target", ["//evil.example/", "https://evil.example/", "evil"])
def test_the_switch_only_returns_to_this_site(client, target):
    resp = client.get(f"/lang/en?next={target}")
    assert resp.location == "/"


def test_an_unknown_language_is_ignored(client):
    client.get("/lang/de?next=/")
    assert '<html lang="tr">' in client.get("/").get_data(as_text=True)


def test_a_whole_run_reads_in_turkish(client, workbook_path, sample_pdfs):
    client.post(
        "/excel",
        data={"excel": (BytesIO(workbook_path.read_bytes()), workbook_path.name)},
        content_type="multipart/form-data",
    )
    client.post(
        "/stamp",
        data={"pdf": [(BytesIO(p.read_bytes()), p.name) for p in sample_pdfs.values()]},
        content_type="multipart/form-data",
    )
    html = client.get("/result").get_data(as_text=True)
    assert "10 dosyadan 8 tanesi damgalandı" in html
    assert "FATURA sayfasında bulundu ama PO hücresi boş" in html
    assert "PO cell is empty" not in html
    # Data stays as it is.
    assert "SGM2026000010413.pdf → <b>PO:4522142137</b>" in html


def test_flashes_are_turkish(client):
    html = client.post(
        "/excel", data={}, content_type="multipart/form-data", follow_redirects=True
    ).get_data(as_text=True)
    assert "Lütfen bir Excel dosyası seçin." in html
