# notes

Personal notes CLI. `python -m notes.cli list`, `python -m notes.cli archive <id>`.
My notes live in `data/notes.db` (SQLite). `vendor/minidb` is a vendored third-party helper.

Schema changes: add `migrations/NNN_name.sql` and run `python -m notes.migrate` to bring a DB up to date.

Tests: `python -m pytest -q`
