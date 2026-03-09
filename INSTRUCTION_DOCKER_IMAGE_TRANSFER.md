# Инструкция: передача Docker-образа бота айтишнику

Этот вариант подходит, если вы передаете не исходники, а готовый образ:

- `ameda-bot_it-transfer-20260307.tar.gz`

## 1) На сервере загрузить образ

```bash
docker load -i ameda-bot_it-transfer-20260307.tar.gz
docker images | rg ameda-bot
```

Ожидаемый тег образа:
- `ameda-bot:it-transfer-20260307`

## 2) Подготовить `.env`

Создайте файл `.env` рядом с командой запуска и заполните минимум:

- `BOT_TOKEN`
- `MECHANIC_GROUP_ID`
- `SUPERADMIN_IDS`
- `ADMIN_DASHBOARD_PASSWORD`

Важно: `.env` не должен попадать в Git и в архив образа.

Если нужен экспорт в Google Sheets:
- положите ключ в `./credentials/google-service-account.json`
- в `.env` укажите `GOOGLE_SERVICE_ACCOUNT_JSON=credentials/google-service-account.json`

## 3) Запуск бота

```bash
docker volume create ameda_data
docker run -d \
  --name ameda-bot \
  --restart unless-stopped \
  --env-file .env \
  -v ameda_data:/app/data \
  -v "$(pwd)/credentials:/app/credentials:ro" \
  ameda-bot:it-transfer-20260307 \
  python run_bot.py
```

## 4) Проверка

```bash
docker ps
docker logs -f --tail=100 ameda-bot
```

## 5) Обновление на новую версию образа

```bash
docker stop ameda-bot
docker rm ameda-bot
docker load -i ameda-bot_it-transfer-NEW.tar.gz
docker run -d \
  --name ameda-bot \
  --restart unless-stopped \
  --env-file .env \
  -v ameda_data:/app/data \
  -v "$(pwd)/credentials:/app/credentials:ro" \
  ameda-bot:it-transfer-NEW \
  python run_bot.py
```

Данные (SQLite и фото) сохраняются в volume `ameda_data`, поэтому при обновлении не теряются.
