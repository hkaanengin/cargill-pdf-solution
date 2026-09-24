---
area: data
priority: high
created: 2026-09-20
completed: 2026-09-22
---
# 020 — A key matching more than one row is an exception

Spec reference: **R8**, **R18**, **R19**, **R21**. Closes Q7 in [[spec]].

## Problem

R8 assumes `Fatura No` identifies exactly one row in the routed sheet. In the
new workbook that is false for DEKONT: **26 keys appear on two rows each**, 52
rows in total.

| Case | Keys | Consequence |
|---|---|---|
| Both rows carry a **different** `PO` | **6** | unresolvable — see below |
| One row has a `PO`, the other is empty | 7 | probably "take the filled one", but unstated |
| Both rows empty | 13 | falls into R18 either way, harmless |

The six conflicting keys are the ones that matter:

| Key | Row A | Row B |
|---|---|---|
| `919290` | 62 → `4522245727` | 78 → `4522320826` |
| `919303` | 63 → `4522245728` | 80 → `4522320828` |
| `919466` | 68 → `4522245733` | 95 → `4522320847` |
| `919467` | 67 → `4522245732` | 94 → `4522320844` |
| `919468` | 66 → `4522245731` | 92 → `4522320836` |
| `919471` | 69 → `4522245734` | 96 → `4522320838` |

In every one of those pairs the two rows agree on `Dosya No`, `Referans No` and
`DEKONT TUTARI`. **Nothing in the row distinguishes them.** A lookup cannot
choose correctly on the data available.

## Why this is not a small thing

As specified, an implementation would return whichever row it encountered first
and stamp that PO. The document would look perfectly normal and carry the wrong
purchase order — the outcome [[spec]] names as the worst in the project. There
is no signal at stamping time that anything went wrong, so R17 would not catch
it either: the stamp renders fine, it is just wrong.

## Answered — 2026-09-20

**The duplicates are a data-entry mistake on the workbook side**, confirmed by
the user. There is no tiebreak to find, because there is no legitimate second
row to choose between.

So: a key matching more than one row in its sheet is an **exception for that
input** (R18). The app never guesses. Every other file in the batch is still
stamped and delivered (R19), and the failure is named on the summary screen at
the end of the run (R21) along with every other exception and success.

This closes [[spec]] Q7. What remains is implementation.

### Worth noting for whoever builds it

- The rule is **per sheet, not per DEKONT**. FATURA has no duplicate keys in
  this workbook, but nothing guarantees next month's. Write it as "the key
  matched more than one row", not as a DEKONT special case.
- **Detection must survive the empty-PO cases.** 13 of the 26 duplicated keys
  have *both* rows empty and 7 have one of each. Whether "duplicate key" is
  reported, or "empty PO" is reported, depends on the order the checks run.
  Duplicate-key should be decided first: it is the more specific fault, and
  reporting "PO is empty" for a key that appears twice would send the user
  looking in the wrong place.
- The exception message should name the fault as a **workbook problem**, since
  that is what it is and the fix is in the spreadsheet, not the PDF.
- The 6 conflicting keys listed above make the obvious test fixture; the
  current sample inputs contain none, so a test needs a crafted workbook or a
  direct call into the lookup.

## Done when

- [x] The user states the rule — 2026-09-20
- [x] [[spec]] Q7 becomes a requirement — R18 gained the case
- [x] Lookup reports the exception on a key matching more than one row, in
      either sheet, and checks for it before checking whether `PO` is empty —
      built in [[025-po-lookup-and-exceptions]], 2026-09-22
- [x] A duplicated key is covered by a test — all six conflicting keys, plus
      `919476` (blank on both rows) and `919479` (one blank), in
      `tests/test_lookup.py`
- [x] The summary names it as a workbook data problem (R21) — the message
      reads "a data-entry problem in the workbook, so the fix is in the
      spreadsheet, not the PDF", and a test asserts it

## Closed — 2026-09-22

Built as part of [[025-po-lookup-and-exceptions]], which owns the code. Nothing
about the rule changed between the user's answer on 2026-09-20 and the
implementation: a key on more than one row of the routed sheet is refused, in
either sheet, before its `PO` is looked at.

One thing this task predicted correctly and it is worth recording that it did.
"Whether *duplicate key* is reported, or *empty PO* is reported, depends on the
order the checks run" — 13 of the 26 duplicated keys are blank on both rows, so
a blank-first implementation is wrong for half of them while still passing a
test written against the six conflicting keys. `tests/test_lookup.py` has a
test named for that case, on `919476`.

The refusal is a returned value rather than a raised exception —
[[decisions/0013-exceptions-as-returned-values]] — so R19 holds by
construction: a duplicated key cannot end the batch.

**The 26 duplicates are still in the workbook.** Nothing here fixes the data;
the app refuses to guess and names the fault. Whether the workbook should be
checked for duplicates *at upload time*, rather than one file at a time, is the
parked discussion in [[030-workbook-verification]] ([[spec]] Q15, phase 2).
