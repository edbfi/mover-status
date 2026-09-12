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

No branch protections or rulesets are configured; automerge remains disabled.
Manually review exact head/base, full diff, author/DCO, all expected CI jobs and
relevant artifacts before merging through the maintainer ghmerge function.
