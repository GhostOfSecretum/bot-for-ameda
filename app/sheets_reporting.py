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
        self._ensure_headers()

    def append_report(self, summary: dict[str, Any]) -> None:
        row = self._build_report_row(summary)
        self.reports_sheet.append_row(row, value_input_option="USER_ENTERED")
        self._rebuild_grouped_sheet()

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
