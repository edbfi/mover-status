#!/usr/bin/env bash
set -euo pipefail
bash -n moverStatus.sh
shellcheck moverStatus.sh
git diff --exit-code HEAD
