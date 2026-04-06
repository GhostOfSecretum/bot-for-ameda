from __future__ import annotations

import base64
import os
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from app.db import Database
from app.i18n import (
    CHECKLIST_ITEMS_FOREIGN_I18N,
    CHECKLIST_ITEMS_I18N,
    CHECKLIST_ITEMS_ROLLERS_I18N,
    CHECKLIST_ITEMS_SPECIAL_I18N,
    CHECKLIST_ITEMS_SPECIAL_WITHOUT_JOINTS_I18N,
    DUMP_TRUCK_TENT_ITEM_I18N,
    required_photo_labels,
)
from app.time_utils import now_moscow


load_dotenv()

db_path = Path(os.getenv("DATABASE_PATH", "data/inspection.db"))
db = Database(db_path)
REQUIRED_PHOTO_LABELS_RU = required_photo_labels("ru")
REQUIRED_PHOTO_TYPE_ALIASES = {"back": "rear"}
INSPECTION_STATUS_LABELS_RU = {
    "draft": "Черновик",
    "submitted": "Отправлен",
    "closed": "Закрыт",
    "approved": "Одобрено",
    "rejected": "Отклонено",
}
MECHANIC_DECISION_LABELS_RU = {
    "approved": "Одобрено",
    "rejected": "Отклонено",
    "repair": "В ремонт",
}
DAILY_DELIVERY_STATUS_LABELS_RU = {
    "pending": "В очереди",
    "sent": "Отправлено",
    "failed": "Ошибка доставки",
}
DAILY_ACTION_STATUS_LABELS_RU = {
    "yes": "Да",
    "no": "Нет",
    "done": "Выполнено",
    "not_done": "Не выполнено",
    "required": "Требуется",
    "completed": "Выполнено",
}
DAILY_ACTION_FILTER_LABELS_RU = {
    "all": "Все",
    "refuel": "Заправка",
    "end_workday": "Завершение смены",
    "service": "Обслуживание",
}
CHECKLIST_I18N_GROUPS = [
    CHECKLIST_ITEMS_I18N,
    CHECKLIST_ITEMS_FOREIGN_I18N,
    CHECKLIST_ITEMS_ROLLERS_I18N,
    CHECKLIST_ITEMS_SPECIAL_I18N,
    CHECKLIST_ITEMS_SPECIAL_WITHOUT_JOINTS_I18N,
]
DASHBOARD_SECTION_LINKS = [
    ("Аналитика", "section-analytics"),
    ("История отчетов", "section-inspections-history"),
    ("Журнал действий в течении смены", "section-daily-actions"),
    ("Панель техники", "section-equipment-panel"),
    ("Панель водителей", "section-driver-panel"),
]
DASHBOARD_LOGO_MIME_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "svg": "image/svg+xml",
}


def _list_logo_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    for extension in DASHBOARD_LOGO_MIME_TYPES:
        files.extend(directory.glob(f"*.{extension}"))
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)


def _dashboard_logo_candidates() -> list[Path]:
    explicit_logo_path = os.getenv("ADMIN_DASHBOARD_LOGO_PATH", "").strip()
    project_root = Path(__file__).resolve().parent
    candidates: list[Path] = []

    if explicit_logo_path:
        logo_path = Path(explicit_logo_path).expanduser()
        candidates.append(logo_path if logo_path.is_absolute() else (project_root / logo_path))

    candidates.extend(
        [
            project_root / "assets" / "dashboard_logo.png",
            project_root / "assets" / "logo.png",
            project_root / "assets" / "drlogo.png",
        ]
    )
    project_assets_dir = project_root / "assets"
    if project_assets_dir.exists():
        candidates.extend(_list_logo_files(project_assets_dir))

    workspace_slug = str(project_root).strip("/").replace("/", "-").replace(" ", "-")
    cursor_assets_dir = Path.home() / ".cursor" / "projects" / workspace_slug / "assets"
    if cursor_assets_dir.exists():
        candidates.extend(_list_logo_files(cursor_assets_dir))

    unique_candidates: list[Path] = []
    seen_candidates: set[Path] = set()
    for candidate in candidates:
        resolved_candidate = candidate.resolve()
        if resolved_candidate in seen_candidates:
            continue
        seen_candidates.add(resolved_candidate)
        unique_candidates.append(resolved_candidate)
    return unique_candidates


def _load_dashboard_logo_data_uri() -> str | None:
    for logo_path in _dashboard_logo_candidates():
        if not logo_path.exists() or not logo_path.is_file():
            continue

        logo_mime_type = DASHBOARD_LOGO_MIME_TYPES.get(logo_path.suffix.lower().lstrip("."))
        if logo_mime_type is None:
            continue

        encoded_logo = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        return f"data:{logo_mime_type};base64,{encoded_logo}"
    return None


def _inject_toolbar_logo() -> None:
    logo_data_uri = _load_dashboard_logo_data_uri()
    if logo_data_uri is None:
        return

    st.html(
        f"""
        <style>
        .dr-header-logo {{
            position: fixed;
            top: 0;
            left: 0;
            z-index: 999990;
            height: 52px;
            padding: 6px 16px;
            display: flex;
            align-items: center;
            pointer-events: none;
        }}
        .dr-header-logo img {{
            height: 36px;
            width: auto;
            object-fit: contain;
        }}
        @media (max-width: 768px) {{
            .dr-header-logo {{
                height: 44px;
                padding: 4px 10px;
            }}
            .dr-header-logo img {{
                height: 28px;
            }}
        }}
        </style>
        <div class="dr-header-logo">
            <img src="{logo_data_uri}" alt="Logo" />
        </div>
        """
    )


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


def _daily_action_photo_caption(photo_type: str | None) -> str:
    if not photo_type:
        return "Фото к действию"
    if photo_type == "fuel":
        return "Уровень топлива"
    return _required_photo_caption(photo_type)


def _build_checklist_item_to_ru_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for group in CHECKLIST_I18N_GROUPS:
        ru_items = group.get("ru", [])
        for items_by_language in group.values():
            for index, localized_item in enumerate(items_by_language):
                if index >= len(ru_items):
                    continue
                localized_key = str(localized_item).strip()
                ru_label = str(ru_items[index]).strip()
                if localized_key and ru_label:
                    mapping[localized_key] = ru_label

    ru_dump_truck_tent = str(DUMP_TRUCK_TENT_ITEM_I18N.get("ru", "")).strip()
    if ru_dump_truck_tent:
        for localized_tent in DUMP_TRUCK_TENT_ITEM_I18N.values():
            localized_key = str(localized_tent).strip()
            if localized_key:
                mapping[localized_key] = ru_dump_truck_tent
    return mapping


CHECKLIST_ITEM_TO_RU = _build_checklist_item_to_ru_map()


def _checklist_item_label_ru(item_name: str | None) -> str:
    normalized = str(item_name or "").strip()
    if not normalized:
        return "—"
    return CHECKLIST_ITEM_TO_RU.get(normalized, normalized)


def _translate_status(value: str | None, labels: dict[str, str], default: str = "—") -> str:
    if not value:
        return default
    normalized = str(value).strip()
    if not normalized or normalized == "-":
        return default
    return labels.get(normalized.lower(), normalized)


def _dashboard_status_key(raw_status: str | None, mechanic_decision: str | None) -> str:
    if mechanic_decision in {"approved", "rejected"}:
        return mechanic_decision
    return raw_status or "-"


def _dashboard_status_label(raw_status: str | None, mechanic_decision: str | None) -> str:
    return _translate_status(
        _dashboard_status_key(raw_status, mechanic_decision),
        INSPECTION_STATUS_LABELS_RU,
    )


def _mechanic_decision_label(mechanic_decision: str | None) -> str:
    return _translate_status(mechanic_decision, MECHANIC_DECISION_LABELS_RU)


def _delivery_status_label(status: str | None) -> str:
    return _translate_status(status, DAILY_DELIVERY_STATUS_LABELS_RU)


def _daily_action_status_label(status_label: str | None, status_key: str | None) -> str:
    if status_label:
        return _translate_status(status_label, DAILY_ACTION_STATUS_LABELS_RU)
    return _translate_status(status_key, DAILY_ACTION_STATUS_LABELS_RU)


def _daily_action_type_key(action_key: str | None) -> str:
    normalized = (action_key or "").strip().lower()
    if normalized == "refuel":
        return "refuel"
    if normalized == "end_workday":
        return "end_workday"
    return "service"


def _daily_action_type_filter_label(filter_key: str) -> str:
    return DAILY_ACTION_FILTER_LABELS_RU.get(filter_key, filter_key)


def _inspection_status_filter_label(status_key: str) -> str:
    if status_key == "Все":
        return "Все"
    return _translate_status(status_key, INSPECTION_STATUS_LABELS_RU)


def _clamp_date_filter(value: date, min_date: date, max_date: date) -> date:
    if value < min_date:
        return min_date
    if value > max_date:
        return max_date
    return value


def _render_section_anchor(anchor_id: str) -> None:
    st.markdown(
        f'<div id="{anchor_id}" style="scroll-margin-top: 4.5rem;"></div>',
        unsafe_allow_html=True,
    )


def _render_quick_navigation_menu() -> None:
    with st.expander("Быстрый переход", expanded=False):
        st.caption("Нажмите на раздел, чтобы перейти")
        for section_label, section_anchor in DASHBOARD_SECTION_LINKS:
            st.markdown(f"- [{section_label}](#{section_anchor})")


def _on_equipment_type_change() -> None:
    st.session_state["inspection_filter_equipment_brand"] = "Все"
    st.session_state["inspection_filter_equipment_number"] = "Все"


def _on_equipment_brand_change() -> None:
    st.session_state["inspection_filter_equipment_number"] = "Все"


def _equipment_label(equipment_type: str | None, brand: str | None, reg_number: str | None) -> str:
    parts = [
        str(equipment_type or "").strip(),
        str(brand or "").strip(),
        str(reg_number or "").strip(),
    ]
    return " ".join([part for part in parts if part]) or "—"


def _render_equipment_details_panel(equipment_id: int) -> None:
    equipment = db.get_equipment(equipment_id)
    if equipment is None:
        st.warning("Техника не найдена")
        return

    equipment_name = _equipment_label(equipment["type"], equipment["brand"], equipment["reg_number"])
    history_rows = db.get_equipment_inspection_history_for_dashboard(equipment_id)
    repair_rows = db.get_equipment_repairs_for_dashboard(equipment_id)
    drivers_rows = db.get_equipment_drivers_for_dashboard(equipment_id)
    checks_with_issues = sum(1 for row in history_rows if int(row["nok_count"] or 0) > 0)

    st.markdown(f"### Техника #{equipment['id']}: {equipment_name}")
    metric_col_total, metric_col_issues, metric_col_repairs, metric_col_drivers = st.columns(4)
    with metric_col_total:
        st.metric("Всего проверок", len(history_rows))
    with metric_col_issues:
        st.metric("С проблемами", checks_with_issues)
    with metric_col_repairs:
        st.metric("Ремонты", len(repair_rows))
    with metric_col_drivers:
        st.metric("Кто ездил", len(drivers_rows))

    history_tab, repairs_tab, drivers_tab = st.tabs(
        ["История всех проверок", "Ремонты", "Кто ездил"]
    )

    with history_tab:
        if not history_rows:
            st.info("По этой технике пока нет проверок")
        else:
            history_table: list[dict[str, object]] = []
            for row in history_rows:
                ok_count = int(row["ok_count"] or 0)
                nok_count = int(row["nok_count"] or 0)
                total_count = ok_count + nok_count
                history_table.append(
                    {
                        "ID проверки": row["id"],
                        "Дата": pd.to_datetime(row["started_at"], errors="coerce"),
                        "Водитель": row["driver_full_name"] or "—",
                        "Итог": f"{ok_count}/{total_count}" if total_count else "—",
                        "Проблемы": nok_count,
                        "Статус": _dashboard_status_label(row["status"], row["mechanic_decision"]),
                        "Решение": _mechanic_decision_label(row["mechanic_decision"]),
                    }
                )
            st.dataframe(
                history_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Дата": st.column_config.DatetimeColumn("Дата", format="YYYY-MM-DD HH:mm:ss"),
                },
            )

    with repairs_tab:
        if not repair_rows:
            st.info("Ремонтов по этой технике пока нет")
        else:
            repairs_table: list[dict[str, object]] = []
            for row in repair_rows:
                repair_at = row["mechanic_decision_at"] or row["started_at"]
                repairs_table.append(
                    {
                        "ID проверки": row["id"],
                        "Дата ремонта": pd.to_datetime(repair_at, errors="coerce"),
                        "Водитель": row["driver_full_name"] or "—",
                        "Проблемы": int(row["nok_count"] or 0),
                        "Комментарий механика": row["mechanic_comment"] or "—",
                    }
                )
            st.dataframe(
                repairs_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Дата ремонта": st.column_config.DatetimeColumn(
                        "Дата ремонта",
                        format="YYYY-MM-DD HH:mm:ss",
                    ),
                },
            )

    with drivers_tab:
        if not drivers_rows:
            st.info("По этой технике пока нет данных о водителях")
        else:
            drivers_table: list[dict[str, object]] = []
            for row in drivers_rows:
                driver_name = (row["driver_full_name"] or "").strip()
                if not driver_name:
                    driver_name = f"ID {row['driver_telegram_id']}"
                drivers_table.append(
                    {
                        "Водитель": driver_name,
                        "Проверок": int(row["inspections_count"] or 0),
                        "Первый выезд": pd.to_datetime(row["first_drive_at"], errors="coerce"),
                        "Последний выезд": pd.to_datetime(row["last_drive_at"], errors="coerce"),
                    }
                )
            st.dataframe(
                drivers_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Первый выезд": st.column_config.DatetimeColumn(
                        "Первый выезд",
                        format="YYYY-MM-DD HH:mm:ss",
                    ),
                    "Последний выезд": st.column_config.DatetimeColumn(
                        "Последний выезд",
                        format="YYYY-MM-DD HH:mm:ss",
                    ),
                },
            )


def _driver_rating_value(ok_count: int, total_items_count: int) -> float | None:
    if total_items_count <= 0:
        return None
    return (ok_count / total_items_count) * 5


def _driver_rating_label(ok_count: int, total_items_count: int) -> str:
    rating_value = _driver_rating_value(ok_count, total_items_count)
    if rating_value is None:
        return "—"
    return f"{rating_value:.2f} / 5"


def _driver_rating_status(ok_count: int, total_items_count: int) -> str:
    rating_value = _driver_rating_value(ok_count, total_items_count)
    if rating_value is None:
        return "—"
    if rating_value >= 4.0:
        return "отлично"
    if rating_value >= 3.0:
        return "нормально"
    return "проблема"


def _driver_rating_cell_value(ok_count: int, total_items_count: int) -> str:
    rating_status = _driver_rating_status(ok_count, total_items_count)
    rating_label = _driver_rating_label(ok_count, total_items_count)
    if rating_status == "—":
        return "—"
    return f"{rating_status} ({rating_label})"


def _driver_rating_cell_style(value: object) -> str:
    normalized = str(value).strip().lower()
    if normalized.startswith("отлично"):
        return "background-color: #E8F5E9; color: #1B5E20; font-weight: 700;"
    if normalized.startswith("нормально"):
        return "background-color: #FFF8E1; color: #8A6D1F; font-weight: 700;"
    if normalized.startswith("проблема"):
        return "background-color: #FFEBEE; color: #B71C1C; font-weight: 700;"
    return ""


def _percent(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return (value / total) * 100


def _build_recent_inspections_analytics(rows: list[object]) -> dict[str, object]:
    checks_count = len(rows)
    checks_with_issues = 0
    approved_checks = 0
    pending_checks = 0
    issue_by_driver: dict[str, int] = {}
    issue_by_equipment: dict[str, int] = {}
    checks_by_day: dict[date, int] = {}

    for row in rows:
        status_key = _dashboard_status_key(row["status"], row["mechanic_decision"])
        if status_key == "approved":
            approved_checks += 1
        raw_status = (row["status"] or "").strip().lower()
        mechanic_decision = (row["mechanic_decision"] or "").strip().lower()
        has_final_decision = mechanic_decision in {"approved", "rejected", "repair"}
        if raw_status in {"draft", "submitted"} or (raw_status == "closed" and not has_final_decision):
            pending_checks += 1

        nok_count = int(row["nok_count"] or 0)
        has_issues = nok_count > 0
        if has_issues:
            checks_with_issues += 1
            driver_name = (row["driver_full_name"] or "").strip() or "Не указан"
            issue_by_driver[driver_name] = issue_by_driver.get(driver_name, 0) + 1
            equipment_name = _equipment_label(row["type"], row["brand"], row["reg_number"])
            issue_by_equipment[equipment_name] = issue_by_equipment.get(equipment_name, 0) + 1

        started_at_dt = pd.to_datetime(row["started_at"], errors="coerce")
        if pd.notna(started_at_dt):
            started_date = started_at_dt.date()
            checks_by_day[started_date] = checks_by_day.get(started_date, 0) + 1

    top_driver_issue = None
    if issue_by_driver:
        top_driver_issue = max(issue_by_driver.items(), key=lambda item: item[1])

    top_equipment_issue = None
    if issue_by_equipment:
        top_equipment_issue = max(issue_by_equipment.items(), key=lambda item: item[1])

    active_days_count = len(checks_by_day)
    avg_checks_per_day = (checks_count / active_days_count) if active_days_count else 0.0

    return {
        "checks_count": checks_count,
        "checks_with_issues": checks_with_issues,
        "approved_checks": approved_checks,
        "pending_checks": pending_checks,
        "issue_rate": _percent(checks_with_issues, checks_count),
        "approval_rate": _percent(approved_checks, checks_count),
        "top_driver_issue": top_driver_issue,
        "top_equipment_issue": top_equipment_issue,
        "avg_checks_per_day": avg_checks_per_day,
    }


def _render_recommendation_analytics_block(
    dashboard_stats: dict[str, int],
    recent_rows: list[object],
) -> None:
    st.markdown("#### Рекомендации по реализации")
    with st.container(border=True):
        if not recent_rows:
            st.info("Недостаточно данных: добавьте больше отчетов, чтобы строить рекомендации.")
            return

        analytics = _build_recent_inspections_analytics(recent_rows)
        issue_rate = float(analytics["issue_rate"])
        approval_rate = float(analytics["approval_rate"])
        pending_checks = int(analytics["pending_checks"])
        top_driver_issue = analytics["top_driver_issue"]
        top_equipment_issue = analytics["top_equipment_issue"]

        issue_col, approval_col, pending_col = st.columns(3)
        with issue_col:
            st.metric("Доля проверок с косяками", f"{issue_rate:.1f}%")
        with approval_col:
            st.metric("Доля одобрений", f"{approval_rate:.1f}%")
        with pending_col:
            st.metric("Без финального решения", pending_checks)

        recommendations: list[str] = []
        if issue_rate >= 35:
            recommendations.append(
                "Высокая доля косяков: добавьте обязательный чек проблемных узлов перед выездом."
            )
        elif issue_rate >= 20:
            recommendations.append(
                "Средняя доля косяков: внедрите еженедельный разбор типовых неисправностей."
            )
        else:
            recommendations.append(
                "Качество стабильное: закрепите текущий процесс и контролируйте отклонения по неделям."
            )

        if pending_checks > 0:
            recommendations.append(
                f"Есть незавершенные приемки ({pending_checks}): добавьте SLA для решения механика."
            )

        if top_driver_issue is not None:
            recommendations.append(
                f"Точка обучения: водитель «{top_driver_issue[0]}» чаще других с косяками ({top_driver_issue[1]})."
            )

        if top_equipment_issue is not None:
            recommendations.append(
                "Техника с максимальным риском: "
                f"«{top_equipment_issue[0]}» ({top_equipment_issue[1]} проблемных проверок)."
            )

        if dashboard_stats["today_checks"] == 0:
            recommendations.append(
                "Сегодня нет новых проверок: проверьте, что у водителей не сломалась отправка в боте."
            )

        for recommendation in recommendations:
            st.write(f"- {recommendation}")

        st.caption(
            "Основа аналитики: последние "
            f"{analytics['checks_count']} проверок, средняя нагрузка "
            f"{analytics['avg_checks_per_day']:.1f} проверки/день."
        )


def _render_driver_details_panel(driver_telegram_id: int) -> None:
    summary = db.get_driver_dashboard_summary(driver_telegram_id)
    if summary is None:
        st.warning("Водитель не найден")
        return

    driver_name = (summary["driver_full_name"] or "").strip() or f"ID {driver_telegram_id}"
    driver_phone = summary["driver_phone"] or "—"
    shifts_count = int(summary["shifts_count"] or 0)
    issues_count = int(summary["issues_count"] or 0)
    ok_count = int(summary["ok_count"] or 0)
    total_items_count = int(summary["total_items_count"] or 0)
    rating_label = _driver_rating_label(ok_count, total_items_count)
    last_shift_dt = pd.to_datetime(summary["last_shift_at"], errors="coerce")
    last_shift_label = (
        last_shift_dt.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(last_shift_dt) else "—"
    )

    st.markdown(f"### Водитель: {driver_name}")
    main_col, result_col = st.columns([2, 1])
    with main_col:
        with st.container(border=True):
            st.markdown("#### Основное")
            st.write(f"**Телефон:** {driver_phone}")
            st.write(f"**Последняя смена:** {last_shift_label}")
            st.write(f"**ID водителя:** {driver_telegram_id}")
    with result_col:
        with st.container(border=True):
            st.markdown("#### Результат")
            st.metric("Сколько смен", shifts_count)
            st.metric("Сколько косяков", issues_count)
            st.metric("Рейтинг", rating_label)

    inspections_rows = db.get_driver_inspections_for_dashboard(driver_telegram_id)
    st.markdown("#### История смен")
    if not inspections_rows:
        st.info("По этому водителю пока нет проверок")
    else:
        history_table: list[dict[str, object]] = []
        for row in inspections_rows:
            ok_value = int(row["ok_count"] or 0)
            nok_value = int(row["nok_count"] or 0)
            total_value = ok_value + nok_value
            history_table.append(
                {
                    "ID проверки": row["id"],
                    "Дата": pd.to_datetime(row["started_at"], errors="coerce"),
                    "Техника": _equipment_label(row["type"], row["brand"], row["reg_number"]),
                    "Итог": f"{ok_value}/{total_value}" if total_value else "—",
                    "Косяки": nok_value,
                    "Статус": _dashboard_status_label(row["status"], row["mechanic_decision"]),
                    "Решение": _mechanic_decision_label(row["mechanic_decision"]),
                }
            )
        st.dataframe(
            history_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Дата": st.column_config.DatetimeColumn("Дата", format="YYYY-MM-DD HH:mm:ss"),
            },
        )


def _render_inspection_details(inspection_id: int) -> None:
    try:
        details = db.get_inspection_details_for_dashboard(inspection_id)
    except ValueError:
        st.warning("Отчет с таким ID не найден")
        return

    inspection = details["inspection"]
    equipment = details["equipment"]
    equipment_parts = [
        str(equipment.get("type") or "").strip(),
        str(equipment.get("brand") or "").strip(),
        str(equipment.get("reg_number") or "").strip(),
    ]
    equipment_label = " ".join([part for part in equipment_parts if part]) or "—"
    status_label = _dashboard_status_label(inspection.get("status"), inspection.get("mechanic_decision"))
    total_items = details["ok_count"] + details["nok_count"]
    total_label = f"{details['ok_count']}/{total_items}" if total_items else "0/0"

    st.markdown(f"### Отчет #{inspection['id']}")
    main_col, result_col = st.columns([2, 1])
    with main_col:
        with st.container(border=True):
            st.markdown("#### Основное")
            st.write(f"**Водитель:** {inspection.get('driver_full_name') or '—'}")
            st.write(f"**Техника:** {equipment_label}")
            st.write(f"**Дата:** {inspection.get('started_at') or '—'}")
    with result_col:
        with st.container(border=True):
            st.markdown("#### Результат")
            st.metric("Итог", total_label, help="Количество OK-пунктов / все пункты чек-листа")
            if total_items:
                st.progress(
                    details["ok_count"] / total_items,
                    text=f"OK: {details['ok_count']} из {total_items}",
                )
            st.write(f"**Статус:** {status_label}")

    problematic_items = [item for item in details["items"] if item["is_ok"] == 0]
    st.markdown("#### Проблемы")
    with st.container(border=True):
        if not problematic_items:
            st.success("Проблемы не выявлены")
        else:
            for index, item in enumerate(problematic_items, start=1):
                item_label = _checklist_item_label_ru(item["item_name"])
                st.write(f"**{index}. {item_label}**")
                st.caption(item["comment"] or "Комментарий не указан")
                issue_photo_path = item["issue_photo_path"]
                if issue_photo_path and Path(issue_photo_path).exists():
                    st.image(
                        issue_photo_path,
                        caption=f"Неисправность: {item_label}",
                        width=320,
                    )
                if index < len(problematic_items):
                    st.divider()

    st.markdown("#### Пункты чек-листа")
    with st.expander("Показать все пункты"):
        for item in details["items"]:
            status = "✅" if item["is_ok"] == 1 else "❌"
            item_label = _checklist_item_label_ru(item["item_name"])
            st.write(f"- {item_label}: {status}")
            if item["comment"]:
                st.caption(f"Комментарий: {item['comment']}")

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

    st.divider()
    with st.expander("Удаление отчёта", expanded=False):
        st.caption(
            "Безвозвратно удалит этот отчёт из базы, все пункты чек-листа и фото на диске. "
            "Привязка к отчёту в журнале смены будет снята."
        )
        confirm_key = f"inspection_delete_confirm_{inspection_id}"
        st.checkbox("Я понимаю последствия и хочу удалить этот отчёт", key=confirm_key)
        delete_clicked = st.button(
            "Удалить отчёт безвозвратно",
            type="primary",
            key=f"inspection_delete_btn_{inspection_id}",
            disabled=not st.session_state.get(confirm_key, False),
        )
        if delete_clicked and st.session_state.get(confirm_key, False):
            if db.delete_inspection(inspection_id):
                if str(st.query_params.get("inspection_id", "")) == str(inspection_id):
                    del st.query_params["inspection_id"]
                st.success(f"Отчёт #{inspection_id} удалён.")
                st.rerun()
            else:
                st.error("Не удалось удалить отчёт (возможно, он уже удалён).")


st.set_page_config(page_title="Приемка спецтехники", layout="wide")

if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

_admin_password = os.getenv("ADMIN_DASHBOARD_PASSWORD", "change_me").strip()

if not st.session_state["auth_ok"]:
    _inject_toolbar_logo()
    st.title("Вход в админ-панель")
    with st.form("admin_login"):
        pwd = st.text_input("Пароль", type="password")
        submitted = st.form_submit_button("Войти")
    if submitted:
        if pwd == _admin_password:
            st.session_state["auth_ok"] = True
            st.rerun()
        st.error("Неверный пароль")
    st.stop()

_inject_toolbar_logo()
title_col, quick_nav_col = st.columns([5, 1.6])
with title_col:
    st.title("Админ-панель: цифровая приемка спецтехники")
with quick_nav_col:
    _render_quick_navigation_menu()

dashboard_stats = db.get_inspection_dashboard_stats(today_date=now_moscow().date().isoformat())
rows = db.get_recent_inspections(limit=300)
_render_section_anchor("section-analytics")
st.subheader("Аналитика")
stats_col_total, stats_col_today, stats_col_issues, stats_col_approved = st.columns(4)
with stats_col_total:
    st.metric("Всего проверок", dashboard_stats["total_checks"])
with stats_col_today:
    st.metric("Сегодня", dashboard_stats["today_checks"])
with stats_col_issues:
    st.metric("С проблемами", dashboard_stats["checks_with_issues"])
with stats_col_approved:
    st.metric("Одобрено", dashboard_stats["approved_checks"])
_render_recommendation_analytics_block(dashboard_stats, rows)

_render_section_anchor("section-inspections-history")
st.subheader("История отчетов")
if not rows:
    st.info("Пока нет отчетов приемки")
else:
    table_rows = []
    for r in rows:
        started_at_dt = pd.to_datetime(r["started_at"], errors="coerce")
        table_rows.append(
            {
                "ID": r["id"],
                "Дата старта": started_at_dt,
                "Водитель": r["driver_full_name"],
                "Техника": f"{r['type']} {r['brand']} {r['reg_number']}",
                "Статус": _dashboard_status_label(r["status"], r["mechanic_decision"]),
                "Решение": _mechanic_decision_label(r["mechanic_decision"]),
                "_date": started_at_dt.date() if pd.notna(started_at_dt) else None,
                "_driver": (r["driver_full_name"] or "").strip(),
                "_equipment_type": (r["type"] or "").strip(),
                "_equipment_brand": (r["brand"] or "").strip(),
                "_equipment_reg_number": (r["reg_number"] or "").strip(),
                "_status": _dashboard_status_key(r["status"], r["mechanic_decision"]),
                "_has_issues": int(r["nok_count"] or 0) > 0,
            }
        )

    table_df = pd.DataFrame(table_rows)

    if table_df["_date"].dropna().empty:
        min_date = date.today()
        max_date = date.today()
    else:
        min_date = min(table_df["_date"].dropna())
        max_date = max(table_df["_date"].dropna())

    driver_options = ["Все"] + sorted([v for v in table_df["_driver"].unique().tolist() if v])

    equipment_catalog_rows = db.list_equipment_catalog()
    equipment_catalog_items = []
    for catalog_row in equipment_catalog_rows:
        catalog_type = (catalog_row["type"] or "").strip()
        catalog_brand = (catalog_row["brand"] or "").strip()
        catalog_number = (catalog_row["reg_number"] or "").strip()
        if not catalog_type and not catalog_brand and not catalog_number:
            continue
        equipment_catalog_items.append(
            {
                "_equipment_type": catalog_type,
                "_equipment_brand": catalog_brand,
                "_equipment_reg_number": catalog_number,
            }
        )
    if equipment_catalog_items:
        equipment_catalog_df = pd.DataFrame(equipment_catalog_items).drop_duplicates()
    else:
        equipment_catalog_df = table_df[
            ["_equipment_type", "_equipment_brand", "_equipment_reg_number"]
        ].drop_duplicates()

    equipment_type_options = ["Все"] + sorted(
        [v for v in equipment_catalog_df["_equipment_type"].unique().tolist() if v]
    )
    status_options = ["Все", "draft", "approved", "rejected"]
    issues_options = ["Все", "есть косяки", "без косяков"]

    if "inspection_filter_date_from" not in st.session_state:
        st.session_state["inspection_filter_date_from"] = min_date
    if "inspection_filter_date_to" not in st.session_state:
        st.session_state["inspection_filter_date_to"] = max_date
    if "inspection_filter_driver" not in st.session_state:
        st.session_state["inspection_filter_driver"] = "Все"
    if "inspection_filter_equipment_type" not in st.session_state:
        st.session_state["inspection_filter_equipment_type"] = "Все"
    if "inspection_filter_equipment_brand" not in st.session_state:
        st.session_state["inspection_filter_equipment_brand"] = "Все"
    if "inspection_filter_equipment_number" not in st.session_state:
        st.session_state["inspection_filter_equipment_number"] = "Все"
    if "inspection_filter_status" not in st.session_state:
        st.session_state["inspection_filter_status"] = "Все"
    if "inspection_filter_issues" not in st.session_state:
        st.session_state["inspection_filter_issues"] = "Все"
    if "inspection_filters_reset_requested" not in st.session_state:
        st.session_state["inspection_filters_reset_requested"] = False

    if st.session_state["inspection_filters_reset_requested"]:
        st.session_state["inspection_filter_date_from"] = min_date
        st.session_state["inspection_filter_date_to"] = max_date
        st.session_state["inspection_filter_driver"] = "Все"
        st.session_state["inspection_filter_equipment_type"] = "Все"
        st.session_state["inspection_filter_equipment_brand"] = "Все"
        st.session_state["inspection_filter_equipment_number"] = "Все"
        st.session_state["inspection_filter_status"] = "Все"
        st.session_state["inspection_filter_issues"] = "Все"
        st.session_state["inspection_filters_reset_requested"] = False

    if st.session_state["inspection_filter_driver"] not in driver_options:
        st.session_state["inspection_filter_driver"] = "Все"
    if st.session_state["inspection_filter_equipment_type"] not in equipment_type_options:
        st.session_state["inspection_filter_equipment_type"] = "Все"
    if st.session_state["inspection_filter_status"] not in status_options:
        st.session_state["inspection_filter_status"] = "Все"
    if st.session_state["inspection_filter_issues"] not in issues_options:
        st.session_state["inspection_filter_issues"] = "Все"

    selected_type_for_options = st.session_state["inspection_filter_equipment_type"]
    brand_source_df = equipment_catalog_df
    if selected_type_for_options != "Все":
        brand_source_df = brand_source_df[brand_source_df["_equipment_type"] == selected_type_for_options]
    equipment_brand_options = ["Все"] + sorted(
        [v for v in brand_source_df["_equipment_brand"].unique().tolist() if v]
    )
    if st.session_state["inspection_filter_equipment_brand"] not in equipment_brand_options:
        st.session_state["inspection_filter_equipment_brand"] = "Все"

    selected_brand_for_options = st.session_state["inspection_filter_equipment_brand"]
    number_source_df = equipment_catalog_df
    if selected_type_for_options != "Все":
        number_source_df = number_source_df[number_source_df["_equipment_type"] == selected_type_for_options]
    if selected_brand_for_options != "Все":
        number_source_df = number_source_df[number_source_df["_equipment_brand"] == selected_brand_for_options]
    equipment_number_options = ["Все"] + sorted(
        [v for v in number_source_df["_equipment_reg_number"].unique().tolist() if v]
    )
    if st.session_state["inspection_filter_equipment_number"] not in equipment_number_options:
        st.session_state["inspection_filter_equipment_number"] = "Все"

    st.session_state["inspection_filter_date_from"] = _clamp_date_filter(
        st.session_state["inspection_filter_date_from"],
        min_date,
        max_date,
    )
    st.session_state["inspection_filter_date_to"] = _clamp_date_filter(
        st.session_state["inspection_filter_date_to"],
        min_date,
        max_date,
    )

    st.markdown("#### Фильтры")
    date_from_col, date_to_col, driver_col = st.columns(3)
    with date_from_col:
        st.date_input(
            "Дата (от)",
            min_value=min_date,
            max_value=max_date,
            value=st.session_state["inspection_filter_date_from"],
            key="inspection_filter_date_from",
        )
    with date_to_col:
        st.date_input(
            "Дата (до)",
            min_value=min_date,
            max_value=max_date,
            value=st.session_state["inspection_filter_date_to"],
            key="inspection_filter_date_to",
        )
    with driver_col:
        st.selectbox("Водитель", driver_options, key="inspection_filter_driver")

    equipment_type_col, equipment_brand_col, equipment_number_col, status_col = st.columns(4)
    with equipment_type_col:
        st.selectbox(
            "Техника: тип",
            equipment_type_options,
            key="inspection_filter_equipment_type",
            on_change=_on_equipment_type_change,
        )
    with equipment_brand_col:
        st.selectbox(
            "Техника: марка",
            equipment_brand_options,
            key="inspection_filter_equipment_brand",
            on_change=_on_equipment_brand_change,
        )
    with equipment_number_col:
        st.selectbox(
            "Техника: номер",
            equipment_number_options,
            key="inspection_filter_equipment_number",
        )
    with status_col:
        st.selectbox(
            "Статус",
            status_options,
            key="inspection_filter_status",
            format_func=_inspection_status_filter_label,
        )

    issues_col, apply_col, reset_col = st.columns([2, 1, 1])
    with issues_col:
        st.selectbox("Проблемы", issues_options, key="inspection_filter_issues")
    with apply_col:
        st.button("Применить", use_container_width=True, key="inspection_filters_apply_button")
    with reset_col:
        reset_filters_clicked = st.button(
            "Сбросить",
            use_container_width=True,
            key="inspection_filters_reset_button",
        )

    if reset_filters_clicked:
        st.session_state["inspection_filters_reset_requested"] = True
        st.rerun()

    filtered_df = table_df.copy()
    date_from_filter = st.session_state["inspection_filter_date_from"]
    date_to_filter = st.session_state["inspection_filter_date_to"]
    if date_from_filter > date_to_filter:
        date_from_filter, date_to_filter = date_to_filter, date_from_filter

    filtered_df = filtered_df[
        (filtered_df["_date"].notna())
        & (filtered_df["_date"] >= date_from_filter)
        & (filtered_df["_date"] <= date_to_filter)
    ]

    driver_filter = st.session_state["inspection_filter_driver"]
    if driver_filter != "Все":
        filtered_df = filtered_df[filtered_df["_driver"] == driver_filter]

    equipment_type_filter = st.session_state["inspection_filter_equipment_type"]
    if equipment_type_filter != "Все":
        filtered_df = filtered_df[filtered_df["_equipment_type"] == equipment_type_filter]

    equipment_brand_filter = st.session_state["inspection_filter_equipment_brand"]
    if equipment_brand_filter != "Все":
        filtered_df = filtered_df[filtered_df["_equipment_brand"] == equipment_brand_filter]

    equipment_number_filter = st.session_state["inspection_filter_equipment_number"]
    if equipment_number_filter != "Все":
        filtered_df = filtered_df[filtered_df["_equipment_reg_number"] == equipment_number_filter]

    status_filter = st.session_state["inspection_filter_status"]
    if status_filter != "Все":
        filtered_df = filtered_df[filtered_df["_status"] == status_filter]

    issues_filter = st.session_state["inspection_filter_issues"]
    if issues_filter == "есть косяки":
        filtered_df = filtered_df[filtered_df["_has_issues"]]
    elif issues_filter == "без косяков":
        filtered_df = filtered_df[~filtered_df["_has_issues"]]

    display_df = filtered_df[["ID", "Дата старта", "Водитель", "Техника", "Статус", "Решение"]]

    st.caption(f"Показано: {len(display_df)} из {len(table_df)}")

    st.caption("Сортировка: кликните по заголовку столбца «Дата старта», «Водитель», «Техника» или «Статус».")
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Дата старта": st.column_config.DatetimeColumn(
                "Дата старта",
                format="YYYY-MM-DD HH:mm:ss",
            ),
        },
    )

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
_render_section_anchor("section-daily-actions")
st.subheader("Журнал действий в течении смены")
daily_rows = db.get_recent_daily_action_reports(limit=300)
if not daily_rows:
    st.info("Пока нет отчетов по действиям в течении дня")
else:
    daily_table = []
    for row in daily_rows:
        created_at_dt = pd.to_datetime(row["created_at"], errors="coerce")
        driver_name = (row["driver_full_name"] or "").strip() or "—"
        action_type_key = _daily_action_type_key(row["action_key"])
        daily_table.append(
            {
                "id": row["id"],
                "_created_at_dt": created_at_dt,
                "_date": created_at_dt.date() if pd.notna(created_at_dt) else None,
                "_driver": driver_name,
                "_action_type": action_type_key,
                "action_label": row["action_label"],
                "status_label": _daily_action_status_label(row["status_label"], row["status_key"]),
                "linked_inspection_label": row["linked_inspection_id"] or "—",
            }
        )

    daily_df = pd.DataFrame(daily_table)
    if daily_df["_date"].dropna().empty:
        min_daily_date = date.today()
        max_daily_date = date.today()
    else:
        min_daily_date = min(daily_df["_date"].dropna())
        max_daily_date = max(daily_df["_date"].dropna())

    if "daily_action_filter_date_from" not in st.session_state:
        st.session_state["daily_action_filter_date_from"] = min_daily_date
    if "daily_action_filter_date_to" not in st.session_state:
        st.session_state["daily_action_filter_date_to"] = max_daily_date
    if "daily_action_filter_driver" not in st.session_state:
        st.session_state["daily_action_filter_driver"] = "Все"
    if "daily_action_filter_type" not in st.session_state:
        st.session_state["daily_action_filter_type"] = "all"

    st.session_state["daily_action_filter_date_from"] = _clamp_date_filter(
        st.session_state["daily_action_filter_date_from"],
        min_daily_date,
        max_daily_date,
    )
    st.session_state["daily_action_filter_date_to"] = _clamp_date_filter(
        st.session_state["daily_action_filter_date_to"],
        min_daily_date,
        max_daily_date,
    )

    daily_driver_options = ["Все"] + sorted(
        [value for value in daily_df["_driver"].dropna().unique().tolist() if value and value != "—"]
    )
    if st.session_state["daily_action_filter_driver"] not in daily_driver_options:
        st.session_state["daily_action_filter_driver"] = "Все"

    daily_action_type_options = list(DAILY_ACTION_FILTER_LABELS_RU.keys())
    if st.session_state["daily_action_filter_type"] not in daily_action_type_options:
        st.session_state["daily_action_filter_type"] = "all"

    st.markdown("#### Фильтры")
    daily_date_from_col, daily_date_to_col, daily_driver_col, daily_type_col = st.columns(4)
    with daily_date_from_col:
        st.date_input(
            "Дата (от)",
            min_value=min_daily_date,
            max_value=max_daily_date,
            value=st.session_state["daily_action_filter_date_from"],
            key="daily_action_filter_date_from",
        )
    with daily_date_to_col:
        st.date_input(
            "Дата (до)",
            min_value=min_daily_date,
            max_value=max_daily_date,
            value=st.session_state["daily_action_filter_date_to"],
            key="daily_action_filter_date_to",
        )
    with daily_driver_col:
        st.selectbox("Водитель", daily_driver_options, key="daily_action_filter_driver")
    with daily_type_col:
        st.selectbox(
            "Тип действия",
            daily_action_type_options,
            key="daily_action_filter_type",
            format_func=_daily_action_type_filter_label,
        )

    filtered_daily_df = daily_df.copy()
    daily_date_from_filter = st.session_state["daily_action_filter_date_from"]
    daily_date_to_filter = st.session_state["daily_action_filter_date_to"]
    if daily_date_from_filter > daily_date_to_filter:
        daily_date_from_filter, daily_date_to_filter = daily_date_to_filter, daily_date_from_filter

    filtered_daily_df = filtered_daily_df[
        (filtered_daily_df["_date"].notna())
        & (filtered_daily_df["_date"] >= daily_date_from_filter)
        & (filtered_daily_df["_date"] <= daily_date_to_filter)
    ]

    selected_daily_driver = st.session_state["daily_action_filter_driver"]
    if selected_daily_driver != "Все":
        filtered_daily_df = filtered_daily_df[filtered_daily_df["_driver"] == selected_daily_driver]

    selected_daily_type = st.session_state["daily_action_filter_type"]
    if selected_daily_type != "all":
        filtered_daily_df = filtered_daily_df[filtered_daily_df["_action_type"] == selected_daily_type]

    filtered_daily_df = filtered_daily_df.sort_values(
        by=["_created_at_dt", "id"],
        ascending=[False, False],
        na_position="last",
    )
    st.caption(f"Показано: {len(filtered_daily_df)} из {len(daily_df)}")

    if filtered_daily_df.empty:
        st.info("По выбранным фильтрам действия не найдены")
    else:
        grouped_dates = filtered_daily_df["_date"].dropna().unique().tolist()
        for current_date in grouped_dates:
            st.markdown(f"#### 📅 {current_date.strftime('%d.%m.%Y')}")
            day_rows = filtered_daily_df[filtered_daily_df["_date"] == current_date]
            for _, day_row in day_rows.iterrows():
                time_label = "--:--"
                if pd.notna(day_row["_created_at_dt"]):
                    time_label = day_row["_created_at_dt"].strftime("%H:%M")
                st.markdown(
                    f"— **#{int(day_row['id'])}** {time_label} | {day_row['_driver']} | "
                    f"{day_row['action_label']} | статус: {day_row['status_label']} | "
                    f"ID приемки: {day_row['linked_inspection_label']}"
                )

daily_id = st.number_input("Открыть действие по ID", min_value=1, step=1, key="daily_action_id")
if st.button("Показать действие", key="show_daily_action"):
    action = db.get_daily_action_report(int(daily_id))
    if action is None:
        st.warning("Действие с таким ID не найдено")
    else:
        action_status_label = _daily_action_status_label(action["status_label"], action["status_key"])
        fuel_decision_label = _mechanic_decision_label(action["fuel_decision"])
        delivery_status_label = _delivery_status_label(action["delivery_status"])
        st.markdown(f"### Действие #{action['id']}")
        main_col, result_col = st.columns([2, 1])
        with main_col:
            with st.container(border=True):
                st.markdown("#### Основное")
                st.write(f"**Водитель:** {action['driver_full_name'] or '—'}")
                st.write(f"**Телефон:** {action['driver_phone'] or '—'}")
                st.write(f"**Тип действия:** {action['action_label'] or '—'}")
                st.write(f"**ID приемки:** {action['linked_inspection_id'] or '—'}")
                st.write(f"**Дата:** {action['created_at'] or '—'}")
        with result_col:
            with st.container(border=True):
                st.markdown("#### Результат")
                st.write(f"**Статус:** {action_status_label}")
                st.write(f"**Решение по ГСМ:** {fuel_decision_label}")
                st.write(f"**Статус доставки:** {delivery_status_label}")

        st.markdown("#### Комментарий")
        with st.container(border=True):
            if action["comment"]:
                st.write(action["comment"])
            else:
                st.caption("Комментарий отсутствует")

        action_images: list[dict[str, str]] = []
        for photo in db.get_daily_action_report_photos(int(action["id"])):
            path = Path(str(photo["file_path"]))
            if path.exists():
                action_images.append(
                    {
                        "path": str(path),
                        "caption": _daily_action_photo_caption(photo["photo_type"]),
                    }
                )
        if not action_images and action["photo_path"] and Path(action["photo_path"]).exists():
            action_images.append(
                {
                    "path": action["photo_path"],
                    "caption": "Фото к действию",
                }
            )
        if action_images:
            st.markdown("#### Фото к действию")
            _render_images_in_single_row(action_images)

st.divider()
_render_section_anchor("section-equipment-panel")
st.subheader("Панель техники")
equipment_panel_rows = db.list_equipment_catalog_for_dashboard()
if not equipment_panel_rows:
    st.info("Пока нет техники в каталоге")
else:
    equipment_catalog_table: list[dict[str, object]] = []
    for row in equipment_panel_rows:
        equipment_catalog_table.append(
            {
                "ID": row["id"],
                "Техника": _equipment_label(row["type"], row["brand"], row["reg_number"]),
                "Активна": "Да" if int(row["is_active"] or 0) == 1 else "Нет",
                "Проверок": int(row["inspections_count"] or 0),
                "Последняя проверка": pd.to_datetime(row["last_inspection_at"], errors="coerce"),
            }
        )

    st.markdown("#### Полный список техники")
    st.dataframe(
        equipment_catalog_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Последняя проверка": st.column_config.DatetimeColumn(
                "Последняя проверка",
                format="YYYY-MM-DD HH:mm:ss",
            ),
        },
    )

    if "equipment_panel_selected_id" not in st.session_state:
        st.session_state["equipment_panel_selected_id"] = None

    st.markdown("#### Техника")
    equipment_by_type: dict[str, list[object]] = {}
    for row in equipment_panel_rows:
        equipment_type = (row["type"] or "").strip() or "Без типа"
        if equipment_type not in equipment_by_type:
            equipment_by_type[equipment_type] = []
        equipment_by_type[equipment_type].append(row)

    for equipment_type in sorted(equipment_by_type.keys(), key=lambda value: value.lower()):
        type_rows = equipment_by_type[equipment_type]
        with st.expander(f"📂 {equipment_type} ({len(type_rows)})", expanded=False):
            type_button_columns = st.columns(2)
            for index, row in enumerate(type_rows):
                short_name = " ".join(
                    [
                        part
                        for part in [str(row["brand"] or "").strip(), str(row["reg_number"] or "").strip()]
                        if part
                    ]
                )
                equipment_name = short_name or _equipment_label(
                    row["type"], row["brand"], row["reg_number"]
                )
                checks_label = int(row["inspections_count"] or 0)
                is_active_label = "активна" if int(row["is_active"] or 0) == 1 else "не активна"
                with type_button_columns[index % 2]:
                    if st.button(
                        f"🚜 {equipment_name}\nПроверок: {checks_label} • {is_active_label}",
                        key=f"equipment_panel_select_{row['id']}",
                        use_container_width=True,
                    ):
                        st.session_state["equipment_panel_selected_id"] = int(row["id"])

    selected_equipment_id = _parse_positive_int(st.session_state["equipment_panel_selected_id"])
    if selected_equipment_id is not None:
        _render_equipment_details_panel(selected_equipment_id)

st.divider()
_render_section_anchor("section-driver-panel")
st.subheader("Панель водителей")
driver_panel_rows = db.list_drivers_for_dashboard()
if not driver_panel_rows:
    st.info("Пока нет данных по водителям")
else:
    drivers_table: list[dict[str, object]] = []
    selectable_driver_rows = []
    for row in driver_panel_rows:
        driver_id = _parse_positive_int(row["driver_telegram_id"])
        if driver_id is None:
            continue
        selectable_driver_rows.append(row)
        driver_name = (row["driver_full_name"] or "").strip() or f"ID {driver_id}"
        shifts_count = int(row["shifts_count"] or 0)
        issues_count = int(row["issues_count"] or 0)
        ok_count = int(row["ok_count"] or 0)
        total_items_count = int(row["total_items_count"] or 0)
        drivers_table.append(
            {
                "ID": driver_id,
                "Водитель": driver_name,
                "Телефон": row["driver_phone"] or "—",
                "Смен": shifts_count,
                "Косяков": issues_count,
                "Рейтинг": _driver_rating_cell_value(ok_count, total_items_count),
                "Последняя смена": pd.to_datetime(row["last_shift_at"], errors="coerce"),
            }
        )

    st.markdown("#### Все водители")
    drivers_df = pd.DataFrame(drivers_table)
    styled_drivers_df = drivers_df.style.applymap(
        _driver_rating_cell_style,
        subset=["Рейтинг"],
    )
    st.dataframe(
        styled_drivers_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Последняя смена": st.column_config.DatetimeColumn(
                "Последняя смена",
                format="YYYY-MM-DD HH:mm:ss",
            ),
        },
    )

    if "driver_panel_selected_id" not in st.session_state:
        st.session_state["driver_panel_selected_id"] = None

    st.markdown("#### Клик по водителю")
    driver_button_columns = st.columns(3)
    for index, row in enumerate(selectable_driver_rows):
        driver_id = int(row["driver_telegram_id"])
        driver_name = (row["driver_full_name"] or "").strip() or f"ID {driver_id}"
        shifts_count = int(row["shifts_count"] or 0)
        with driver_button_columns[index % 3]:
            if st.button(
                f"👤 {driver_name}\nСмен: {shifts_count}",
                key=f"driver_panel_select_{driver_id}",
                use_container_width=True,
            ):
                st.session_state["driver_panel_selected_id"] = driver_id

    selected_driver_id = _parse_positive_int(st.session_state["driver_panel_selected_id"])
    if selected_driver_id is not None:
        _render_driver_details_panel(selected_driver_id)
