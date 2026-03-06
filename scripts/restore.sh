#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

VOLUME_NAME="${VOLUME_NAME:-ameda_data}"
AUTO_YES="false"

if [[ "${1:-}" == "--yes" ]]; then
  AUTO_YES="true"
  shift
fi

BACKUP_FILE="${1:-}"
if [[ -z "$BACKUP_FILE" ]]; then
  echo "Usage: bash scripts/restore.sh [--yes] <backup-file>"
  echo "Example: bash scripts/restore.sh backups/ameda_data_20260306_010203.tar.gz"
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" && -f "$PROJECT_DIR/backups/$BACKUP_FILE" ]]; then
  BACKUP_FILE="$PROJECT_DIR/backups/$BACKUP_FILE"
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

BACKUP_DIR="$(cd "$(dirname "$BACKUP_FILE")" && pwd)"
BACKUP_NAME="$(basename "$BACKUP_FILE")"

if [[ "$AUTO_YES" != "true" ]]; then
  echo "This will REPLACE current data in volume '${VOLUME_NAME}' with '${BACKUP_NAME}'."
  read -r -p "Continue? [y/N]: " confirm
  if [[ "${confirm,,}" != "y" ]]; then
    echo "Restore cancelled."
    exit 0
  fi
fi

echo "Stopping services..."
docker compose down

echo "Ensuring volume '${VOLUME_NAME}' exists..."
docker volume create "$VOLUME_NAME" >/dev/null

echo "Clearing existing data in '${VOLUME_NAME}'..."
docker run --rm \
  -v "${VOLUME_NAME}:/volume" \
  alpine:3.20 \
  sh -c "rm -rf /volume/* /volume/.[!.]* /volume/..?*"

echo "Restoring '${BACKUP_NAME}' into volume '${VOLUME_NAME}'..."
docker run --rm \
  -v "${VOLUME_NAME}:/volume" \
  -v "${BACKUP_DIR}:/backup:ro" \
  alpine:3.20 \
  sh -c "tar -xzf \"/backup/${BACKUP_NAME}\" -C /volume"

echo "Starting services..."
docker compose up -d

echo "Restore completed successfully."
