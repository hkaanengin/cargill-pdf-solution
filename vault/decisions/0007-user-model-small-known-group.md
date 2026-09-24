---
created: 2026-09-08
---
# 0007 — The audience is a few known users, not a public product

Answers open question 1, which was gating the whole cloud track.

The user's call, 2026-09-08: *"There will be a few users of this application.
They will expect to upload pdfs into the web site and receive/download stamped
pdfs back."*

## What this settles

- **A few users, known in advance.** Accounts are provisioned by hand. No signup
  flow, no email verification, no password reset, no billing.
- **No per-tenant isolation.** One shared deployment. Sessions still need to not
  collide with each other ([[005-shared-session-state]]), but that is a
  correctness requirement, not a tenancy boundary.
- **The web app is the product.** The CLI stays a local tool for the maintainer;
  it is not what these users touch.
- **Cheapest hosting that runs a container is fine.** Small, single-region, scale-
  to-zero acceptable. See [[cloud-hosting-options]].

## Why it matters

The alternative branch — external paying customers — implied signup, per-tenant
isolation, support, and real obligations around other companies' financial data.
That is a different project with a different cost. Ruling it out turns
[[003-auth-and-multi-user]] from weeks into roughly a day, and lets
[[004-cloud-deployment]] pick the boring option.

Still a real obligation: the workbook holds invoice and customs numbers, so the
deployment needs HTTPS and login in front of it. "A few users" lowers the
engineering, not the care.

## The flow the users expect

Upload PDFs → download stamped PDFs. Note the plural — the users' mental model is
a batch, which promotes [[002-batch-upload-zip]] from a nice-to-have onto the
main path.

**Left open:** whether these users upload the Excel workbook themselves each
session, or whether one maintainer loads the month's workbook and everyone else
only ever touches PDFs. The user described only the PDF half. This reshapes
[[decisions/0001-excel-per-session-upload]], [[005-shared-session-state]] and
[[001-multi-workbook-support]] — see open question 6 in [[open-questions]].
