---
area: infra
priority: high
created: 2026-08-07
---
# 004 — Deploy to a cloud platform

The goal that most other tasks feed into: host this so other people can use it.

## Problem

It runs locally and in Docker on a laptop. Nothing exists for hosting — no
platform chosen, no CI, no secret management, no logs, no domain.

## Done when

- [ ] Reachable at a stable URL by someone who is not on this machine
- [ ] Deploys from a repo push rather than a manual `docker build`
- [ ] Secrets come from the platform's secret store, not the image
- [ ] Logs and errors are visible after the fact
- [ ] A rollback path exists

## Depends on

- ~~[[005-shared-session-state]]~~ — closed 2026-09-16, see below
- ~~[[003-auth-and-multi-user]]~~ — **no longer blocks this** (2026-09-23): the
  user postponed the gate, [[spec]] R26 amended. `SECRET_KEY` from env is done;
  HTTPS moved here.

## Prerequisite that's easy to miss

**This project is not a git repository.** `git init`, a remote, and a `.gitignore`
covering `.venv/`, `output/`, `__pycache__/`, and the source data are step zero
for any push-to-deploy setup. The workbook and `samples/` contain real
customer data and must not be committed.

## Notes

Platform not chosen — see [[brainstorm/cloud-hosting-options]]. The image already
runs gunicorn, so most container platforms will take it close to as-is.

## Unblocked and cheaper — 2026-09-16

[[decisions/0008-single-user-session-scoped]] closed [[005-shared-session-state]]
without building anything, which removes the session backend from this task's
shopping list: no managed Redis, no external service, no extra secret.

**It adds one hard requirement instead, and everything depends on it being right:**

- [x] **Run exactly one gunicorn worker** (`--workers 1`). Done 2026-09-16 —
      the Dockerfile said `--workers 2`, which was the bug 005 described sitting
      live in the image: Excel uploaded to worker A, PDF posted to worker B, "no
      source loaded", intermittently. Now `--workers 1 --threads 4` with the
      `gthread` class, so one process keeps the state and threads keep the page
      responsive during a batch. **Do not raise the worker count.**
      *Unverified in a build* — the Docker daemon wasn't running on 2026-09-16,
      so the edited CMD has never been executed. The first `docker build && docker
      run` should confirm gunicorn takes the flags and the app answers on 8000;
      it's a flag change to a valid exec-form CMD, so a surprise is unlikely, but
      it hasn't been seen working.
- [ ] Pick a platform that doesn't quietly run multiple instances. Scale-to-zero
      is fine and even good here; **scale-to-many is not** — an autoscaler is the
      same bug wearing a different hat. Cap max instances at 1.
- [ ] Generous request timeout: a batch of PDFs takes longer than a single one,
      and the default 30s gunicorn timeout could cut a large batch off
      ([[002-batch-upload-zip]] now accepts up to 200 MB per upload).

The git-repository prerequisite above is unchanged and is still step zero.

## Memory on a free tier — raised 2026-09-22

The user mentioned it while settling 027: the app will most likely run on a
free-tier host. Size of the *download* does not matter (see
[[027-output-naming-and-packaging]]). **Memory does.** A batch is held
entirely in process RAM: uploaded PDFs, stamped copies and the zip, plus the
last download kept in `DOWNLOADS` until the next batch. `MAX_CONTENT_LENGTH`
is 200 MB, so a maximum upload could need about 3× that. Many free tiers give
512 MB. Real sizes: DEKONT scans are about 0.7–0.8 MB each, e-Faturas about
50 KB, so 100 files is about 40 MB. **Open question for when this task
starts:** lower the cap to fit the chosen tier, or leave it. Not decided and
not assumed.

## Platform chosen, image verified — 2026-09-23

- **Platform: Oracle Cloud Always Free VM** —
  [[decisions/0017-oracle-cloud-always-free-vm]]. The user had an account.
- **The upload cap is settled:** 100 MB, [[spec]] R34. On A1 the memory worry
  above mostly goes away, but the user chose the cap.
- **Up and down by hand** ([[spec]] R35): 2–3 hours a day, started and stopped
  by the user. This replaces the "stable URL, always on" assumption in *Done
  when*. The URL must still be stable across a stop and a start.
- [x] **First real Docker build** (arm64, image 227 MB). gunicorn took the
      flags and booted one `gthread` worker. A curl walk through the running
      container worked: workbook uploaded → three PDFs posted → zip downloaded.
      The zip held `PO4522207293-917031.pdf` and `PO4522142137-SGM2026000010413.pdf`,
      and the blank-PO `SGM2026000010415` was left out, as it should be.
- [x] **`.dockerignore` recreated** — see [[014-docker-packaging]].
- [x] `SECRET_KEY` read from the environment, with a random fallback.

### Left for the deploy session

1. Create the VM: A1 shape if capacity allows, Ubuntu, and open 80/443 in the
   security list. Check the home region (0017, *verify*).
2. Install Docker, `git clone`, `docker build`, and run the container with
   `--restart unless-stopped` and `-e SECRET_KEY=…`.
3. **HTTPS: needs a hostname — ask the user**: their own domain, or
   `<ip>.sslip.io`. Caddy in front, auto Let's Encrypt.
4. **Start/stop: ask the user which.** Stopping the container over SSH is
   fastest and keeps the IP. Stopping the VM saves nothing on the free tier
   and needs a reserved public IP to keep the URL stable. Check Oracle's
   idle-reclamation policy against either choice (0017).
5. Logs: `docker logs` is the minimum. Rollback: rebuild the previous commit.

## Schedule, no-disk rule, HTTPS options — 2026-09-23 (later)

The user answered the questions above, and added two things:

- **[[spec]] R35 rewritten:** the app is up **every day from 14:00 to 15:00
  Istanbul time** (11:00–12:00 UTC; Türkiye has no DST), automatically. The
  user starts it by hand outside that window when needed.
- **[[spec]] R36, new:** no uploaded PDF touches the server's disk. **A real
  gap was found and fixed:** Werkzeug writes any upload over 500 KB to a
  temporary file, and DEKONT scans are ~0.8 MB. `app.py` now sets an
  `InMemoryRequest` whose upload stream is a `BytesIO`, and
  `test_uploads_over_500_kb_never_touch_disk` fails without it. The image was
  rebuilt and re-walked. The container wrote nothing to disk except Docker's
  own `/etc` files and Python bytecode.
  **Consequence for the reverse proxy: use Caddy, not nginx.** nginx buffers
  large request bodies to a temporary file by default. Caddy streams them.
  Recheck this when Caddy's config is written.
- **Region:** Frankfurt ([[decisions/0017-oracle-cloud-always-free-vm]]).
- **A domain is not needed.** The options put to the user were a free
  `<ip>.sslip.io` name with a normal Let's Encrypt certificate, or a
  certificate for the bare IP (Let's Encrypt has issued these since Jan 2026,
  but only as 6-day certificates, and Caddy's support is still rough).
  Plain HTTP is ruled out by R26. **Waiting on the user.**
- **Container stop vs VM stop:** put to the user with pros and cons.
  Recommended: **stop the VM**, scheduled with OCI's scheduler, because a VM
  that runs all day and works one hour of it matches Oracle's idle-reclamation
  test. **Waiting on the user.**

## Answered, files written — 2026-09-23 (evening)

- **VM stop**, chosen by the user. **Domain `po-vim.help`** (Namecheap), bought
  by the user. **The region stays Frankfurt**: it cannot change, and it would
  not help. All three are recorded in [[decisions/0017-oracle-cloud-always-free-vm]].
- The user asked what reclamation means in practice. Oracle **stops** the idle
  instance, and the next scheduled start brings it back. Only A1 capacity at
  start-up can get in the way.
- Written: `deploy/compose.yaml`, `deploy/Caddyfile`, `deploy/setup-vm.sh`,
  `deploy/deploy.sh`. The compose stack was tested locally: the app is
  read-only, and the walk works through Caddy. **Runbook:
  [[architecture/deployment]].**
- *Done when* adjusted: "deploys from a repo push" became `deploy.sh` from the
  dev machine, for the reason in 0017. "Reachable at a stable URL" now means
  during the R35 window, or whenever the user has started the VM.

### Left — needs the user's console access

- [x] Steps 1–8 of the runbook: the instance, security list, IP, DNS, setup,
      deploy, and the schedule (2026-09-24)
- [x] Confirm `https://po-vim.help` from outside and run a real stamp
      (2026-09-24). The logs have not been looked at yet.
- [ ] After the first scheduled stop and start: did the app come up by itself?
      (Oracle's docs say an ephemeral IP stays through a stop, so no reserved
      IP was planned. Confirm it did.)
- The runbook was rewritten step by step for the user on 2026-09-23, with
  console paths, Namecheap records, the scheduler policy and troubleshooting.

## Session 2026-09-24 — Step 1 done, paused before Step 2

- **The VM exists**: `po-stamper`, A1.Flex 1 OCPU / 6 GB, Ubuntu 24.04,
  **AD-3**, public IPv4 on, the Mac's `id_ed25519.pub` pasted. The user
  paused here; **next is runbook Step 2** (ports 80/443), then Step 3 (note
  the IP).
- **A1 was out of capacity in AD-1, AD-2 and AD-3** on the Free Tier account.
  The user **upgraded to Pay As You Go** (Individual, "tax information not
  available"), and creation then succeeded in AD-3. The card saw a ~€93
  verification hold, which Oracle's upgrade page says is reversed
  automatically. A **budget `free-tier`** was created: root compartment,
  monthly, amount 1, alert on actual spend ≥ 0.01 by email.
- **The runbook's point 7 did not work as written.** With *Create new VCN* +
  *Create new public subnet* in the instance form, the *Automatically assign
  public IPv4* toggle stayed disabled. Fix used: create the network first with
  **Networking → Virtual cloud networks → Start VCN Wizard → Create VCN with
  Internet Connectivity** (`po-vcn`), then pick *existing* `po-vcn` and its
  **public** subnet. The runbook is updated.
- The instance form has a **Security** page (shielded instance / confidential
  computing) the runbook did not mention. Both left off: confidential
  computing is AMD-only, and a shielded instance cannot be edited after launch.
- The user was advised against a second Oracle account in another region
  (one Always Free account per person; capacity is short elsewhere too).

## Session 2026-09-24 (cont.) — Steps 2–3 done, on Step 4

- **Public IP: `130.61.27.207`** (Frankfurt). The user read it from the
  instance page while the instance was **stopped**, which fits Oracle's
  docs: an ephemeral IP stays with a stopped instance. It hasn't been
  confirmed across a full stop→start cycle yet. Check after the next start.
- The user first looked for the IP on the VCN page and found the
  *IPv4 CIDR Block* (`10.0.0.0/16`) there. That is the network's private
  range, not the VM's address. The runbook's Step 3 already says "instance
  page", so it was left as written.
- **Next: runbook Step 4** (Namecheap A records `@` and `www` →
  `130.61.27.207`). The instance must be **started** before Step 5 (SSH).
- **Step 4 done.** A records `@` and `www` → `130.61.27.207`. Namecheap's
  default `@` **URL Redirect Record** had been left in place, so the apex also
  resolved to `162.255.119.194` (Namecheap's redirect server). Once it was
  deleted, the authoritative servers, 1.1.1.1 and 8.8.8.8 all return only
  `130.61.27.207`. Runbook Step 4.3 already says to delete it; it's easy to
  miss because it's a redirect record, not a CNAME.
- **Next: Step 5** (start the instance, then `scp`/`ssh` the setup script).
- **Steps 5–6 done; the site is live** (checked from outside 2026-09-24):
  `https://po-vim.help` → 200, Turkish page, a valid Let's Encrypt cert
  (issued 2026-09-24, expires 2026-12-23; Caddy renews it).
  `https://www.po-vim.help` → 301 to the apex. `http://` → 308 to https.
- A small slip in Step 6: the user ran `deploy.sh` **on the VM**, still logged
  in from Step 5, and typed `<ip>` literally. The runbook does say "From the
  Mac". What fixed it: `exit` first, then run with the real IP.
- **Next: Step 7.2** (the user's upload/stamp/download walk on the live site),
  then **Step 8** (schedule).

## Session 2026-09-24 (cont.) — Step 8 done

- The IAM policy `resource-scheduler-instances` was created in root, using
  `manage instances` (plural). Oracle's example page writes `instance`, which
  is not a listed IAM resource type.
- **Schedules `po-start` (`0 11 * * *`) and `po-stop` (`0 12 * * *`)** are both
  *Enabled*, in UTC, on `po-stamper`, active from **2026-09-25**. Their first
  runs are 2026-09-25 at 11:00 and 12:00 UTC. The form asks for a start
  date/time (when the schedule becomes active) and has an optional
  *Apply parameters* step, which was skipped. The runbook now says both.
- **Step 7.2 done:** the user ran the upload → stamp → download walk on the
  live site, and the results matched local testing.
- The policy was checked from the user's screenshot: *Active*, in root, and
  the statement says `manage instances` in tenancy for
  `request.principal.type='resourceschedule'`.
- **Next: Step 9** on 2026-09-25. Just after 11:00 UTC, check that the site
  is up and the IP is still `130.61.27.207`. After 12:00 UTC, check that it is
  down, and look at each schedule's *Last run*. The start is only a real test
  if the VM was **stopped** beforehand.
