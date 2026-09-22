#!/usr/bin/env python3
"""Web app, two-step flow:

  1. User uploads the Excel workbook (the source of Tescil numbers).
  2. The page then asks for SGM PDFs; each is matched against the uploaded Excel,
     the Tescil No is stamped on it, and the stamped files come back — a single
     PDF for a single file, a zip (with a manifest) for a batch.

Single user, single session: the parsed Excel mapping and the pending download
are held server-side in this process, keyed by a per-browser session id. Nothing
is written to disk; everything is done in memory.
See decisions/0008-single-user-session-scoped.
"""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import secrets

import fitz  # PyMuPDF
from flask import (
    Flask, request, render_template, send_file, flash, redirect, url_for, session
)
from werkzeug.utils import secure_filename

from stamp_tescil import (
    load_tescil_map, STAMP_X, STAMP_Y, FONT_SIZE, FONT, COLOR,
)

app = Flask(__name__)
app.secret_key = "sgm-tescil-stamp"  # signs the session cookie / flash messages
# A batch of receipts, not one file: SGM PDFs are ~100 KB each, so this leaves
# room for a few hundred of them.
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB upload cap

# Server-side store: session id -> {"filename": str, "mapping": {key: tescil}}
SOURCES: dict[str, dict] = {}
# Server-side store: session id -> {"data": bytes, "name": str, "mimetype": str}.
# One pending download per session; the next batch replaces it.
DOWNLOADS: dict[str, dict] = {}


def current_source():
    """Return the uploaded-Excel record for this session, or None."""
    sid = session.get("sid")
    return SOURCES.get(sid) if sid else None


def stamp_bytes(pdf_stream, text: str) -> bytes:
    """Stamp `text` onto the first page of an in-memory PDF; return new PDF bytes."""
    doc = fitz.open(stream=pdf_stream.read(), filetype="pdf")
    page = doc[0]
    page.insert_text(
        (STAMP_X, STAMP_Y), text,
        fontsize=FONT_SIZE, fontname=FONT, color=COLOR,
    )
    out = doc.tobytes()
    doc.close()
    return out


def unique_name(name: str, taken: set[str]) -> str:
    """Return `name`, suffixed if needed, so two same-named uploads don't collide."""
    if name not in taken:
        taken.add(name)
        return name
    stem, _, ext = name.rpartition(".")
    n = 2
    while f"{stem}_{n}.{ext}" in taken:
        n += 1
    out = f"{stem}_{n}.{ext}"
    taken.add(out)
    return out


def build_manifest(source: dict, stamped: list, skipped: list) -> str:
    """Plain-text record of what the batch did, carried inside the zip.

    Skipped files are named with their reason here as well as on the page, so the
    zip is self-explanatory once it's been downloaded and the page is gone.
    See decisions/0006-skip-missing-keys-with-warning.
    """
    lines = [
        "SGM Tescil Stamper",
        f"Batch of {datetime.now():%Y-%m-%d %H:%M}",
        f"Excel source: {source['filename']} ({len(source['mapping'])} entries)",
        "",
        f"STAMPED ({len(stamped)})",
    ]
    for out_name, original, tescil in stamped:
        lines.append(f"  {original}  ->  {out_name}    Tescil No: {tescil}")
    if skipped:
        lines += ["", f"SKIPPED ({len(skipped)}) — not stamped, nothing was changed"]
        for name, reason in skipped:
            lines.append(f"  {name} — {reason}")
    lines.append("")
    return "\n".join(lines)


def build_zip(source: dict, stamped: list, skipped: list) -> bytes:
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as z:
        for out_name, _original, _tescil, data in stamped:
            z.writestr(out_name, data)
        z.writestr("MANIFEST.txt", build_manifest(
            source, [(n, o, t) for n, o, t, _ in stamped], skipped))
    return buf.getvalue()


@app.route("/")
def index():
    """Step 1: upload the Excel source (or jump to step 2 if already loaded)."""
    if current_source():
        return redirect(url_for("stamp_page"))
    return render_template("excel.html")


@app.route("/excel", methods=["POST"])
def upload_excel():
    file = request.files.get("excel")
    if not file or not file.filename:
        flash("Please choose an Excel file.", "error")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    if not filename.lower().endswith((".xlsx", ".xlsm")):
        flash("Please upload an Excel workbook (.xlsx).", "error")
        return redirect(url_for("index"))

    try:
        mapping = load_tescil_map(file.stream)
    except Exception as e:  # noqa: BLE001
        flash(f"Could not read that workbook: {e}", "error")
        return redirect(url_for("index"))

    if not mapping:
        flash("That workbook's FATURA sheet had no usable Fatura No / Tescil No rows.",
              "error")
        return redirect(url_for("index"))

    sid = session.get("sid") or secrets.token_hex(16)
    session["sid"] = sid
    SOURCES[sid] = {"filename": filename, "mapping": mapping}
    DOWNLOADS.pop(sid, None)  # a new source invalidates the previous batch
    flash(f"Loaded {len(mapping)} entries from “{filename}”.", "ok")
    return redirect(url_for("stamp_page"))


@app.route("/reset")
def reset():
    """Clear the loaded Excel so the user can upload a different one."""
    sid = session.pop("sid", None)
    if sid:
        SOURCES.pop(sid, None)
        DOWNLOADS.pop(sid, None)
    return redirect(url_for("index"))


@app.route("/stamp", methods=["GET"])
def stamp_page():
    """Step 2: upload SGM PDFs to stamp."""
    src = current_source()
    if not src:
        flash("Upload the Excel source first.", "error")
        return redirect(url_for("index"))
    pending = DOWNLOADS.get(session.get("sid"))
    return render_template(
        "stamp.html",
        source=src["filename"],
        count=len(src["mapping"]),
        pending=pending,
        # Set only on the redirect straight after a batch, so the download fires
        # once rather than on every later view of this page.
        auto=bool(request.args.get("ready")),
    )


@app.route("/stamp", methods=["POST"])
def stamp():
    src = current_source()
    if not src:
        flash("Upload the Excel source first.", "error")
        return redirect(url_for("index"))

    files = [f for f in request.files.getlist("pdf") if f and f.filename]
    if not files:
        flash("Please choose at least one PDF file.", "error")
        return redirect(url_for("stamp_page"))

    stamped: list[tuple[str, str, str, bytes]] = []  # (out_name, original, tescil, data)
    skipped: list[tuple[str, str]] = []              # (name, reason)
    taken: set[str] = set()

    for file in files:
        filename = secure_filename(file.filename) or "unnamed"
        if not filename.lower().endswith(".pdf"):
            skipped.append((filename, "not a PDF"))
            continue

        key = Path(filename).stem  # e.g. SGM2026000010413
        tescil = src["mapping"].get(key)
        if not tescil:
            # Skip, don't fail: one bad file must not sink the batch. The file is
            # left unstamped and named, here and in the zip's manifest.
            # See decisions/0006-skip-missing-keys-with-warning.
            skipped.append((filename, f"‘{key}’ was not found in “{src['filename']}”"))
            continue

        try:
            data = stamp_bytes(file.stream, tescil)
        except Exception as e:  # noqa: BLE001
            skipped.append((filename, f"could not be stamped ({e})"))
            continue

        stamped.append((unique_name(f"{key}_stamped.pdf", taken), filename, tescil, data))

    for name, reason in skipped:
        flash(f"Skipped “{name}” — {reason}.", "warn")

    if not stamped:
        flash("Nothing was stamped — no file matched a 'Fatura No' in the "
              "FATURA sheet. Check the file names.", "error")
        return redirect(url_for("stamp_page"))

    if len(stamped) == 1 and not skipped:
        out_name, _original, _tescil, data = stamped[0]
        payload, mimetype = data, "application/pdf"
    else:
        payload = build_zip(src, stamped, skipped)
        out_name = f"stamped_{datetime.now():%Y%m%d_%H%M%S}.zip"
        mimetype = "application/zip"

    DOWNLOADS[session["sid"]] = {"data": payload, "name": out_name, "mimetype": mimetype}
    flash(f"Stamped {len(stamped)} file(s)" +
          (f", skipped {len(skipped)}." if skipped else "."), "ok")
    return redirect(url_for("stamp_page", ready=1))


@app.route("/download")
def download():
    """Hand over the last batch. Kept until the next batch replaces it, so the
    link still works if the automatic download was blocked."""
    item = DOWNLOADS.get(session.get("sid"))
    if not item:
        flash("That download is no longer available — upload the PDFs again.", "error")
        return redirect(url_for("stamp_page"))
    return send_file(
        BytesIO(item["data"]),
        mimetype=item["mimetype"],
        as_attachment=True,
        download_name=item["name"],
    )


@app.errorhandler(413)
def too_large(_e):
    limit = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    flash(f"That upload is over the {limit} MB limit. Send the PDFs in smaller "
          "batches.", "error")
    return redirect(url_for("stamp_page" if current_source() else "index")), 302


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
