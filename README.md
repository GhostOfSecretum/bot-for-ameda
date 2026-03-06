# Цифровая приёмка спецтехники через Telegram

Локальный MVP:
- Telegram-бот для водителя
- Обязательная фотофиксация (5 фото)
- Отправка отчёта механикам с кнопками решения
- Хранение истории и фото в локальной БД/файлах
- Веб-панель (Streamlit) для поиска и просмотра

## 1) Быстрый старт локально

1. Установите Python 3.11+.
2. Создайте виртуальное окружение:
   - macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Создайте `.env` на основе примера:
   ```bash
   cp .env.example .env
   ```
5. Заполните переменные в `.env`:
   - `BOT_TOKEN` — токен вашего бота
   - `MECHANIC_GROUP_ID` — ID группы механиков (бот должен быть в группе)
   - `SUPERADMIN_IDS` — ваш Telegram user_id (можно список через запятую)
6. Запустите бота:
   ```bash
   python run_bot.py
   ```
7. (Опционально) Запустите админ-панель:
   ```bash
   streamlit run admin_dashboard.py
   ```

## 2) Что уже реализовано в MVP

- Сценарий водителя:
  - ФИО
  - Выбор техники (тип → марка → номер)
  - Чек-лист с ответами `ОК/Не ОК`
  - Для `Не ОК`: обязательный комментарий и фото неисправности
  - Обязательные 5 фото перед отправкой:
    - спереди, сзади, слева, справа, приборная панель
- Итоговый отчёт уходит в группу механиков
- Механик принимает решение кнопками:
  - `Разрешить выезд`
  - `Запретить выезд`
  - `В ремонт`
- Водитель получает автоматическое уведомление
- Вся история сохраняется в SQLite

## 3) Архитектура и передача управления

Проект построен так, чтобы вы могли передать доступ компании:
- Все настройки через `.env`
- Роли:
  - superadmin — владелец системы (вы)
  - mechanic/admin — сотрудники компании
- Отдельная админ-панель для поиска, фильтрации и просмотра фото
- В будущем перенос на PostgreSQL и сервер без переписывания бизнес-логики

## 4) Следующий этап после теста

1. Развернуть на сервере (Docker + systemd/compose).
2. Переключить БД на PostgreSQL.
3. Вынести фото в S3-совместимое хранилище.
4. Настроить резервные копии.
5. Добавить аудит действий администраторов.

## 5) Деплой на сервере через Docker Compose

Ниже базовый вариант запуска через SSH (например, в Termius).

### 5.1 Подготовка сервера (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

После `usermod` перелогиньтесь по SSH.

### 5.2 Загрузка проекта

Вариант A (git):
```bash
git clone <URL_ВАШЕГО_РЕПО> ameda-bot
cd ameda-bot
```

Вариант B (без git): загрузите папку проекта на сервер в `/opt/ameda-bot` и перейдите в нее.

### 5.3 Настройка переменных

```bash
cp .env.example .env
nano .env
```

Заполните минимум:
- `BOT_TOKEN`
- `MECHANIC_GROUP_ID`
- `SUPERADMIN_IDS`
- `ADMIN_DASHBOARD_PASSWORD`

Пути `DATABASE_PATH=data/inspection.db` и `PHOTOS_DIR=data/photos` оставьте как есть,  
они уже соответствуют Docker named volume `ameda_data:/app/data`.

Если включаете экспорт в Google Sheets и хотите кликабельную ссылку на карточку отчета:
- `REPORTS_SPREADSHEET_ID` — ID таблицы Google Sheets
- `GOOGLE_SERVICE_ACCOUNT_JSON` — путь к service account JSON
- `ADMIN_DASHBOARD_BASE_URL` — внешний URL админ-панели (например, `https://dashboard.company.ru`)

Тогда в листе `Отчеты` появится колонка `Карточка отчета` с ссылкой `.../?inspection_id=<id>`.

### 5.4 Сборка и запуск

Запуск Telegram-бота с автобэкапом:
```bash
docker compose up -d --build
```

Запуск бота + админ-панели:
```bash
docker compose --profile dashboard up -d --build
```

### 5.5 Полезные команды

Логи бота:
```bash
docker compose logs -f bot
```

Логи панели:
```bash
docker compose logs -f dashboard
```

Логи автобэкапа:
```bash
docker compose logs -f backup
```

Перезапуск после обновлений:
```bash
docker compose up -d --build
```

Остановка:
```bash
docker compose down
```

### 5.6 Автобэкап уже включен (без cron)

После запуска `docker compose up -d --build` автоматически стартует сервис `backup`.
Он делает:
- 1 бэкап сразу при старте
- далее ежедневный бэкап по расписанию (`BACKUP_HOUR`/`BACKUP_MINUTE`)
- ротацию: хранит только последние `BACKUP_KEEP_LAST` архивов

Архивы лежат на сервере в папке проекта: `./backups`.

Что попадает в бэкап:
- SQLite (`/app/data/inspection.db`)
- Фото (`/app/data/photos/...`)

Важно: `.env` в бэкап не входит, храните его отдельно в защищенном месте.

Опциональные настройки в `.env`:
- `TZ=UTC`
- `BACKUP_HOUR=3`
- `BACKUP_MINUTE=10`
- `BACKUP_KEEP_LAST=14`
- `BACKUP_PREFIX=ameda_data`

### 5.7 Ручные команды backup/restore

Создать бэкап вручную:
```bash
make backup
```

Восстановить из бэкапа:
```bash
make restore FILE=backups/ameda_data_YYYYMMDD_HHMMSS.tar.gz
```

### 5.8 Если раньше использовали `./data:/app/data`

Если у вас уже были данные в папке `./data`, разово перенесите их в новый volume:

```bash
docker volume create ameda_data
docker run --rm -v ameda_data:/to -v "$(pwd)/data:/from:ro" alpine:3.20 sh -c "cp -a /from/. /to/"
```

После этого можно запускать новую конфигурацию `docker compose up -d --build`.

## 6) Security/Secrets

Чтобы безопасно хранить проект в GitHub:

- Никогда не коммитьте `.env` и другие секреты (токены, пароли, API-ключи).
- Используйте только шаблон `.env.example` без реальных значений.
- Храните production-секреты в защищенном хранилище (например, GitHub Secrets, 1Password, Vault).
- Не публикуйте `credentials/*.json` в репозитории.

Если секрет уже утек:

1. Сразу отзовите/перевыпустите токен или ключ у провайдера.
2. Удалите секрет из Git-истории.
3. Обновите `.env` на сервере и перезапустите сервисы.
