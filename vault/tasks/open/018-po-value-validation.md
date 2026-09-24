---
area: data
priority: low
created: 2026-09-20
---
# 018 — Should the PO value be checked before it is stamped?

Spec reference: **non-goal** in [[spec]] — deferred by explicit decision on
2026-09-20, recorded here rather than dropped.

## The question

The spec takes the `PO` cell as-is and stamps it. No format check. The user's
call: *"Lets keep this as a to-do/discussion later... Lets just make sure that
we get the correct PO number from the excel."*

So the priority is **reading the right cell**, not validating its contents.

## Why it may still be worth doing

A format guard catches a whole class of failure that R17 cannot. R17 confirms
the PO *rendered onto the page*; it says nothing about whether the value was the
right one. If a column shifts and the app reads a neighbouring cell, R17 passes
happily and the document is wrong — the exact outcome the spec calls the worst
in the project.

The two PO values supplied as examples were `4522142137` and `4522182195`: both
10 digits, both beginning `45`. **Two examples is not a format** — recorded as
observation, not as a rule.

## Done when

- [ ] Enough real PO values exist to say whether they follow a reliable shape
- [ ] A decision is recorded either way — guard, or explicitly no guard
- [ ] If a guard: a value failing it becomes an exception under R18

## Needs first

The new workbook. The `PO` column is empty in all 22 data rows of the only
workbook in the repo, so there is nothing to characterise yet.
