from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from app.db import Database
from app.i18n import required_photo_labels


load_dotenv()

db_path = Path(os.getenv("DATABASE_PATH", "data/inspection.db"))
dashboard_password = os.getenv("ADMIN_DASHBOARD_PASSWORD", "change_me")
db = Database(db_path)
REQUIRED_PHOTO_LABELS_RU = required_photo_labels("ru")
REQUIRED_PHOTO_TYPE_ALIASES = {"back": "rear"}


def _parse_positive_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        value = value[0]
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = int(raw)
    except ValueError:
        return None
    return parsed if parsed >= 1 else None


def _render_images_in_single_row(images: list[dict[str, str]]) -> None:
    if not images:
        return

    columns = st.columns(len(images))
    for index, image in enumerate(images):
        with columns[index]:
            st.image(image["path"], caption=image["caption"], use_container_width=True)


def _required_photo_caption(photo_type: str) -> str:
    normalized = REQUIRED_PHOTO_TYPE_ALIASES.get(photo_type, photo_type)
    return REQUIRED_PHOTO_LABELS_RU.get(normalized, photo_type)


def _render_inspection_details(inspection_id: int) -> None:
    try:
        details = db.get_inspection_details_for_dashboard(inspection_id)
    except ValueError:
        st.warning("Отчет с таким ID не найден")
        return

    inspection = details["inspection"]
    equipment = details["equipment"]

    st.markdown(f"### Отчет #{inspection['id']}")
    st.write(f"**Водитель:** {inspection['driver_full_name']}")
    st.write(f"**Техника:** {equipment.get('type')} {equipment.get('brand')} {equipment.get('reg_number')}")
    st.write(f"**Дата:** {inspection['started_at']}")
    st.write(f"**Итог:** ✅ {details['ok_count']} / ❌ {details['nok_count']}")
    st.write(f"**Решение механика:** {inspection['mechanic_decision'] or '—'}")

    st.markdown("#### Пункты чек-листа")
    for item in details["items"]:
        status = "✅" if item["is_ok"] == 1 else "❌"
        st.write(f"- {item['item_name']}: {status}")
        if item["comment"]:
            st.caption(f"Комментарий: {item['comment']}")
        if item["issue_photo_path"] and Path(item["issue_photo_path"]).exists():
            st.image(item["issue_photo_path"], caption=f"Неисправность: {item['item_name']}", width=280)

    st.markdown("#### Обязательные фото")
    required_images: list[dict[str, str]] = []
    for photo in details["required_photos"]:
        path = Path(photo["file_path"])
        if path.exists():
            required_images.append(
                {
                    "path": str(path),
                    "caption": _required_photo_caption(str(photo["photo_type"])),
                }
            )

    _render_images_in_single_row(required_images)


st.set_page_config(page_title="Приемка спецтехники", layout="wide")
st.title("Админ-панель: цифровая приемка спецтехники")

if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

if not st.session_state["auth_ok"]:
    st.subheader("Вход")
    password = st.text_input("Пароль панели", type="password")
    if st.button("Войти"):
        if password == dashboard_password:
            st.session_state["auth_ok"] = True
            st.success("Доступ открыт")
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

st.subheader("История отчетов")
rows = db.get_recent_inspections(limit=300)
if not rows:
    st.info("Пока нет отчетов приемки")
else:
    table = []
    for r in rows:
        table.append(
            {
                "ID": r["id"],
                "Дата старта": r["started_at"],
                "Водитель": r["driver_full_name"],
                "Техника": f"{r['type']} {r['brand']} {r['reg_number']}",
                "Статус": r["status"],
                "Решение": r["mechanic_decision"] or "-",
            }
        )

    st.dataframe(table, use_container_width=True, hide_index=True)

query_inspection_id = _parse_positive_int(st.query_params.get("inspection_id"))
selected_default = query_inspection_id or 1
selected_id = st.number_input("Открыть отчет по ID", min_value=1, step=1, value=selected_default)

show_details_clicked = st.button("Показать детали")
target_inspection_id: int | None = None
if show_details_clicked:
    target_inspection_id = int(selected_id)
    if str(st.query_params.get("inspection_id", "")) != str(target_inspection_id):
        st.query_params["inspection_id"] = str(target_inspection_id)
elif query_inspection_id is not None:
    target_inspection_id = query_inspection_id

if target_inspection_id is not None:
    _render_inspection_details(target_inspection_id)

st.divider()
st.subheader("Журнал действий в течении дня")
daily_rows = db.get_recent_daily_action_reports(limit=300)
if not daily_rows:
    st.info("Пока нет отчетов по действиям в течении дня")
else:
    daily_table = []
    for row in daily_rows:
        daily_table.append(
            {
                "ID": row["id"],
                "Дата": row["created_at"],
                "Сотрудник": row["driver_full_name"],
                "Действие": row["action_label"],
                "Статус": row["status_label"] or "-",
                "ID приемки": row["linked_inspection_id"] or "-",
                "Решение по ГСМ": row["fuel_decision"] or "-",
                "Доставка": row["delivery_status"],
            }
        )
    st.dataframe(daily_table, use_container_width=True, hide_index=True)

daily_id = st.number_input("Открыть действие по ID", min_value=1, step=1, key="daily_action_id")
if st.button("Показать действие", key="show_daily_action"):
    action = db.get_daily_action_report(int(daily_id))
    if action is None:
        st.warning("Действие с таким ID не найдено")
    else:
        st.markdown(f"### Действие #{action['id']}")
        st.write(f"**Сотрудник:** {action['driver_full_name']}")
        st.write(f"**Телефон:** {action['driver_phone'] or '—'}")
        st.write(f"**Тип действия:** {action['action_label']}")
        st.write(f"**ID приемки:** {action['linked_inspection_id'] or '—'}")
        st.write(f"**Статус:** {action['status_label'] or '—'}")
        st.write(f"**Решение по ГСМ:** {action['fuel_decision'] or '—'}")
        st.write(f"**Комментарий:** {action['comment'] or '—'}")
        st.write(f"**Дата:** {action['created_at']}")
        st.write(f"**Статус доставки:** {action['delivery_status']}")
        if action["photo_path"] and Path(action["photo_path"]).exists():
            st.image(action["photo_path"], caption="Фото к действию", width=320)
