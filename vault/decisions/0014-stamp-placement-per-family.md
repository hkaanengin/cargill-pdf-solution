---
status: accepted
date: 2026-09-22
supersedes: 0002-stamp-placement
---
# 0014 — Stamp placement, one coordinate per family

Replaces [[decisions/0002-stamp-placement]], whose single `(240, 170)` is
withdrawn. Settles [[spec]] **Q5**, which the user deliberately left to be
worked out during [[017-dekont-stamp-placement]] against the real samples.

## Decision

The stamp is `PO:<value>`, **helvetica-bold, 14pt, red `(1, 0, 0)`** (R12
unchanged), drawn on **page 1 only** (R28), at a **baseline** whose coordinate
depends on the routed family (R12a):

| Family | Routed from | Baseline `(x, y)` | Lands in |
|---|---|---|---|
| **FATURA** | `SGM`, `SUB` | **`(300, 45)`** | the top whitespace band, right of the logo |
| **DEKONT** | all-digit | **`(220, 475)`** | the empty mid-page band under the line-item table |

Coordinates are **absolute points**, top-left origin, and assume A4
(595 × 842) — see *Consequences*.

## Why

**Both numbers were measured, not chosen by eye.** Page 1 of all ten clean
samples was rendered at 1px/pt and reduced to an ink map on a 5pt grid, then
unioned per family, so a candidate is only clear if it is clear on *every*
sample of that family.

- **The two families have genuinely disjoint free space.** FATURA's is
  `x≈165–595, y≈0–70`; DEKONT's is the full width between `y≈400` and `y≈726`.
  A single coordinate cannot serve both, which is what R12a already said and
  what this confirms with numbers.
- **Both chosen points sit where the current manual process already puts the
  stamp** — the six files in `samples_stamped_reference/` measure at
  `x≈294–317, y≈38–47` for FATURA and `x≈218–243, y≈464–480` for DEKONT
  ([[017-dekont-stamp-placement]]). Matching human practice means the person
  reading the document finds the PO where they already look. Nothing else
  recommended a different spot, so there was no reason to invent one.
- **The measured clearance is comfortable and identical across every sample of
  a family**, because both layouts are fixed templates:

  | Family | above | below | left | right |
  |---|---|---|---|---|
  | FATURA | >200pt | 32pt | 143pt | >200pt |
  | DEKONT | 80pt | >200pt | >200pt | >200pt |

  Measured against the widest stamp the data can produce — `PO:` plus a
  10-digit PO is 102.7pt at 14pt bold.
- **14pt stands.** R12's size was marked revisitable during this task; rendered
  against both layouts it is legible without dominating, so it is confirmed
  rather than changed. It is also markedly clearer than what the manual process
  produces — grey 7.8–10.8pt on invoices, black 12pt on DEKONTs.
- **Drawn with `insert_text`, never `insert_textbox`.** A text box is what
  wrapped the last digit of `917034`'s PO onto a second line in the reference
  sample — a document that looks stamped and is wrong. `insert_text` does not
  wrap. This is a placement decision because it is the placement API that
  caused the defect.

## Confirmed by the user — 2026-09-22

Not just measured and eyeballed by the session: **the user looked at every
stamped sample and confirmed it.** The two coordinates above are approved, as
is 14pt bold red.

They were shown a proof sheet rendering all eight stampable samples in both
families, with each crop switchable between the clean input, the app's stamp
and the hand-placed stamp at identical geometry — https://claude.ai/artifact/BhZADA5bXawBGFbauYGjrf. Built from a throwaway
prototype; `stamper.py` was not touched.

## Consequences

- **Absolute points, stated deliberately rather than by omission** (the
  question [[017-dekont-stamp-placement]] asked). Every sample seen is A4 and
  unrotated, so page fractions would buy nothing today and would obscure the
  measurements above. A non-A4 page puts the stamp in the wrong place with no
  error — that is [[008-pdf-layout-robustness]], unchanged by this decision.
- **The DEKONT band is the one that can close.** Its line-item table grows
  downward from `y≈400` toward a footer pinned at `y≈727`. Every sample has a
  one-row table, leaving 80pt of clear space above the stamp; a DEKONT with
  roughly five or more rows would reach it. Not observed, not guessed at — 
  recorded as a finding on [[008-pdf-layout-robustness]].
- FATURA has no equivalent risk: its stamp is above the entire document body,
  in a header band that is fixed template on all seven samples.
- The two coordinates belong to [[026-stamp-the-po]] as constants keyed by
  `Family`. Making them configurable is [[009-configurable-stamp-style]], which
  is more attractive now that there are provably two of everything.

## Revisit if

A non-A4, rotated, or multi-column layout appears; a DEKONT arrives with a
long line-item table; or the workbook starts producing PO values longer than
10 digits.
