# Development CI

Run `bash .github/scripts/check.sh` locally with Bash and ShellCheck. Every PR,
default-branch push and manual dispatch runs these same checks without executing
the mover script. ShellCheck comes from the Ubuntu 24.04 runner image; its patch
updates follow the runner maintenance cycle rather than a separate download.

The shared `ci / required` gate requires all prerequisites to succeed and checks
explicitly dispatched PR identities before and after validation. Tokens are
read-only; actions use full version tags. Renovate inherits the versioned shared
base policy. No irrelevant formatter, package manager or placeholder test is added.

There is no automated Unraid runtime/integration coverage yet. In particular,
`DRY_RUN=true` still sends notifications and is not a CI smoke test. Progress,
state recovery and notification behavior need an isolated Unraid fixture harness
before broader dependency or runtime changes can be considered low-risk.

Shared actions, workflows and presets use immutable `v3.0.0` references.
Renovate is the sole ongoing dependency merge owner. Direct automerge remains
explicitly disabled, including matching package rules, until the hosted rollout
proves native Renovate operation behind complete required CI. The legacy Actions
merger and its comment commands are retired.

The separate PR policy workflow verifies Conventional Commit titles, genuine
matching author sign-offs, Renovate provenance, holds, outstanding review requests
and unresolved changes requests. Require its actual emitted policy context alongside
all existing application/content checks, pinned to GitHub Actions, with strict
up-to-date branch protection. Preserve stronger review requirements. Explicit CI
dispatches do not substitute for a missing metadata policy result. Review exact
head/base, full diffs and all required results before a bootstrap merge, then
verify resulting default-branch CI. Repository-specific updater ownership and
manual publication or delivery controls remain unchanged.
