from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    bot_token: str
    mechanic_group_id: int
    superadmin_ids: list[int]
    allowed_employee_ids: list[int]
    database_path: Path
    photos_dir: Path
    admin_dashboard_password: str


def _parse_int_list(value: str) -> list[int]:
    items = [i.strip() for i in value.split(",") if i.strip()]
    return [int(i) for i in items]


def load_settings() -> Settings:
    # Local .env must override inherited shell vars.
    load_dotenv(override=True)

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    mechanic_group_id = int(os.getenv("MECHANIC_GROUP_ID", "0"))
    superadmin_ids = _parse_int_list(os.getenv("SUPERADMIN_IDS", ""))
    allowed_employee_ids = _parse_int_list(os.getenv("ALLOWED_EMPLOYEE_IDS", ""))
    database_path = Path(os.getenv("DATABASE_PATH", "data/inspection.db"))
    photos_dir = Path(os.getenv("PHOTOS_DIR", "data/photos"))
    admin_dashboard_password = os.getenv("ADMIN_DASHBOARD_PASSWORD", "change_me")

    if not bot_token:
        raise ValueError("BOT_TOKEN is required in .env")
    if mechanic_group_id == 0:
        raise ValueError("MECHANIC_GROUP_ID is required in .env")
    if not superadmin_ids:
        raise ValueError("SUPERADMIN_IDS is required in .env")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    photos_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        bot_token=bot_token,
        mechanic_group_id=mechanic_group_id,
        superadmin_ids=superadmin_ids,
        allowed_employee_ids=allowed_employee_ids,
        database_path=database_path,
        photos_dir=photos_dir,
        admin_dashboard_password=admin_dashboard_password,
    )
