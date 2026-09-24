# 0016 — Translations live in a Python dict, not gettext

**Date:** 2026-09-23 · **Serves:** R31 · **Task:** [[033-turkish-language]]

## Decision

The Turkish text is a single `dict` in `i18n.py`, keyed by the English source
string. Templates and `app.py` call `_("English text", **params)`. The per-file
reasons are keyed by `Problem` and filled from a `details` dict that
`stamper.py` returns alongside each English message. The language is kept in
the Flask session, `tr` by default.

## Why

- **About 70 strings and one language pair.** Flask-Babel and gettext bring
  `.po`/`.mo` files, an extraction step and a compile step. Those would be a
  new runtime dependency in the image, and a build step R25's
  single-container deploy does not have today.
- **The reviewer edits one file.** The user reviews the Turkish (R31). A
  Python dict with the English beside each line is easier to review than a
  `.po` file, and needs no tooling.
- **A missing translation cannot pass silently.** A test checks that every
  string the templates ask for, and every `Problem`, has a Turkish entry.
  Without that, a string falls back to English, and nobody reading only
  Turkish would notice.
- **Reasons are keyed by `Problem`, not by message text.** A reason carries
  values such as the sheet, a row count or the stamp. Keying on the English
  sentence would break the moment its wording changed. `Problem` already
  exists as a stable identity for exactly this reason (see its docstring).

## Revisit if

A third language arrives, or the string count grows past a few hundred. At
that point gettext's tooling pays for itself.
