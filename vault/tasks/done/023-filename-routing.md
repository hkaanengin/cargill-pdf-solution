---
area: code
priority: high
created: 2026-09-22
completed: 2026-09-22
---
# 023 — Route a filename to its sheet

Spec reference: **R1**, **R2**, **R3**, **R4**, **R5**.

## Problem

The current code has no routing at all. `stamp_tescil.py` globs `SGM*.pdf` and
`app.py` takes `Path(filename).stem` straight to one hardcoded FATURA mapping.
`SUB` and digit-named files are not merely mishandled — they are invisible.

## What makes this safe

Measured in [[architecture/data-layout]]: no key shape appears in both sheets.
FATURA holds 164 `SUB` and 44 `SGM` keys and **zero** all-digit keys; DEKONT
holds 194 all-digit keys and **zero** non-digit keys. Routing on filename shape
alone is therefore unambiguous, which is what R2–R4 rest on.

## Scope

Pure function, no I/O, no PDF, no workbook. Given a filename it returns the
family — FATURA, DEKONT, or unroutable — and the key.

**The key is the filename with `.pdf` removed and nothing else done to it**
(R1). No normalisation, no trimming of suffixes, no case folding.

## The distinction worth getting right

Routing and lookup fail differently, and `SGM2026000011171 (1).pdf` shows why:
it begins `SGM`, so it **routes successfully** to FATURA, and then fails at
lookup because the key is not in the sheet. R18's near-miss case (Q11) is
therefore a [[025-po-lookup-and-exceptions]] concern, not a routing one. Only a
name matching none of R2–R4 is unroutable (R5).

## Done when

- [x] `SGM…` and `SUB…` route to FATURA (R2, R3); an all-digit name routes to
      DEKONT (R4)
- [x] Digit names of **4, 5 and 6** digits all route — any length is valid (R4)
- [x] A name matching none of them is returned as unroutable, not guessed at
      (R5)
- [x] The key is the stem verbatim (R1); a test asserts no PDF is opened to get
      it
- [x] Tests cover all ten sample filenames plus the `(1)` near-miss and an
      unroutable name

## Notes

Case: every observed key is upper-case `SGM`/`SUB`. Whether `sgm2026…` should
route is **not stated by the user** — treat as unroutable for now and raise it
if a real file turns up, rather than quietly lower-casing. Same reasoning as
R18's refusal to repair near misses.

---

## What was built — 2026-09-22

`route_filename()` in `stamper.py`, and `tests/test_routing.py` — 17 assertions
across 10 test cases. The suite is 31 green, up from 14. Nothing else moved:
`app.py` and `stamp_tescil.py` still run the old Tescil path, as the build order
intends until [[029-wire-app-to-module]].

```python
key = Path(name).stem
if key.startswith(("SGM", "SUB")):   # R2, R3
    return Routed(key, Family.FATURA)
if key.isdigit():                    # R4, any length
    return Routed(key, Family.DEKONT)
return Routed(key, None)             # R5
```

## Findings

**The declared signature was refined, as [[022-core-module-and-tests]]
permitted.** The frame declared `route_filename(name) -> Family | None`, but
this task's own scope asks for "the family **and** the key", and R1 defines the
key. Returning only the family would have left every caller deriving the key
itself — R1 implemented in as many places as there are callers. It now returns
a `Routed` NamedTuple of `(key, family)`, so R1 lives in one line. Tuple-shaped
on purpose: `route_filename(n) == ("917031", Family.DEKONT)` reads well in a
test, and `.family` reads well at a call site.

**Routing stays total — it never raises, and R5 is `family=None`.** R18 groups
"filename matches no known pattern" with the lookup exceptions, so the obvious
alternative was to raise the same exception type. That type does not exist yet:
[[025-po-lookup-and-exceptions]] owns designing it, and 022 deliberately
declared nothing so it would be designed once against the requirement. So
classification here returns a value and the exception layer sits above it.
**A note for 025:** if it wraps routing and lookup in one exception type, this
is where the `None` becomes one — and that is a change of layer, not of rule.

**The unroutable case still carries its key.** R21 accounts for *every* input by
name, so the caller needs something to print even when no sheet was chosen.

**Lower case is left unroutable, and that is a decision, not an omission.** The
Notes above called it; the implementation and a named test now hold it. `sgm…`
matches no rule and is refused rather than folded — the same refusal to repair
that R18 makes for near misses. If a real lower-case file appears, the test is
the place that says so.

**`Path(name).stem` strips whatever final extension is there, not specifically
`.pdf`.** `917031.txt` would yield the key `917031`. Faithful to R1 in every
case the app can actually meet, since only PDFs are uploaded, and the idiom
`app.py` already uses. Worth knowing rather than worth guarding.

**`str.isdigit()` is true for non-ASCII digits** — `"١٢٣"` routes to DEKONT and
then fails lookup, where an ASCII-strict test would have failed at routing.
Both are R18 exceptions naming the file, so the user sees the same thing with a
different reason. Left as-is, matching the `stem.isdigit()` the fixture tests
already use.

**The near-miss test is the one that matters most here.**
`SGM2026000011171 (1).pdf` routes *successfully* to FATURA. If a later session
is tempted to make routing reject it, R18's near-miss case has moved to the
wrong layer — the sheet is what proves a key absent, not the name.

**`test_frame.py` lost its `route_filename` stub case**, as that file's own
docstring instructs: a deleted parameter is a function that now has a real
test elsewhere. Four stubs remain — 024, 025, 026, 007.
