# Development CI

Run `bash .github/scripts/check.sh` locally with Bash and ShellCheck. Every PR,
default-branch push and manual dispatch runs these same checks and an isolated runtime contract fixture. ShellCheck comes from the Ubuntu 24.04 runner image; its patch
updates follow the runner maintenance cycle rather than a separate download.

The shared `ci / required` gate requires all prerequisites to succeed and checks
explicitly dispatched PR identities before and after validation. Tokens are
read-only; actions use full version tags. Renovate inherits the versioned shared
base policy. No irrelevant formatter, package manager or placeholder test is added.

`python3 tests/runtime.py` executes the real entry point with disposable cache,
INI and state paths. Synthetic commands supply mover identity, time, disk usage
and native notification delivery; no mover or network notification is started.
The mandatory `runtime` job covers idle detection, 0/50/completed progress,
missing/malformed INI preparation, standard-mover fallback, notification failure
and invalid cache rejection. Every process has a ten-second deadline and a
process-group cleanup; temporary state is removed on failure as well as success.

This proves the simulated Unraid command contract, not real disk movement,
Unraid plugin lifecycle, `/proc` identity or delivery through Unraid's actual
notification service. Those still require a disposable licensed Unraid runner
with User Scripts and Mover Tuning. No production host or live recipient belongs
in CI. On macOS the contract fixture needs Homebrew GNU coreutils.

Negative fixture inputs are part of the same required run. An assertion failure
or timeout exits nonzero, and `ci / required` directly requires `runtime`.

Shared actions, workflows and presets use immutable `v3.0.1` references.
Renovate is the sole ongoing dependency merge owner. It merges eligible dependency
PRs by rebasing only after current required CI and policy checks pass. Native
platform automerge stays off. Shared Renovate policy updates remain manual;
release-age rules, holds and repository-specific updater ownership still apply.
The legacy Actions merger and its comment commands are retired.

The separate PR policy workflow verifies Conventional Commit titles, genuine
matching author sign-offs, Renovate provenance, holds, outstanding review requests
and unresolved changes requests. Require its actual emitted policy context alongside
all existing application/content checks, pinned to GitHub Actions, with strict
up-to-date branch protection. Preserve stronger review requirements. Explicit CI
dispatches do not substitute for a missing metadata policy result. Review exact
head/base, full diffs and all required results before a bootstrap merge, then
verify resulting default-branch CI. Repository-specific updater ownership and
manual publication or delivery controls remain unchanged.
