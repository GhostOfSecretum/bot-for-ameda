#!/usr/bin/env bash
set -euo pipefail

BRANCH="${1:-main}"

# Always run from project root, even if script was called from elsewhere.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "==> Deploy started"
echo "Project: ${PROJECT_ROOT}"
echo "Branch:  ${BRANCH}"

if [ ! -d ".git" ]; then
  echo "Error: .git directory not found. Deploy script expects a git checkout." >&2
  exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
  echo "Error: docker-compose.yml not found in ${PROJECT_ROOT}" >&2
  exit 1
fi

echo "==> Updating source code"
git fetch origin "${BRANCH}"
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}"

echo "==> Rebuilding and restarting containers"
docker compose up -d --build --remove-orphans

echo "==> Current services"
docker compose ps

echo "==> Deploy completed successfully"
