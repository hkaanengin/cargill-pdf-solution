---
status: open
created: 2026-08-07
updated: 2026-09-16
---
# Open questions

Unresolved things that shape multiple tasks. Each should eventually become a
decision or a task. **A session that can get one of these answered should ask.**

## 3. Should originals ever be overwritten?

Currently a firm no — [[decisions/0003-never-modify-originals]]. Worth confirming
this matches how the output is actually used. If someone is manually copying
`output/` back over the sources, that's a workflow the tool should support
properly rather than leave to hand-copying.

Less pressing now that the web app is the product: it never touches originals,
it returns downloads.

## 4. Can the same `Fatura No` appear in two months?

Blocks the collision rule in [[001-multi-workbook-support]]. If invoice
numbers are globally unique, merging workbooks is trivial. If they repeat with
different Tescil numbers, merging is unsafe and months need to be first-class.

Answerable by checking a second month's workbook against August.

---

## Answered

### 1. Who are the "other users"? — answered 2026-09-08

A few known users, provisioned by hand; not external customers. See
[[decisions/0007-user-model-small-known-group]].

### 2. Will future SGM PDFs share the current layout? — still unknown, but parked

Not answerable yet: the user has no real SGM PDFs beyond the original 4 samples
and said they'd deal with it later.
[[010-confirm-placement-across-layouts]] moved to `blocked/` on 2026-09-08.
Until then the (240, 170) coordinate is unvalidated beyond one layout.

> **Closed 2026-09-22.** Both tasks are done. The coordinate was not merely
> unvalidated, it was wrong for *both* layouts — replaced by `(300, 45)` for
> FATURA and `(220, 475)` for DEKONT,
> [[decisions/0014-stamp-placement-per-family]]. Kept as written; this file is
> historical.

### 5. Why do keys go missing from the Excel? — no longer blocking, 2026-09-08

Still unknown, but [[decisions/0006-skip-missing-keys-with-warning]] deliberately
treats a typo'd filename and an absent invoice row identically: skip, warn by
name. If they ever need different handling that's a new decision, not this one.

### 6. Who uploads the Excel workbook? — answered 2026-09-16

Neither option. The user chose a third: *"Lets make this for one user only where
only the current session matter. In that session, we upload excel, then pdf
file/s, then we download files."*

So: the person stamping uploads the workbook, every session, and nothing
persists between sessions. See [[decisions/0008-single-user-session-scoped]].
This closed [[005-shared-session-state]] unbuilt, shrank
[[003-auth-and-multi-user]] to one shared password, and left
[[001-multi-workbook-support]] with almost nothing to do.

It also confirmed [[decisions/0001-excel-per-session-upload]] rather than
overturning it.

<details>
<summary>The question as it stood before it was answered</summary>

New on 2026-09-08, and now the one that gates the most.

The user described the flow as *"upload pdfs into the web site and
receive/download stamped pdfs back"* — no mention of the workbook. Today every
user uploads it themselves each session
([[decisions/0001-excel-per-session-upload]]). Two very different shapes:

- *Each user uploads the workbook too* → today's flow stands. Per-session state
  is real, and [[005-shared-session-state]] needs a shared backend (Redis or
  similar) before hosting.
- *One maintainer loads the month's workbook, everyone else only touches PDFs* →
  the mapping becomes one shared server-side object. [[005-shared-session-state]]
  mostly evaporates, [[001-multi-workbook-support]] becomes "which month is
  loaded", and [[003-auth-and-multi-user]] gains a second role (who may replace
  the workbook).

Cheap to ask, and it changes what gets built first. **Ask before starting 005.**

</details>
