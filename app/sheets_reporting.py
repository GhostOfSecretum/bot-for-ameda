from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

from app.time_utils import now_iso

logger = logging.getLogger(__name__)

REPORTS_SHEET_TITLE = "Отчеты"
GROUPED_SHEET_TITLE = "Группировка"
END_WORKDAY_SHEET_TITLE = "Завершение смены"
DAILY_ACTIONS_SHEET_TITLE = "Действия в течении дня"

REPORT_HEADERS = [
    "ID отчета",
    "Дата отчета",
    "Сотрудник",
    "Телефон",
    "Техника",
    "Геолокация",
    "OK",
    "NOK",
    "Группа",
    "Кол-во замечаний",
    "Замечания",
    "Комментарии",
    "Обязательных фото",
    "Карточка отчета",
    "Экспортировано в",
]

GROUPED_HEADERS = [
    "Дата отчета",
    "Сотрудник",
    "Техника",
    "Группа",
    "Кол-во отчетов",
    "Сумма замечаний",
]

END_WORKDAY_HEADERS = [
    "ID отчета действий",
    "Дата отчета",
    "Время отчета",
    "Сотрудник",
    "Телефон",
    "Статус заправки (ключ)",
    "Статус заправки",
    "Комментарий",
    "Геолокация",
    "Связанная приемка",
    "Статус доставки",
    "ID сообщения в группе",
    "Фото ГСМ",
    "Обязательных фото",
    "Всего фото",
    "Экспортировано в",
]

DAILY_ACTION_HEADERS = [
    "ID отчета действий",
    "Дата отчета",
    "Время отчета",
    "Сотрудник",
    "Телефон",
    "Действие (ключ)",
    "Действие",
    "Статус (ключ)",
    "Статус",
    "Комментарий",
    "Связанная приемка",
    "Статус доставки",
    "ID сообщения в группе",
    "Фото",
    "Решение по ГСМ",
    "Кто решил ГСМ",
    "Время решения ГСМ",
    "Экспортировано в",
]


class GoogleSheetsReporter:
    def __init__(
        self,
        spreadsheet_id: str,
        credentials_path: Path,
        admin_dashboard_base_url: str | None = None,
    ) -> None:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
        ]
        credentials = Credentials.from_service_account_file(
            str(credentials_path),
            scopes=scopes,
        )
        client = gspread.authorize(credentials)
        self.spreadsheet = client.open_by_key(spreadsheet_id)
        self.admin_dashboard_base_url = admin_dashboard_base_url.rstrip("/") if admin_dashboard_base_url else None
        self.reports_sheet = self._get_or_create_sheet(REPORTS_SHEET_TITLE, rows=1000, cols=20)
        self.grouped_sheet = self._get_or_create_sheet(GROUPED_SHEET_TITLE, rows=1000, cols=12)
        self.end_workday_sheet = self._get_or_create_sheet(
            END_WORKDAY_SHEET_TITLE,
            rows=1000,
            cols=20,
        )
        self.daily_actions_sheet = self._get_or_create_sheet(
            DAILY_ACTIONS_SHEET_TITLE,
            rows=1000,
            cols=24,
        )
        self._ensure_headers()

    def append_report(self, summary: dict[str, Any]) -> None:
        row = self._build_report_row(summary)
        self.reports_sheet.append_row(row, value_input_option="USER_ENTERED")
        self._rebuild_grouped_sheet()

    def append_end_workday_report(self, summary: dict[str, Any]) -> None:
        row = self._build_end_workday_row(summary)
        self.end_workday_sheet.append_row(row, value_input_option="USER_ENTERED")

    def append_daily_action_report(self, report: dict[str, Any]) -> None:
        row = self._build_daily_action_row(report)
        self.daily_actions_sheet.append_row(row, value_input_option="USER_ENTERED")

    def _get_or_create_sheet(self, title: str, *, rows: int, cols: int):
        try:
            return self.spreadsheet.worksheet(title)
        except WorksheetNotFound:
            logger.info("Worksheet '%s' not found. Creating it.", title)
            return self.spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)

    def _ensure_headers(self) -> None:
        report_header_row = self.reports_sheet.row_values(1)
        if report_header_row[: len(REPORT_HEADERS)] != REPORT_HEADERS:
            self.reports_sheet.update("A1", [REPORT_HEADERS])

        grouped_header_row = self.grouped_sheet.row_values(1)
        if grouped_header_row[: len(GROUPED_HEADERS)] != GROUPED_HEADERS:
            self.grouped_sheet.update("A1", [GROUPED_HEADERS])

        end_workday_header_row = self.end_workday_sheet.row_values(1)
        if end_workday_header_row[: len(END_WORKDAY_HEADERS)] != END_WORKDAY_HEADERS:
            self.end_workday_sheet.update("A1", [END_WORKDAY_HEADERS])

        daily_action_header_row = self.daily_actions_sheet.row_values(1)
        if daily_action_header_row[: len(DAILY_ACTION_HEADERS)] != DAILY_ACTION_HEADERS:
            self.daily_actions_sheet.update("A1", [DAILY_ACTION_HEADERS])

    def _build_report_row(self, summary: dict[str, Any]) -> list[str]:
        inspection = summary["inspection"]
        items: list[dict[str, Any]] = summary["items"]
        required_photos: list[dict[str, Any]] = summary["required_photos"]

        latitude = inspection.get("driver_latitude")
        longitude = inspection.get("driver_longitude")
        if latitude is None or longitude is None:
            geo_text = "-"
        else:
            lat = float(latitude)
            lon = float(longitude)
            coords_label = f"{lat:.6f}, {lon:.6f}"
            map_url = f"https://maps.google.com/?q={lat:.6f},{lon:.6f}"
            geo_text = f'=HYPERLINK("{map_url}"; "{coords_label}")'

        nok_items = [item for item in items if item.get("is_ok") == 0]
        issue_names = "; ".join(item.get("item_name", "") for item in nok_items if item.get("item_name"))
        issue_comments = "; ".join(
            item.get("comment", "").strip() for item in nok_items if (item.get("comment") or "").strip()
        )

        started_at = str(inspection.get("started_at") or "")
        report_date = started_at.split("T", maxsplit=1)[0] if started_at else ""
        group_label = "Без замечаний" if summary["nok_count"] == 0 else "С замечаниями"
        inspection_id = str(inspection.get("id") or "")
        dashboard_link = self._build_dashboard_link(inspection_id=inspection_id)

        return [
            inspection_id,
            report_date,
            str(inspection.get("driver_full_name") or ""),
            str(inspection.get("driver_phone") or ""),
            str(inspection.get("equipment_snapshot") or ""),
            geo_text,
            str(summary["ok_count"]),
            str(summary["nok_count"]),
            group_label,
            str(len(nok_items)),
            issue_names,
            issue_comments,
            str(len(required_photos)),
            dashboard_link,
            now_iso(timespec="seconds"),
        ]

    def _build_dashboard_link(self, inspection_id: str) -> str:
        if not self.admin_dashboard_base_url or not inspection_id:
            return "-"
        try:
            parsed = urlsplit(self.admin_dashboard_base_url)
            query_items = parse_qsl(parsed.query, keep_blank_values=True)
            filtered_items = [(key, value) for key, value in query_items if key != "inspection_id"]
            filtered_items.append(("inspection_id", inspection_id))
            query = urlencode(filtered_items)
            target_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))
            return f'=HYPERLINK("{target_url}"; "Открыть")'
        except Exception:
            logger.exception("Failed to build dashboard URL for inspection_id=%s", inspection_id)
            return "-"

    def _build_end_workday_row(self, summary: dict[str, Any]) -> list[str]:
        report = summary["report"]

        created_at = str(report.get("created_at") or "")
        report_date = created_at.split("T", maxsplit=1)[0] if created_at else ""
        report_time = created_at.split("T", maxsplit=1)[1] if "T" in created_at else ""

        location = summary.get("location")
        latitude: float | None = None
        longitude: float | None = None
        if isinstance(location, (tuple, list)) and len(location) == 2:
            try:
                latitude = float(location[0])
                longitude = float(location[1])
            except (TypeError, ValueError):
                latitude = None
                longitude = None

        geo_text = "-"
        if latitude is not None and longitude is not None:
            coords_label = f"{latitude:.6f}, {longitude:.6f}"
            map_url = f"https://maps.google.com/?q={latitude:.6f},{longitude:.6f}"
            geo_text = f'=HYPERLINK("{map_url}"; "{coords_label}")'

        linked_inspection_id = report.get("linked_inspection_id")
        linked_inspection_ref = (
            f"#{linked_inspection_id}" if linked_inspection_id is not None else "—"
        )

        required_photo_count = int(summary.get("required_photo_count") or 0)
        total_photo_count = int(summary.get("total_photo_count") or 0)
        fuel_photo_exists = "Да" if str(report.get("photo_path") or "").strip() else "Нет"

        return [
            str(report.get("id") or ""),
            report_date,
            report_time,
            str(report.get("driver_full_name") or ""),
            str(report.get("driver_phone") or ""),
            str(report.get("status_key") or ""),
            str(report.get("status_label") or ""),
            str(report.get("comment") or ""),
            geo_text,
            linked_inspection_ref,
            str(report.get("delivery_status") or ""),
            str(report.get("mechanic_message_id") or ""),
            fuel_photo_exists,
            str(required_photo_count),
            str(total_photo_count),
            now_iso(timespec="seconds"),
        ]

    def _build_daily_action_row(self, report: dict[str, Any]) -> list[str]:
        created_at = str(report.get("created_at") or "")
        report_date = created_at.split("T", maxsplit=1)[0] if created_at else ""
        report_time = created_at.split("T", maxsplit=1)[1] if "T" in created_at else ""

        linked_inspection_id = report.get("linked_inspection_id")
        linked_inspection_ref = (
            f"#{linked_inspection_id}" if linked_inspection_id is not None else "—"
        )

        photo_exists = "Да" if str(report.get("photo_path") or "").strip() else "Нет"

        return [
            str(report.get("id") or ""),
            report_date,
            report_time,
            str(report.get("driver_full_name") or ""),
            str(report.get("driver_phone") or ""),
            str(report.get("action_key") or ""),
            str(report.get("action_label") or ""),
            str(report.get("status_key") or ""),
            str(report.get("status_label") or ""),
            str(report.get("comment") or ""),
            linked_inspection_ref,
            str(report.get("delivery_status") or ""),
            str(report.get("mechanic_message_id") or ""),
            photo_exists,
            str(report.get("fuel_decision") or ""),
            str(report.get("fuel_decision_by") or ""),
            str(report.get("fuel_decision_at") or ""),
            now_iso(timespec="seconds"),
        ]

    def _rebuild_grouped_sheet(self) -> None:
        records = self.reports_sheet.get_all_records(default_blank="")
        grouped: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(
            lambda: {"reports": 0, "issues": 0}
        )

        for row in records:
            report_date = str(row.get("Дата отчета") or "")
            driver_name = str(row.get("Сотрудник") or "")
            equipment = str(row.get("Техника") or "")
            group_label = str(row.get("Группа") or "")

            issue_count_raw = row.get("Кол-во замечаний")
            try:
                issue_count = int(str(issue_count_raw).strip() or "0")
            except ValueError:
                issue_count = 0

            key = (report_date, driver_name, equipment, group_label)
            grouped[key]["reports"] += 1
            grouped[key]["issues"] += issue_count

        grouped_rows = [
            [
                report_date,
                driver_name,
                equipment,
                group_label,
                str(stats["reports"]),
                str(stats["issues"]),
            ]
            for (report_date, driver_name, equipment, group_label), stats in grouped.items()
        ]
        grouped_rows.sort(key=lambda row: (row[0], row[1], row[2], row[3]), reverse=True)

        self.grouped_sheet.clear()
        self.grouped_sheet.update("A1", [GROUPED_HEADERS] + grouped_rows)
