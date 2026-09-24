# Deployment

How the app runs locally, in Docker, and hosted on Oracle Cloud at
`https://po-vim.help`, including the step-by-step runbook for the first deploy.

## Today — local

```bash
.venv/bin/python3 app.py        # Flask dev server → http://localhost:8000
```

## Today — Docker

```bash
docker build -t sgm-stamper .
docker run -p 8000:8000 sgm-stamper
```

- The image runs **gunicorn** (`app:app`), not the Flask dev server, with
  `--workers 1 --threads 4 --worker-class gthread --timeout 300`.
- **No Excel is baked into the image** — it's uploaded in the browser each
  session. See [[decisions/0001-excel-per-session-upload]].
- `.dockerignore` keeps customs data, `.venv`, `.git`, `vault` and `tests` out
  of the build context (recreated 2026-09-23). The image is arm64 when built
  on the dev Mac, 227 MB.
- `SECRET_KEY` comes from the environment (`-e SECRET_KEY=…`). When it is unset
  the app generates a random key at start-up, which just means sessions do not
  survive a restart, and they already don't.
- **First built and run for real on 2026-09-23**: one `gthread` worker, and the
  full upload → stamp → download walk works through the container.

## The single-worker rule — 2026-09-16

**`--workers 1` is load-bearing. Do not raise it.**

The app keeps the uploaded workbook and the pending download in process memory.
With two workers, the Excel lands on worker A, the PDFs post to worker B, and the
user is told no source is loaded — looks random, is deterministic. The image
shipped with `--workers 2` until 2026-09-16; that was this bug, live.

This used to be filed as the thing blocking hosting
([[005-shared-session-state]]). It isn't any more:
[[decisions/0008-single-user-session-scoped]] scoped the app to one user and one
session, which makes in-process state correct and makes the single worker the
design rather than a stopgap. Restarts dropping sessions is accepted — the user
re-uploads the workbook, one click.

`--threads 4` keeps the page responsive while a batch stamps, without splitting
the memory the way a second worker would. `--timeout 300` exists because a batch
of PDFs takes longer than gunicorn's 30-second default.

**What this demands of the platform:** it must not silently run more than one
instance. Scale-to-zero is fine and even desirable; autoscaling to two is the
same bug in a different costume. Cap max instances at 1.

## Hosted — Oracle Cloud Always Free VM, `https://po-vim.help`

Chosen 2026-09-23: [[decisions/0017-oracle-cloud-always-free-vm]]. One Ubuntu
VM in Frankfurt runs `deploy/compose.yaml`: the app (read-only container, `/tmp`
in RAM, R36) behind Caddy, which does HTTPS for `po-vim.help` (Namecheap DNS).
Docker starts on boot and both containers restart with it, so **starting the
VM starts the app**. OCI Resource Scheduler starts the VM at 11:00 UTC and
stops it at 12:00 UTC, which is 14:00–15:00 Istanbul time. Türkiye has no DST,
so this holds all year (R35). By hand: Start or Stop in the console.

| File | Runs where | Does |
|---|---|---|
| `deploy/compose.yaml` | VM | app + Caddy, restart policies, read-only app |
| `deploy/Caddyfile` | VM | `po-vim.help` → `app:8000`, `www.` redirects |
| `deploy/setup-vm.sh` | VM, once | Docker, compose, opens 80/443 in the VM's iptables |
| `deploy/deploy.sh ubuntu@<ip>` | dev machine | rsync the build files by name, rebuild on the VM |

Tested locally 2026-09-23 with `SITE_ADDRESS=:80`: the read-only app booted,
and upload → stamp → download worked through Caddy. `deploy.sh`'s file list was
checked with macOS's `openrsync`: exactly the 13 build files, and no data.

**Facts the runbook relies on, checked against Oracle's docs on 2026-09-23:**

- An ephemeral public IP **stays with the instance when it is stopped**. It
  changes only if the instance is terminated and recreated. So the daily stop
  does not break DNS, and no reserved IP is needed.
- The Always Free A1 allowance is **2 OCPUs and 12 GB in total** (it used to be
  4/24). `VM.Standard.E2.1.Micro` is 1/8 OCPU and 1 GB, up to two instances.
- Resource Scheduler times are **UTC**. A schedule has no permission to act
  until an IAM policy grants it.
- Idle reclamation **stops** the instance; it does not delete it.

### Runbook — first deploy

Written for the user, who runs it. `<ip>` means the VM's public IP address
from step 3 throughout.

**What you need before starting:** your Oracle Cloud login, your Namecheap
login, and a terminal on your Mac, opened in this repo's folder. Docker does
not need to be running on the Mac, because the image is built on the VM.

**About the SSH key.** It is how your Mac logs in to the VM. Oracle's Ubuntu
VMs have no password login at all. The key is a pair of files already on your
Mac:

- `~/.ssh/id_ed25519.pub` is the **public** half. You paste it into Oracle in
  step 1, and it is safe to share. It works like a lock that you install on
  the VM.
- `~/.ssh/id_ed25519` is the **private** half. It works like the key to that
  lock. It never leaves your Mac and is never pasted anywhere.

Once the public half is on the VM, `ssh`, `scp` and `deploy.sh` log in with no
password. The pair was created on 2023-08-07. It is most likely the same key
your Mac uses for GitHub (the repo's remote is `git@github.com:…`), and
reusing it for the VM is fine.

#### Step 1 — Create the VM

1. Log in at <https://cloud.oracle.com>. Check that the region in the top
   bar is **Germany Central (Frankfurt)**.
2. Open the menu ☰ → **Compute** → **Instances** → **Create instance**.
3. **Name:** `po-stamper`. **Compartment:** leave it as the default (your root
   compartment).
4. **Placement:** leave it as AD-1. If creating fails with *"Out of host
   capacity"*, come back here and try AD-2, then AD-3.
5. **Image:** click *Change image* → **Ubuntu** → **Canonical Ubuntu 24.04**
   (not "Minimal"). Oracle picks the ARM build to match the shape.
6. **Shape:** click *Change shape* → *Virtual machine* → **Ampere** →
   **VM.Standard.A1.Flex**. Set **1 OCPU** and **6 GB memory**. It should show
   an "Always Free-eligible" label.
   - If A1 is out of capacity in every AD, use *Specialty and previous
     generation* → **VM.Standard.E2.1.Micro** instead. That works too, because
     the image is built on the VM. It only has 1 GB of RAM, so keep batches
     modest.
7. **Security page:** leave *Shielded instance* and *Confidential computing*
   both off. Confidential computing needs AMD, and a shielded instance cannot
   be changed after launch.
8. **Networking:** create the network **first**, in another tab. Creating it
   from this form leaves the public-IP toggle disabled (seen 2026-09-24).
   ☰ → **Networking** → **Virtual cloud networks** → **Start VCN Wizard** →
   **Create VCN with Internet Connectivity**, name `po-vcn`, defaults, Create.
   Back here: *Select existing virtual cloud network* → `po-vcn`, *Select
   existing subnet* → its **public** subnet, and switch on **"Automatically
   assign public IPv4 address"**. Check that Review says Public IPv4: **Yes**.
9. **SSH keys:** choose *Paste public keys*. On your Mac, run
   `cat ~/.ssh/id_ed25519.pub`, copy the whole line (it starts `ssh-ed25519`),
   and paste it in.
10. **Boot volume:** leave the default (about 47 GB, within the 200 GB free).
11. Click **Create**. Wait until the status reads **Running** (a minute or
    two).

#### Step 2 — Open ports 80 and 443 in Oracle's firewall

Oracle blocks everything except SSH by default. HTTPS needs 443, and 80 is
needed for the certificate check and for redirecting to HTTPS.

1. On the instance page, find **Primary VNIC** and click its **Subnet** link.
2. Open the subnet's **Security** tab (older consoles: *Security Lists*),
   then click **Default Security List for …**.
3. Open **Security rules** → **Add Ingress Rules** and fill in:
   - **Stateless:** unticked
   - **Source type:** CIDR, **Source CIDR:** `0.0.0.0/0`
   - **IP protocol:** TCP
   - **Source port range:** leave empty
   - **Destination port range:** `80,443`
   - **Description:** `web`
4. Click **Add Ingress Rules**. Leave the existing port 22 (SSH) rule alone.

The VM also has its own firewall inside Ubuntu. Step 5 opens that one.

#### Step 3 — Note the public IP

On the instance page, copy **Public IPv4 address**. That is `<ip>` for every
step below. It stays the same through stops and starts. It changes only if the
instance is terminated, and then you would redo steps 1–7 anyway.

> **Checkpoint: send Claude the VM's IP.** Once you have it, share it in the
> session. Claude will check `https://po-vim.help` from outside as the
> remaining steps land, and help with anything that gets stuck.

#### Step 4 — Point `po-vim.help` at the VM (Namecheap)

1. Log in at <https://namecheap.com> → **Domain List** → **Manage** next to
   `po-vim.help`.
2. **Domain** tab: under *Nameservers*, check that it says **Namecheap
   BasicDNS**.
3. **Advanced DNS** tab → *Host Records*. **Delete** the default parking
   records: usually a `CNAME Record` for `www` → `parkingpage.namecheap.com`
   and a `URL Redirect Record` for `@`.
4. **Add New Record** twice:
   - `A Record`, **Host** `@`, **Value** `<ip>`, **TTL** Automatic
   - `A Record`, **Host** `www`, **Value** `<ip>`, **TTL** Automatic
5. Click the green ✓ on each to save. It usually takes effect within a few
   minutes, but can take up to 30. Check from the Mac with
   `dig +short po-vim.help`. When it prints `<ip>`, DNS is ready.

#### Step 5 — Set up the VM (once)

From the Mac, in the repo folder:

```bash
scp deploy/setup-vm.sh ubuntu@<ip>:~     # copy the setup script over
ssh ubuntu@<ip>                           # log in; answer "yes" to the fingerprint question
bash setup-vm.sh                          # on the VM: installs Docker, opens 80/443
exit                                      # log out; it must be a fresh login next time
```

The script takes a few minutes and ends with *"Done. Log out and back in…"*.
Logging out is required: it is what gives the `ubuntu` user permission to use
Docker.

#### Step 6 — Deploy the app

From the Mac, in the repo folder:

```bash
deploy/deploy.sh ubuntu@<ip>
```

This copies only the app's own files to `~/sgm` on the VM. The workbook and
`samples/` never leave the Mac. It then builds and starts both containers. The
first run takes a few minutes, because it downloads Python, the dependencies
and Caddy. It ends with *"Deployed. https://po-vim.help"*.

#### Step 7 — Check it works

1. Open **<https://po-vim.help>** in a browser. The first visit can take up to
   a minute while Caddy gets the certificate. After that, the padlock should
   show and the app loads in Turkish.
2. Upload the workbook and a couple of PDFs, then download the result, the same
   walk as locally.
3. Also try <https://www.po-vim.help>. It should land on `po-vim.help`.
4. If the page doesn't load, check the logs (see *Day to day*), and look for
   `certificate obtained successfully` from Caddy.

#### Step 8 — Schedule 14:00–15:00 Istanbul time

Two parts: a policy that allows schedules to start and stop instances, then two
schedules. **Times are entered in UTC: 11:00 and 12:00.**

1. **The policy.** Menu ☰ → **Identity & Security** → **Policies**. Choose the
   **root** compartment → **Create Policy**.
   - **Name:** `resource-scheduler-instances`
   - **Description:** `Lets resource schedules start and stop instances`
   - Switch on **Show manual editor** and paste:
     ```
     Allow any-user to manage instances in tenancy where all {request.principal.type='resourceschedule'}
     ```
     It says `instances`, plural, which is the IAM resource type for compute
     instances. Oracle's example page writes `instance`, which is not a listed
     resource type, so the plural is the safer choice (2026-09-24).
   - **Create.** This allows *any schedule in your tenancy* to manage
     instances. On a one-person account that is fine. Oracle's stricter form
     names a single schedule's OCID instead, and you can switch to it after
     the schedules exist.
2. **The start schedule.** Type **Resource Scheduler** in the console's search
   bar and open it → **Schedules** → **Create schedule**.
   - **General information:** Name `po-start`, **Action to be executed:**
     **Start**, resource selection **Static**, compartment root.
   - **Resources:** tick `po-stamper`.
   - **Apply parameters:** skip. Leave the JSON empty and tick nothing.
     Start and stop take no parameters.
   - **Schedule:** *Cron expression* `0 11 * * *`, **Time zone** UTC.
     **Start date** and **start time** only set when the schedule becomes
     active, not when it runs. Use tomorrow at `00:00`. **End date:** leave
     it empty.
   - **Create.** The list then shows *Enabled* and a *Next run date*.
3. **The stop schedule.** Same again: **Name** `po-stop`, **Action**
   **Stop**, the same instance, cron `0 12 * * *`, the same start date.

#### Step 9 — Check the schedule the next day

- **Just after 14:00 Istanbul:** the instance shows *Running*, and
  <https://po-vim.help> loads within about two minutes of the start.
- **After 15:00:** the instance shows *Stopped*.
- If neither happened, open the schedule in Resource Scheduler and check its
  run history. A permission error there means the step 8 policy is missing or
  wrong.

### Day to day

**Start it outside the window:** console → Compute → Instances → `po-stamper`
→ **Start**. The site is up about two minutes later. You can do this from a
phone browser too.

**Stop it:** same page → **Stop**. Leave *Force stop* unticked. A stop wipes
whatever was loaded, which is intended (R23).

**Things to know:**

- If you start it by hand at, say, 14:50, the scheduled stop still turns it
  off at 15:00.
- If Oracle reclaims the VM for being idle, that is a *stop*. The next
  scheduled start, or your Start click, brings it back.
- *Out of host capacity* when starting: wait a bit and retry. This is the one
  failure the free tier can have. Upgrading the account to Pay As You Go (still
  free within Always Free limits) removes both the capacity queue and
  reclamation.
- While it is up, **anyone with the URL can use it**. There is no password,
  by choice (R26, [[003-auth-and-multi-user]]).

**Deploy a new version:** by hand, always. There is no CI/CD
([[decisions/0018-manual-deploy-no-cicd]]). Pick a time outside 14:00–15:00,
run the tests, start the VM if it is stopped, then run
`deploy/deploy.sh ubuntu@<ip>` from the repo folder. It deploys whatever is
checked out on the Mac, uncommitted changes included. Stop the VM again if you
started it. The user's step-by-step version of this is `DEPLOY.md` in the repo
root, which is gitignored.

**Roll back:** `git checkout <previous-commit>`, then run `deploy/deploy.sh`
again, then `git checkout master` to return.

**Logs:**
`ssh ubuntu@<ip> docker compose -f sgm/deploy/compose.yaml logs --tail 100`.
Add `app` or `caddy` at the end for just one of them. Logs are lost when the
container is rebuilt. That's fine: they hold no file names (Caddy keeps no
access log, and gunicorn's is off).

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| *Out of host capacity* creating the VM | No free A1 in that AD | Try AD-2 / AD-3, retry later, use E2.1.Micro, or upgrade to Pay As You Go (what worked on 2026-09-24, in AD-3) |
| `ssh` times out | VM stopped, or wrong IP | Check the instance is Running; recopy the IP |
| `ssh`: *Permission denied (publickey)* | A different key was pasted in step 1 | Instance → edit → SSH keys, or recreate the VM with the right key |
| `deploy.sh`: *permission denied … docker.sock* | Still logged in from before setup | `exit` the SSH session, then run it again |
| Browser can't connect at all | Ports not open | Recheck step 2's rule, and that step 5 ran |
| Browser: certificate warning | DNS not pointing at `<ip>` yet when Caddy tried | Wait until `dig +short po-vim.help` shows `<ip>`, then `ssh ubuntu@<ip> docker compose -f sgm/deploy/compose.yaml restart caddy` |
| Site down just after 14:00 | VM still booting | Give it about two minutes |

## History of the platform question

- ~~Which platform~~ — settled, 0017. Redis is **no longer a requirement** — 0008 removed it. The
  test is now "can it run exactly one container instance, cheaply, with HTTPS".
- ~~Who are the users~~ — settled:
  [[decisions/0007-user-model-small-known-group]], narrowed by
  [[decisions/0008-single-user-session-scoped]] to one at a time. The shared gate
  ([[003-auth-and-multi-user]]) was postponed by the user on 2026-09-23.
- ~~Do uploaded workbooks get stored~~ — settled: no. Per-session only, nothing
  at rest. That keeps customer financial data out of storage entirely, which is
  the cheapest possible answer to the obligation.
