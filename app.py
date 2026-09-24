#!/usr/bin/env python3
"""Web app: upload, call, render. The walk is R29's six steps.

  1. User uploads the Excel workbook. It is parsed in memory by
     `stamper.load_workbook()` and never written to disk (R23, R24).
  2. The page then asks for PDFs. The batch goes to `stamper.run()` whole, and
     the browser is redirected to the results screen: the download (a bare PDF
     or a zip, R15) and the summary of every input (R21), on one page.

Everything that decides what a file is, what it is stamped with and what it is
called lives in `stamper.py`. This file keeps only what is genuinely web:
routes, the session id, uploads, flashes for operational errors, the upload cap
and the download response. See decisions/0011-one-entry-point.

Single user, single session: the parsed workbook and the last run are held
server-side in this process, keyed by a per-browser session id. Nothing is
written to disk. See decisions/0008-single-user-session-scoped.
"""

from io import BytesIO
import os
import secrets

from flask import (
    Flask, Request, request, render_template, send_file, flash, redirect, url_for,
    session,
)

import i18n
import stamper


class InMemoryRequest(Request):
    """Uploads stay in memory, whatever their size (R36). Werkzeug otherwise
    writes anything over 500 KB to a temporary file, and a DEKONT scan is ~0.8 MB."""

    def _get_file_stream(self, total_content_length, content_type, filename=None,
                         content_length=None):
        return BytesIO()


app = Flask(__name__)
app.request_class = InMemoryRequest
# Signs the session cookie / flash messages. From the environment (R26); a
# random key when unset is safe, because a restart already drops every session
# with the in-memory state (R23), and there is only ever one worker (R25).
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
# A batch of receipts, not one file: DEKONT scans are ~0.8 MB and e-Faturas
# ~50 KB, so this leaves room for over a hundred of them. The whole batch sits
# in RAM, which is why it is not higher (R34).
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB upload cap

# Server-side store: session id -> {"filename": str, "index": stamper.PoIndex}
SOURCES: dict[str, dict] = {}
# Server-side store: session id -> the last `stamper.Run`. Kept here rather than
# in flashes so the results page survives a reload; the next batch replaces it.
DOWNLOADS: dict[str, stamper.Run] = {}


def current_language() -> str:
    """The session's language, Turkish unless the user switched (R31)."""
    lang = session.get("lang")
    return lang if lang in i18n.LANGUAGES else i18n.DEFAULT_LANGUAGE


def _(text: str, **params) -> str:
    """`text` in the session's language. See i18n.py."""
    return i18n.translate(text, current_language(), **params)


@app.context_processor
def translation_helpers():
    lang = current_language()
    return {
        "_": _,
        "lang": lang,
        "reason": lambda outcome: i18n.reason(outcome, lang),
    }


@app.context_processor
def progress():
    """What the step list needs: which steps have something to show (R29)."""
    return {"has_source": current_source() is not None, "has_run": current_run() is not None}


@app.route("/lang/<code>")
def set_language(code: str):
    """Switch language for the session, then go back to the page it came from."""
    if code in i18n.LANGUAGES:
        session["lang"] = code
    target = request.args.get("next", "")
    # Only a path on this site. `//host` is another site to a browser.
    if not target.startswith("/") or target.startswith("//"):
        target = url_for("index")
    return redirect(target)


def current_source():
    """Return the uploaded-workbook record for this session, or None."""
    sid = session.get("sid")
    return SOURCES.get(sid) if sid else None


def current_run():
    """Return this session's last run, or None."""
    sid = session.get("sid")
    return DOWNLOADS.get(sid) if sid else None


@app.route("/")
def index():
    """Step 1: upload the workbook (or jump to step 2 if already loaded)."""
    if current_source():
        return redirect(url_for("stamp_page"))
    return render_template("excel.html")


@app.route("/excel", methods=["GET"])
def excel_page():
    """Step 1, always reachable: shows the loaded workbook, if any, and
    offers to replace it. Looking changes nothing (R29)."""
    src = current_source()
    return render_template(
        "excel.html",
        source=src["filename"] if src else None,
        count=entry_count(src["index"]) if src else None,
    )


@app.route("/excel", methods=["POST"])
def upload_excel():
    file = request.files.get("excel")
    if not file or not file.filename:
        flash(_("Please choose an Excel file."), "error")
        return redirect(url_for("index"))

    filename = file.filename  # shown as uploaded, never altered (R33)
    if not filename.lower().endswith((".xlsx", ".xlsm")):
        flash(_("Please upload an Excel workbook (.xlsx)."), "error")
        return redirect(url_for("index"))

    # Only what the loader already raises is caught here, so an unreadable
    # upload is a message rather than a 500. What else the workbook should be
    # checked for is Q15, parked as 030-workbook-verification.
    try:
        index = stamper.load_workbook(file.stream)
    except Exception as e:  # noqa: BLE001
        flash(_("Could not read that workbook: {error}", error=e), "error")
        return redirect(url_for("index"))

    sid = session.get("sid") or secrets.token_hex(16)
    session["sid"] = sid
    SOURCES[sid] = {"filename": filename, "index": index}
    DOWNLOADS.pop(sid, None)  # a new source invalidates the previous run
    flash(_("Loaded {n} entries from “{name}”.", n=entry_count(index), name=filename), "ok")
    return redirect(url_for("stamp_page"))


def entry_count(index: stamper.PoIndex) -> int:
    """Distinct keys across both sheets, for the "N entries loaded" line."""
    return sum(len(sheet) for sheet in index.values())


@app.route("/reset")
def reset():
    """Clear the loaded workbook so the user can upload a different one."""
    sid = session.pop("sid", None)
    if sid:
        SOURCES.pop(sid, None)
        DOWNLOADS.pop(sid, None)
    return redirect(url_for("index"))


@app.route("/stamp", methods=["GET"])
def stamp_page():
    """Step 2: upload PDFs to stamp."""
    src = current_source()
    if not src:
        flash(_("Upload the Excel source first."), "error")
        return redirect(url_for("index"))
    return render_template(
        "stamp.html",
        source=src["filename"],
        count=entry_count(src["index"]),
        last_run=current_run(),
    )


@app.route("/stamp", methods=["POST"])
def stamp():
    src = current_source()
    if not src:
        flash(_("Upload the Excel source first."), "error")
        return redirect(url_for("index"))

    uploads = [f for f in request.files.getlist("pdf") if f and f.filename]
    if not uploads:
        flash(_("Please choose at least one PDF file."), "error")
        return redirect(url_for("stamp_page"))

    # Every upload goes in, whatever its extension: `run()` refuses a non-PDF
    # itself, and filtering here would drop it from the summary (R21, Q16).
    # The name passed is the one the key is derived from, exactly as uploaded:
    # it is never altered, so the summary lists what the user chose (R1, R33).
    # A name with a folder part is unroutable (see `route_filename()`), so no
    # uploaded name can put a path into the download.
    files = [(f.filename, f.read()) for f in uploads]
    DOWNLOADS[session["sid"]] = stamper.run(src["index"], files)
    return redirect(url_for("result"))


@app.route("/result")
def result():
    """Step 3: the download and the summary, on one screen (R29 step 6)."""
    run = current_run()
    if not run:
        return redirect(url_for("stamp_page"))
    return render_template(
        "result.html",
        run=run,
        groups=stamper.summarise(run.outcomes),
    )


@app.route("/download")
def download():
    """Hand over the last run's file, only ever on the user's click (R29).
    Kept until the next run replaces it, so it can be downloaded again."""
    run = current_run()
    item = run.download if run else None
    if not item:
        flash(_("That download is no longer available — upload the PDFs again."), "error")
        return redirect(url_for("stamp_page"))
    return send_file(
        BytesIO(item.data),
        mimetype=item.mimetype,
        as_attachment=True,
        download_name=item.name,
    )


@app.errorhandler(413)
def too_large(_e):
    limit = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    flash(_("That upload is over the {limit} MB limit. Send the PDFs in smaller "
            "batches.", limit=limit), "error")
    return redirect(url_for("stamp_page" if current_source() else "index")), 302


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
