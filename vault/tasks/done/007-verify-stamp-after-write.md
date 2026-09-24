---
area: cli
priority: high
created: 2026-08-07
updated: 2026-09-22
completed: 2026-09-22
---
# 007 — Verify the stamp actually landed

## Problem

Nothing asserts the stamp is present in the output. `insert_text` is trusted to
have worked. If it silently no-ops — bad font, off-page coordinate, an unexpected
PDF structure — the pipeline reports success and produces an unstamped file that
looks correct until someone checks it by hand.

## Done when

- [ ] After writing, the output PDF is re-opened and searched for the stamped text
- [ ] A missing stamp is a loud failure, not a warning
- [ ] Verification runs in both the CLI and the web path
- [ ] Tested by deliberately forcing a bad coordinate and confirming it's caught

## How

PyMuPDF can search the written page for the string. Roughly: reopen the saved
bytes, `page.search_for(tescil_no)`, assert a non-empty result. Cheap — one extra
open per file.

Worth also asserting the hit is inside the page rectangle, which catches
off-page coordinates that [[008-pdf-layout-robustness]] is about.

## Notes

This is the cheapest insurance in the backlog and pairs naturally with
[[008-pdf-layout-robustness]] — the same check catches both classes of silent
failure. Consider doing them together.

## Rewritten against the spec — 2026-09-22

This task predates [[spec]] and describes verifying a `Tescil No`. Two things
change, and the scope grows by one check.

### What R17 actually requires

- The string searched for is the literal **`PO:<value>`**, prefix included — not
  the bare number. That is what distinguishes the app's own stamp from a number
  that merely happens to appear in the document. The user's reasoning, closing
  Q10.
- A file that fails verification is **withheld**, not delivered with a warning
  (R18, closing Q3). "A loud failure" in the original *Done when* meant aborting;
  it does not. The batch continues (R19) and the file is named on the summary
  screen (R21).
- There is no CLI to verify in any more — R27 is withdrawn,
  [[decisions/0011-one-entry-point]]. One path, one check.

### The new half: refuse an input that is already stamped

R18 also makes **an input already carrying a `PO:` stamp** an exception — it
should not occur, and if it does the file is refused rather than stamped twice
(Q9). That is the same `search_for("PO:")` mechanic pointed at the input instead
of the output, so it belongs here rather than in a task of its own.

Note what makes it cheap: a DEKONT scan has **no text layer at all**, so any
`PO:` found in one can only have been added. A FATURA e-Fatura does have a text
layer, so a false positive is conceivable — confirm none of the five clean
FATURA samples trips it.

### The fixture is real

`samples_stamped_reference/917034` reads `PO:452220729` with the final `0`
wrapped onto the next line — a text box one character too narrow.
`search_for("4522207290")` finds nothing. It is a genuine defective document
produced by the current manual process, and it is exactly the failure R17
exists to catch. Use it — [[017-dekont-stamp-placement]] found it.

### Done when — superseding the list above

- [x] After stamping and **before delivery**, the output is reopened and searched
      for the literal `PO:<value>` (R17)
- [x] A miss **withholds** that file; the batch continues and the summary names
      it (R18, R19, R21)
- [x] An input already carrying a `PO:` stamp is refused, not stamped twice
      (R18, Q9)
- [x] None of the five clean FATURA samples is falsely flagged as pre-stamped
      — *there are seven, not five. None of the seven is flagged, and neither
      are the three DEKONT ones*
- [x] A deliberately bad coordinate is caught by a test
- [x] `917034` from `samples_stamped_reference/` is a regression fixture proving
      the wrapped-digit case fails verification

### What this check cannot do

Text search confirms the stamp **exists**, never **where it landed** — a stamp
rendered on top of existing content passes. That is not a verification problem
and is not solved here: it is handled by choosing good coordinates in
[[017-dekont-stamp-placement]] and confirming them in
[[010-confirm-placement-across-layouts]]. Recorded in [[spec]] under *A note on
Q10* so it is not mistaken for an oversight.

Asserting the hit lies inside the page rectangle is still worth doing and still
overlaps [[008-pdf-layout-robustness]].

## Built — 2026-09-22

The code is in `stamper.py` and the tests in `tests/test_verify.py`. The suite
went from 161 to **241 tests, all passing**. The reasoning is in
[[decisions/0015-verification-and-prestamp-detection]].

**Three functions, not one.** The frame declared a single `verify()` to serve
both checks. The two checks turned out to ask different questions:

| | Looks for | Pages |
|---|---|---|
| `verify(pdf, po)` — R17 | exactly `PO:<po>`, and not followed by another digit | page 1 only (R28) |
| `already_stamped(pdf)` — R18 | any `PO:` followed by a digit, with no letter just before it | every page |

`stamp_checked(pdf, po, family) -> Stamped` wraps `stamp()` in both checks. It
returns a `Stamped`, which is shaped like `Lookup`: either a PDF or a `Problem`,
never both. `pdf is None` is what "withheld" means. **029 should call
`stamp_checked()`, never `stamp()` directly.** `Problem` gained
`ALREADY_STAMPED` and `STAMP_NOT_VERIFIED`, so R18 has all seven cases.

**Findings:**

- **The manual stamps look nothing like ours.** They are black `MinionPro` on
  the DEKONTs and grey `0x666666` `ArialMT`/`Tahoma` on the FATURAs. So
  detection matches text, never style. All six references are caught.
- **Off-page text is invisible to extraction.** `page.get_text()` clips to the
  page by default. A stamp drawn entirely off the page returns nothing, and one
  running off the right edge returns `P`. So an exact `PO:<po>` match also
  proves the stamp is on the page. The "inside the page rectangle" check this
  task suggested comes for free, and the tests cover the stamp being below,
  left of, and off the right edge of the page.
- **PyMuPDF raises nothing for an off-page coordinate.** The bad-coordinate
  test moves `STAMP_POSITION` to `(300, 2000)`, and `stamp()` returns normally.
  Only verification catches it, which is exactly the silent failure R17 is for.
- **`917034` is confirmed as the regression case.** Its whole manual stamp for
  `4522207290` fails `verify()`. Three of the whole manual stamps pass the
  same search, so what fails is the missing digit, not the font.
- **`917034` and `SUB2026000019890` share a PO** (`4522207290`) in the
  workbook, one in each sheet. That is not an R18 duplicate, which is per key,
  per sheet. Recorded so nobody mistakes it for one.
- **`search_for()` is case-insensitive**, so it would match `po:` or `Depo:`.
  The checks use a case-sensitive regex over `get_text()` instead.
- `tests/test_frame.py` lost its stub test, because no stubs are left.
  `tests/conftest.py` gained `already_stamped_bytes`, the named way to reach
  `samples_stamped_reference/` that its docstring had set aside for this task.

**Not done here:** placing the withheld file on the summary screen is
[[028-summary-screen-and-run-flow]]'s job, which groups on `Problem` and shows
`message`, just as for a `Lookup`.
