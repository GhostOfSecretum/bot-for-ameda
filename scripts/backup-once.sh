#!/bin/sh
set -eu

DATA_DIR="${DATA_DIR:-/data}"
BACKUP_DIR="${BACKUP_DIR:-/backup}"
BACKUP_PREFIX="${BACKUP_PREFIX:-ameda_data}"
BACKUP_KEEP_LAST="${BACKUP_KEEP_LAST:-14}"
export TZ="${TZ:-Europe/Moscow}"

case "$BACKUP_KEEP_LAST" in
  ''|*[!0-9]*)
    BACKUP_KEEP_LAST=14
    ;;
esac

if [ "$BACKUP_KEEP_LAST" -lt 1 ]; then
  BACKUP_KEEP_LAST=14
fi

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_PATH="${BACKUP_DIR}/${BACKUP_PREFIX}_${TIMESTAMP}.tar.gz"

tar -czf "$ARCHIVE_PATH" -C "$DATA_DIR" .

COUNT=0
for FILE in $(ls -1t "${BACKUP_DIR}/${BACKUP_PREFIX}"_*.tar.gz 2>/dev/null || true); do
  COUNT=$((COUNT + 1))
  if [ "$COUNT" -gt "$BACKUP_KEEP_LAST" ]; then
    rm -f "$FILE"
  fi
done

echo "Backup completed: ${ARCHIVE_PATH}"
