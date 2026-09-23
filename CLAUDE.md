# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

The product is one file, `moverStatus.sh`. Users paste it whole into Unraid's User Scripts plugin and edit the variables at the top, so it must stay self-contained. Don't split it into sourced libraries or add runtime dependencies beyond what it already calls (bash, curl, jq, du, pgrep, GNU date/stat).

## Commands

| Task | Command |
| --- | --- |
| Syntax check + lint (use while editing) | `bash -n moverStatus.sh && shellcheck moverStatus.sh` |
| Full CI shell job | `bash .github/scripts/check.sh` |
| Runtime contract tests (~17 s) | `python3 tests/runtime.py` |
| One test case | `python3 tests/runtime.py RuntimeContract.test_missing_cache_fails_before_notification` |

- `check.sh`, and the CI `runtime` job after the tests, both end with `git diff --exit-code HEAD`, so `check.sh` always fails on a dirty tree. Before committing, run the two lint commands directly. Tests must not leave files behind in the repo.
- `test_running_and_completion` loops over the scenarios `normal`, `missing`, `malformed`, `du`, `notify-error` as `subTest`s, so one scenario can't be picked from the CLI. Run the whole method (`RuntimeContract.test_running_and_completion`).
- The script needs GNU `stat -c` / `date -d`. On macOS, `tests/runtime.py` puts `/opt/homebrew/opt/coreutils/libexec/gnubin` on its PATH when it exists (`brew install coreutils`).
- There is no formatter, package manager or build step. Don't add one (`CI.md` rules this out).

## How the runtime test works

`tests/runtime.py` runs the real script with a temp dir and a PATH of shims for `curl pgrep stat date du sleep notify`. All of them are one Python adapter that reads a `step` counter.

- Only `sleep` advances `step`, so every `sleep` call moves the simulated mover forward. Adding, removing or reordering `sleep` calls in the monitor loop changes what the fixture sees.
- The `curl` shim asserts that its only caller is the GitHub releases version check. Only the native Unraid channel (`MOVER_STATUS_USE_UNRAID=true`) runs under test. Telegram, Discord, Pushover and Apprise are never exercised.
- `send_pushover`, the Apprise API path and the dry-run Discord post call `/usr/bin/curl` by absolute path, which skips the shim. Tests that enable those channels would reach the real network.
- The test counts completion once the log contains `Restarting monitoring after completion`, and it expects `state/last-run` to exist and `state/state` to be gone. Keep those log strings and files as they are, or update the test in the same change.

## Script invariants

- Booleans are run as commands (`if $USE_DISCORD; then`), so every flag must be exactly `true` or `false`.
- Settings that tests or CI need to override use `VAR=${MOVER_STATUS_<NAME>:-default}`. Keep the plain default for copy-paste users, and list any new override under "Isolated runtime inputs" in `README.md`.
- Progress comes from one of three `DATA_SOURCE` values, chosen per mover run in `detect_data_source`:

  | Condition | `DATA_SOURCE` | Progress from |
  | --- | --- | --- |
  | `mover.ini` mtime >= mover start and a stable, valid snapshot | `mover_ini` | `load_mover_ini_snapshot` (never parse the INI any other way) |
  | `age_mover` running, no current INI yet | `preparing` | none. Sends `PREPARING_MESSAGE` and switches to `mover_ini` when the INI appears |
  | otherwise (standard mover) | `du_polling` | `du -sb $CACHE_PATH` compared with `initial_size` |

- `get_progress` caps `PROGRESS_PERCENT` at 99. You only get 100% or the completion message when the mover process exits, and then `send_notification` swaps in `build_completion_summary` output. Don't send 100 from the progress path.
- After a completion the loop waits for the next mover run. It never exits, even though README "How it works" says it does.
- `load_state` sources the state file with `.` and checks for `STATE_VERSION=1`. When you add a field, write it in `save_state` and read it in `load_state` with a `${FIELD:-default}` fallback. Only bump `STATE_VERSION` if old files can't be resumed, because a bump throws away in-flight state.
- Apprise target URLs contain credentials and are never logged (see `send_apprise_target`). Keep new code the same way.
- `CURRENT_VERSION` is compared with the newest GitHub release `tag_name`, and tags have no `v` prefix (e.g. `0.1.0`). Bump it in its own commit, following `chore: update script version`.

## Delivery model

"Direct" channels are Telegram, Discord, Pushover and Unraid (`direct_notifications_enabled`). They are all sent by one `send_notification percent remaining [pushover_only] [skip_pushover] [message_override]` call. Apprise is separate and keeps its own per-target retry state (`send_apprise_progress`, `retry_apprise_*`).

| Channel | Failure detected? | Retried? |
| --- | --- | --- |
| Pushover | yes (`curl -fsS` + `.status == 1`) | yes. Coalesced to newest percent and retried every loop |
| Apprise | yes, per target | yes, per target. Healthy targets are not resent |
| Unraid `notify` | yes (exit code) | no. Logged once, never resent |
| Telegram / Discord | no (`curl -s`, response only logged in debug) | no |

Build JSON payloads with `jq -n --arg ...` as in `send_notification`. The hand-built JSON string in the dry-run Discord block is legacy, so don't copy it.

## Adding a notification channel or setting

Derived from the Apprise (#28) and native Unraid (#29) commits. Each one touched only `moverStatus.sh` and `README.md` (#28 also added a README image):

1. Settings block at the top: `USE_<X>=false` plus its credentials and `<X>_MOVING_MESSAGE` / `<X>_COMPLETION_MESSAGE=""` templates.
2. The all-disabled check (`if ! $USE_TELEGRAM && ...`) and a `if [[ $USE_<X> == true ]]` validation block that `exit 1`s.
3. `direct_notifications_enabled` (skip this for an Apprise-style independent channel), and the non-Pushover channel list in the main loop (`if $USE_TELEGRAM || $USE_DISCORD || $USE_UNRAID`).
4. The dry-run block (`if $DRY_RUN; then`): template substitution and a test send that `exit 1`s on failure.
5. `calculate_etc` platform list, `build_completion_summary` (`COMPLETION_SUMMARY_<X>`), and the send in `send_notification` (placeholders `{percent} {remaining_data} {etc} {file_count} {current_file}`; completion uses `{total_moved} {file_count} {duration} {avg_speed}`).
6. `README.md`: the Table of Contents, the "Script Settings" list, and a setup section.

## Reference docs

- `CI.md`: CI jobs, the runtime-fixture scope (what it does and doesn't prove), and Renovate/PR-policy ownership. Read it before changing `.github/workflows/`, `tests/runtime.py` or `renovate.json`.
- `README.md`: user-facing settings and setup. Update it whenever a user-editable variable changes.
- PR titles must be Conventional Commits and carry matching author sign-offs (checked by the shared `edbfi/automation` PR-policy workflow).
