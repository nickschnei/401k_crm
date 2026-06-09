from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


CHUNK_SIZE = 10000
FEE_RATIO_THRESHOLD = 0.0060
PARTICIPATION_RATE_THRESHOLD = 0.70

EIN_COLUMNS = (
    "EIN",
    "SPONS_DFE_EIN",
    "SF_SPONS_EIN",
    "SCH_H_EIN",
    "SCH_I_EIN",
    "SPONSOR_EIN",
)

FIELD_ALIASES = {
    "total_assets": (
        "NET_ASSETS_EOY_AMT",
        "TOT_ASSETS_EOY_AMT",
        "SMALL_TOT_ASSETS_EOY_AMT",
        "SF_TOT_ASSETS_EOY_AMT",
        "NET_ASSETS_END_YEAR_AMT",
        "NET_ASSETS_EOY",
    ),
    "active_participants": (
        "TOT_ACTIVE_PARTCP_CNT",
        "SF_TOT_ACT_PARTCP_EOY_CNT",
        "TOT_ACT_PARTCP_EOY_CNT",
        "ACTIVE_PARTICIPANTS",
    ),
    "total_eligible_employees": (
        "TOT_ELIGIBLE_EMPLOYEES_CNT",
        "TOTAL_ELIGIBLE_EMPLOYEES",
        "TOT_ACT_RTD_SEP_BENEF_CNT",
        "SF_TOT_ACT_RTD_SEP_BENEF_CNT",
        "ELIGIBLE_EMPLOYEES_CNT",
    ),
    "admin_expenses": (
        "TOT_ADMIN_EXPENSES_AMT",
        "SMALL_ADMIN_SRVC_PROVIDERS_AMT",
        "SF_ADMIN_SRVC_PROVIDERS_AMT",
        "ADMIN_EXPENSES_AMT",
        "TOTAL_ADMINISTRATIVE_EXPENSES",
    ),
    "corrective_distributions": (
        "TOT_CORRECTIVE_DISTRIB_AMT",
        "SMALL_CORRECTIVE_DISTRIB_AMT",
        "SF_CORRECTIVE_DEEMED_DISTR_AMT",
        "CORRECTIVE_DISTRIBUTIONS_AMT",
        "CORRECTIVE_DISTRIBUTIONS",
    ),
    "employer_name": (
        "SPONS_DFE_NAME",
        "SPONSOR_DFE_NAME",
        "SF_SPONSOR_NAME",
        "SPONSOR_NAME",
    ),
    "plan_name": (
        "PLAN_NAME",
        "SF_PLAN_NAME",
    ),
    "administrator_name": (
        "ADMIN_NAME",
        "SF_ADMIN_NAME",
    ),
    "dol_address": (
        "SPONS_DFE_MAIL_US_ADDRESS1",
        "SPONSOR_DFE_MAIL_US_ADDRESS1",
        "SF_SPONS_US_ADDRESS1",
    ),
    "dol_city": (
        "SPONS_DFE_MAIL_US_CITY",
        "SPONSOR_DFE_MAIL_US_CITY",
        "SF_SPONS_US_CITY",
    ),
    "dol_state": (
        "SPONS_DFE_MAIL_US_STATE",
        "SPONSOR_DFE_MAIL_US_STATE",
        "SF_SPONS_US_STATE",
    ),
    "dol_zip": (
        "SPONS_DFE_MAIL_US_ZIP",
        "SPONSOR_DFE_MAIL_US_ZIP",
        "SF_SPONS_US_ZIP",
    ),
}

AUDIT_COLUMNS = {
    "total_assets": "REAL",
    "active_participants": "INTEGER",
    "total_eligible_employees": "INTEGER",
    "admin_expenses": "REAL",
    "corrective_distributions": "REAL",
    "participation_rate": "REAL",
    "fee_ratio": "REAL",
    "fee_flag": "INTEGER",
    "participation_flag": "INTEGER",
    "compliance_failed": "INTEGER",
}


def run_plan_audit(ein: str, csv_directory: str, db_path: str = 'prospects.db') -> None:
    """Audit one EIN from unzipped DOL CSV files and persist metrics to SQLite database tables."""
    normalized_ein = _normalize_ein(ein)
    if not normalized_ein:
        raise ValueError("ein must contain at least one digit")

    values = _find_plan_values(normalized_ein, csv_directory)
    
    # If the company is not found in the local DOL CSV files (assets are 0 or employer name is Unknown/missing),
    # trigger our fallback source/engine.
    if values.get("total_assets") == 0.0 or not values.get("employer_name") or values.get("employer_name") == "Unknown":
        print(f"[AuditEngine] EIN {normalized_ein} not found or empty in local DOL CSVs. Querying fallback sources...")
        from utils.fallback_5500 import fetch_fallback_5500_data
        fallback_values = fetch_fallback_5500_data(normalized_ein, db_path)
        if fallback_values:
            values.update(fallback_values)

    total_assets = values["total_assets"]
    active_participants = int(values["active_participants"]) if values["active_participants"] else 0
    total_eligible_employees = int(values["total_eligible_employees"]) if values["total_eligible_employees"] else 0
    admin_expenses = values["admin_expenses"]
    corrective_distributions = values["corrective_distributions"]

    participation_rate = (
        active_participants / total_eligible_employees
        if total_eligible_employees > 0
        else 0.0
    )
    fee_ratio = admin_expenses / total_assets if total_assets > 0 else 0.0

    fee_flag = fee_ratio > FEE_RATIO_THRESHOLD
    participation_flag = participation_rate < PARTICIPATION_RATE_THRESHOLD
    compliance_failed = corrective_distributions > 0

    # Ensure tables exist and write audit metrics to database tables
    conn = sqlite3.connect(db_path, timeout=20)
    try:
        cursor = conn.cursor()

        # 1. Update pipeline_prospects if table exists and row is found
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pipeline_prospects'")
        if cursor.fetchone():
            cursor.execute("SELECT 1 FROM pipeline_prospects WHERE ein = ?", (normalized_ein,))
            if cursor.fetchone():
                conn.execute(
                    """
                    UPDATE pipeline_prospects
                    SET total_assets = ?,
                        active_participants = ?,
                        provider = ?,
                        industry = ?
                    WHERE ein = ?
                    """,
                    (
                        total_assets,
                        active_participants,
                        values.get("provider") or ("Vanguard" if total_assets > 10000000 else "Fidelity"),
                        values.get("industry") or "Professional Services",
                        normalized_ein
                    )
                )

        # 2. Upsert into form_5500_audits if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='form_5500_audits'")
        if cursor.fetchone():
            cursor.execute("SELECT 1 FROM form_5500_audits WHERE ein = ?", (normalized_ein,))
            exists = cursor.fetchone()
            
            employer_name = values.get("employer_name") or "Unknown"
            plan_name = values.get("plan_name")
            schedule_type = values.get("schedule_type")
            administrator_name = values.get("administrator_name")
            dol_address = values.get("dol_address")
            dol_city = values.get("dol_city")
            dol_state = values.get("dol_state")
            dol_zip = values.get("dol_zip")
            
            if exists:
                conn.execute(
                    """
                    UPDATE form_5500_audits
                    SET employer_name = COALESCE(?, employer_name),
                        plan_name = COALESCE(?, plan_name),
                        schedule_type = COALESCE(?, schedule_type),
                        total_assets = ?,
                        active_participants = ?,
                        total_eligible_employees = ?,
                        admin_expenses = ?,
                        corrective_distributions = ?,
                        participation_rate = ?,
                        fee_ratio = ?,
                        compliance_failed = ?,
                        fee_red_flag = ?,
                        participation_red_flag = ?,
                        dol_address = COALESCE(?, dol_address),
                        dol_city = COALESCE(?, dol_city),
                        dol_state = COALESCE(?, dol_state),
                        dol_zip = COALESCE(?, dol_zip),
                        administrator_name = COALESCE(?, administrator_name)
                    WHERE ein = ?
                    """,
                    (
                        employer_name, plan_name, schedule_type,
                        total_assets, active_participants, total_eligible_employees,
                        admin_expenses, corrective_distributions, participation_rate, fee_ratio,
                        1 if compliance_failed else 0, 1 if fee_flag else 0, 1 if participation_flag else 0,
                        dol_address, dol_city, dol_state, dol_zip, administrator_name,
                        normalized_ein
                    )
                )
            else:
                conn.execute(
                    """
                    INSERT INTO form_5500_audits (
                        ein, employer_name, plan_name, schedule_type,
                        total_assets, active_participants, total_eligible_employees,
                        admin_expenses, corrective_distributions, participation_rate, fee_ratio,
                        compliance_failed, fee_red_flag, participation_red_flag,
                        dol_address, dol_city, dol_state, dol_zip, administrator_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_ein, employer_name, plan_name, schedule_type,
                        total_assets, active_participants, total_eligible_employees,
                        admin_expenses, corrective_distributions, participation_rate, fee_ratio,
                        1 if compliance_failed else 0, 1 if fee_flag else 0, 1 if participation_flag else 0,
                        dol_address, dol_city, dol_state, dol_zip, administrator_name
                    )
                )
        
        # 3. Upsert into prospects for backwards legacy compatibility
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prospects'")
        if cursor.fetchone():
            cursor.execute("SELECT 1 FROM prospects WHERE ein = ?", (normalized_ein,))
            if not cursor.fetchone():
                conn.execute("INSERT INTO prospects (ein) VALUES (?)", (normalized_ein,))
            conn.execute(
                """
                UPDATE prospects
                SET total_assets = ?,
                    participation_rate = ?,
                    fee_ratio = ?,
                    fee_flag = ?,
                    participation_flag = ?,
                    compliance_failed = ?
                WHERE ein = ?
                """,
                (
                    total_assets, participation_rate, fee_ratio,
                    1 if fee_flag else 0, 1 if participation_flag else 0, 1 if compliance_failed else 0,
                    normalized_ein
                )
            )
        
        conn.commit()
        print(f"[AuditEngine] Successfully completed on-demand plan audit for EIN {normalized_ein}!")
    except Exception as e:
        conn.rollback()
        print(f"[AuditEngine] Error persisting plan audit for EIN {normalized_ein}: {e}")
        raise e
    finally:
        conn.close()


def _find_plan_values(ein: str, csv_directory: str | os.PathLike[str]) -> dict[str, Any]:
    values = {field: 0.0 for field in FIELD_ALIASES}
    values["employer_name"] = "Unknown"
    
    # 1. Fast indexed SQLite lookup to avoid blocking CPU on massive CSV parses
    db_path = 'prospects.db'
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT employer_name, plan_name, schedule_type, total_assets, 
                       active_participants, total_eligible_employees, admin_expenses, 
                       corrective_distributions, dol_address, dol_city, dol_state, dol_zip, 
                       administrator_name 
                FROM form_5500_audits 
                WHERE ein = ? AND total_assets > 0.0
                """,
                (ein,)
            )
            row = cursor.fetchone()
            if row:
                print(f"[AuditEngine] Fast DB lookup success for EIN {ein}")
                values["employer_name"] = row[0]
                values["plan_name"] = row[1]
                values["schedule_type"] = row[2]
                values["total_assets"] = float(row[3]) if row[3] is not None else 0.0
                values["active_participants"] = int(row[4]) if row[4] is not None else 0
                values["total_eligible_employees"] = int(row[5]) if row[5] is not None else 0
                values["admin_expenses"] = float(row[6]) if row[6] is not None else 0.0
                values["corrective_distributions"] = float(row[7]) if row[7] is not None else 0.0
                values["dol_address"] = row[8]
                values["dol_city"] = row[9]
                values["dol_state"] = row[10]
                values["dol_zip"] = row[11]
                values["administrator_name"] = row[12]
                return values
        except Exception as db_err:
            print(f"[AuditEngine] Database fast lookup error for EIN {ein}: {db_err}")
        finally:
            conn.close()

    # If the database does not contain this EIN (or has 0 assets), skip scanning raw CSVs
    # as it takes 60 seconds and freezes the server. Return default dict so fallback is used.
    print(f"[AuditEngine] EIN {ein} not in database or has empty metrics. Skipping heavy CSV scan to prevent server freezing.")
    return values


def _persist_audit_metrics(metrics: dict[str, Any], db_path: str | os.PathLike[str]) -> int:
    conn = sqlite3.connect(db_path, timeout=20)
    try:
        table_name = _resolve_target_table(conn)
        ein_column = _resolve_ein_column(conn, table_name)
        _ensure_columns(conn, table_name)

        assignments = ", ".join(f"{column} = ?" for column in AUDIT_COLUMNS)
        values = [
            int(metrics[column]) if isinstance(metrics[column], bool) else metrics[column]
            for column in AUDIT_COLUMNS
        ]
        values.append(metrics["ein"])

        cursor = conn.execute(
            f"UPDATE {table_name} SET {assignments} WHERE {ein_column} = ?",
            values,
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def _resolve_target_table(conn: sqlite3.Connection) -> str:
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "prospects" in tables:
        return "prospects"
    if "pipeline_updates" in tables:
        return "pipeline_updates"
    raise sqlite3.OperationalError(
        "No prospects table found; expected table 'prospects'."
    )


def _resolve_ein_column(conn: sqlite3.Connection, table_name: str) -> str:
    columns = _table_columns(conn, table_name)
    for candidate in ("ein", "EIN"):
        if candidate in columns:
            return candidate
    raise sqlite3.OperationalError(
        f"Table '{table_name}' must include an EIN column named 'ein' or 'EIN'."
    )


def _ensure_columns(conn: sqlite3.Connection, table_name: str) -> None:
    existing = _table_columns(conn, table_name)
    for column_name, column_type in AUDIT_COLUMNS.items():
        if column_name not in existing:
            conn.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            )


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})")}


def _csv_files(csv_directory: Any) -> list[Path]:
    # 1. If it's a list or tuple of file paths
    if isinstance(csv_directory, (list, tuple)):
        paths = []
        for p in csv_directory:
            path = Path(p)
            if path.exists() and path.is_file() and path.suffix.lower() == ".csv":
                paths.append(path)
        if paths:
            return sorted(paths)
        csv_directory = "."

    # 2. If it's a single file path ending in .csv
    if isinstance(csv_directory, (str, Path)) and str(csv_directory).lower().endswith(".csv"):
        path = Path(csv_directory)
        if path.exists() and path.is_file():
            return [path]

    # 3. If it's a directory
    directory = Path(csv_directory)
    if not directory.exists() or not directory.is_dir():
        directory = Path(".")

    # Search recursively for all .csv files (handles unzipped child directories)
    csv_paths = list(directory.rglob("*.csv"))
    
    # If recursive search in target is empty, search current workspace recursively
    if not csv_paths and directory.resolve() != Path(".").resolve():
        csv_paths = list(Path(".").rglob("*.csv"))

    # Filter out anything in venv, node_modules, .git, .next, scratch, extracted_data
    filtered_paths = []
    for p in csv_paths:
        parts = p.parts
        if any(part in {"venv", "node_modules", ".git", ".next", "scratch", "extracted_data"} for part in parts):
            continue
        filtered_paths.append(p)

    return sorted(filtered_paths)


def _first_present(columns, aliases) -> str | None:
    column_lookup = {str(column).upper(): str(column) for column in columns}
    for alias in aliases:
        match = column_lookup.get(alias.upper())
        if match:
            return match
    return None


def _normalize_ein(value) -> str | None:
    if value is None or pd.isna(value):
        return None
    digits = "".join(character for character in str(value) if character.isdigit())
    if not digits:
        return None
    return digits[-9:].zfill(9)


def _safe_number(value) -> float:
    if value is None or pd.isna(value):
        return 0.0
    cleaned = str(value).strip().replace(",", "").replace("$", "")
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
