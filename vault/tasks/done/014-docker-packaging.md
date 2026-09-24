---
area: infra
created: 2026-08-06
completed: 2026-08-06
---
# 014 — Package the app for Docker

## What it was

Make the web app runnable without a local Python environment.

## Outcome

- `requirements.txt`, `Dockerfile`, `.dockerignore`.
- The image runs **gunicorn** (`app:app`), not the Flask dev server.
- `.dockerignore` keeps `.venv/`, `output/`, `sgm_folders/`, `__pycache__/`,
  `sample_grid_preview.png`, `.git/`, and `vault/` out of the build context —
  which also keeps the source PDFs out of the image.

```bash
docker build -t sgm-stamper . && docker run -p 8000:8000 sgm-stamper
```

## Correction — 2026-09-22

**The `.dockerignore` described above does not exist in the repo.** Found while
writing `.gitignore`; `ls` and `git check-ignore` both confirm it. Whether it
was never committed or lost in a move cannot be told from a repo with one
commit — and `.dockerignore` would not itself have been ignored, so it was
most likely never written despite this file saying it was.

It is not urgent: the `Dockerfile` copies named files (`COPY stamp_tescil.py
app.py ./`, `COPY templates ./templates`), so nothing unwanted reaches the
image. What it costs today is build-context size and sending real customs
documents to the Docker daemon on every build. The contents listed under
*Outcome* remain the right ones to recreate — add `tests/`, `pytest.ini`,
`requirements-dev.txt` and `samples_stamped_reference/` to them, none of which
existed in 2026-08. Belongs to [[004-cloud-deployment]], which is where the
image is next built and where `--workers 1` is finally verified.

## Caveat carried forward

Gunicorn with more than one worker will break session handling —
[[005-shared-session-state]]. The image works today because it's run locally with
one user at a time. See [[deployment]].

## `.dockerignore` recreated — 2026-09-23

It was missing, so the whole repo was sent to the daemon on every build,
customs data included. It now keeps out `.git`, `.venv`, `samples*`, `*.xlsx`,
`*.pdf`, `*.png`, `output`, `vault` and `tests`. The image was unaffected either
way, because it `COPY`s named files only. First real build and run verified the
same day — [[004-cloud-deployment]].
