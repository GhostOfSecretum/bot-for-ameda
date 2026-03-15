from __future__ import annotations

from pathlib import Path

from aiogram import Bot


class PhotoStorage:
    def __init__(self, photos_root: Path):
        root = photos_root.expanduser()
        if not root.is_absolute():
            project_root = Path(__file__).resolve().parents[1]
            root = project_root / root
        self.photos_root = root.resolve()
        self.photos_root.mkdir(parents=True, exist_ok=True)

    async def save_telegram_photo(
        self,
        bot: Bot,
        telegram_file_id: str,
        inspection_id: int,
        category: str,
        filename: str,
    ) -> str:
        target_dir = self.photos_root / str(inspection_id) / category
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        await bot.download(telegram_file_id, destination=target_path)
        return str(target_path)

    async def save_daily_action_photo(
        self,
        bot: Bot,
        telegram_file_id: str,
        driver_tg_id: int,
        filename: str,
    ) -> str:
        target_dir = self.photos_root / "daily_actions" / str(driver_tg_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        await bot.download(telegram_file_id, destination=target_path)
        return str(target_path)
