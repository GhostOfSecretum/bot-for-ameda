.PHONY: backup restore deploy install-ssh-key

backup:
	bash scripts/backup.sh

restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make restore FILE=backups/ameda_data_YYYYMMDD_HHMMSS.tar.gz"; \
		exit 1; \
	fi
	bash scripts/restore.sh "$(FILE)"

deploy:
	bash scripts/deploy.sh "$(BRANCH)"

# Однократно: скопировать SSH-ключ на сервер (Host ameda в ~/.ssh/config), дальше вход без пароля.
install-ssh-key:
	bash scripts/install-ssh-pubkey.sh
