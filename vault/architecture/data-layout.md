# Data layout

The shape of the inputs. **Re-verified 2026-09-20** against the new workbook and
the new sample PDFs. Requirements live in [[spec]] (R6–R10); this file records
what the data actually looks like.

## `SUBASI FATURA-DEKONT AGUSTOS.xlsx`

Same filename as the August workbook it replaced, but a different file — far
more rows, and `PO` populated.

- Sheets, in position order: `PIVOT TABLE` (empty), **`FATURA`** (sheet 2),
  **`DEKONT`** (sheet 3). Position is authoritative and the name is not read at all — R6, R7.
- Header in row 1, data from row 2.

| Sheet | Data rows | Key column | Key type | `PO` filled |
|---|---|---|---|---|
| `FATURA` | 208 | `Fatura No` | `str`, 16 chars | 90 (43%) |
| `DEKONT` | 194 | `Fatura No` | `int`, 5–6 digits | 81 (42%) |

Both sheets also carry `Dosya No`, `Tescil No` and a `PO Tarihi`. Columns are
matched by header text, never by letter — [[decisions/0004-match-columns-by-header]].
**The two sheets do not agree on where they are:** `Fatura No` is column 3 in
FATURA and column 5 in DEKONT, and `PO` is column 14 and column 12. R8 is not a
precaution against a future edit — a by-letter loader cannot read both sheets
today.

### Keys

- **FATURA** keys are strings: 164 begin `SUB`, 44 begin `SGM`. All exactly 16
  characters. Zero all-digit keys.
- **DEKONT** keys are integers: 191 six-digit, 3 five-digit (`14898`, `15052`
  ×2). Range `14898`–`926227`; the bulk sit in `915622`–`926227`. Zero
  non-digit keys.
- **Routing is therefore unambiguous** — no key shape appears in both sheets,
  which is what makes R2–R4 safe.

### Gotchas — each one produces silently wrong output

- **DEKONT keys are `int`, FATURA keys are `str`.** Always `str(cell).strip()`,
  never `cell.strip()`.
- **`.strip()` every string cell.** Values carry trailing whitespace — and at
  least one carries a **trailing newline**: `FATURA` row 127 has `PO` as the
  string `'4522320805\n'`. Use bare `.strip()`, not `.rstrip(' ')`.
- **27 FATURA keys carry trailing spaces** — `'SGM2026000010589    '`. Measured
  2026-09-22 while implementing [[024-workbook-access]]; it had not been
  recorded before. The `.strip()` is therefore load-bearing on the **key**, not
  only on the value: without it 27 of 208 rows are unfindable, and each one
  would be reported to the user as a missing key (R18) rather than stamped.
- **`PO` must be matched exactly, never by prefix.** Both sheets carry a second
  column whose header starts `PO` — `PO Tarihi` in FATURA, `PO TARIHI` in
  DEKONT — and in FATURA it sits immediately after `PO`. A `startswith` match
  stamps a date onto a customs document.
- **`PO` is usually `int`, occasionally `str`.** 89 ints and 1 string in FATURA,
  81 ints in DEKONT. Never assume the type.
- **Over half of all rows have an empty `PO`.** 118/208 FATURA and 113/194
  DEKONT. The R18 empty-PO exception is the common path, not an edge case.
- **Open with `data_only=True`** or formula cells return formulas.
- **A key with a leading zero could not be recovered** — Excel stores `091702`
  as `91702`. The user confirmed on 2026-09-20 that such keys do not occur, in
  filenames or in the workbook, so no normalisation rule exists — [[spec]] Q6.
- **26 DEKONT keys are duplicated** across two rows each. `Fatura No` is not a
  unique key in DEKONT — [[spec]] Q7, [[020-duplicate-dekont-keys]]. Broken
  down 2026-09-22: **6** carry two genuinely different `PO` values with nothing
  in the row to tell them apart, **7** pair a `PO` with a blank, and **13** are
  blank on both rows. All 26 are R18 exceptions either way — the requirement is
  "matches more than one row" — but the 6 are where guessing would put a wrong
  PO on a customs document.

### What does *not* hold

`PO` does **not** follow `Dosya No` across the two sheets — 18 of 70 comparable
pairs disagree. `Tescil No` does (192/192), which is what made the cross-check
look plausible. Measured and closed 2026-09-20; see [[spec]] Q1.

## `samples/`

Renamed from `sgm_folders/` on 2026-09-23 ([[019-tescil-to-po-rename]]): it
holds `SUB` and digit-named files too, and it is a test fixture, not an input
directory.

Ten clean input PDFs covering all three filename shapes. All A4 (595 × 842 pt),
unrotated.

| File(s) | Type | Pages | Text layer | Workbook `PO` |
|---|---|---|---|---|
| `SGM2026000010413`, `...0414` | e-Fatura | 1 | yes | present |
| `SGM2026000010415`, `...0416` | e-Fatura | 1 | yes | **empty** — R18 cases |
| `SGM2026000011171` | e-Fatura | 1 | yes | present |
| `SUB2026000019889`, `...9890` | e-Fatura | 1 | yes | present |
| `917031`, `917034`, `917035` | DEKONT | **2** | **none** | present |

- **The two document families look nothing alike.** An `SGM`/`SUB` file is a
  born-digital e-Fatura with a real text layer, a QR block and a logo. A
  digit-named file is a **two-page scan** — 50–104 embedded images per page and
  no text at all. This is why R12 makes position type-dependent.
- The filename **is** the key; content is never parsed — R1.
- Six of these arrived already stamped by the current manual process and were
  de-stamped to make them usable as inputs —
  [[decisions/0010-destamped-sample-pdfs]].

### Page layout — measured 2026-09-22

Established while settling the stamp coordinates
([[017-dekont-stamp-placement]], [[010-confirm-placement-across-layouts]]) by
rendering page 1 of every clean sample at 1px/pt and reducing it to an ink map.

- **There are exactly two layouts, and they are the two routing families.**
  `Family` is therefore both the sheet a file is looked up in *and* the layout
  it is stamped on. `SUB` shares the e-Fatura layout with `SGM` — no third
  layout exists in the data.
- **Within a family the layout does not vary at all.** Measured clearance
  around the stamp is *identical* across all seven FATURA files, August batch
  and September batch alike. These are fixed templates, which is what makes one
  absolute coordinate per family defensible.
- **Free space, as the union of the ink on every sample in the family:**

  | Family | Empty band | Stamp goes at |
  |---|---|---|
  | FATURA | `x≈165–595`, `y≈0–70` (above the letterhead) | `(300, 45)` |
  | DEKONT | full width, `y≈400–726` (between table and footer) | `(220, 475)` |

- **Page 2 of a DEKONT is a different document** — a `TAHSİLAT MAKBUZU`
  receipt, not a continuation of page 1. R28's "page 1 only" is not a
  simplification for convenience; stamping page 2 would put the PO on an
  unrelated document.
- **The DEKONT footer is pinned at `y≈727`** on all three samples, and the
  line-item table grows downward from `y≈400` into the band the stamp sits in.
  Every sample has a one-row table. A long table is the one layout risk in the
  data — [[008-pdf-layout-robustness]].
- All ten are A4 (595 × 842) and unrotated. `917031`/`917035` measure
  595.3 × 841.9; the `SGM`/`SUB` files measure exactly 595 × 842.

## `samples_stamped_reference/`

The six supplied files **as delivered**, before de-stamping. Not inputs — they
are the ground truth for where a human puts the stamp, and the evidence behind
[[spec]] Q5 and Q8, **both now closed**. Measured positions are recorded in
[[017-dekont-stamp-placement]]; the app's own coordinates landed on top of them
([[decisions/0014-stamp-placement-per-family]]). Do not feed these to the app —
feeding one back is precisely the already-stamped exception in R18.

**`917034` is a defective reference.** Its PO reads `PO:452220729` with the
final `0` wrapped onto the next line — a text box one character too narrow.
It looks stamped and is wrong, which is the exact failure R17 exists to catch,
found in real production output. R12a now requires `insert_text` rather than
`insert_textbox` so the app cannot reproduce it.

## `sample_grid_preview.png`

A 2026-08 SGM sample under a 50pt coordinate grid, used to pick the original
stamp position. **Stale, and deliberately left that way.** It shows only one of
the two layout families and the coordinate chosen off it is withdrawn — worse,
that coordinate was wrong for the family it was chosen *on* (`y=170` sits in the
recipient address block). Q5 was settled 2026-09-22 by the per-family ink-map
method in [[017-dekont-stamp-placement]], which supersedes a single-sample grid
image rather than needing it regenerated.
