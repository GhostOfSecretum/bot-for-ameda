from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.constants import DECISION_LABELS


def yes_no_keyboard(
    item_index: int,
    can_go_back: bool,
    *,
    ok_text: str = "✅ ОК",
    nok_text: str = "❌ Не ОК",
    back_text: str = "↩️ Назад",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=ok_text, callback_data=f"item:{item_index}:ok")
    builder.button(text=nok_text, callback_data=f"item:{item_index}:nok")
    if can_go_back:
        builder.button(text=back_text, callback_data=f"item:{item_index}:undo")
        builder.adjust(2, 1)
    else:
        builder.adjust(2)
    return builder.as_markup()


def simple_reply_keyboard(
    options: list[str],
    width: int = 2,
    with_back: bool = False,
    back_text: str = "Назад",
) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for option in options:
        builder.add(KeyboardButton(text=option))
    if with_back:
        builder.add(KeyboardButton(text=back_text))
        option_rows = (len(options) + width - 1) // width
        row_sizes = [width] * option_rows + [1]
        builder.adjust(*row_sizes)
    else:
        builder.adjust(width)
    return builder.as_markup(resize_keyboard=True)


def required_photo_keyboard(
    photos_state: dict[str, bool],
    labels: dict[str, str],
    *,
    submit_text: str = "📤 Отправить отчет",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in labels.items():
        state = "✅" if photos_state.get(key) else "⬜️"
        builder.button(text=f"{state} {label}", callback_data=f"req_photo:{key}")
    builder.button(text=submit_text, callback_data="req_photo:submit")
    builder.adjust(1)
    return builder.as_markup()


def submit_report_keyboard(submit_text: str = "📤 Отправить отчет") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=submit_text,
                    callback_data="req_photo:submit",
                )
            ]
        ]
    )


def request_location_keyboard(button_text: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=button_text,
                    request_location=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def language_keyboard(selected_language: str | None = None) -> InlineKeyboardMarkup:
    labels = {
        "ru": "Русский",
        "tg": "Тоҷикӣ",
        "uz": "O'zbekcha",
    }
    builder = InlineKeyboardBuilder()
    for code, label in labels.items():
        prefix = "✅ " if selected_language == code else ""
        builder.button(text=f"{prefix}{label}", callback_data=f"lang:{code}")
    builder.adjust(1)
    return builder.as_markup()


def personal_data_consent_keyboard(
    *,
    policy_text: str,
    policy_url: str,
    agree_text: str,
    decline_text: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=policy_text, url=policy_url)
    builder.button(text=agree_text, callback_data="regconsent:agree")
    builder.button(text=decline_text, callback_data="regconsent:decline")
    builder.adjust(1)
    return builder.as_markup()


def mechanic_decision_keyboard(inspection_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=DECISION_LABELS["approved"],
        callback_data=f"mechanic:{inspection_id}:approved",
    )
    builder.button(
        text=DECISION_LABELS["rejected"],
        callback_data=f"mechanic:{inspection_id}:rejected",
    )
    builder.button(
        text=DECISION_LABELS["repair"],
        callback_data=f"mechanic:{inspection_id}:repair",
    )
    # Two rows display better on mobile clients for long decision labels.
    builder.adjust(2, 1)
    return builder.as_markup()


def daily_refuel_decision_keyboard(
    report_id: int,
    *,
    approve_text: str = "✅ Одобрить заправку",
    reject_text: str = "🚫 Запретить заправку",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=approve_text,
        callback_data=f"dailyfuel:{report_id}:approved",
    )
    builder.button(
        text=reject_text,
        callback_data=f"dailyfuel:{report_id}:rejected",
    )
    builder.adjust(2)
    return builder.as_markup()
