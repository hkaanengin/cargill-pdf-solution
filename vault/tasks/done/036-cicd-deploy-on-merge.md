---
area: infra
priority: medium
created: 2026-09-23
completed: 2026-09-24
---
# 036 — Deploy to Oracle on every merge into master

> **Closed 2026-09-24 without building anything.** Offered Q17's options (a)
> start–deploy–stop and (c) pull on boot, the user said: "I neither liked (a)
> or (c). I think I will deploy it manually. lets get rid of cicd-deployment
> completely." R37 is withdrawn, CI/CD is a non-goal, and Q17–Q19 are settled
> in [[spec]]. Why: [[decisions/0018-manual-deploy-no-cicd]]. The user's
> redeploy checklist is `DEPLOY.md` in the repo root, gitignored at their
> request.
>
> **What was measured before closing:** the full suite takes about 3 s
> locally. On a clean `git archive HEAD` checkout, with no workbook and no
> `samples/`, **206 pass and 256 fail or error**, so a GitHub runner could not
> have run it as the repo stands. Q19 was answered before the closure: the
> user deploys outside 14:00–15:00.

Satisfied [[spec]] R37, now withdrawn. **Starts after the first manual deploy** of
[[004-cloud-deployment]] is done and verified. That order is the user's.

## Decide first — [[spec]] Q17–Q19

- **Q17 — merge while the VM is stopped.** It is stopped 23 hours a day.
- **Q18 — what runs as a test.** The suite needs customs data that is not in
  the repo.
- **Q19 — merge while the app is in use.** A deploy wipes the session.

## Constraints already known

- **Free tiers.** GitHub Actions is free and unlimited for public repos, and
  about 2,000 minutes a month for private repos on the free plan. A deploy is
  a few minutes. Oracle API calls (start/stop instance) cost nothing. The build
  stays on the VM, as today, so nothing new is needed on Oracle's side.
  *From memory, not checked 2026-09-23:* confirm the current Actions limits
  and whether the repo is private.
- **Secrets the pipeline would hold:** an SSH key that can log in to the VM
  (its own key, not the user's `~/.ssh/id_ed25519`). For Q17(a), also an
  OCI API key and the instance OCID. Each belongs in GitHub encrypted secrets
  and nowhere in the repo.
- **R36 still holds:** the pipeline sends code, never data. `deploy.sh`'s
  file list is already the right set.
- **Supersedes part of [[decisions/0017-oracle-cloud-always-free-vm]]:**
  "deploy by copying from the dev machine" becomes the fallback rather than
  the path. `deploy.sh` stays useful by hand.

## Done when

- [ ] Q17–Q19 answered and folded into [[spec]]
- [ ] A merge into `master` deploys to `po-vim.help` with no manual step
- [ ] Behaviour matches the Q17 and Q19 answers, tested for real once each
- [ ] No secret in the repo; the pipeline's SSH key is its own and revocable
- [ ] The runbook in [[architecture/deployment]] describes the pipeline
