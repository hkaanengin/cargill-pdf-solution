---
created: 2026-09-24
---
# 0018 — Deploy by hand, no CI/CD

## Decision

There is **no pipeline**. The user deploys a new version by hand from their
Mac: start the VM if it is stopped, run `deploy/deploy.sh ubuntu@<ip>`, and
stop the VM again if they started it. R37 (deploy on merge) is withdrawn and
[[036-cicd-deploy-on-merge]] closed unbuilt. The step-by-step checklist is
`DEPLOY.md` in the repo root. It is **gitignored by the user's choice**, so it
exists only on their machine. The versioned runbook stays in
[[architecture/deployment]].

## Why

The user's words, 2026-09-24: "I neither liked (a) or (c). I think I will
deploy it manually. lets get rid of cicd-deployment completely."

The options put to them for Q17 (a merge while the VM is stopped) each added
something the manual path does not need:

- **(a) The pipeline starts the VM, deploys, and stops it.** This needs an
  Oracle API key and an SSH key stored as GitHub secrets. It must also avoid
  stopping a VM the user is using, and takes an estimated 3–6 minutes a run.
- **(c) The VM pulls `master` when it starts.** This needs a deploy key on the
  VM and puts the whole repo there. A failed deploy is only noticed when the
  site misbehaves.

Q18 added a third cost: the tests need the workbook and `samples/`, which are
not in the repo. On a clean checkout 206 tests pass and 256 fail or error, so
a pipeline would either test less or hold real customs data as a secret.

Deploys are rare and made by one person, who already has the data and the
SSH key on their Mac. The manual path runs the full suite locally in about
3 seconds and ships only the named build files
([[decisions/0017-oracle-cloud-always-free-vm]]).

## Revisit if

Someone other than the user needs to deploy, or deploys become frequent enough
that the manual steps are a burden. Either would start as a new requirement in
[[spec]].
