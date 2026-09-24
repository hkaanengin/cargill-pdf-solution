---
area: web
priority: medium
created: 2026-09-23
---
# 031 — Restyle the web app in the Workbench direction

Spec reference: **R30**, while keeping **R20**, **R21** and **R29** true.

## Problem

The templates are functional but plain. On 2026-09-23 the user picked the
Workbench direction from three drawn options ([[brainstorm/visual-refresh]]).

## Scope

Templates and CSS only: `base.html`, `excel.html`, `stamp.html` and
`result.html`. No route, no `stamper.py` change, and no new behaviour.

## Done when

- [x] All three steps use the Workbench shell: a dark ground, a sidebar with
      the steps and the loaded workbook, and the amber accent
- [x] The results page keeps R21's grouping. Outcomes are grouped under
      headings, not shown as the mockup's flat list
- [x] R20's case, nothing stamped, still says so and offers no download
- [ ] Flashes (operational errors, the 413) are still visible and readable
- [x] `tests/test_app.py` and `tests/test_summary.py` still pass
- [ ] The user has looked at it in a browser

## Notes

**Step 1 was never drawn.** The canvas covers the PDF step and the results. The
workbook step is built in the same shell by inference, not from a mockup.

**The mockup's "Routes to" column is dropped.** Showing it before upload would
mean restating R2–R5 in browser JavaScript, a second copy of the routing rule,
which [[decisions/0011-one-entry-point]] exists to avoid. The queue before
stamping lists file names only. The sheet appears on the results page, where
the server has decided it.

**Built 2026-09-23.** It waits on the user looking at it, which can happen in
the same browser session as 029's click-through.

- **`base.html` is the shell.** It has the CSS custom properties, the sidebar
  and a `stepitem` macro that marks each step done, active or todo. Each page
  fills `{% block sidebar %}`. Step 1 shows what the workbook needs, step 2
  shows the loaded workbook with a link to the last run, and step 3 shows the
  stamped count, a bar split by group, and the next actions. Below 760px the
  sidebar stacks above the content.
- **`result.html` keeps what the tests pin down.** The `<h2>` per group
  must stay bare because the heading test splits on it. The stamped row
  keeps the exact `name → <b>PO:…</b>` form. The sidebar has no `<h2>` and
  no download link, so R20's "no `href="/download"`" check still holds.
- **The fonts come from Google Fonts** (Space Grotesk, JetBrains Mono), with
  system fallbacks. That is an outside request from a hosted app. Worth a
  look in [[004-cloud-deployment]] if the deployment should make no
  third-party calls. Self-hosting the two fonts would be the fix.
- The "Tescil" page title is gone. It is now "PO Stamper".

**2026-09-23:** the user said the look is "ok for now", with more testing to come.
This task stays open until they say it is settled. Changes they want will be
added here, or as new tasks under [[032-ux-ui-rework]].
