from __future__ import annotations

import asyncio
import logging
import socket
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    FSInputFile,
    InputMediaPhoto,
    Message,
    ReplyKeyboardRemove,
)

from app.config import load_settings
from app.constants import (
    MECHANIC_ROLES,
    REQUIRED_PHOTOS,
)
from app.db import Database
from app.i18n import (
    back_label,
    checklist_items,
    daily_actions_display_map,
    driver_license_type_display_map,
    driver_license_type_labels,
    driver_status_text,
    equipment_type_display_map,
    is_back_text,
    normalize_language,
    required_photo_labels,
    t,
)
from app.keyboards import (
    daily_refuel_decision_keyboard,
    language_keyboard,
    mechanic_decision_keyboard,
    personal_data_consent_keyboard,
    request_location_keyboard,
    simple_reply_keyboard,
    submit_report_keyboard,
    yes_no_keyboard,
)
from app.storage import PhotoStorage
from app.time_utils import now_compact_timestamp, now_iso


logger = logging.getLogger(__name__)
PERSONAL_DATA_POLICY_URL = "https://telegra.ph/Politika-Personalnyh-Dannyh-03-06-2"


def _build_session() -> AiohttpSession:
    import platform

    session = AiohttpSession()
    if platform.system() == "Darwin":
        # macOS + LibreSSL can stall on IPv6 TLS handshake with Telegram API.
        session._connector_init["family"] = socket.AF_INET
    return session


@dataclass
class InspectionDraft:
    driver_tg_id: int
    language: str | None = None
    waiting_for_language_selection: bool = False
    waiting_for_personal_data_consent: bool = False
    waiting_for_registration_full_name: bool = False
    waiting_for_registration_phone: bool = False
    pending_registration_full_name: str | None = None
    start_after_registration: bool = False
    driver_license_type: str | None = None
    driver_license_type_display_to_raw: dict[str, str] = field(default_factory=dict)
    equipment_type: str | None = None
    equipment_brand: str | None = None
    equipment_id: int | None = None
    checklist_index: int = 0
    inspection_id: int | None = None
    # status for current checklist question when answer is "Не ОК"
    waiting_for_issue_comment: bool = False
    waiting_for_issue_photo: bool = False
    pending_nok_comment: str | None = None
    # required photos
    required_photos: dict[str, str] = field(default_factory=dict)
    waiting_for_required_location: bool = False
    required_location: tuple[float, float] | None = None
    equipment_type_display_to_raw: dict[str, str] = field(default_factory=dict)
    inspection_flow_started: bool = False
    waiting_for_daily_actions_root: bool = False
    waiting_for_daily_actions_submenu: bool = False
    daily_actions_display_to_key: dict[str, str] = field(default_factory=dict)
    waiting_for_daily_filter_result: bool = False
    waiting_for_daily_comment: bool = False
    waiting_for_daily_optional_photo: bool = False
    waiting_for_daily_refuel_confirm: bool = False
    waiting_for_daily_refuel_photo: bool = False
    waiting_for_daily_end_workday_refuel: bool = False
    waiting_for_daily_end_workday_fuel_photo: bool = False
    waiting_for_daily_end_workday_photos: bool = False
    waiting_for_daily_end_workday_location: bool = False
    daily_action_key: str | None = None
    daily_action_status_key: str | None = None
    daily_action_comment: str | None = None
    daily_end_workday_fuel_photo_path: str | None = None
    daily_end_workday_required_photos: dict[str, str] = field(default_factory=dict)
    daily_end_workday_location: tuple[float, float] | None = None


class InspectionBot:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.db = Database(self.settings.database_path)
        self.storage = PhotoStorage(self.settings.photos_dir)
        self.bot = Bot(
            token=self.settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            session=_build_session(),
        )
        self.dp = Dispatcher()
        self.router = Router()
        self.dp.include_router(self.router)
        self.drafts: dict[int, InspectionDraft] = {}
        self.photo_locks: dict[int, asyncio.Lock] = {}
        self.required_photo_group_tasks: dict[int, asyncio.Task[None]] = {}
        self._register_handlers()

        for sid in self.settings.superadmin_ids:
            self.db.upsert_user(telegram_id=sid, role="superadmin", full_name=None)

    def _register_handlers(self) -> None:
        private_chat = F.chat.type == "private"

        self.router.message.register(self.cmd_start, Command("start"), private_chat)
        self.router.message.register(self.cmd_endday, Command("endday"), private_chat)
        self.router.message.register(self.cmd_register, Command("register"), private_chat)
        self.router.message.register(self.cmd_actions, Command("actions"), private_chat)
        self.router.message.register(self.cmd_help, Command("help"), private_chat)
        self.router.message.register(self.cmd_role, Command("role"), private_chat)
        self.router.message.register(self.cmd_setrole, Command("setrole"), private_chat)
        self.router.message.register(self.on_text, F.text, private_chat)
        self.router.message.register(self.on_photo, F.photo, private_chat)
        self.router.message.register(self.on_location, F.location, private_chat)
        self.router.callback_query.register(
            self.on_language_selected,
            F.data.startswith("lang:"),
            F.message.chat.type == "private",
        )
        self.router.callback_query.register(
            self.on_registration_consent,
            F.data.startswith("regconsent:"),
            F.message.chat.type == "private",
        )
        self.router.callback_query.register(
            self.on_item_answer,
            F.data.startswith("item:"),
            F.message.chat.type == "private",
        )
        self.router.callback_query.register(
            self.on_required_photo_action,
            F.data.startswith("req_photo:"),
            F.message.chat.type == "private",
        )
        self.router.callback_query.register(self.on_mechanic_decision, F.data.startswith("mechanic:"))
        self.router.callback_query.register(
            self.on_daily_refuel_decision,
            F.data.startswith("dailyfuel:"),
        )

    async def run(self) -> None:
        for attempt in range(1, 6):
            try:
                await self.bot.delete_webhook(drop_pending_updates=True)
                break
            except TelegramNetworkError:
                delay = min(attempt * 5, 30)
                logger.warning(
                    "delete_webhook failed (attempt %d/5), retrying in %ds…",
                    attempt, delay,
                )
                await asyncio.sleep(delay)
        else:
            logger.error("Could not reach Telegram API after 5 attempts, starting polling anyway")

        try:
            await self._configure_bot_commands()
        except TelegramNetworkError:
            logger.warning("Failed to set bot commands, will retry on next restart")

        await self.dp.start_polling(
            self.bot,
            allowed_updates=self.dp.resolve_used_update_types(),
        )

    async def _configure_bot_commands(self) -> None:
        await self.bot.set_my_commands(
            [
                BotCommand(command="start", description="🚀 Начало приемки"),
                BotCommand(command="actions", description="🗂️ Действия в течении смены"),
                BotCommand(command="endday", description="🏁 Завершение смены"),
                BotCommand(command="register", description="👤 Регистрация сотрудника"),
            ]
        )

    def _get_or_create_draft(self, user_id: int) -> InspectionDraft:
        draft = self.drafts.get(user_id)
        if not draft:
            draft = InspectionDraft(driver_tg_id=user_id)
            self.drafts[user_id] = draft
        return draft

    def _get_photo_lock(self, user_id: int) -> asyncio.Lock:
        lock = self.photo_locks.get(user_id)
        if lock is None:
            lock = asyncio.Lock()
            self.photo_locks[user_id] = lock
        return lock

    def _resolve_stored_photo_path(self, stored_path: str) -> Path:
        raw_path = Path(stored_path).expanduser()
        if raw_path.is_absolute():
            return raw_path

        project_root = Path(__file__).resolve().parents[1]
        photos_root = self.storage.photos_root
        candidates = [
            Path.cwd() / raw_path,
            project_root / raw_path,
            photos_root / raw_path,
            photos_root.parent / raw_path,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return (project_root / raw_path).resolve()

    def _cancel_required_photo_group_task(self, user_id: int) -> None:
        task = self.required_photo_group_tasks.pop(user_id, None)
        if task and not task.done():
            task.cancel()

    async def _notify_missing_required_photos_delayed(self, user_id: int, chat_id: int) -> None:
        try:
            await asyncio.sleep(1.2)
            lock = self._get_photo_lock(user_id)
            async with lock:
                draft = self.drafts.get(user_id)
                if not draft or not draft.inspection_id:
                    return
                lang = self._draft_language(user_id=user_id, draft=draft)
                if draft.checklist_index < len(
                    checklist_items(lang, draft.driver_license_type, draft.equipment_type)
                ):
                    return
                missing_count = len(self._missing_required_photos(draft))
                if missing_count == 0:
                    return
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=t(lang, "required_photos_need_more_count", remaining=missing_count),
                    reply_markup=submit_report_keyboard(
                        submit_text=t(lang, "submit_report_button")
                    ),
                )
        except asyncio.CancelledError:
            return
        finally:
            current = self.required_photo_group_tasks.get(user_id)
            if current is asyncio.current_task():
                self.required_photo_group_tasks.pop(user_id, None)

    def _reset_draft(self, user_id: int) -> InspectionDraft:
        draft = self._get_or_create_draft(user_id)
        draft.__dict__.update(InspectionDraft(driver_tg_id=user_id).__dict__)
        return draft

    @staticmethod
    def _is_registered(user: Any | None) -> bool:
        if not user:
            return False
        full_name = (user["full_name"] or "").strip()
        phone = (user["phone"] or "").strip()
        return bool(full_name and phone)

    @staticmethod
    def _normalize_phone(raw_phone: str) -> str | None:
        digits = "".join(ch for ch in raw_phone if ch.isdigit())
        if len(digits) < 10 or len(digits) > 15:
            return None
        if len(digits) == 11 and digits.startswith("8"):
            return f"+7{digits[1:]}"
        return f"+{digits}"

    @staticmethod
    def _user_language(user: Any | None) -> str:
        if not user:
            return "ru"
        language = user["language"] if "language" in user.keys() else None
        return normalize_language(language)

    @staticmethod
    def _personal_data_consent_status(user: Any | None) -> bool | None:
        if not user:
            return None
        if "personal_data_consent" not in user.keys():
            return None
        value = user["personal_data_consent"]
        if value is None:
            return None
        return bool(value)

    async def _ensure_personal_data_consent_message(self, message: Message) -> bool:
        if not message.from_user:
            return False
        user = self.db.get_user(message.from_user.id)
        lang = self._user_language(user)
        consent_status = self._personal_data_consent_status(user)
        if consent_status is True:
            return True
        key = (
            "registration_consent_declined"
            if consent_status is False
            else "consent_required_before_registration"
        )
        await message.answer(t(lang, key))
        return False

    async def _ensure_personal_data_consent_callback(self, callback: CallbackQuery) -> bool:
        if not callback.from_user:
            return False
        user = self.db.get_user(callback.from_user.id)
        lang = self._user_language(user)
        consent_status = self._personal_data_consent_status(user)
        if consent_status is True:
            return True
        await callback.answer(t(lang, "consent_interaction_blocked_short"), show_alert=True)
        return False

    def _draft_language(
        self,
        *,
        user_id: int,
        draft: InspectionDraft | None = None,
        user: Any | None = None,
    ) -> str:
        if draft and draft.language:
            return normalize_language(draft.language)
        if user is None:
            user = self.db.get_user(user_id)
        lang = self._user_language(user)
        if draft is not None:
            draft.language = lang
        return lang

    def _is_user_allowed(self, user_id: int) -> bool:
        allowed_ids = self.settings.allowed_employee_ids
        if not allowed_ids:
            # Empty whitelist means "not enforced yet".
            return True
        if user_id in self.settings.superadmin_ids:
            return True
        return user_id in allowed_ids

    async def _ensure_message_access(self, message: Message) -> bool:
        if not message.from_user:
            return False
        user_id = message.from_user.id
        if self._is_user_allowed(user_id):
            return True
        user = self.db.get_user(user_id)
        lang = self._user_language(user)
        await message.answer(t(lang, "access_denied_whitelist"))
        return False

    async def _ensure_callback_access(self, callback: CallbackQuery) -> bool:
        if not callback.from_user:
            return False
        user_id = callback.from_user.id
        if self._is_user_allowed(user_id):
            return True
        user = self.db.get_user(user_id)
        lang = self._user_language(user)
        await callback.answer(t(lang, "access_denied_whitelist"), show_alert=True)
        return False

    async def _start_registration(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        continue_to_inspection: bool,
    ) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        draft.waiting_for_personal_data_consent = False
        draft.waiting_for_registration_full_name = False
        draft.waiting_for_registration_phone = False
        draft.pending_registration_full_name = None
        draft.start_after_registration = continue_to_inspection
        consent_status = self.db.get_personal_data_consent(draft.driver_tg_id)
        if consent_status is not True:
            draft.waiting_for_personal_data_consent = True
            await message.answer(t(lang, "registration_consent_policy_hint"))
            await message.answer(
                t(lang, "registration_consent_prompt"),
                reply_markup=personal_data_consent_keyboard(
                    policy_text=t(lang, "registration_consent_policy_button"),
                    policy_url=PERSONAL_DATA_POLICY_URL,
                    agree_text=t(lang, "registration_consent_agree_button"),
                    decline_text=t(lang, "registration_consent_decline_button"),
                ),
            )
            return
        draft.waiting_for_registration_full_name = True
        await message.answer(t(lang, "registration_start"))

    async def _continue_start_flow(self, message: Message, user_id: int) -> None:
        db_user = self.db.get_user(user_id)
        if db_user is None:
            self.db.upsert_user(user_id, role="driver")
            db_user = self.db.get_user(user_id)
        draft = self._get_or_create_draft(user_id)
        lang = self._user_language(db_user)
        if (
            draft.inspection_flow_started
            and draft.driver_license_type is not None
        ):
            draft.language = lang
            if draft.equipment_type is None:
                await self._ask_equipment_type(message, draft)
                return
            if draft.equipment_brand is None:
                await self._ask_equipment_brand(message, draft)
                return
            if draft.equipment_id is None:
                await self._ask_equipment_number(message, draft)
                return
            if draft.inspection_id is not None:
                await message.answer(t(lang, "go_to_inspection"))
                return
            await self._ask_equipment_number(message, draft)
            return
        draft = self._reset_draft(user_id)
        draft.language = lang
        if self.db.get_personal_data_consent(user_id) is not True:
            await self._start_registration(message, draft, continue_to_inspection=True)
            return
        if not self._is_registered(db_user):
            await self._start_registration(message, draft, continue_to_inspection=True)
            return
        await message.answer(t(draft.language, "start_new_inspection"))
        await self._ask_driver_license_type(message, draft)

    async def cmd_start(self, message: Message) -> None:
        if not message.from_user:
            return
        if not await self._ensure_message_access(message):
            return
        user_id = message.from_user.id
        db_user = self.db.get_user(user_id)
        if db_user is None:
            self.db.upsert_user(user_id, role="driver")
        else:
            self.db.upsert_user(user_id, role=None)
        draft = self._reset_draft(user_id)
        draft.language = self._user_language(db_user)
        draft.waiting_for_language_selection = True
        await message.answer(
            t(draft.language, "choose_language_prompt"),
            reply_markup=language_keyboard(selected_language=draft.language),
        )

    async def on_language_selected(self, callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data or not callback.message:
            return
        if not await self._ensure_callback_access(callback):
            return
        user_id = callback.from_user.id
        _, language = callback.data.split(":", maxsplit=1)
        language = normalize_language(language)
        self.db.upsert_user(telegram_id=user_id, role=None, language=language)
        draft = self._get_or_create_draft(user_id)
        draft.language = language
        draft.waiting_for_language_selection = False
        await callback.answer(t(language, "language_saved"))
        await self._try_clear_inline_keyboard(callback)
        await self._continue_start_flow(callback.message, user_id)

    async def on_registration_consent(self, callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data or not callback.message:
            return
        if not await self._ensure_callback_access(callback):
            return
        user_id = callback.from_user.id
        draft = self._get_or_create_draft(user_id)
        lang = self._draft_language(user_id=user_id, draft=draft)
        _, action = callback.data.split(":", maxsplit=1)

        if action == "agree":
            self.db.upsert_user(
                telegram_id=user_id,
                personal_data_consent=True,
                role=None,
                language=lang,
            )
            draft.waiting_for_personal_data_consent = False
            draft.waiting_for_registration_full_name = True
            draft.waiting_for_registration_phone = False
            draft.pending_registration_full_name = None
            await self._try_clear_inline_keyboard(callback)
            await callback.answer(t(lang, "registration_consent_accepted"))
            await callback.message.answer(t(lang, "registration_start"))
            return

        if action == "decline":
            self.db.upsert_user(
                telegram_id=user_id,
                personal_data_consent=False,
                role=None,
                language=lang,
            )
            draft.waiting_for_personal_data_consent = False
            draft.waiting_for_registration_full_name = False
            draft.waiting_for_registration_phone = False
            draft.pending_registration_full_name = None
            draft.start_after_registration = False
            await self._try_clear_inline_keyboard(callback)
            await callback.answer()
            await callback.message.answer(t(lang, "registration_consent_declined"))
            return

        await callback.answer(t(lang, "invalid_button"), show_alert=True)

    async def cmd_register(self, message: Message) -> None:
        if not message.from_user:
            return
        if not await self._ensure_message_access(message):
            return
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        if user is None:
            self.db.upsert_user(user_id, role="driver")
            user = self.db.get_user(user_id)
        draft = self._reset_draft(user_id)
        draft.language = self._user_language(user)
        await self._start_registration(message, draft, continue_to_inspection=False)

    async def cmd_actions(self, message: Message) -> None:
        if not message.from_user:
            return
        if not await self._ensure_message_access(message):
            return
        if not await self._ensure_personal_data_consent_message(message):
            return
        user_id = message.from_user.id
        if self.db.get_user(user_id) is None:
            self.db.upsert_user(user_id, role="driver")
        draft = self._get_or_create_draft(user_id)
        lang = self._draft_language(user_id=user_id, draft=draft)
        await self._ask_daily_actions_submenu(message, draft, lang=lang)

    async def cmd_endday(self, message: Message) -> None:
        if not message.from_user:
            return
        if not await self._ensure_message_access(message):
            return
        if not await self._ensure_personal_data_consent_message(message):
            return
        user_id = message.from_user.id
        if self.db.get_user(user_id) is None:
            self.db.upsert_user(user_id, role="driver")
        draft = self._get_or_create_draft(user_id)
        lang = self._draft_language(user_id=user_id, draft=draft)
        draft.daily_action_key = "end_workday"
        draft.daily_action_status_key = None
        draft.daily_action_comment = None
        self.db.add_audit(
            actor_telegram_id=user_id,
            action="daily_action_end_workday",
            entity_type="menu",
            entity_id=str(user_id),
            details="selected=/endday",
        )
        await self._ask_daily_end_workday_refuel(message, draft, lang=lang)

    async def cmd_help(self, message: Message) -> None:
        if not message.from_user:
            return
        if not await self._ensure_message_access(message):
            return
        user_id = message.from_user.id
        draft = self._get_or_create_draft(user_id)
        lang = self._draft_language(user_id=user_id, draft=draft)
        await message.answer(t(lang, "help_text"))

    async def cmd_role(self, message: Message) -> None:
        if not message.from_user:
            return
        if not await self._ensure_message_access(message):
            return
        user = self.db.get_user(message.from_user.id)
        lang = self._user_language(user)
        role = user["role"] if user else "driver"
        await message.answer(t(lang, "your_role", role=role))

    async def cmd_setrole(self, message: Message) -> None:
        if not message.from_user or not message.text:
            return
        if not await self._ensure_message_access(message):
            return
        actor = self.db.get_user(message.from_user.id)
        lang = self._user_language(actor)
        if not actor or actor["role"] != "superadmin":
            await message.answer(t(lang, "setrole_denied"))
            return

        parts = message.text.strip().split()
        if len(parts) != 3:
            await message.answer(t(lang, "setrole_format"))
            return
        try:
            target_id = int(parts[1])
            role = parts[2].strip()
            self.db.set_role(message.from_user.id, target_id, role)
            await message.answer(t(lang, "setrole_success", target_id=target_id, role=role))
        except Exception as exc:
            await message.answer(t(lang, "setrole_error", error=exc))

    async def on_text(self, message: Message) -> None:
        if not message.from_user or not message.text:
            return
        if not await self._ensure_message_access(message):
            return
        user_id = message.from_user.id
        text = message.text.strip()
        draft = self._get_or_create_draft(user_id)
        lang = self._draft_language(user_id=user_id, draft=draft)
        back_requested = is_back_text(text)

        if draft.waiting_for_language_selection:
            await message.answer(
                t(lang, "choose_language_buttons_hint"),
                reply_markup=language_keyboard(selected_language=lang),
            )
            return

        if draft.waiting_for_personal_data_consent:
            await message.answer(
                t(lang, "registration_consent_buttons_hint"),
                reply_markup=personal_data_consent_keyboard(
                    policy_text=t(lang, "registration_consent_policy_button"),
                    policy_url=PERSONAL_DATA_POLICY_URL,
                    agree_text=t(lang, "registration_consent_agree_button"),
                    decline_text=t(lang, "registration_consent_decline_button"),
                ),
            )
            return

        if not await self._ensure_personal_data_consent_message(message):
            return

        menu_button_label = t(lang, "daily_actions_menu_button")
        if draft.waiting_for_daily_actions_root:
            if back_requested:
                self._clear_daily_actions_state(draft)
                await message.answer(
                    t(lang, "daily_actions_closed"),
                    reply_markup=ReplyKeyboardRemove(),
                )
                return
            await self._ask_daily_actions_submenu(message, draft, lang=lang)
            return

        if draft.waiting_for_daily_actions_submenu:
            if back_requested:
                self._clear_daily_actions_state(draft)
                await message.answer(
                    t(lang, "daily_actions_closed"),
                    reply_markup=ReplyKeyboardRemove(),
                )
                return
            action_key = draft.daily_actions_display_to_key.get(text)
            if action_key is None:
                await message.answer(
                    t(lang, "daily_actions_submenu_buttons_hint"),
                    reply_markup=simple_reply_keyboard(
                        list(draft.daily_actions_display_to_key.keys()),
                        width=1,
                        with_back=True,
                        back_text=back_label(lang),
                    ),
                )
                return
            self.db.add_audit(
                actor_telegram_id=user_id,
                action=f"daily_action_{action_key}",
                entity_type="menu",
                entity_id=str(user_id),
                details=f"selected={text}",
            )
            draft.daily_action_key = action_key
            draft.daily_action_status_key = None
            draft.daily_action_comment = None
            if action_key == "blow_filters":
                await self._ask_daily_filter_result(message, draft, lang=lang)
                return
            if action_key == "workday_situations":
                await self._ask_daily_comment_for_current_action(message, draft, lang=lang)
                return
            if action_key == "refuel":
                await self._ask_daily_refuel_confirm(message, draft, lang=lang)
                return
            if action_key == "end_workday":
                await self._ask_daily_end_workday_refuel(message, draft, lang=lang)
                return
            return

        if draft.waiting_for_daily_filter_result:
            if back_requested:
                await self._ask_daily_actions_submenu(message, draft, lang=lang)
                return
            filter_done = t(lang, "daily_filter_done_button")
            filter_not_done = t(lang, "daily_filter_not_done_button")
            if text == filter_done:
                draft.daily_action_status_key = "done"
                await self._submit_daily_action_report(message, draft)
                return
            if text == filter_not_done:
                draft.daily_action_status_key = "not_done"
                await self._ask_daily_comment_for_current_action(message, draft, lang=lang)
                return
            await message.answer(
                t(lang, "daily_filter_result_buttons_hint"),
                reply_markup=simple_reply_keyboard(
                    [filter_done, filter_not_done],
                    width=2,
                    with_back=True,
                    back_text=back_label(lang),
                ),
            )
            return

        if draft.waiting_for_daily_refuel_confirm:
            if back_requested:
                await self._ask_daily_actions_submenu(message, draft, lang=lang)
                return
            refuel_required = t(lang, "daily_refuel_required_button")
            refuel_completed = t(lang, "daily_refuel_completed_button")
            if text == refuel_required:
                draft.daily_action_status_key = "required"
                await self._ask_daily_refuel_photo(message, draft, lang=lang)
                return
            if text == refuel_completed:
                draft.daily_action_status_key = "completed"
                await self._ask_daily_refuel_photo(message, draft, lang=lang)
                return
            await message.answer(
                t(lang, "daily_refuel_buttons_hint"),
                reply_markup=simple_reply_keyboard(
                    [refuel_required, refuel_completed],
                    width=1,
                    with_back=True,
                    back_text=back_label(lang),
                ),
            )
            return

        if draft.waiting_for_daily_refuel_photo:
            if back_requested:
                await self._ask_daily_refuel_confirm(message, draft, lang=lang)
                return
            await message.answer(
                t(lang, "daily_refuel_fuel_level_photo_waiting"),
                reply_markup=simple_reply_keyboard(
                    [],
                    width=1,
                    with_back=True,
                    back_text=back_label(lang),
                ),
            )
            return

        if draft.waiting_for_daily_end_workday_refuel:
            if back_requested:
                await self._ask_daily_actions_submenu(message, draft, lang=lang)
                return
            refuel_yes = t(lang, "daily_end_workday_refuel_yes_button")
            refuel_no = t(lang, "daily_end_workday_refuel_no_button")
            if text == refuel_yes:
                draft.daily_action_status_key = "yes"
                await self._ask_daily_end_workday_fuel_photo(message, draft, lang=lang)
                return
            if text == refuel_no:
                draft.daily_action_status_key = "no"
                await self._ask_daily_end_workday_fuel_photo(message, draft, lang=lang)
                return
            await message.answer(
                t(lang, "daily_end_workday_refuel_buttons_hint"),
                reply_markup=simple_reply_keyboard(
                    [refuel_yes, refuel_no],
                    width=2,
                    with_back=True,
                    back_text=back_label(lang),
                ),
            )
            return

        if draft.waiting_for_daily_end_workday_fuel_photo:
            if back_requested:
                await self._ask_daily_end_workday_refuel(message, draft, lang=lang)
                return
            await message.answer(
                t(lang, "daily_end_workday_fuel_level_photo_waiting"),
                reply_markup=simple_reply_keyboard(
                    [],
                    width=1,
                    with_back=True,
                    back_text=back_label(lang),
                ),
            )
            return

        if draft.waiting_for_daily_end_workday_photos:
            if back_requested:
                await self._ask_daily_end_workday_fuel_photo(message, draft, lang=lang)
                return
            await message.answer(
                t(lang, "daily_end_workday_photo_waiting"),
                reply_markup=simple_reply_keyboard(
                    [],
                    width=1,
                    with_back=True,
                    back_text=back_label(lang),
                ),
            )
            return

        if draft.waiting_for_daily_end_workday_location:
            if back_requested:
                await self._ask_daily_end_workday_photos(message, draft, lang=lang)
                return
            await message.answer(
                t(lang, "daily_end_workday_location_waiting"),
                reply_markup=request_location_keyboard(
                    button_text=t(lang, "send_location_button"),
                ),
            )
            return

        if draft.waiting_for_daily_comment:
            if back_requested:
                await self._ask_daily_actions_submenu(message, draft, lang=lang)
                return
            normalized_comment = " ".join(text.split())
            if len(normalized_comment) < 3:
                await message.answer(t(lang, "daily_comment_too_short"))
                return
            draft.daily_action_comment = normalized_comment
            await self._ask_daily_optional_photo(message, draft, lang=lang)
            return

        if draft.waiting_for_daily_optional_photo:
            if back_requested:
                await self._ask_daily_comment_for_current_action(message, draft, lang=lang)
                return
            if text == t(lang, "daily_skip_photo_button"):
                await self._submit_daily_action_report(message, draft)
                return
            await message.answer(
                t(lang, "daily_waiting_photo_or_skip"),
                reply_markup=simple_reply_keyboard(
                    [t(lang, "daily_skip_photo_button")],
                    width=1,
                    with_back=True,
                    back_text=back_label(lang),
                ),
            )
            return

        if text == menu_button_label:
            await self._ask_daily_actions_submenu(message, draft, lang=lang)
            return

        if back_requested and (draft.waiting_for_issue_comment or draft.waiting_for_issue_photo):
            draft.waiting_for_issue_comment = False
            draft.waiting_for_issue_photo = False
            draft.pending_nok_comment = None
            await message.answer(
                t(lang, "nok_cancelled_choose_again"),
                reply_markup=ReplyKeyboardRemove(),
            )
            await self._ask_checklist_item(message, draft)
            return

        if back_requested and draft.waiting_for_registration_phone:
            draft.waiting_for_registration_phone = False
            draft.waiting_for_registration_full_name = True
            draft.pending_registration_full_name = None
            await message.answer(t(lang, "enter_name_again"))
            return

        if draft.waiting_for_registration_full_name:
            normalized_name = " ".join(text.split())
            if len(normalized_name) < 5 or len(normalized_name.split()) < 2:
                await message.answer(t(lang, "full_name_invalid"))
                return
            draft.pending_registration_full_name = normalized_name
            draft.waiting_for_registration_full_name = False
            draft.waiting_for_registration_phone = True
            await message.answer(
                t(lang, "enter_phone", back_text=back_label(lang))
            )
            return

        if draft.waiting_for_registration_phone:
            normalized_phone = self._normalize_phone(text)
            if normalized_phone is None:
                await message.answer(t(lang, "invalid_phone"))
                return

            if not draft.pending_registration_full_name:
                await self._start_registration(message, draft, continue_to_inspection=False)
                return

            self.db.upsert_user(
                telegram_id=user_id,
                full_name=draft.pending_registration_full_name,
                phone=normalized_phone,
                role=None,
                language=lang,
            )
            start_after_registration = draft.start_after_registration
            self._reset_draft(user_id)
            await message.answer(t(lang, "registration_completed"))
            if start_after_registration:
                draft = self._get_or_create_draft(user_id)
                draft.language = lang
                await message.answer(t(lang, "go_to_inspection"))
                await self._ask_driver_license_type(message, draft)
            else:
                await message.answer(t(lang, "saved_use_start"))
            return

        user = self.db.get_user(user_id)
        lang = self._draft_language(user_id=user_id, draft=draft, user=user)
        if not self._is_registered(user):
            await message.answer(t(lang, "not_registered"))
            return

        if draft.driver_license_type is None and not draft.inspection_flow_started:
            await message.answer(t(lang, "use_commands_hint"))
            return

        if back_requested and draft.inspection_id is None:
            if draft.equipment_id is not None:
                draft.equipment_id = None
                await self._ask_equipment_number(message, draft)
                return
            if draft.equipment_brand is not None:
                draft.equipment_brand = None
                await self._ask_equipment_brand(message, draft)
                return
            if draft.equipment_type is not None:
                draft.equipment_type = None
                draft.equipment_brand = None
                await self._ask_equipment_type(message, draft)
                return
            if draft.driver_license_type is not None:
                draft.driver_license_type = None
                await self._ask_driver_license_type(message, draft)
                return
            await message.answer(t(lang, "already_first_step"))
            return

        if draft.driver_license_type is None:
            license_display_to_raw = (
                draft.driver_license_type_display_to_raw or driver_license_type_display_map(lang)
            )
            raw_license_type = license_display_to_raw.get(text, text)
            if raw_license_type not in driver_license_type_labels(lang):
                await message.answer(t(lang, "choose_driver_license_type_buttons"))
                return
            draft.driver_license_type = raw_license_type
            await self._ask_equipment_type(message, draft)
            return

        if draft.equipment_type is None:
            raw_type = draft.equipment_type_display_to_raw.get(text, text)
            if raw_type not in self.db.list_equipment_types():
                await message.answer(t(lang, "choose_type_buttons"))
                return
            draft.equipment_type = raw_type
            draft.equipment_brand = None
            await self._ask_equipment_brand(message, draft)
            return

        if draft.equipment_brand is None:
            if text not in self.db.list_brands(draft.equipment_type):
                await message.answer(t(lang, "choose_brand_buttons"))
                return
            draft.equipment_brand = text
            await self._ask_equipment_number(message, draft)
            return

        if draft.equipment_id is None:
            rows = self.db.list_numbers(draft.equipment_type, draft.equipment_brand)
            number_to_id = {r["reg_number"]: r["id"] for r in rows}
            if text not in number_to_id:
                await message.answer(t(lang, "choose_number_buttons"))
                return
            profile = self.db.get_user(user_id)
            if not self._is_registered(profile):
                await message.answer(t(lang, "profile_not_filled"))
                return
            driver_full_name = (profile["full_name"] or "").strip()
            driver_phone = (profile["phone"] or "").strip()
            draft.equipment_id = int(number_to_id[text])
            equipment = self.db.get_equipment(draft.equipment_id)
            snapshot = f'{equipment["type"]} {equipment["brand"]} {equipment["reg_number"]}'
            draft.inspection_id = self.db.create_inspection(
                driver_telegram_id=user_id,
                driver_full_name=driver_full_name,
                driver_phone=driver_phone or None,
                equipment_id=draft.equipment_id,
                equipment_snapshot=snapshot,
            )
            await message.answer(
                t(lang, "equipment_selected_start_checklist", snapshot=snapshot),
                reply_markup=ReplyKeyboardRemove(),
            )
            await self._ask_checklist_item(message, draft)
            return

        if draft.waiting_for_issue_comment:
            if len(text) < 3:
                await message.answer(t(lang, "short_comment"))
                return
            draft.pending_nok_comment = text
            draft.waiting_for_issue_comment = False
            draft.waiting_for_issue_photo = True
            await message.answer(
                t(lang, "attach_issue_photo"),
                reply_markup=simple_reply_keyboard(
                    [t(lang, "issue_skip_photo_button")],
                    width=1,
                    with_back=True,
                    back_text=back_label(lang),
                ),
            )
            return

        if draft.waiting_for_issue_photo:
            if text == t(lang, "issue_skip_photo_button"):
                await self._save_not_ok_item(
                    message,
                    draft,
                    issue_photo_path=None,
                    lang=lang,
                )
                return
            await message.answer(
                t(lang, "issue_waiting_photo_or_skip"),
                reply_markup=simple_reply_keyboard(
                    [t(lang, "issue_skip_photo_button")],
                    width=1,
                    with_back=True,
                    back_text=back_label(lang),
                ),
            )
            return

        if draft.waiting_for_required_location:
            await self._ask_required_location(message, draft)
            return

        await message.answer(t(lang, "follow_instructions"))

    async def on_photo(self, message: Message) -> None:
        if not message.from_user or not message.photo:
            return
        if not await self._ensure_message_access(message):
            return
        if not await self._ensure_personal_data_consent_message(message):
            return
        user_id = message.from_user.id
        lock = self._get_photo_lock(user_id)
        async with lock:
            draft = self._get_or_create_draft(user_id)
            lang = self._draft_language(user_id=user_id, draft=draft)
            best_photo = message.photo[-1]

            if (
                draft.waiting_for_daily_end_workday_refuel
                and draft.daily_action_key == "end_workday"
            ):
                await self._ask_daily_end_workday_refuel(message, draft, lang=lang)
                return

            if (
                draft.waiting_for_daily_end_workday_location
                and draft.daily_action_key == "end_workday"
            ):
                await self._ask_daily_end_workday_location(message, draft, lang=lang)
                return

            if (
                draft.waiting_for_daily_end_workday_fuel_photo
                and draft.daily_action_key == "end_workday"
            ):
                timestamp = now_compact_timestamp()
                fuel_photo_path = await self.storage.save_daily_action_photo(
                    bot=self.bot,
                    telegram_file_id=best_photo.file_id,
                    driver_tg_id=draft.driver_tg_id,
                    filename=f"end_workday_fuel_level_{timestamp}.jpg",
                )
                draft.daily_end_workday_fuel_photo_path = fuel_photo_path
                await self._ask_daily_end_workday_photos(message, draft, lang=lang)
                return

            if (
                draft.waiting_for_daily_end_workday_photos
                and draft.daily_action_key == "end_workday"
            ):
                timestamp = now_compact_timestamp()
                missing_daily_photos = self._missing_daily_end_workday_photos(draft)
                if not missing_daily_photos:
                    await message.answer(t(lang, "daily_end_workday_photo_done"))
                    await self._ask_daily_end_workday_location(message, draft, lang=lang)
                    return
                photo_type = missing_daily_photos[0]
                filename = f"end_workday_{photo_type}_{timestamp}.jpg"
                saved = await self.storage.save_daily_action_photo(
                    bot=self.bot,
                    telegram_file_id=best_photo.file_id,
                    driver_tg_id=draft.driver_tg_id,
                    filename=filename,
                )
                draft.daily_end_workday_required_photos[photo_type] = saved
                remaining = len(self._missing_daily_end_workday_photos(draft))
                if remaining == 0:
                    draft.waiting_for_daily_end_workday_photos = False
                    draft.waiting_for_daily_end_workday_location = True
                    await message.answer(t(lang, "daily_end_workday_photo_done"))
                    await self._ask_daily_end_workday_location(message, draft, lang=lang)
                    return
                if not message.media_group_id:
                    labels = required_photo_labels(lang)
                    received = len(REQUIRED_PHOTOS) - remaining
                    await message.answer(
                        t(
                            lang,
                            "daily_end_workday_photo_progress",
                            label=labels.get(photo_type, photo_type),
                            received=received,
                            total=len(REQUIRED_PHOTOS),
                            remaining=remaining,
                        )
                    )
                return

            if draft.waiting_for_daily_refuel_photo and draft.daily_action_key == "refuel":
                await self._submit_daily_action_report(
                    message,
                    draft,
                    photo_file_id=best_photo.file_id,
                )
                return

            if draft.waiting_for_daily_optional_photo and draft.daily_action_key:
                await self._submit_daily_action_report(
                    message,
                    draft,
                    photo_file_id=best_photo.file_id,
                )
                return

            if not draft.inspection_id:
                await message.answer(t(lang, "inspection_start_first"))
                return

            timestamp = now_compact_timestamp()

            if draft.waiting_for_issue_photo:
                filename = f"issue_{draft.checklist_index}_{timestamp}.jpg"
                saved = await self.storage.save_telegram_photo(
                    bot=self.bot,
                    telegram_file_id=best_photo.file_id,
                    inspection_id=draft.inspection_id,
                    category="issues",
                    filename=filename,
                )
                await self._save_not_ok_item(
                    message,
                    draft,
                    issue_photo_path=saved,
                    lang=lang,
                )
                return

            checklist_done = draft.checklist_index >= len(
                checklist_items(lang, draft.driver_license_type, draft.equipment_type)
            )
            if checklist_done:
                missing_required = self._missing_required_photos(draft)
                if missing_required:
                    photo_type = missing_required[0]
                    remaining = len(missing_required) - 1
                    filename = f"{photo_type}_{timestamp}.jpg"
                    saved = await self.storage.save_telegram_photo(
                        bot=self.bot,
                        telegram_file_id=best_photo.file_id,
                        inspection_id=draft.inspection_id,
                        category="required",
                        filename=filename,
                    )
                    self.db.add_required_photo(draft.inspection_id, photo_type, saved)
                    draft.required_photos[photo_type] = saved
                    if remaining == 0:
                        self._cancel_required_photo_group_task(user_id)
                        draft.waiting_for_required_location = True
                        await message.answer(
                            t(lang, "required_photo_batch_done"),
                        )
                        await self._ask_required_location(message, draft)
                    elif message.media_group_id:
                        self._cancel_required_photo_group_task(user_id)
                        self.required_photo_group_tasks[user_id] = asyncio.create_task(
                            self._notify_missing_required_photos_delayed(
                                user_id=user_id,
                                chat_id=message.chat.id,
                            )
                        )
                    else:
                        await message.answer(
                            t(lang, "required_photos_need_more_count", remaining=remaining),
                            reply_markup=submit_report_keyboard(
                                submit_text=t(lang, "submit_report_button")
                            ),
                        )
                    return
                if draft.required_photos:
                    if draft.waiting_for_required_location:
                        await self._ask_required_location(message, draft)
                    else:
                        await message.answer(
                            t(lang, "required_photos_already_collected"),
                            reply_markup=submit_report_keyboard(
                                submit_text=t(lang, "submit_report_button")
                            ),
                        )
                    return

            await message.answer(t(lang, "photo_not_expected"))

    async def on_location(self, message: Message) -> None:
        if not message.from_user or not message.location:
            return
        if not await self._ensure_message_access(message):
            return
        if not await self._ensure_personal_data_consent_message(message):
            return

        user_id = message.from_user.id
        draft = self._get_or_create_draft(user_id)
        lang = self._draft_language(user_id=user_id, draft=draft)

        if draft.daily_action_key == "end_workday":
            if draft.waiting_for_daily_end_workday_refuel:
                await self._ask_daily_end_workday_refuel(message, draft, lang=lang)
                return
            if draft.waiting_for_daily_end_workday_fuel_photo:
                await self._ask_daily_end_workday_fuel_photo(message, draft, lang=lang)
                return
            if draft.waiting_for_daily_end_workday_photos:
                await self._ask_daily_end_workday_photos(message, draft, lang=lang)
                return

        if (
            draft.waiting_for_daily_end_workday_location
            and draft.daily_action_key == "end_workday"
        ):
            missing_daily_photos = self._missing_daily_end_workday_photos(draft)
            if missing_daily_photos:
                labels = required_photo_labels(lang)
                missing_labels = ", ".join(labels[m] for m in missing_daily_photos)
                await message.answer(
                    t(lang, "missing_photos", missing=missing_labels),
                )
                await self._ask_daily_end_workday_photos(message, draft, lang=lang)
                return
            latitude = float(message.location.latitude)
            longitude = float(message.location.longitude)
            draft.daily_end_workday_location = (latitude, longitude)
            draft.waiting_for_daily_end_workday_location = False
            await message.answer(
                t(lang, "required_location_saved"),
                reply_markup=ReplyKeyboardRemove(),
            )
            daily_photo_paths = [
                draft.daily_end_workday_required_photos[key]
                for key, _ in REQUIRED_PHOTOS
                if key in draft.daily_end_workday_required_photos
            ]
            await self._submit_daily_action_report(
                message,
                draft,
                end_workday_photo_paths=daily_photo_paths,
                end_workday_location=(latitude, longitude),
                end_workday_fuel_photo_path=draft.daily_end_workday_fuel_photo_path,
            )
            return

        if not draft.inspection_id:
            await message.answer(t(lang, "inspection_start_first"))
            return

        checklist_done = draft.checklist_index >= len(
            checklist_items(lang, draft.driver_license_type, draft.equipment_type)
        )
        if not checklist_done:
            await message.answer(t(lang, "location_not_expected_yet"))
            return

        missing_required = self._missing_required_photos(draft)
        if missing_required:
            labels = required_photo_labels(lang)
            missing_labels = ", ".join(labels[m] for m in missing_required)
            await message.answer(
                t(lang, "missing_photos", missing=missing_labels),
            )
            return

        latitude = float(message.location.latitude)
        longitude = float(message.location.longitude)
        self.db.set_inspection_location(
            inspection_id=draft.inspection_id,
            latitude=latitude,
            longitude=longitude,
        )
        draft.waiting_for_required_location = False
        draft.required_location = (latitude, longitude)

        await message.answer(
            t(lang, "required_location_saved"),
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            t(lang, "required_location_submit_hint"),
            reply_markup=submit_report_keyboard(
                submit_text=t(lang, "submit_report_button"),
            ),
        )

    async def on_item_answer(self, callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data or not callback.message:
            return
        if not await self._ensure_callback_access(callback):
            return
        if not await self._ensure_personal_data_consent_callback(callback):
            return
        user_id = callback.from_user.id
        draft = self._get_or_create_draft(user_id)
        lang = self._draft_language(user_id=user_id, draft=draft)
        items = checklist_items(lang, draft.driver_license_type, draft.equipment_type)
        if draft.inspection_id is None or draft.checklist_index >= len(items):
            await callback.answer(t(lang, "checklist_done_or_not_started"), show_alert=True)
            return

        if draft.waiting_for_issue_comment or draft.waiting_for_issue_photo:
            await callback.answer(
                t(lang, "complete_nok_first", back_text=back_label(lang)),
                show_alert=True,
            )
            return

        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer(
                t(lang, "stale_button"),
                show_alert=True,
            )
            return

        _, item_index_str, action = parts
        try:
            item_index = int(item_index_str)
        except ValueError:
            await callback.answer(t(lang, "invalid_button"), show_alert=True)
            return

        if item_index != draft.checklist_index:
            await callback.answer(t(lang, "question_closed"))
            return

        if action == "undo":
            if draft.checklist_index == 0:
                await callback.answer(t(lang, "already_first_question"), show_alert=True)
                return
            removed = self.db.delete_inspection_item(
                inspection_id=draft.inspection_id,
                item_order=draft.checklist_index,
            )
            if not removed:
                await callback.answer(t(lang, "cannot_undo"), show_alert=True)
                return
            draft.checklist_index -= 1
            await self._try_clear_inline_keyboard(callback)
            await callback.answer(t(lang, "undo_saved"))
            await callback.message.answer(t(lang, "returned_previous_question"))
            await self._ask_checklist_item(callback.message, draft)
            return

        if action == "ok":
            item_order = draft.checklist_index + 1
            item_name = items[draft.checklist_index]
            self.db.add_inspection_item(
                inspection_id=draft.inspection_id,
                item_order=item_order,
                item_name=item_name,
                is_ok=True,
                comment=None,
                issue_photo_path=None,
            )
            draft.checklist_index += 1
            await self._try_clear_inline_keyboard(callback)
            await callback.answer(t(lang, "saved"))
            await self._continue_or_required_photos(callback.message, draft)
            return

        if action == "nok":
            draft.waiting_for_issue_comment = True
            draft.waiting_for_issue_photo = False
            draft.pending_nok_comment = None
            await self._try_clear_inline_keyboard(callback)
            await callback.answer()
            await callback.message.answer(
                t(lang, "describe_issue_or_back", back_text=back_label(lang))
            )
            return

        await callback.answer(t(lang, "unknown_action"), show_alert=True)

    async def on_required_photo_action(self, callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data or not callback.message:
            return
        if not await self._ensure_callback_access(callback):
            return
        if not await self._ensure_personal_data_consent_callback(callback):
            return
        user_id = callback.from_user.id
        draft = self._get_or_create_draft(user_id)
        lang = self._draft_language(user_id=user_id, draft=draft)
        if not draft.inspection_id:
            await callback.answer(t(lang, "inspection_not_started"), show_alert=True)
            return

        action = callback.data.split(":")[1]
        if action != "submit":
            await callback.answer(t(lang, "send_required_photos_batch_hint"), show_alert=True)
            return

        missing = self._missing_required_photos(draft)
        if missing:
            labels = required_photo_labels(lang)
            missing_labels = ", ".join(labels[m] for m in missing)
            await callback.answer(
                t(lang, "missing_photos", missing=missing_labels),
                show_alert=True,
            )
            return

        inspection = self.db.get_inspection(draft.inspection_id)
        has_location = (
            inspection is not None
            and inspection["driver_latitude"] is not None
            and inspection["driver_longitude"] is not None
        )
        if not has_location:
            draft.waiting_for_required_location = True
            await callback.answer(t(lang, "required_location_missing"), show_alert=True)
            await self._ask_required_location(callback.message, draft)
            return

        draft.waiting_for_required_location = False
        await callback.answer(t(lang, "sending_report"))
        try:
            await self._submit_inspection(callback.message, draft)
        except Exception:
            logger.exception(
                "Unexpected submit error for inspection_id=%s driver_id=%s",
                draft.inspection_id,
                user_id,
            )
            await callback.message.answer(t(lang, "submit_internal_error"))
        return

    async def on_mechanic_decision(self, callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data or not callback.message:
            return
        if not await self._ensure_callback_access(callback):
            return
        user = self.db.get_user(callback.from_user.id)
        lang = self._user_language(user)
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer(t(lang, "invalid_button"), show_alert=True)
            return

        _, inspection_id_str, decision = parts
        inspection_id = int(inspection_id_str)
        if not user or user["role"] not in MECHANIC_ROLES:
            await callback.answer(t(lang, "mechanic_only"), show_alert=True)
            return

        inspection = self.db.get_inspection(inspection_id)
        if not inspection:
            await callback.answer(t(lang, "report_not_found"), show_alert=True)
            return
        if inspection["mechanic_decision"]:
            await callback.answer(t(lang, "decision_already_saved"), show_alert=True)
            return

        self.db.set_mechanic_decision(
            inspection_id=inspection_id,
            mechanic_telegram_id=callback.from_user.id,
            decision=decision,
            comment=None,
        )
        self.db.add_audit(
            actor_telegram_id=callback.from_user.id,
            action="mechanic_decision",
            entity_type="inspection",
            entity_id=str(inspection_id),
            details=f"decision={decision}",
        )

        await callback.answer(t(lang, "decision_saved"))
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            t(
                lang,
                "decision_by_mechanic",
                inspection_id=inspection_id,
                decision=decision,
                mechanic_name=callback.from_user.full_name,
            )
        )

        driver_profile = self.db.get_user(inspection["driver_telegram_id"])
        driver_lang = self._user_language(driver_profile)
        driver_text = driver_status_text(driver_lang, decision)
        await self.bot.send_message(chat_id=inspection["driver_telegram_id"], text=driver_text)

    async def on_daily_refuel_decision(self, callback: CallbackQuery) -> None:
        if not callback.from_user or not callback.data or not callback.message:
            return
        if not await self._ensure_callback_access(callback):
            return
        user = self.db.get_user(callback.from_user.id)
        lang = self._user_language(user)
        if not user or user["role"] not in MECHANIC_ROLES:
            await callback.answer(t(lang, "mechanic_only"), show_alert=True)
            return

        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer(t(lang, "invalid_button"), show_alert=True)
            return
        _, report_id_str, decision = parts
        if decision not in {"approved", "rejected"}:
            await callback.answer(t(lang, "invalid_button"), show_alert=True)
            return
        try:
            report_id = int(report_id_str)
        except ValueError:
            await callback.answer(t(lang, "invalid_button"), show_alert=True)
            return

        report = self.db.get_daily_action_report(report_id)
        if (
            not report
            or report["action_key"] != "refuel"
            or report["status_key"] != "required"
        ):
            await callback.answer(t(lang, "daily_refuel_report_not_found"), show_alert=True)
            return
        if report["fuel_decision"]:
            await callback.answer(t(lang, "daily_refuel_decision_already_saved"), show_alert=True)
            return

        saved = self.db.set_daily_action_fuel_decision(
            report_id=report_id,
            mechanic_telegram_id=callback.from_user.id,
            decision=decision,
        )
        if not saved:
            await callback.answer(t(lang, "daily_refuel_decision_already_saved"), show_alert=True)
            return

        self.db.add_audit(
            actor_telegram_id=callback.from_user.id,
            action="daily_refuel_decision",
            entity_type="daily_action",
            entity_id=str(report_id),
            details=f"decision={decision}",
        )

        decision_label_key = (
            "daily_refuel_decision_approved_label"
            if decision == "approved"
            else "daily_refuel_decision_rejected_label"
        )
        decision_label_for_mechanic = t(lang, decision_label_key)
        await callback.answer(t(lang, "daily_refuel_decision_saved"))
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            t(
                lang,
                "daily_refuel_decision_by_mechanic",
                report_id=report_id,
                decision=decision_label_for_mechanic,
                mechanic_name=callback.from_user.full_name,
            )
        )

        driver_profile = self.db.get_user(report["driver_telegram_id"])
        driver_lang = self._user_language(driver_profile)
        decision_label_for_driver = t(driver_lang, decision_label_key)
        await self.bot.send_message(
            chat_id=report["driver_telegram_id"],
            text=t(
                driver_lang,
                "daily_refuel_decision_driver",
                decision=decision_label_for_driver,
            ),
        )

    async def _ask_equipment_type(self, message: Message, draft: InspectionDraft) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        raw_options = self.db.list_equipment_types()
        display_map = equipment_type_display_map(lang, raw_options)
        options = list(display_map.keys())
        draft.equipment_type_display_to_raw = display_map
        await message.answer(
            t(lang, "select_equipment_type"),
            reply_markup=simple_reply_keyboard(options, width=2),
        )

    async def _ask_driver_license_type(self, message: Message, draft: InspectionDraft) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        display_map = driver_license_type_display_map(lang)
        options = list(display_map.keys())
        draft.driver_license_type_display_to_raw = display_map
        draft.inspection_flow_started = True
        await message.answer(
            t(lang, "select_driver_license_type"),
            reply_markup=simple_reply_keyboard(options, width=2),
        )

    @staticmethod
    def _reset_daily_actions_waiting_flags(draft: InspectionDraft) -> None:
        draft.waiting_for_daily_actions_root = False
        draft.waiting_for_daily_actions_submenu = False
        draft.waiting_for_daily_filter_result = False
        draft.waiting_for_daily_comment = False
        draft.waiting_for_daily_optional_photo = False
        draft.waiting_for_daily_refuel_confirm = False
        draft.waiting_for_daily_refuel_photo = False
        draft.waiting_for_daily_end_workday_refuel = False
        draft.waiting_for_daily_end_workday_fuel_photo = False
        draft.waiting_for_daily_end_workday_photos = False
        draft.waiting_for_daily_end_workday_location = False

    @staticmethod
    def _clear_daily_actions_state(draft: InspectionDraft) -> None:
        InspectionBot._reset_daily_actions_waiting_flags(draft)
        draft.daily_actions_display_to_key = {}
        draft.daily_action_key = None
        draft.daily_action_status_key = None
        draft.daily_action_comment = None
        draft.daily_end_workday_fuel_photo_path = None
        draft.daily_end_workday_required_photos = {}
        draft.daily_end_workday_location = None

    async def _ask_daily_actions_root(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._clear_daily_actions_state(draft)
        draft.waiting_for_daily_actions_root = True
        menu_button = t(language, "daily_actions_menu_button")
        await message.answer(
            t(language, "daily_actions_open_prompt"),
            reply_markup=simple_reply_keyboard(
                [menu_button],
                width=1,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    async def _ask_daily_actions_submenu(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        display_to_key = daily_actions_display_map(language)
        self._clear_daily_actions_state(draft)
        draft.waiting_for_daily_actions_submenu = True
        draft.daily_actions_display_to_key = display_to_key
        options = list(display_to_key.keys())
        options_preview = "\n".join(f"• {item}" for item in options)
        await message.answer(
            f"{t(language, 'daily_actions_submenu_prompt')}\n\n{options_preview}",
            reply_markup=simple_reply_keyboard(
                options,
                width=1,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    async def _ask_daily_filter_result(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._reset_daily_actions_waiting_flags(draft)
        draft.waiting_for_daily_filter_result = True
        await message.answer(
            t(language, "daily_filter_result_prompt"),
            reply_markup=simple_reply_keyboard(
                [
                    t(language, "daily_filter_done_button"),
                    t(language, "daily_filter_not_done_button"),
                ],
                width=2,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    async def _ask_daily_refuel_confirm(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._reset_daily_actions_waiting_flags(draft)
        draft.waiting_for_daily_refuel_confirm = True
        await message.answer(
            t(language, "daily_refuel_prompt"),
            reply_markup=simple_reply_keyboard(
                [
                    t(language, "daily_refuel_required_button"),
                    t(language, "daily_refuel_completed_button"),
                ],
                width=1,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    async def _ask_daily_refuel_photo(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._reset_daily_actions_waiting_flags(draft)
        draft.waiting_for_daily_refuel_photo = True
        await message.answer(
            t(language, "daily_refuel_fuel_level_photo_prompt"),
            reply_markup=simple_reply_keyboard(
                [],
                width=1,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    async def _ask_daily_end_workday_refuel(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._reset_daily_actions_waiting_flags(draft)
        draft.waiting_for_daily_end_workday_refuel = True
        draft.daily_end_workday_fuel_photo_path = None
        draft.daily_end_workday_required_photos = {}
        draft.daily_end_workday_location = None
        await message.answer(
            t(language, "daily_end_workday_refuel_prompt"),
            reply_markup=simple_reply_keyboard(
                [
                    t(language, "daily_end_workday_refuel_yes_button"),
                    t(language, "daily_end_workday_refuel_no_button"),
                ],
                width=2,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    async def _ask_daily_end_workday_fuel_photo(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._reset_daily_actions_waiting_flags(draft)
        draft.waiting_for_daily_end_workday_fuel_photo = True
        await message.answer(
            t(language, "daily_end_workday_fuel_level_photo_prompt"),
            reply_markup=simple_reply_keyboard(
                [],
                width=1,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    async def _ask_daily_end_workday_photos(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._reset_daily_actions_waiting_flags(draft)
        draft.waiting_for_daily_end_workday_photos = True
        draft.waiting_for_daily_end_workday_location = False
        draft.daily_end_workday_required_photos = {}
        draft.daily_end_workday_location = None
        await message.answer(
            t(language, "daily_end_workday_photos_intro"),
            reply_markup=simple_reply_keyboard(
                [],
                width=1,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    async def _ask_daily_end_workday_location(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._reset_daily_actions_waiting_flags(draft)
        draft.waiting_for_daily_end_workday_location = True
        await message.answer(
            t(language, "daily_end_workday_location_waiting"),
            reply_markup=request_location_keyboard(
                button_text=t(language, "send_location_button"),
            ),
        )

    async def _ask_daily_comment_for_current_action(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._reset_daily_actions_waiting_flags(draft)
        draft.waiting_for_daily_comment = True
        prompt_key = (
            "daily_filter_not_done_comment_prompt"
            if draft.daily_action_key == "blow_filters"
            else "daily_workday_comment_prompt"
        )
        await message.answer(
            t(language, prompt_key),
            reply_markup=simple_reply_keyboard(
                [],
                width=1,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    async def _ask_daily_optional_photo(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        self._reset_daily_actions_waiting_flags(draft)
        draft.waiting_for_daily_optional_photo = True
        await message.answer(
            t(language, "daily_optional_photo_prompt"),
            reply_markup=simple_reply_keyboard(
                [t(language, "daily_skip_photo_button")],
                width=1,
                with_back=True,
                back_text=back_label(language),
            ),
        )

    @staticmethod
    def _daily_action_label(language: str | None, action_key: str | None) -> str:
        key_map = {
            "blow_filters": "daily_action_blow_filters",
            "workday_situations": "daily_action_workday_situations",
            "refuel": "daily_action_refuel",
            "end_workday": "daily_action_end_workday",
        }
        text_key = key_map.get(action_key or "", "daily_actions_menu_button")
        return t(language, text_key)

    @staticmethod
    def _daily_action_status_label(
        language: str | None,
        action_key: str | None,
        status_key: str | None,
    ) -> str | None:
        status_map: dict[tuple[str, str], str] = {
            ("blow_filters", "done"): "daily_filter_done_button",
            ("blow_filters", "not_done"): "daily_filter_not_done_button",
            ("refuel", "required"): "daily_refuel_required_button",
            ("refuel", "completed"): "daily_refuel_completed_button",
            ("end_workday", "yes"): "daily_end_workday_refuel_yes_button",
            ("end_workday", "no"): "daily_end_workday_refuel_no_button",
        }
        text_key = status_map.get((action_key or "", status_key or ""))
        if text_key is None:
            return None
        return t(language, text_key)

    @staticmethod
    def _daily_action_report_title(language: str | None, action_key: str | None) -> str:
        title_map = {
            "blow_filters": "daily_report_title_blow_filters",
            "workday_situations": "daily_report_title_workday",
            "refuel": "daily_report_title_refuel",
            "end_workday": "daily_report_title_end_workday",
        }
        return t(language, title_map.get(action_key or "", "daily_actions_menu_button"))

    async def _submit_daily_action_report(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        photo_file_id: str | None = None,
        end_workday_photo_paths: list[str] | None = None,
        end_workday_location: tuple[float, float] | None = None,
        end_workday_fuel_photo_path: str | None = None,
    ) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        report_lang = "ru"
        action_key = draft.daily_action_key
        if not action_key:
            await message.answer(t(lang, "unknown_action"))
            return
        if action_key == "refuel" and not photo_file_id:
            await self._ask_daily_refuel_photo(message, draft, lang=lang)
            return
        if action_key == "end_workday":
            if draft.daily_action_status_key not in {"yes", "no"}:
                await self._ask_daily_end_workday_refuel(message, draft, lang=lang)
                return
            if end_workday_fuel_photo_path is None:
                end_workday_fuel_photo_path = draft.daily_end_workday_fuel_photo_path
            if not end_workday_fuel_photo_path:
                await self._ask_daily_end_workday_fuel_photo(message, draft, lang=lang)
                return
            if end_workday_photo_paths is None:
                end_workday_photo_paths = [
                    draft.daily_end_workday_required_photos[key]
                    for key, _ in REQUIRED_PHOTOS
                    if key in draft.daily_end_workday_required_photos
                ]
            if len(end_workday_photo_paths) < len(REQUIRED_PHOTOS):
                await self._ask_daily_end_workday_photos(message, draft, lang=lang)
                return
            if end_workday_location is None:
                end_workday_location = draft.daily_end_workday_location
            if end_workday_location is None:
                await self._ask_daily_end_workday_location(message, draft, lang=lang)
                return

        user = self.db.get_user(draft.driver_tg_id)
        full_name = ""
        if user:
            full_name = (user["full_name"] or "").strip()
        if not full_name and message.from_user:
            full_name = (message.from_user.full_name or "").strip()
        if not full_name:
            full_name = str(draft.driver_tg_id)
        phone = (user["phone"] or "").strip() if user else ""

        action_label = self._daily_action_label(report_lang, action_key)
        status_label = self._daily_action_status_label(
            report_lang,
            action_key,
            draft.daily_action_status_key,
        )
        report_title = self._daily_action_report_title(report_lang, action_key)
        photo_path: str | None = None
        if action_key == "end_workday":
            photo_path = end_workday_fuel_photo_path
        elif photo_file_id:
            try:
                photo_path = await self.storage.save_daily_action_photo(
                    bot=self.bot,
                    telegram_file_id=photo_file_id,
                    driver_tg_id=draft.driver_tg_id,
                    filename=(
                        f"{action_key}_{now_compact_timestamp()}.jpg"
                    ),
                )
            except Exception:
                logger.exception(
                    "Failed to save daily action photo action=%s user_id=%s",
                    action_key,
                    draft.driver_tg_id,
                )
                photo_path = None
        linked_inspection = self.db.get_latest_submitted_inspection_for_driver(
            draft.driver_tg_id
        )
        linked_inspection_id = int(linked_inspection["id"]) if linked_inspection else None
        linked_inspection_message_id = (
            int(linked_inspection["mechanic_message_id"])
            if linked_inspection and linked_inspection["mechanic_message_id"] is not None
            else None
        )

        report_id = self.db.create_daily_action_report(
            driver_telegram_id=draft.driver_tg_id,
            driver_full_name=full_name,
            driver_phone=phone or None,
            action_key=action_key,
            action_label=action_label,
            status_key=draft.daily_action_status_key,
            status_label=status_label,
            comment=draft.daily_action_comment,
            photo_path=photo_path,
            linked_inspection_id=linked_inspection_id,
        )
        report_reference = (
            f"#{linked_inspection_id}" if linked_inspection_id is not None else "—"
        )

        report_lines = [
            f"{escape(report_title)}",
            f"{escape(t(report_lang, 'daily_report_id'))}: <b>{report_reference}</b>",
            f"{escape(t(report_lang, 'daily_report_employee'))}: <b>{escape(full_name)}</b>",
            f"{escape(t(report_lang, 'daily_report_action'))}: <b>{escape(action_label)}</b>",
        ]
        if phone:
            report_lines.append(
                f"{escape(t(report_lang, 'daily_report_phone'))}: <b>{escape(phone)}</b>"
            )
        if status_label:
            report_lines.append(
                f"{escape(t(report_lang, 'daily_report_status'))}: <b>{escape(status_label)}</b>"
            )
        if action_key == "blow_filters" and draft.daily_action_status_key == "done":
            report_lines.append(escape(t(report_lang, "daily_report_result_filter_done")))
        elif action_key == "blow_filters" and draft.daily_action_status_key == "not_done":
            report_lines.append(escape(t(report_lang, "daily_report_result_filter_not_done")))
        elif action_key == "workday_situations":
            report_lines.append(escape(t(report_lang, "daily_report_result_workday")))
        elif action_key == "refuel" and draft.daily_action_status_key == "required":
            report_lines.append(escape(t(report_lang, "daily_report_result_refuel")))
        elif action_key == "refuel" and draft.daily_action_status_key == "completed":
            report_lines.append(escape(t(report_lang, "daily_report_result_refuel_completed")))
        elif action_key == "end_workday" and draft.daily_action_status_key == "yes":
            report_lines.append(escape(t(report_lang, "daily_report_result_end_workday_refuel_yes")))
        elif action_key == "end_workday" and draft.daily_action_status_key == "no":
            report_lines.append(escape(t(report_lang, "daily_report_result_end_workday_refuel_no")))
        if action_key == "end_workday" and end_workday_location is not None:
            latitude, longitude = end_workday_location
            report_lines.append(
                f"{escape(t(report_lang, 'daily_report_geo'))}: <b>{latitude:.6f}, {longitude:.6f}</b>"
            )
            report_lines.append(
                f"{escape(t(report_lang, 'daily_report_geo_map'))}: "
                f"https://maps.google.com/?q={latitude},{longitude}"
            )
        if draft.daily_action_comment:
            report_lines.append(
                f"{escape(t(report_lang, 'daily_report_comment'))}: {escape(draft.daily_action_comment)}"
            )
        report_lines.append(
            f"{escape(t(report_lang, 'daily_report_time'))}: {now_iso(timespec='seconds')}"
        )
        if action_key == "refuel" and draft.daily_action_status_key == "required":
            report_lines.append("")
            report_lines.append(escape(t(report_lang, "daily_refuel_mechanic_decision_prompt")))
        report_text = "\n".join(report_lines)

        try:
            reply_markup = None
            if action_key == "refuel" and draft.daily_action_status_key == "required":
                reply_markup = daily_refuel_decision_keyboard(
                    report_id,
                    approve_text=t(report_lang, "daily_refuel_approve_button"),
                    reject_text=t(report_lang, "daily_refuel_reject_button"),
                )
            if action_key == "end_workday":
                report_caption = report_text.replace("<b>", "").replace("</b>", "")
                if len(report_caption) > 1024:
                    report_caption = report_caption[:1019].rstrip() + "\n…"
                endday_paths = [Path(end_workday_fuel_photo_path)] + [
                    Path(path) for path in end_workday_photo_paths
                ]
                expected_endday_photos = len(REQUIRED_PHOTOS) + 1
                if len(endday_paths) < expected_endday_photos or any(
                    not photo_path.exists() for photo_path in endday_paths
                ):
                    logger.error(
                        "Endday report %s has missing photo files: expected=%s got=%s",
                        report_id,
                        expected_endday_photos,
                        len(endday_paths),
                    )
                    self.db.mark_daily_action_report_delivery(report_id, status="failed")
                    await message.answer(t(lang, "daily_report_delivery_failed"))
                    return

                media = []
                for idx, photo_path in enumerate(endday_paths):
                    media.append(
                        InputMediaPhoto(
                            media=FSInputFile(photo_path),
                            caption=report_caption if idx == 0 else None,
                        )
                    )

                try:
                    sent_album = await self.bot.send_media_group(
                        chat_id=self.settings.mechanic_group_id,
                        media=media,
                        reply_to_message_id=linked_inspection_message_id,
                        request_timeout=90,
                    )
                except (TelegramBadRequest, TelegramNetworkError):
                    # If linked message is unavailable, still deliver report without reply linkage.
                    sent_album = await self.bot.send_media_group(
                        chat_id=self.settings.mechanic_group_id,
                        media=media,
                        request_timeout=90,
                    )
                sent_message = sent_album[0]
                self.db.mark_daily_action_report_delivery(
                    report_id,
                    status="sent",
                    mechanic_message_id=sent_message.message_id,
                )
                self.db.add_audit(
                    actor_telegram_id=draft.driver_tg_id,
                    action=f"daily_report_sent_{action_key}",
                    entity_type="daily_action",
                    entity_id=str(draft.driver_tg_id),
                    details=(
                        f"report_id={report_id};status={draft.daily_action_status_key};"
                        f"comment={draft.daily_action_comment or ''};"
                        f"linked_inspection_id={linked_inspection_id or ''};"
                        f"location={end_workday_location[0]:.6f},{end_workday_location[1]:.6f}"
                    ),
                )
                self._clear_daily_actions_state(draft)
                await message.answer(
                    t(lang, "daily_report_sent"),
                    reply_markup=ReplyKeyboardRemove(),
                )
                return

            photo_exists = bool(photo_path and Path(photo_path).exists())
            can_embed_refuel_report_in_caption = (
                action_key == "refuel"
                and photo_exists
                and len(report_text) <= 1024
            )

            if can_embed_refuel_report_in_caption:
                sent_message = await self.bot.send_photo(
                    chat_id=self.settings.mechanic_group_id,
                    photo=FSInputFile(photo_path),
                    caption=report_text,
                    reply_markup=reply_markup,
                )
            else:
                sent_message = await self.bot.send_message(
                    chat_id=self.settings.mechanic_group_id,
                    text=report_text,
                    reply_markup=reply_markup,
                )
                if photo_exists:
                    await self.bot.send_photo(
                        chat_id=self.settings.mechanic_group_id,
                        photo=FSInputFile(photo_path),
                        caption=t(report_lang, "daily_report_photo_caption"),
                        reply_to_message_id=sent_message.message_id,
                    )
            self.db.mark_daily_action_report_delivery(
                report_id,
                status="sent",
                mechanic_message_id=sent_message.message_id,
            )
        except (TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError):
            logger.exception(
                "Failed to deliver daily action report action=%s user_id=%s",
                action_key,
                draft.driver_tg_id,
            )
            self.db.mark_daily_action_report_delivery(report_id, status="failed")
            await message.answer(t(lang, "daily_report_delivery_failed"))
            return

        self.db.add_audit(
            actor_telegram_id=draft.driver_tg_id,
            action=f"daily_report_sent_{action_key}",
            entity_type="daily_action",
            entity_id=str(draft.driver_tg_id),
            details=(
                f"report_id={report_id};status={draft.daily_action_status_key};"
                f"comment={draft.daily_action_comment or ''};"
                f"linked_inspection_id={linked_inspection_id or ''}"
            ),
        )
        self._clear_daily_actions_state(draft)
        await message.answer(
            t(lang, "daily_report_sent"),
            reply_markup=ReplyKeyboardRemove(),
        )

    async def _ask_equipment_brand(self, message: Message, draft: InspectionDraft) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        options = self.db.list_brands(draft.equipment_type)
        await message.answer(
            t(lang, "select_equipment_brand"),
            reply_markup=simple_reply_keyboard(
                options,
                width=2,
                with_back=True,
                back_text=back_label(lang),
            ),
        )

    async def _ask_equipment_number(self, message: Message, draft: InspectionDraft) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        rows = self.db.list_numbers(draft.equipment_type, draft.equipment_brand)
        options = [r["reg_number"] for r in rows]
        await message.answer(
            t(lang, "select_equipment_number"),
            reply_markup=simple_reply_keyboard(
                options,
                width=2,
                with_back=True,
                back_text=back_label(lang),
            ),
        )

    async def _ask_checklist_item(self, message: Message, draft: InspectionDraft) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        items = checklist_items(lang, draft.driver_license_type, draft.equipment_type)
        idx = draft.checklist_index
        if idx >= len(items):
            await self._ask_required_photos(message, draft)
            return
        item = items[idx]
        ok_text = {"ru": "✅ ОК", "tg": "✅ ОК", "uz": "✅ OK"}[normalize_language(lang)]
        nok_text = {"ru": "❌ Не ОК", "tg": "❌ На ОК", "uz": "❌ OK emas"}[normalize_language(lang)]
        await message.answer(
            t(lang, "checklist_item", current=idx + 1, total=len(items), item=item),
            reply_markup=yes_no_keyboard(
                item_index=idx,
                can_go_back=idx > 0,
                ok_text=ok_text,
                nok_text=nok_text,
                back_text=f"↩️ {back_label(lang)}",
            ),
        )

    async def _continue_or_required_photos(self, message: Message, draft: InspectionDraft) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        if draft.checklist_index < len(
            checklist_items(lang, draft.driver_license_type, draft.equipment_type)
        ):
            await self._ask_checklist_item(message, draft)
            return
        await self._ask_required_photos(message, draft)

    async def _save_not_ok_item(
        self,
        message: Message,
        draft: InspectionDraft,
        *,
        issue_photo_path: str | None,
        lang: str | None = None,
    ) -> None:
        language = lang or self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        if draft.inspection_id is None:
            await message.answer(t(language, "inspection_start_first"))
            return

        items = checklist_items(language, draft.driver_license_type, draft.equipment_type)
        if draft.checklist_index >= len(items):
            await self._continue_or_required_photos(message, draft)
            return

        item_order = draft.checklist_index + 1
        item_name = items[draft.checklist_index]
        self.db.add_inspection_item(
            inspection_id=draft.inspection_id,
            item_order=item_order,
            item_name=item_name,
            is_ok=False,
            comment=draft.pending_nok_comment,
            issue_photo_path=issue_photo_path,
        )
        draft.waiting_for_issue_photo = False
        draft.pending_nok_comment = None
        draft.checklist_index += 1
        await message.answer(
            t(language, "issue_recorded"),
            reply_markup=ReplyKeyboardRemove(),
        )
        await self._continue_or_required_photos(message, draft)

    async def _ask_required_photos(self, message: Message, draft: InspectionDraft) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        labels = required_photo_labels(lang)
        photos_text = "\n".join(f"- {label}" for label in labels.values())
        await message.answer(
            t(lang, "required_photos_intro", photos=photos_text),
            reply_markup=submit_report_keyboard(
                submit_text=t(lang, "submit_report_button"),
            ),
        )

    async def _ask_required_location(self, message: Message, draft: InspectionDraft) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        await message.answer(
            t(lang, "required_location_request"),
            reply_markup=request_location_keyboard(
                button_text=t(lang, "send_location_button"),
            ),
        )

    @staticmethod
    def _missing_required_photos(draft: InspectionDraft) -> list[str]:
        return [key for key, _ in REQUIRED_PHOTOS if key not in draft.required_photos]

    @staticmethod
    def _missing_daily_end_workday_photos(draft: InspectionDraft) -> list[str]:
        return [
            key
            for key, _ in REQUIRED_PHOTOS
            if key not in draft.daily_end_workday_required_photos
        ]

    async def _try_clear_inline_keyboard(self, callback: CallbackQuery) -> None:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except (TelegramBadRequest, AttributeError):
            # Message can already be edited or become unavailable; this is non-critical.
            return

    async def _submit_inspection(self, message: Message, draft: InspectionDraft) -> None:
        lang = self._draft_language(user_id=draft.driver_tg_id, draft=draft)
        inspection_id = draft.inspection_id
        if inspection_id is None:
            await message.answer(t(lang, "inspection_not_started_use_start"))
            return

        summary = self.db.get_inspection_summary(inspection_id)
        inspection = summary["inspection"]
        latitude = inspection.get("driver_latitude")
        longitude = inspection.get("driver_longitude")
        location_time = inspection.get("driver_location_at")
        if latitude is not None and longitude is not None:
            geo_text = f"{float(latitude):.6f}, {float(longitude):.6f}"
            geo_map_url = f"https://maps.google.com/?q={latitude},{longitude}"
        else:
            geo_text = "не передана"
            geo_map_url = "-"

        required_photo_map: dict[str, Path] = {}
        for photo_item in summary["required_photos"]:
            photo_type = str(photo_item.get("photo_type") or "").strip()
            file_path = str(photo_item.get("file_path") or "").strip()
            if not photo_type or not file_path:
                continue
            resolved_path = self._resolve_stored_photo_path(file_path)
            if resolved_path.exists():
                required_photo_map[photo_type] = resolved_path

        required_photos_ordered: list[tuple[str, Path]] = []
        for photo_type, _ in REQUIRED_PHOTOS:
            photo_path = required_photo_map.get(photo_type)
            if photo_path:
                required_photos_ordered.append((photo_type, photo_path))
        for photo_type, photo_path in required_photo_map.items():
            if photo_type not in {required_type for required_type, _ in REQUIRED_PHOTOS}:
                required_photos_ordered.append((photo_type, photo_path))

        report_lines = [
            f"🧾 <b>Отчет приемки #{inspection['id']}</b>",
            f"Сотрудник: <b>{inspection['driver_full_name']}</b>",
            f"Телефон: <b>{inspection.get('driver_phone') or 'не указан'}</b>",
            f"Техника: <b>{inspection['equipment_snapshot']}</b>",
            f"Дата: {inspection['started_at']}",
            f"Геолокация: <b>{geo_text}</b>",
            f"Время геометки: {location_time or '-'}",
            f"Карта: {geo_map_url}",
            "",
            f"Итог: ✅ {summary['ok_count']} / ❌ {summary['nok_count']}",
            "",
            "<b>Замечания:</b>",
        ]
        has_issues = False
        for item in summary["items"]:
            if item["is_ok"] == 0:
                has_issues = True
                report_lines.append(f"• {item['item_name']}: ❌")
                if item["comment"]:
                    report_lines.append(f"  Комментарий: {item['comment']}")
        if not has_issues:
            report_lines.append("• Не выявлено")

        report_lines.extend(
            [
                "",
                "Обязательные фото приложены в этом сообщении.",
                "Примите решение кнопками ниже:",
            ]
        )
        report_text = "\n".join(report_lines)
        report_caption = report_text.replace("<b>", "").replace("</b>", "")
        if len(report_caption) > 1024:
            report_caption = report_caption[:1019].rstrip() + "\n…"

        required_photos_sent_with_report = False
        try:
            if len(required_photos_ordered) >= 2:
                try:
                    media = []
                    for idx, (_, photo_path) in enumerate(required_photos_ordered):
                        media.append(
                            InputMediaPhoto(
                                media=FSInputFile(photo_path),
                                caption=report_caption if idx == 0 else None,
                            )
                        )
                    sent_album = await self.bot.send_media_group(
                        chat_id=self.settings.mechanic_group_id,
                        media=media,
                        request_timeout=90,
                    )
                    sent = sent_album[0]
                    required_photos_sent_with_report = True
                    try:
                        await self.bot.edit_message_caption(
                            chat_id=self.settings.mechanic_group_id,
                            message_id=sent.message_id,
                            caption=report_caption,
                            reply_markup=mechanic_decision_keyboard(inspection_id),
                        )
                    except TelegramBadRequest:
                        try:
                            await self.bot.edit_message_reply_markup(
                                chat_id=self.settings.mechanic_group_id,
                                message_id=sent.message_id,
                                reply_markup=mechanic_decision_keyboard(inspection_id),
                            )
                        except TelegramBadRequest:
                            # Some Telegram clients/chats can reject keyboard editing for media group item.
                            sent = await self.bot.send_message(
                                chat_id=self.settings.mechanic_group_id,
                                text="Примите решение кнопками ниже:",
                                reply_markup=mechanic_decision_keyboard(inspection_id),
                                reply_to_message_id=sent.message_id,
                            )
                except (TelegramBadRequest, TelegramNetworkError):
                    # Fallback when media group cannot be delivered.
                    logger.exception(
                        "Failed to send report media group for inspection #%s, fallback to text+separate photos",
                        inspection_id,
                    )
                    sent = await self.bot.send_message(
                        chat_id=self.settings.mechanic_group_id,
                        text=report_caption,
                        reply_markup=mechanic_decision_keyboard(inspection_id),
                    )
            elif len(required_photos_ordered) == 1:
                _, first_path = required_photos_ordered[0]
                sent = await self.bot.send_photo(
                    chat_id=self.settings.mechanic_group_id,
                    photo=FSInputFile(first_path),
                    caption=report_caption,
                    reply_markup=mechanic_decision_keyboard(inspection_id),
                )
                required_photos_sent_with_report = True
            else:
                sent = await self.bot.send_message(
                    chat_id=self.settings.mechanic_group_id,
                    text=report_caption,
                    reply_markup=mechanic_decision_keyboard(inspection_id),
                )
        except (TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError):
            logger.exception(
                "Failed to deliver inspection #%s to mechanic chat_id=%s",
                inspection_id,
                self.settings.mechanic_group_id,
            )
            await message.answer(t(lang, "report_delivery_failed"))
            return

        self.db.set_mechanic_message(inspection_id, sent.message_id)

        # Attach issue photos and required photos to mechanic group
        mechanic_labels = required_photo_labels("ru")
        photo_send_errors = 0
        for item in summary["items"]:
            if item.get("issue_photo_path"):
                photo_path = self._resolve_stored_photo_path(str(item["issue_photo_path"]))
                if photo_path.exists():
                    try:
                        await self.bot.send_photo(
                            chat_id=self.settings.mechanic_group_id,
                            photo=FSInputFile(photo_path),
                            caption=f"Неисправность: {item['item_name']}",
                        )
                    except Exception:
                        photo_send_errors += 1
                        logger.exception(
                            "Failed to send issue photo for inspection #%s path=%s",
                            inspection_id,
                            photo_path,
                        )

        if not required_photos_sent_with_report:
            for photo_type, photo_path in required_photos_ordered:
                try:
                    await self.bot.send_photo(
                        chat_id=self.settings.mechanic_group_id,
                        photo=FSInputFile(photo_path),
                        caption=(
                            "Обязательное фото к отчету: "
                            f"{mechanic_labels.get(photo_type, photo_type)}"
                        ),
                        reply_to_message_id=sent.message_id,
                    )
                except Exception:
                    photo_send_errors += 1
                    logger.exception(
                        "Failed to send required photo for inspection #%s path=%s",
                        inspection_id,
                        photo_path,
                    )

        self.db.complete_inspection(inspection_id)

        if photo_send_errors:
            await message.answer(
                t(
                    lang,
                    "report_delivered_with_missing_photos",
                    inspection_id=inspection_id,
                    photo_send_errors=photo_send_errors,
                ),
                reply_markup=None,
            )
        else:
            await message.answer(
                t(lang, "report_delivered_success", inspection_id=inspection_id),
                reply_markup=None,
            )
        self._cancel_required_photo_group_task(draft.driver_tg_id)
        self.drafts.pop(draft.driver_tg_id, None)
        self.photo_locks.pop(draft.driver_tg_id, None)


async def main() -> None:
    app = InspectionBot()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
