---
status: accepted
date: 2026-09-22
---
# 0015 — Two stamp checks, and one function that runs both

Made while building [[007-verify-stamp-after-write]]. It implements [[spec]]
R17 and the last two cases of R18. No requirement changed.

## Decision

1. **`verify(pdf, po)` passes only if exactly `PO:<po>` is on page 1**, and
   the next character is not a digit. Page 1 only, because R28 makes page 1
   the only right place for the stamp.
2. **`already_stamped(pdf)` flags any `PO:` followed by a digit on any page**,
   unless a letter comes straight before it. The match is case-sensitive. It
   does not look for this file's PO, and it ignores font and colour.
3. **Both read `page.get_text()`**, which clips to the page by default. They
   do not use `search_for()`.
4. **`stamp_checked(pdf, po, family)` is the only stamping call the app
   makes.** It returns a `Stamped`, meaning either the bytes or a `Problem`,
   never both, and it never raises. This follows
   [[decisions/0013-exceptions-as-returned-values]].

## Why

- **Two functions, because they are two questions.** R17 asks whether *this*
  PO is where it belongs. R18 asks whether *anyone's* PO is anywhere. A
  different PO already on the page is the worse case for R18, because a
  second stamp would leave the document naming two POs. It is also
  invisible to a search for this file's PO. The frame's single `verify()`
  could not answer both.
- **The match stops at the last digit.** Without that, `PO:45222072` would
  pass a check for `PO:452220729`. `917034`'s wrapped stamp shows that a PO
  with one digit missing is a real defect, not a theoretical one.
- **Text, not style.** The manual stamps are black MinionPro on the DEKONTs
  and grey Arial or Tahoma on the FATURAs. Anything keyed on red Helvetica
  would miss all six.
- **"No letter before it" and "case-sensitive"** keep a Turkish word ending
  in `po` or `PO` (`Depo:`, `DEPO:`) from reading as a stamp. None of the ten
  clean samples contains `po:` in any case, so this is a guard, not a fix for
  something observed.
- **Clipped extraction instead of a separate on-page check.** Text drawn off
  the page is not extracted at all. Text running off an edge is extracted
  cut short. So one exact match proves both that the stamp exists and that it
  is on the page. `search_for()` was rejected because it is case-insensitive.
- **`stamp_checked()` exists so "withheld" cannot be forgotten.** If the app
  called `stamp()` and then `verify()`, withholding the file would depend on
  every caller remembering the second call. Here a failed check has no bytes
  to deliver.

## Consequences

- Our own output reads as stamped. A file downloaded and uploaded again is
  refused under R18, not stamped twice. The tests assert this.
- Text search still says nothing about *where on the page* the stamp landed,
  or what it covers. That stays with the measured coordinates,
  [[decisions/0014-stamp-placement-per-family]], as [[spec]]'s note on Q10
  says.
- A manual stamp written without the colon, or as an image with no text
  layer, would not be detected. None has been seen. If one appears, the rule
  is changed here first.
