---
created: 2026-09-24
---
# 0019 — Versions are git tags

## Decision

A version of the app is an **annotated git tag** on `master`, named
`vMAJOR.MINOR.PATCH`, and pushed to `origin`. The user creates and pushes the
tags, as they do commits.

- **`v1.0.0`** is on `9d80856` ("Manual deploy decision, close task 036"),
  created 2026-09-24. It is the first deployed release at
  `https://po-vim.help`.
- Work is done on `master`, not on a checked-out tag. Checking out a tag gives
  a detached HEAD, and commits made there belong to no branch.
- A published tag is never moved or re-pointed. A fix gets the next version.
- Pushing a tag does not push the branch. Push both:
  `git push && git push origin vX.Y.Z`. On 2026-09-24 only the tag was pushed
  at first, and `master` showed "ahead of origin/master by 1 commit".

**Recommended, not confirmed by the user** (inference, so treat as an open
point rather than a rule):

- Tag every deploy, so a rollback target always exists
  ([[architecture/deployment]] → *Roll back*).
- Version bumps: PATCH for fixes, MINOR for new behaviour that breaks nothing,
  MAJOR for changes to the workbook layout, filenames or output naming that the
  user must adapt to.
- To fix an old release while `master` holds unfinished work, branch from the
  tag (`git switch -c hotfix-X.Y.Z vX.Y.Z`), tag there, and merge back into
  `master`. Rarely needed with one developer.

## Why

The user asked on 2026-09-24 to "create tags for my repository to keep versions
of this application", and created and pushed `v1.0.0` themselves. Deploys are
by hand ([[decisions/0018-manual-deploy-no-cicd]]) and ship whatever is checked
out, so a named tag is the simplest way to know what is live and to redeploy a
known-good version. Annotated tags record who tagged, when, and why. Lightweight
tags do not.
