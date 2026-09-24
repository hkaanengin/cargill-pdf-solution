---
status: accepted
date: 2026-09-22
---
# 0013 — An exception is a returned value, not a raise

## Decision

Taken during [[025-po-lookup-and-exceptions]], which [[spec]] and the task both
left to the implementation. Three parts:

- **`lookup_po()` returns a `Lookup`, it never raises.** `Lookup` is
  `(po, problem, message)`: either a PO to stamp, or a `Problem` and the reason
  in words. Never both — `po` is `None` whenever `problem` is set.
- **`Problem` is a `StrEnum` of slugs**, one member per group the summary
  screen needs (R21): `UNROUTABLE`, `NOT_IN_WORKBOOK`, `DUPLICATE_KEY`,
  `PO_BLANK`. The member is what the app groups on; `message` is what it shows.
- **`lookup_po()` accepts `sheet=None`.** An unroutable filename (R5) is
  reported by the same call, as `Problem.UNROUTABLE`, so
  `lookup_po(index, *route_filename(name))` is the whole of resolving one
  upload. This is the question [[023-filename-routing]] left open, answered
  yes: R5 and a failed lookup are the same kind of outcome.

## Why

**R19 is a structural property, not a promise to remember.** "An exception never
aborts the batch" is satisfied by a returned value in a way it can never be by a
raise. A raise needs a `try` around every call, in a loop over whatever the user
uploaded; the day someone adds a call site without one, a single bad filename
ends the run and the other nine files are lost. A value has no such failure
mode. The task file said this outright — "a value returned per file, not a raise
that unwinds the batch" — and the frame's placeholder docstring said "raise";
the task won, because it is the one that cites the requirement.

**The alternative that was rejected:** a `LookupError` subclass carrying a
`.reason`. It reads more like idiomatic Python and it is how the old `app.py`
would have done it. It was rejected on the above, and on a second point:
exceptions are for the unexpected, and in this workbook **failure is the common
path**. Over half of all rows have a blank `PO` (118/208 FATURA, 113/194
DEKONT). Raising on the majority case is the wrong shape.

**Why a slug enum and a separate message.** R21 groups the summary by outcome,
so the app needs an identity to group on; R18 says the user is told *why*, so it
needs a sentence. One string doing both means rewording a message silently
changes a grouping. Two fields, and the slugs never appear on screen.

**Why the message is a fragment.** It is written to follow the filename —
`917031.pdf — on 2 rows of the DEKONT sheet…` — so it opens lower case and ends
without a stop. The existing `app.py` already flashes exactly this shape
(`Skipped "x" — not a PDF.`). How it is finally presented is
[[028-summary-screen-and-run-flow]]'s to decide; this keeps both options open.

**Why one total lookup rather than two call sites.** The app has to account for
every input file (R21), and an unroutable name is one of the things it must
account for. Splitting it — routing returns `None`, and the caller writes its
own branch for the R5 message — puts one of R18's cases in the web layer, where
no test in this suite reaches it. Folding it in means there is exactly one
function to call per file and exactly one place that can name a reason.

## Consequences

- [[026-stamp-the-po]] takes `lookup.po`, which is never `None` and never `''`
  by the time it is called. It has no blank-PO case of its own.
- [[028-summary-screen-and-run-flow]] groups on `Problem` and renders `message`.
  It inherits four members and will add the two that [[007-verify-stamp-after-write]]
  owns — a pre-stamped input, and a stamp that failed to render.
- Adding a new exception case means adding a `Problem` member. That is the
  single place to look for "what can go wrong with one file".
- `Lookup.ok` exists as a property so call sites read as intent rather than as a
  `None` check.
