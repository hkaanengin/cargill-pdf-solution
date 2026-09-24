---
status: accepted
date: 2026-09-20
---
# 0010 — The supplied sample PDFs were de-stamped to make them inputs

## Decision

Six of the ten PDFs in `sgm_folders/` arrived **already carrying a PO stamp on
the page**, printed by whatever process does this work today. They have been
de-stamped in place so they function as clean inputs. The originals are kept
untouched in **`samples_stamped_reference/`**, suffixed `.STAMPED.pdf`.

Affected: `SGM2026000011171`, `SUB2026000019889`, `SUB2026000019890`, `917031`,
`917034`, `917035`. The four older `SGM2026000104xx` files were already clean.

## Why

The user supplied them as inputs and renamed them from `PO<value>-<key>.pdf` to
`<key>.pdf`. The rename changed the filename only — the mark was **on the page**,
not in the name, so all six were still stamped.

Left as they were, they were unusable in both directions: feeding them to the
app would print a **second** PO onto a document that already had one, and any
verification of stamping would be reading someone else's stamp rather than ours.

That the mark was added afterwards, rather than being part of the source
document, is established two ways:

- The three DEKONT files are **pure scans with no text layer** — 13–14
  characters on the whole page, all of it the `PO:` mark, over 50–104 images.
  Someone added a text layer to a scanned image.
- `SGM2026000010413` and `SGM2026000011171` are the same e-Fatura layout from
  the same issuer. The older one has no PO mark; the newer one does.

## How

Targeted redaction of the stamp spans with PyMuPDF: `add_redact_annot(rect,
fill=False)` then `apply_redactions(images=PDF_REDACT_IMAGE_NONE,
graphics=PDF_REDACT_LINE_ART_NONE)` — erase the glyphs, paint nothing over the
scan beneath. `917034` needed two spans, its stamp having wrapped across two
lines.

Verified afterwards: no `PO:` text remains on any page; invoice text dropped by
exactly the stamp's 13–14 characters and DEKONT pages to zero; page counts
unchanged; and a rendered pixel diff against the originals differs by
0.04–0.08%, consistent with removing thin glyphs and nothing else. Two were
also checked by eye.

## Consequences

- `sgm_folders/` now covers all three filename shapes with clean inputs: 5
  FATURA-family, 3 DEKONT-family, plus 2 whose workbook `PO` is empty and which
  therefore exercise R18.
- `samples_stamped_reference/` is the **ground truth for stamp placement** — the
  only evidence of where a human puts this mark, and the basis of
  [[017-dekont-stamp-placement]] and [[spec]] Q5/Q8. It must not be fed to the
  app or cleaned up.
- This is the one deliberate exception to
  [[decisions/0003-never-modify-originals]]. That decision governs the
  **stamping pipeline**, which still never writes to its inputs. This was a
  one-off data-preparation step, done at the user's explicit request, with the
  originals preserved.

## Revisit if

Genuinely unstamped originals of these six turn up, in which case use those and
keep the de-stamped copies only as a cross-check. The de-stamping is faithful
but it is still a reconstruction.
