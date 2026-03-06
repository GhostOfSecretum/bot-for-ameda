from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.constants import ALLOWED_ROLES, DEFAULT_EQUIPMENT, HIDDEN_EQUIPMENT_TYPES


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    full_name TEXT,
                    phone TEXT,
                    role TEXT NOT NULL DEFAULT 'driver',
                    language TEXT NOT NULL DEFAULT 'ru',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    reg_number TEXT NOT NULL UNIQUE,
                    is_active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_telegram_id INTEGER NOT NULL,
                    driver_full_name TEXT NOT NULL,
                    driver_phone TEXT,
                    driver_latitude REAL,
                    driver_longitude REAL,
                    driver_location_at TEXT,
                    equipment_id INTEGER NOT NULL,
                    equipment_snapshot TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'draft',
                    mechanic_decision TEXT,
                    mechanic_telegram_id INTEGER,
                    mechanic_comment TEXT,
                    mechanic_decision_at TEXT,
                    mechanic_message_id INTEGER,
                    FOREIGN KEY(driver_telegram_id) REFERENCES users(telegram_id),
                    FOREIGN KEY(equipment_id) REFERENCES equipment(id)
                );

                CREATE TABLE IF NOT EXISTS inspection_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inspection_id INTEGER NOT NULL,
                    item_order INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    is_ok INTEGER NOT NULL,
                    comment TEXT,
                    issue_photo_path TEXT,
                    FOREIGN KEY(inspection_id) REFERENCES inspections(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS inspection_required_photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inspection_id INTEGER NOT NULL,
                    photo_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    FOREIGN KEY(inspection_id) REFERENCES inspections(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_telegram_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS daily_action_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_telegram_id INTEGER NOT NULL,
                    driver_full_name TEXT NOT NULL,
                    driver_phone TEXT,
                    action_key TEXT NOT NULL,
                    action_label TEXT NOT NULL,
                    status_key TEXT,
                    status_label TEXT,
                    comment TEXT,
                    photo_path TEXT,
                    linked_inspection_id INTEGER,
                    created_at TEXT NOT NULL,
                    delivered_at TEXT,
                    delivery_status TEXT NOT NULL DEFAULT 'pending',
                    mechanic_message_id INTEGER,
                    fuel_decision TEXT,
                    fuel_decision_by INTEGER,
                    fuel_decision_at TEXT,
                    FOREIGN KEY(driver_telegram_id) REFERENCES users(telegram_id)
                );
                """
            )

            user_columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
            if "phone" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            if "language" not in user_columns:
                conn.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'ru'")

            inspection_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(inspections)").fetchall()
            }
            if "driver_phone" not in inspection_columns:
                conn.execute("ALTER TABLE inspections ADD COLUMN driver_phone TEXT")
            if "driver_latitude" not in inspection_columns:
                conn.execute("ALTER TABLE inspections ADD COLUMN driver_latitude REAL")
            if "driver_longitude" not in inspection_columns:
                conn.execute("ALTER TABLE inspections ADD COLUMN driver_longitude REAL")
            if "driver_location_at" not in inspection_columns:
                conn.execute("ALTER TABLE inspections ADD COLUMN driver_location_at TEXT")

            daily_action_columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(daily_action_reports)").fetchall()
            }
            if "linked_inspection_id" not in daily_action_columns:
                conn.execute(
                    "ALTER TABLE daily_action_reports ADD COLUMN linked_inspection_id INTEGER"
                )
            if "fuel_decision" not in daily_action_columns:
                conn.execute("ALTER TABLE daily_action_reports ADD COLUMN fuel_decision TEXT")
            if "fuel_decision_by" not in daily_action_columns:
                conn.execute("ALTER TABLE daily_action_reports ADD COLUMN fuel_decision_by INTEGER")
            if "fuel_decision_at" not in daily_action_columns:
                conn.execute("ALTER TABLE daily_action_reports ADD COLUMN fuel_decision_at TEXT")

            # Seed техники для теста
            existing_count = conn.execute("SELECT COUNT(*) AS c FROM equipment").fetchone()["c"]
            if existing_count == 0:
                conn.executemany(
                    "INSERT INTO equipment (type, brand, reg_number, is_active) VALUES (?, ?, ?, 1)",
                    DEFAULT_EQUIPMENT,
                )
            for equipment_type in HIDDEN_EQUIPMENT_TYPES:
                conn.execute(
                    "UPDATE equipment SET is_active = 0 WHERE type = ?",
                    (equipment_type,),
                )

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat(timespec="seconds")

    def upsert_user(
        self,
        telegram_id: int,
        full_name: str | None = None,
        phone: str | None = None,
        role: str | None = None,
        language: str | None = None,
    ) -> None:
        if role is not None and role not in ALLOWED_ROLES:
            raise ValueError(f"Unsupported role: {role}")

        with self._connect() as conn:
            row = conn.execute(
                "SELECT telegram_id, full_name, phone, role, language FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()
            now = self._now()
            if row:
                next_full_name = full_name if full_name is not None else row["full_name"]
                next_phone = phone if phone is not None else row["phone"]
                next_role = role if role is not None else row["role"]
                next_language = language if language is not None else row["language"]
                conn.execute(
                    """
                    UPDATE users
                    SET full_name = ?, phone = ?, role = ?, language = ?, updated_at = ?, is_active = 1
                    WHERE telegram_id = ?
                    """,
                    (next_full_name, next_phone, next_role, next_language, now, telegram_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO users (
                        telegram_id, full_name, phone, role, language, is_active, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (telegram_id, full_name, phone, role or "driver", language or "ru", now, now),
                )

    def get_user(self, telegram_id: int) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE telegram_id = ? AND is_active = 1",
                (telegram_id,),
            ).fetchone()

    def list_equipment_types(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT type FROM equipment WHERE is_active = 1 ORDER BY type"
            ).fetchall()
        return [r["type"] for r in rows if r["type"] not in HIDDEN_EQUIPMENT_TYPES]

    def list_brands(self, equipment_type: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT brand FROM equipment
                WHERE is_active = 1 AND type = ?
                ORDER BY brand
                """,
                (equipment_type,),
            ).fetchall()
        return [r["brand"] for r in rows]

    def list_numbers(self, equipment_type: str, brand: str) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT id, reg_number FROM equipment
                WHERE is_active = 1 AND type = ? AND brand = ?
                ORDER BY reg_number
                """,
                (equipment_type, brand),
            ).fetchall()

    def get_equipment(self, equipment_id: int) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM equipment WHERE id = ?",
                (equipment_id,),
            ).fetchone()

    def create_inspection(
        self,
        driver_telegram_id: int,
        driver_full_name: str,
        driver_phone: str | None,
        equipment_id: int,
        equipment_snapshot: str,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO inspections (
                    driver_telegram_id, driver_full_name, driver_phone, equipment_id, equipment_snapshot, started_at, status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'draft')
                """,
                (
                    driver_telegram_id,
                    driver_full_name,
                    driver_phone,
                    equipment_id,
                    equipment_snapshot,
                    self._now(),
                ),
            )
            return int(cur.lastrowid)

    def add_inspection_item(
        self,
        inspection_id: int,
        item_order: int,
        item_name: str,
        is_ok: bool,
        comment: str | None,
        issue_photo_path: str | None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM inspection_items
                WHERE inspection_id = ? AND item_order = ?
                """,
                (inspection_id, item_order),
            )
            conn.execute(
                """
                INSERT INTO inspection_items (
                    inspection_id, item_order, item_name, is_ok, comment, issue_photo_path
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (inspection_id, item_order, item_name, int(is_ok), comment, issue_photo_path),
            )

    def delete_inspection_item(self, inspection_id: int, item_order: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """
                DELETE FROM inspection_items
                WHERE inspection_id = ? AND item_order = ?
                """,
                (inspection_id, item_order),
            )
            return cur.rowcount > 0

    def add_required_photo(self, inspection_id: int, photo_type: str, file_path: str) -> None:
        with self._connect() as conn:
            existing = conn.execute(
                """
                SELECT id FROM inspection_required_photos
                WHERE inspection_id = ? AND photo_type = ?
                """,
                (inspection_id, photo_type),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE inspection_required_photos SET file_path = ? WHERE id = ?",
                    (file_path, existing["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO inspection_required_photos (inspection_id, photo_type, file_path)
                    VALUES (?, ?, ?)
                    """,
                    (inspection_id, photo_type, file_path),
                )

    def get_required_photos(self, inspection_id: int) -> dict[str, str]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT photo_type, file_path
                FROM inspection_required_photos
                WHERE inspection_id = ?
                """,
                (inspection_id,),
            ).fetchall()
        return {r["photo_type"]: r["file_path"] for r in rows}

    def set_inspection_location(self, inspection_id: int, latitude: float, longitude: float) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE inspections
                SET driver_latitude = ?,
                    driver_longitude = ?,
                    driver_location_at = ?
                WHERE id = ?
                """,
                (latitude, longitude, self._now(), inspection_id),
            )

    def complete_inspection(self, inspection_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE inspections
                SET status = 'submitted', completed_at = ?
                WHERE id = ?
                """,
                (self._now(), inspection_id),
            )

    def set_mechanic_message(self, inspection_id: int, message_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE inspections SET mechanic_message_id = ? WHERE id = ?",
                (message_id, inspection_id),
            )

    def get_inspection_summary(self, inspection_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            inspection = conn.execute(
                "SELECT * FROM inspections WHERE id = ?",
                (inspection_id,),
            ).fetchone()
            if not inspection:
                raise ValueError("Inspection not found")

            items = conn.execute(
                """
                SELECT item_name, is_ok, comment, issue_photo_path
                FROM inspection_items
                WHERE inspection_id = ?
                ORDER BY item_order
                """,
                (inspection_id,),
            ).fetchall()
            photos = conn.execute(
                """
                SELECT photo_type, file_path
                FROM inspection_required_photos
                WHERE inspection_id = ?
                ORDER BY id
                """,
                (inspection_id,),
            ).fetchall()

        ok_count = sum(1 for i in items if i["is_ok"] == 1)
        nok_count = sum(1 for i in items if i["is_ok"] == 0)

        return {
            "inspection": dict(inspection),
            "items": [dict(i) for i in items],
            "required_photos": [dict(p) for p in photos],
            "ok_count": ok_count,
            "nok_count": nok_count,
        }

    def set_mechanic_decision(
        self,
        inspection_id: int,
        mechanic_telegram_id: int,
        decision: str,
        comment: str | None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE inspections
                SET status = 'closed',
                    mechanic_decision = ?,
                    mechanic_telegram_id = ?,
                    mechanic_comment = ?,
                    mechanic_decision_at = ?
                WHERE id = ?
                """,
                (decision, mechanic_telegram_id, comment, self._now(), inspection_id),
            )

    def get_inspection(self, inspection_id: int) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM inspections WHERE id = ?",
                (inspection_id,),
            ).fetchone()

    def get_recent_inspections(self, limit: int = 100) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT i.*, e.type, e.brand, e.reg_number
                FROM inspections i
                JOIN equipment e ON e.id = i.equipment_id
                ORDER BY i.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def get_latest_submitted_inspection_id_for_driver(self, driver_telegram_id: int) -> int | None:
        row = self.get_latest_submitted_inspection_for_driver(driver_telegram_id)
        if row is None:
            return None
        return int(row["id"])

    def get_latest_submitted_inspection_for_driver(
        self,
        driver_telegram_id: int,
    ) -> sqlite3.Row | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, mechanic_message_id
                FROM inspections
                WHERE driver_telegram_id = ?
                  AND status IN ('submitted', 'closed')
                ORDER BY id DESC
                LIMIT 1
                """,
                (driver_telegram_id,),
            ).fetchone()
        return row

    def create_daily_action_report(
        self,
        *,
        driver_telegram_id: int,
        driver_full_name: str,
        driver_phone: str | None,
        action_key: str,
        action_label: str,
        status_key: str | None,
        status_label: str | None,
        comment: str | None,
        photo_path: str | None,
        linked_inspection_id: int | None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO daily_action_reports (
                    driver_telegram_id,
                    driver_full_name,
                    driver_phone,
                    action_key,
                    action_label,
                    status_key,
                    status_label,
                    comment,
                    photo_path,
                    linked_inspection_id,
                    created_at,
                    delivery_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (
                    driver_telegram_id,
                    driver_full_name,
                    driver_phone,
                    action_key,
                    action_label,
                    status_key,
                    status_label,
                    comment,
                    photo_path,
                    linked_inspection_id,
                    self._now(),
                ),
            )
            return int(cur.lastrowid)

    def mark_daily_action_report_delivery(
        self,
        report_id: int,
        *,
        status: str,
        mechanic_message_id: int | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE daily_action_reports
                SET delivery_status = ?,
                    delivered_at = ?,
                    mechanic_message_id = COALESCE(?, mechanic_message_id)
                WHERE id = ?
                """,
                (status, self._now(), mechanic_message_id, report_id),
            )

    def get_recent_daily_action_reports(self, limit: int = 100) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT *
                FROM daily_action_reports
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def get_daily_action_report(self, report_id: int) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT *
                FROM daily_action_reports
                WHERE id = ?
                """,
                (report_id,),
            ).fetchone()

    def set_daily_action_fuel_decision(
        self,
        report_id: int,
        *,
        mechanic_telegram_id: int,
        decision: str,
    ) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE daily_action_reports
                SET fuel_decision = ?,
                    fuel_decision_by = ?,
                    fuel_decision_at = ?
                WHERE id = ?
                  AND action_key = 'refuel'
                  AND fuel_decision IS NULL
                """,
                (decision, mechanic_telegram_id, self._now(), report_id),
            )
            return cur.rowcount > 0

    def get_inspection_details_for_dashboard(self, inspection_id: int) -> dict[str, Any]:
        summary = self.get_inspection_summary(inspection_id)
        with self._connect() as conn:
            equipment = conn.execute(
                """
                SELECT e.type, e.brand, e.reg_number
                FROM inspections i
                JOIN equipment e ON e.id = i.equipment_id
                WHERE i.id = ?
                """,
                (inspection_id,),
            ).fetchone()
        summary["equipment"] = dict(equipment) if equipment else {}
        return summary

    def add_audit(
        self,
        actor_telegram_id: int,
        action: str,
        entity_type: str,
        entity_id: str,
        details: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (
                    actor_telegram_id, action, entity_type, entity_id, details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (actor_telegram_id, action, entity_type, entity_id, details, self._now()),
            )

    def set_role(self, actor_telegram_id: int, target_telegram_id: int, role: str) -> None:
        if role not in ALLOWED_ROLES:
            raise ValueError("Invalid role")
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT telegram_id FROM users WHERE telegram_id = ?",
                (target_telegram_id,),
            ).fetchone()
            now = self._now()
            if existing:
                conn.execute(
                    "UPDATE users SET role = ?, updated_at = ? WHERE telegram_id = ?",
                    (role, now, target_telegram_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO users (telegram_id, full_name, role, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, 1, ?, ?)
                    """,
                    (target_telegram_id, None, role, now, now),
                )
        self.add_audit(
            actor_telegram_id=actor_telegram_id,
            action="set_role",
            entity_type="user",
            entity_id=str(target_telegram_id),
            details=f"role={role}",
        )
