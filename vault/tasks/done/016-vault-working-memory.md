---
area: docs
created: 2026-08-07
completed: 2026-08-07
---
# 016 — Set up this vault as project working memory

## What it was

Re-explaining project state at the start of every Claude session was the
recurring cost. With the project heading toward cloud hosting, the amount worth
remembering was about to grow.

## Outcome

- `vault/` created **inside the project**, so notes are readable with plain
  Read/Grep and don't depend on the Obsidian MCP server being up.
- Structure: `tasks/` (open · blocked · done, one file per point),
  `architecture/`, `decisions/`, `brainstorm/`.
- Root `to-do.md` migrated into individual task files and deleted. Backlog items
  gained the design questions and dependencies a flat checklist had no room for.
- Five previously-implicit decisions written up in `decisions/`.
- Five open questions captured in [[open-questions]].
- `CLAUDE.md` rewritten to stable facts plus a session protocol.
- The `obsidian` MCP server re-scoped from two unrelated opendota vaults to this
  one. That misconfiguration is why unrelated vaults had been showing up here.

Full reasoning in [[0005-vault-as-working-memory]].

## What writing it up revealed

The tasks sorted into a dependency order that wasn't visible in the flat list:
[[005-shared-session-state]] blocks essentially all cloud work, and question 1 in
[[open-questions]] — internal tool vs external product — gates the entire cloud
track.
