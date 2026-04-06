#!/usr/bin/env bash
# Однократно копирует публичный ключ на сервер (запросит пароль SSH один раз).
# После этого: ssh ameda — без пароля (если в ~/.ssh/config задан Host ameda).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SSH_HOST="${SSH_HOST:-ameda}"
SSH_USER="${SSH_USER:-root}"
PUBKEY="${PUBKEY:-$HOME/.ssh/ameda_rsa.pub}"

if [ ! -f "$PUBKEY" ]; then
  echo "Нет файла $PUBKEY — задайте PUBKEY=... или создайте ключ: ssh-keygen -t ed25519 -f ~/.ssh/ameda_ed25519" >&2
  exit 1
fi

echo "==> Копирую ключ в authorized_keys на ${SSH_USER}@${SSH_HOST}"
echo "    (один раз понадобится пароль от SSH)"
ssh-copy-id -i "$PUBKEY" "${SSH_USER}@${SSH_HOST}"

echo "==> Проверка входа без пароля"
ssh -o BatchMode=yes -o ConnectTimeout=10 "${SSH_USER}@${SSH_HOST}" "echo OK: вход по ключу работает"

echo "==> Готово. Дальше: ssh ${SSH_HOST}"
