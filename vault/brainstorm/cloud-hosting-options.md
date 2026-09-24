---
status: open
created: 2026-08-07
---
# Cloud hosting — options and thinking

**Settled 2026-09-23 → [[decisions/0017-oracle-cloud-always-free-vm]].** Kept
as the record of the thinking. When it settles, it graduates to a file in
`decisions/` and this note links to it. Feeds [[004-cloud-deployment]].

## What we actually need

Modest requirements — worth stating before shopping, because they rule most
things in rather than out:

- Runs a container (the image already runs gunicorn)
- HTTPS and a stable URL
- Somewhere to put secrets
- A shared store for session state — [[005-shared-session-state]]
- Low, predictable cost; this is a small internal-ish tool

Explicitly **not** needed: autoscaling, multi-region, a managed database. The
data is uploaded and discarded per session.

## Shapes worth considering

- **Container-as-a-service** (Cloud Run, Fly, Render, Railway, App Runner) —
  closest fit to what exists. Push an image, get a URL. Scale-to-zero suits
  intermittent use. Main question per platform is whether cheap managed Redis
  sits next to it.
- **A single small VM** — most control, least magic, and honestly plausible for
  one small app. Cost is flat and predictable. Downside: OS patching, TLS renewal,
  and deploys are all yours.
- **PaaS with an app-shaped abstraction** (Heroku-alikes) — least infra work,
  usually bundles Redis, typically the most expensive per unit.

Serverless functions are a poor fit: PyMuPDF is a heavy dependency and the
session model wants a warm process.

## Things to check before choosing — do not assume

- Managed Redis availability and real monthly cost at this tiny scale
- Request timeout and upload body-size limits — batch zip uploads
  ([[002-batch-upload-zip]]) could bump into both
- Whether scale-to-zero cold starts are tolerable with PyMuPDF in the image
- Data residency: this is Turkish customs data — is there a jurisdiction
  requirement? **Ask before choosing a region.**

## The question that actually gates this

Internal tool or external product? See [[brainstorm/open-questions]]. An internal
tool behind SSO can go on the cheapest thing that works. An external product
needs an auth story, a support story, and a real answer on data handling — a
different project, not a different deployment.

Recommend answering that before evaluating any platform.
