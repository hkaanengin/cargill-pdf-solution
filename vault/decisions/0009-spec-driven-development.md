---
created: 2026-09-20
---
# 0009 — The project runs a spec-driven loop

The user's call on 2026-09-20, restarting the project after a break: *"I would
like to use spec driven development on this project."*

## What this settles

Work moves through five steps, in order, and each has one home:

| Step | Home |
|---|---|
| Spec | [[spec]] |
| Plan | `architecture/`, `decisions/` |
| Tasks | `tasks/` |
| Execute | the code |
| Update state | back into the vault |

- **[[spec]] is the source of truth for requirements**, numbered `R1…Rn`. Tasks
  cite IDs rather than restating them.
- **No code without a requirement.** Work nothing asks for means the spec is
  wrong or the work isn't wanted. Fix the spec first, with the user.
- **Never assume a requirement.** Anything not plainly stated is an open
  question in [[spec]], not a default. Explicit user instruction, same day.
- **The loop is written into `CLAUDE.md`**, not just recorded here, because
  `CLAUDE.md` is what loads into every session automatically. A process nobody
  reads at the start of a session is not a process.

## Why

The vault already had four of the five steps and had been maintaining them well
— Plan, Tasks, Execute and Update state were all real, and task files carried
genuine revision history. What was missing was the Spec layer: requirements were
implicit in working code, non-goals were scattered across eight decision files,
and acceptance criteria existed per-task but never for the product.

Adopting the loop was therefore mostly *adding the missing layer*, not
restructuring. `decisions/` was explicitly kept as-is: it is the reasoning trail,
plain spec-driven development has no equivalent to it, and rewriting those files
into spec prose would have traded something better for something more standard.

**The trap that was named and avoided:** the loop assumes greenfield — spec
first, then code. This project had working code, so the spec written on
2026-09-20 is a *retro-spec*. The failure mode is reading the code, writing down
what it does, and calling it a requirement — producing a document that is green
on day one and has told you nothing. The test applied instead: **at least one
requirement must currently fail.** Several do — R11 (PO, not Tescil), R2–R6
(routing), R14 (renaming), R17 (verification), R26 (auth).

## Consequences

- `CLAUDE.md` was rewritten around the loop, and its reading order now starts at
  [[spec]] rather than [[Home]].
- Questions moved: [[spec]] *Open questions* is now the single home for them.
  [[open-questions]] becomes historical — the record of how 0007 and 0008 were
  reached.
- The user handles git and commits. The Execute step ends at "implemented and
  tested"; committing is not Claude's.
- Superseded decisions are **not deleted**. They keep their reasoning and gain a
  pointer to [[spec]] — see [[019-tescil-to-po-rename]].
