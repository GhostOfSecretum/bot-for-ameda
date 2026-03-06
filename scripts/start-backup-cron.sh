#!/bin/sh
set -eu

if command -v apk >/dev/null 2>&1; then
  apk add --no-cache tzdata >/dev/null 2>&1 || true
fi

BACKUP_HOUR="${BACKUP_HOUR:-3}"
BACKUP_MINUTE="${BACKUP_MINUTE:-10}"

case "$BACKUP_HOUR" in
  ''|*[!0-9]*)
    BACKUP_HOUR=3
    ;;
esac
case "$BACKUP_MINUTE" in
  ''|*[!0-9]*)
    BACKUP_MINUTE=10
    ;;
esac

if [ "$BACKUP_HOUR" -gt 23 ]; then
  BACKUP_HOUR=3
fi
if [ "$BACKUP_MINUTE" -gt 59 ]; then
  BACKUP_MINUTE=10
fi

CRON_LINE="${BACKUP_MINUTE} ${BACKUP_HOUR} * * * sh /usr/local/bin/backup-once.sh >> /var/log/backup.log 2>&1"
echo "$CRON_LINE" > /etc/crontabs/root

# Run first backup immediately on container start.
sh /usr/local/bin/backup-once.sh

echo "Backup schedule enabled: ${CRON_LINE}"
exec crond -f -l 8
