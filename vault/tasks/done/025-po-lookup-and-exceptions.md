---
area: data
priority: high
created: 2026-09-22
completed: 2026-09-22
---
# 025 — Look up the PO, and name every way it can fail

Spec reference: **R8**, **R18**, **R19**, **R21**.
**Absorbs [[020-duplicate-dekont-keys]]**, whose rule is already decided.

## Problem

Given a key and a routed sheet, produce the PO — or a named reason there isn't
one. Four of R18's seven exception cases are decided here; the rest belong to
[[023-filename-routing]] (R5), [[007-verify-stamp-after-write]] (R17 and the
already-stamped input), and the app.

## The order of the checks is the requirement

Not an implementation detail. From [[020-duplicate-dekont-keys]]:

1. **The key matches more than one row** → exception, named as a **workbook**
   problem. Checked **first**, and per sheet rather than as a DEKONT special
   case — FATURA has no duplicates in this workbook and nothing guarantees next
   month's.
2. **The key is absent** → exception, named against the uploaded workbook.
3. **The row exists, `PO` is blank** → exception, distinct message.

13 of the 26 duplicated DEKONT keys have *both* rows empty and 7 have one of
each, so the order decides which message the user gets. Reporting "PO is empty"
for a key that appears twice sends them looking in the wrong place.

## Why duplicates matter more than they look

The six conflicting keys are listed in [[020-duplicate-dekont-keys]]. In every
pair the two rows agree on `Dosya No`, `Referans No` and `DEKONT TUTARI` —
nothing distinguishes them. Left as-is, an implementation returns whichever row
it met first and stamps a wrong PO onto a document that looks perfectly normal.
**R17 would not catch it**: the stamp renders fine, it is simply wrong. The app
never guesses.

## Done when

- [x] Returns the PO for a key matching exactly one row with a filled `PO`
- [x] The three checks run in the order above, each with its own reason string
- [x] The duplicate rule is written per sheet, not as a DEKONT branch
- [x] The duplicate message names it as a workbook data problem — the fix is in
      the spreadsheet, not the PDF (R21)
- [x] A near miss such as `SGM2026000011171 (1)` falls out as "key not found",
      with no normalisation attempted (R18, Q11)
- [x] An exception here never aborts anything — it is a value returned per file,
      not a raise that unwinds the batch (R19)
- [x] Tests cover: the 6 conflicting DEKONT keys; a duplicate whose rows are
      both empty (asserting *duplicate* is reported, not *empty*); a missing key;
      and the two empty-PO samples `SGM2026000010415` / `…0416`
- [x] [[020-duplicate-dekont-keys]] moves to `done/`

## Notes

`PO` is usually `int`, occasionally `str` — 89 ints and 1 string in FATURA.
Never assume the type; the value is stamped as text (R12) and the spec
explicitly does not format-check it ([[018-po-value-validation]], a non-goal).

The current sample inputs contain **no** duplicated key, so that test needs a
crafted workbook or a direct call into the index from
[[024-workbook-access]].

## What was built — 2026-09-22

`lookup_po(index, key, sheet) -> Lookup`, in `stamper.py`, and
`tests/test_lookup.py` beside it. The suite is **100 green**, up from 50.

Three design questions were open when this started; all three are settled in
[[decisions/0013-exceptions-as-returned-values]]:

- **It returns a value, it never raises.** `Lookup(po, problem, message)` —
  either a PO or a named reason, never both. R19 is then a property of the
  shape rather than something every future call site has to remember to wrap.
- **`Problem` is a `StrEnum` of four slugs** — `UNROUTABLE`,
  `NOT_IN_WORKBOOK`, `DUPLICATE_KEY`, `PO_BLANK`. The member is what
  [[028-summary-screen-and-run-flow]] groups on (R21); `message` is what it
  shows. Two fields, so rewording a message cannot change a grouping.
- **`sheet` accepts `None`.** This answers the question
  [[023-filename-routing]] left open: **yes**, an unroutable name is the same
  kind of outcome as a failed lookup. `lookup_po(index, *route_filename(name))`
  is therefore the whole of resolving one upload, and R18's R5 case is covered
  by a test in this suite instead of living in the web layer.

### What the checks look like

In the required order, and per sheet rather than per DEKONT:

```python
rows = index.get(sheet, {}).get(key, [])
if len(rows) > 1:  DUPLICATE_KEY
if not rows:       NOT_IN_WORKBOOK
if not rows[0]:    PO_BLANK
```

`index.get(sheet, {})` rather than `index[sheet]` is deliberate: a family
missing from a hand-built index answers "not in the workbook", which is true,
instead of raising a `KeyError` that becomes a 500 inside a request.

### Findings

- **The check order is genuinely load-bearing, and cheap to get wrong.** 13 of
  the 26 duplicated DEKONT keys are blank on *both* rows. A blank-first
  implementation passes a duplicate test written against the six conflicting
  keys and still reports "the PO is empty" for the other 13 — sending the user
  to fill in a PO when the real fault is a repeated row. There is now a test
  named for exactly that (`…reports_the_duplicate_not_the_blank`, on `919476`).
- **`str.isdigit()` is true for non-ASCII digits.** `'٤٥٢٢'.isdigit()` is
  `True`, so an Arabic-Indic-numeral filename routes to DEKONT under R4 and
  then fails lookup as a key the sheet does not have. The user is still
  correctly refused (R18) — only the *reason* differs from "unroutable", and no
  such filename is plausible here. Recorded rather than fixed; a narrowing to
  ASCII belongs to [[023-filename-routing]]'s rule, not to lookup.
- **Failure is the majority path in this workbook**, which is part of why
  raising was the wrong shape: 118/208 FATURA and 113/194 DEKONT rows have a
  blank `PO`.
- **Nothing in the spec turned out to be wrong.** R8, R18, R19 and R21 were
  implementable as written; the only additions are vocabulary, and they are in
  the decision record rather than the spec.

### What 026 inherits

`lookup.po` is never `None` and never `''` by the time [[026-stamp-the-po]] is
called — every blank and every ambiguity has already been refused here. 026 has
no empty-PO case of its own.
