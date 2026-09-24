#!/usr/bin/env bash
# Ship the app to the VM and rebuild it there. Run from your own machine:
#
#   deploy/deploy.sh ubuntu@<vm-ip>
#
# Deploys whatever is checked out, so rolling back is: check out the previous
# commit, run this again.
set -euo pipefail
host="${1:?usage: deploy/deploy.sh ubuntu@<vm-ip>}"
cd "$(dirname "$0")/.."

# Only what the image and the proxy need, by name. The workbook, samples/ and
# everything else in the repo never leave this machine.
rsync -az --delete --relative \
  Dockerfile .dockerignore requirements.txt app.py stamper.py i18n.py \
  templates static deploy/compose.yaml deploy/Caddyfile \
  "$host:sgm/"

ssh "$host" 'cd sgm && docker compose -f deploy/compose.yaml up -d --build --remove-orphans && docker image prune -f'
echo "Deployed. https://po-vim.help"
