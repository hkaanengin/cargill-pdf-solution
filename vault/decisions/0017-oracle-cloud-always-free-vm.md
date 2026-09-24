---
created: 2026-09-23
---
# 0017 — Host on an Oracle Cloud Always Free VM

## Decision

The app is hosted on **one Oracle Cloud Infrastructure (OCI) Always Free VM**
running the existing Docker image. The user already has an Oracle Cloud
account and chose this on 2026-09-23. Platform options that were weighed are in
[[brainstorm/cloud-hosting-options]].

## Why

- **Free.** Costing nothing was the user's one stated requirement.
- **One machine makes R25 true by construction.** Nothing can autoscale to a
  second instance, and the Dockerfile keeps `--workers 1`.
- **Memory stops being a concern.** An Ampere A1 shape can have up to 12 GB
  of RAM on the free tier (2 OCPUs / 12 GB in total, per Oracle 2026-09-23), against the 512 MB that made the upload cap a question
  (R34 still sets it at 100 MB, which the user chose).
- **Start and stop by hand works well here** (R35): the user can stop the
  container over SSH, or stop the VM itself in the console.
- **Same CPU architecture as the dev machine.** A1 is arm64, like the Mac the
  image was first built on (2026-09-23), so the image that was tested is the
  one that runs.

## What it costs us

This is a VM, not a platform. That makes these our job:

- **HTTPS (R26).** Nothing provides it. Caddy sits in front and gets a
  Let's Encrypt certificate for **`po-vim.help`**, a domain the user bought
  at Namecheap on 2026-09-23. `www.` redirects to the bare name.
- **OS updates** and the Docker install.
- **Deploys.** Pushing to the repo does not deploy anything.
  `deploy/deploy.sh` copies the named build files from the dev machine and
  rebuilds on the VM. See *Settled later* for why.

## Things to verify, not assumed

- ~~**Region.**~~ The account's home region is **Germany Central (Frankfurt)**,
  per the user on 2026-09-23. Always Free resources exist only there. The
  user is in Turkey and has stated no data-residency rule.
- **Idle reclamation — checked 2026-09-23 against Oracle's Always Free page.**
  A VM counts as idle if, over 7 days, 95th-percentile CPU is under 20%,
  network use is under 20%, and (A1 only) memory use is under 20%. A VM that
  runs all day and works one hour of it **fits that description**. Whether a
  *stopped* VM is also reclaimed is not stated there and was not checked.
  *Widely reported, not verified:* upgrading the account to Pay As You Go
  removes reclamation, and Always Free resources stay free after the upgrade.
- **A1 capacity.** Free A1 capacity is sometimes unavailable in popular
  regions. If so, the AMD `E2.1.Micro` shape (1 GB RAM) is the fallback, and
  the 100 MB cap was chosen to fit something that size.

## Ruled out

- **Render free** was recommended first and was not chosen. It has 512 MB of
  RAM and sleeps when idle.
- **Google Cloud Run** has a 32 MB request limit on HTTP/1.
- **Hugging Face Spaces** would put the customs data on a platform built for
  ML demos.
- **Fly.io and Railway** no longer have a real free tier.

## Settled later — 2026-09-23

**The VM is stopped, not the container.** The user chose this. OCI Resource
Scheduler starts it at 11:00 UTC and stops it at 12:00 UTC (14:00–15:00
Istanbul, R35). A start by hand is one click in the console. Why:

- **Reclamation turns out to be a stop, not a deletion.** Oracle's page says
  an idle Always Free instance is *stopped*, and can be started again if the
  shape has capacity. The next scheduled start would bring it back, and
  nothing is lost because the app holds no data (R23). The one real risk is A1
  capacity at start-up time, which Frankfurt is known to run short of.
  Converting to Pay As You Go removes reclamation and stays free within the
  Always Free limits (Oracle's page, same day).
- Nothing listens outside the window, which matters with no gate (R26).
- Starting by hand needs the console, not SSH.

**The region stays Frankfurt.** It cannot change: Always Free compute exists
only in the home region, which is fixed at sign-up. Moving would mean a new
account. Region does not affect reclamation either.

**Deploy by copying from the dev machine, not from a repo push.** Building on
the VM from a `git clone` would need GitHub credentials on the VM if the repo
is private. It would also put the whole repo there, vault included.
`deploy.sh` sends only the files the image needs, by name. Rollback is to
check out the previous commit and run it again. Push-to-deploy was
considered and dropped on 2026-09-24: [[decisions/0018-manual-deploy-no-cicd]].

**The container is read-only**, with `/tmp` as RAM. That enforces R36 at the
OS level as well as in `app.py`. Caddy was chosen over nginx because it
streams uploads instead of buffering them to disk.

## Settled later — 2026-09-24

**The account is Pay As You Go.** A1 was out of capacity in all three
Frankfurt ADs on Free Tier. The user upgraded rather than fall back to
E2.1.Micro or open a second account. **Why:** it got A1 at once (AD-3), and
per the notes above it also removes idle reclamation and the capacity risk at
each scheduled start. The cost is that Oracle no longer refuses paid
resources, so a $1 budget with a 0.01 actual-spend email alert (`free-tier`)
is the guard, and only *Always Free-eligible* resources may be created.
