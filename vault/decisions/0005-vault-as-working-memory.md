---
status: accepted
date: 2026-08-07
---
# 0005 — This vault is the project's working memory

## Decision

An Obsidian vault at `vault/` holds all volatile project knowledge: task status,
architecture, decisions, brainstorming, and a session log. `CLAUDE.md` holds only
stable facts plus a protocol telling each session to read and update the vault.

The root `to-do.md` was migrated into `tasks/` and deleted.

## Why

- **Re-explaining context every session was the actual problem.** A tracker that
  only a human maintains doesn't solve it; the protocol in `CLAUDE.md` does,
  because that file is loaded automatically every session.
- **One task per file** rather than a shared checklist, because tasks accumulate
  design questions and links. A 12-line checklist entry can't hold the collision
  rule discussion in [[001-multi-workbook-support]].
- **Inside the project, not `~/Documents/Obsidian/`.** This is the load-bearing
  part: `vault/*.md` is readable with plain Read/Grep, so the memory works even
  if the Obsidian MCP server is down or a session doesn't have it. The MCP is
  convenience; the file location is what makes it reliable.
- **Decisions separate from brainstorming**, so a future session can tell what's
  settled from what's still open and doesn't re-litigate old ground.

## Consequences

- Three sources of truth collapsed to one. `CLAUDE.md` must never regain a status
  section — that's the drift failure mode this was meant to fix.
- The `obsidian` MCP server, previously pointed at two unrelated opendota vaults,
  is now scoped to this project's vault only.
- Requires discipline: a session that doesn't update the vault leaves stale
  memory, which is worse than none because the next session trusts it. Mitigated
  by dated log entries making staleness visible, and by `tasks/_index.md` being
  the single place status is asserted.

## Consequence worth watching

`vault/` is excluded in `.dockerignore` but this project has no git repository
yet. When [[004-cloud-deployment]] adds one, the vault should be committed —
it's documentation, not secrets — while the workbook and `samples/` (formerly `sgm_folders/`) must not be.
