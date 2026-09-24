# cargill-pdf-solution

A small Flask web app that stamps a **PO number** onto customs document PDFs.

Upload the Excel workbook and the PDFs. For each PDF, the app picks the sheet
from the filename (`SGM`/`SUB…` → FATURA, all digits → DEKONT), looks up the
row's `PO`, stamps `PO:<value>` on page 1, and returns it as
`PO<value>-<original>.pdf`. One file downloads as a PDF, several as a zip.
Files it could not stamp are listed with the reason.

Live at `https://po-vim.help` (up daily 14:00–15:00 Istanbul time).

## Run locally

```bash
python3 -m venv .venv
.venv/bin/python3 -m pip install -r requirements-dev.txt

.venv/bin/python3 app.py          # http://localhost:8000
.venv/bin/python3 -m pytest       # tests
```

## Docker

```bash
docker build -t sgm-stamper .
docker run -p 8000:8000 sgm-stamper
```

## Deploy

```bash
deploy/deploy.sh ubuntu@<vm-ip>
```

See `vault/architecture/deployment.md`.

## Layout

| Path | What |
|---|---|
| `app.py` | Flask app: upload, call, render |
| `stamper.py` | Routing, lookup, stamping, naming, packaging |
| `i18n.py` | Turkish and English strings |
| `tests/` | pytest suite |
| `deploy/` | Compose, Caddy, VM setup and deploy scripts |
| `vault/` | Spec, architecture, decisions, tasks |

The spec is `vault/spec.md`.
