#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

VOLUME_NAME="${VOLUME_NAME:-ameda_data}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
KEEP_LAST="${KEEP_LAST:-14}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_NAME="ameda_data_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"

if ! [[ "$KEEP_LAST" =~ ^[0-9]+$ ]] || [ "$KEEP_LAST" -lt 1 ]; then
  echo "KEEP_LAST must be a positive integer (current: ${KEEP_LAST})."
  exit 1
fi

if ! docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1; then
  echo "Docker volume '${VOLUME_NAME}' not found. Start services first: docker compose up -d"
  exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "Creating backup '${ARCHIVE_PATH}' from volume '${VOLUME_NAME}'..."
docker run --rm \
  -v "${VOLUME_NAME}:/volume:ro" \
  -v "${BACKUP_DIR}:/backup" \
  alpine:3.20 \
  sh -c "tar -czf \"/backup/${ARCHIVE_NAME}\" -C /volume ."

mapfile -t BACKUPS < <(ls -1t "${BACKUP_DIR}"/ameda_data_*.tar.gz 2>/dev/null || true)
if (( ${#BACKUPS[@]} > KEEP_LAST )); then
  echo "Applying rotation: keep last ${KEEP_LAST} backups."
  for old_file in "${BACKUPS[@]:KEEP_LAST}"; do
    rm -f "$old_file"
    echo "Deleted old backup: ${old_file}"
  done
fi

echo "Backup completed: ${ARCHIVE_PATH}"
