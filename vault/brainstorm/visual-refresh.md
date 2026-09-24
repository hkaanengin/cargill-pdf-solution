---
created: 2026-09-23
---
# Visual refresh of the web app

The user asked on 2026-09-23 to make the site "a little bit more appealing".
They said they did not know what they wanted and left the direction open. They
also asked for somewhere to try out ideas.

**Nothing in [[spec]] asks for this yet.** Before any template changes, the
direction they choose becomes a requirement (or a note under R29), and then a
task. That order is what CLAUDE.md sets.

## Three directions, drawn on a design canvas

Canvas: https://claude.ai/artifact/46qrMmGwS8cc1KJuPbsozi (private to the user).
Each direction has an upload screen and a results screen. Both use the real
outcomes of the ten samples: 8 stamped and 2 with a blank PO.

- **A · Ledger** is calm and paper-like, with a serif headline, a
  results table, and a side card explaining how filename shapes route to sheets.
- **B · Workbench** is dark and dense, a tool. A sidebar shows the steps,
  the workbook facts, and an 8/10 progress bar. The queue and results are
  monospace lists with status dots.
- **C · Stamp** is bold, cream and red, with the rubber stamp as the brand.
  Results are shown as cards, each a mini document carrying its stamp badge.

Each direction has an accent-colour tweak. The user can edit the text, colours
and layout on the canvas directly.

## Things a redesign must not change

These are the spec's rules. Only the look may change:

- R21: every input appears in the summary, grouped by outcome.
- R29: the six steps, in order, with the download and summary on one screen.
- R20: when nothing was stamped there is no download, and the page says so.

## Outcome — 2026-09-23

The user chose **B · Workbench**. It is now R30 in [[spec]], built in
[[031-workbench-visual-style]]. The page title question was settled there too:
"Tescil" is gone from the title. The user may want UX/UI changes later, parked
as [[032-ux-ui-rework]].
