#!/usr/bin/env python3
"""Stamp the Tescil No from the Excel workbook onto SGM receipt PDFs.

For each SGM PDF, derive its key from the filename (e.g. SGM2026000010413),
look up the matching row in the FATURA sheet (Fatura No == key), read the
Tescil No, and stamp it in bold red onto the PDF. Stamped copies go to output/;
originals are never modified.
"""

from pathlib import Path
import argparse
import sys

import openpyxl
import fitz  # PyMuPDF

# --- config ---
WORKBOOK = "SUBASI FATURA-DEKONT AGUSTOS.xlsx"
SHEET = "FATURA"
KEY_HEADER = "Fatura No"       # column holding SGM number
VALUE_HEADER = "Tescil No"     # column holding value to stamp

SGM_DIR = Path("sgm_folders")
OUTPUT_DIR = Path("output")

# stamp placement (target box: 250<x<350, 200<y<250); baseline start point
STAMP_X = 240
STAMP_Y = 170
FONT_SIZE = 14
FONT = "helvetica-bold"
COLOR = (1, 0, 0)  # red


def load_tescil_map(workbook) -> dict[str, str]:
    """Return {SGM key -> Tescil No} from the FATURA sheet, matched by header.

    `workbook` may be a file path or a file-like object (e.g. an upload stream).
    Raises ValueError if the sheet or expected columns are missing.
    """
    wb = openpyxl.load_workbook(workbook, data_only=True)
    if SHEET not in wb.sheetnames:
        raise ValueError(
            f"Sheet '{SHEET}' not found in the workbook. Sheets present: {wb.sheetnames}"
        )
    ws = wb[SHEET]
    rows = ws.iter_rows(values_only=True)
    header = [str(c).strip() if c is not None else "" for c in next(rows)]
    try:
        key_i = header.index(KEY_HEADER)
        val_i = header.index(VALUE_HEADER)
    except ValueError:
        raise ValueError(
            f"Expected columns '{KEY_HEADER}' and '{VALUE_HEADER}' in sheet "
            f"'{SHEET}'. Found headers: {header}"
        )

    mapping: dict[str, str] = {}
    for row in rows:
        key = row[key_i]
        val = row[val_i]
        if key is None or val is None:
            continue
        mapping[str(key).strip()] = str(val).strip()
    return mapping


def stamp_pdf(pdf_path: Path, text: str, out_path: Path) -> None:
    doc = fitz.open(pdf_path)
    page = doc[0]
    page.insert_text(
        (STAMP_X, STAMP_Y), text,
        fontsize=FONT_SIZE, fontname=FONT, color=COLOR,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    doc.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdfs", nargs="*", help="specific PDF paths; default: all in sgm_folders/")
    args = ap.parse_args()

    try:
        mapping = load_tescil_map(WORKBOOK)
    except (ValueError, FileNotFoundError) as e:
        raise SystemExit(f"Error reading '{WORKBOOK}': {e}")

    if args.pdfs:
        pdfs = [Path(p) for p in args.pdfs]
    else:
        pdfs = sorted(SGM_DIR.glob("SGM*.pdf"))

    if not pdfs:
        print("No PDFs to process.")
        return 1

    ok = 0
    skipped: list[str] = []
    for pdf in pdfs:
        key = pdf.stem  # e.g. SGM2026000010413
        tescil = mapping.get(key)
        if not tescil:
            print(f"  SKIP  {pdf.name}: '{key}' not found in the Excel", file=sys.stderr)
            skipped.append(pdf.name)
            continue
        out = OUTPUT_DIR / pdf.name
        stamp_pdf(pdf, tescil, out)
        print(f"  OK    {pdf.name} -> {out}  ({tescil})")
        ok += 1

    print(f"\nDone. Stamped {ok}, skipped {len(skipped)}.")
    if skipped:
        # Repeated at the end so a long run's skips can't scroll past unnoticed.
        print(
            f"\nWARNING: {len(skipped)} file(s) were NOT stamped — no matching "
            f"'{KEY_HEADER}' in '{WORKBOOK}':",
            file=sys.stderr,
        )
        for name in skipped:
            print(f"  - {name}", file=sys.stderr)
    return 0 if not skipped else 2


if __name__ == "__main__":
    sys.exit(main())
