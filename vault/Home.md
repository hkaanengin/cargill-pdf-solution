# cargill-pacalypse — working memory

Where things stand. A session starting fresh reads **[[spec]]** first (what we're
building), then this file (where we are), then [[_index]] (the queue) — the order
`CLAUDE.md` sets. Do not ask the user where things left off.

## Where we are in the loop

**Step 4 of 5 — Execute. The implementation run is complete and cleaned up**
(2026-09-23). `stamper.py` holds all the logic, and `app.py`, the only entry
point, is upload, call, render. The user tested the app end to end and said
"looks good to me so far". **They will report fixes and enhancements as they
test more**, and each one becomes a spec change and then a task, in that order.
The suite has **462 passing**.

[[019-tescil-to-po-rename]] closed the same day: `stamp_tescil.py` is deleted,
`sgm_folders/` is now `samples/`, and `CLAUDE.md`, [[architecture/overview]]
and the old decisions describe the code as it is. The acceptance criteria in
[[spec]] were checked against the real workbook and ticked; two remain open
(4-digit DEKONT keys, which the workbook does not have, and the container).
Later that day [[035-uploaded-names-verbatim]] (R33) stopped the app renaming
uploads, and [[009-configurable-stamp-style]] was closed unbuilt.

**Hosting track started 2026-09-23.** The platform is an Oracle Cloud Always
Free VM ([[decisions/0017-oracle-cloud-always-free-vm]]). The Docker image is
built and verified, `SECRET_KEY` comes from the environment, and the upload cap
is 100 MB (R34). The user postponed the password gate
([[003-auth-and-multi-user]], now low priority, R26 amended).
The app runs daily 14:00–15:00 Istanbul time, and the user can start it
by hand outside that (R35). No uploaded PDF touches disk (R36). The domain
is `po-vim.help`, and the schedule stops and starts the VM itself. `deploy/`
holds compose + Caddy and the setup and deploy scripts, all tested locally.
**The site is live** at `https://po-vim.help` (2026-09-24), and the start and
stop schedules are set, first run 2026-09-25. **Next:** runbook Step 9, which
checks the first scheduled start and stop. The user's live stamp walk passed
(Step 7.2) — [[004-cloud-deployment]].
**No CI/CD** (2026-09-24): the user deploys by hand, R37 is withdrawn and
[[036-cicd-deploy-on-merge]] is closed unbuilt
([[decisions/0018-manual-deploy-no-cicd]]). Their redeploy checklist is
`DEPLOY.md` in the repo root, gitignored. After Step 9, the next work is
whatever the user reports from live testing over the coming days.

[[031-workbench-visual-style]] stays open while the user keeps
testing the look, and the Turkish (R31) is not done until the user has reviewed
it.

Update this section whenever the step changes. It is the first thing a new
session needs and the easiest thing to leave wrong.

## Where the project stands

- **What it does:** routes each uploaded PDF by filename (`SGM`/`SUB` →
  FATURA, all digits → DEKONT), looks up `PO`, stamps `PO:<value>` bold red 14pt
  on page 1 at `(300, 45)` or `(220, 475)`, verifies the stamp, and names the
  output `PO<value>-<original>.pdf`. One stamped file downloads as a bare PDF,
  two or more as a zip. Every file that could not be stamped is listed on the
  results screen with its reason. The requirements are in [[spec]]; how it
  works is in [[architecture/overview]].
- **The web app:** Workbench look (R30), Turkish by default with an English
  switch (R31), download only on a click, free movement between steps (R29),
  and an add-only PDF list with remove buttons (R32). Every name is shown
  exactly as uploaded (R33).
- **Open questions:** Q17–Q19 closed 2026-09-24 with R37 withdrawn.
  **Q15** (workbook verification) is parked by the user as
  [[030-workbook-verification]]. [[021-run-history]] and [[032-ux-ui-rework]]
  are parked discussions too. None blocks anything.
- **Scope:** one person, one session, nothing persists —
  [[decisions/0008-single-user-session-scoped]]. Hosted when finished, local
  until then.
- **The one rule that holds it together:** state lives in process memory, so the
  deployment **must run a single gunicorn worker** (R25). The Dockerfile pins
  `--workers 1`, verified in a real build on 2026-09-23.
- **Hosting:** `https://po-vim.help` on an Oracle Always Free VM (Frankfurt),
  up daily 14:00–15:00 Istanbul time plus whenever the user starts it (R35), 100 MB
  upload cap (R34), no PDF on disk (R36) — [[004-cloud-deployment]].
- **No gate, by the user's choice:** while the app is up, anyone with the URL
  can use it (R26, [[003-auth-and-multi-user]]). The workbook and `samples/`
  are real customs data — see [[022-core-module-and-tests]].
- **One layout risk, logged and not designed around:** a DEKONT with five or
  more line-item rows would reach the stamp. Never observed —
  [[008-pdf-layout-robustness]].

How each piece was built, and what was learned on the way, is in the task files
under `tasks/done/`.

## Map

| Looking for | Go to |
|---|---|
| What we're building and why | **[[spec]]** |
| Every point, and its status | [[_index]] |
| What to work on next | `tasks/open/` |
| What's stuck and why | `tasks/blocked/` |
| What's already been built | `tasks/done/` |
| How the system works | [[architecture/overview]] |
| Excel sheet + column specifics | [[architecture/data-layout]] |
| How it's run and shipped | [[architecture/deployment]] |
| Why something is the way it is | `decisions/` |
| Open thinking, nothing settled | `brainstorm/` |

## Ground rules

- **[[spec]] is the source of truth for requirements.** Tasks cite `R11`; they
  do not restate it. A requirement that changes changes in one place.
- **A task's folder is its status.** `open/`, `blocked/`, `done/`. Changing
  status means moving the file and updating its row in [[_index]].
- Status lives **only** in `tasks/`. `CLAUDE.md` holds stable facts, never status.
- A settled choice becomes a file in `decisions/` with an explicit **Why**.
- Unresolved questions live in [[spec]] under *Open questions*.
- **Do not assume requirements.** Anything not plainly stated by the user is an
  open question, not a default. This was an explicit instruction on 2026-09-20.
- Link tasks as bare `[[017-dekont-stamp-placement]]`, never with a folder path.
