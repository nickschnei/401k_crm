"""
DOL Form 5500 audit engine — parses Schedule H/I and main filings by EIN.
"""

from __future__ import annotations

import os
import re
import zipfile
from typing import Optional

import pandas as pd

_YEAR_IN_ZIP = re.compile(r"_(\d{4})_")

FEE_RATIO_RED_THRESHOLD = 0.0060
PARTICIPATION_RATE_RED_THRESHOLD = 0.70

# Schedule H (large plans) — financial schedule fields
SCHEDULE_H_MAP = {
    "EIN": "SCH_H_EIN",
    "total_assets": "TOT_ASSETS_EOY_AMT",
    "admin_expenses": "TOT_ADMIN_EXPENSES_AMT",
    "corrective_distributions": "TOT_CORRECTIVE_DISTRIB_AMT",
}

# Schedule I (small plans) — financial schedule fields
SCHEDULE_I_MAP = {
    "EIN": "SCH_I_EIN",
    "total_assets": "SMALL_TOT_ASSETS_EOY_AMT",
    "admin_expenses": "SMALL_ADMIN_SRVC_PROVIDERS_AMT",
    "corrective_distributions": "SMALL_CORRECTIVE_DISTRIB_AMT",
}

# Form 5500 main — participant counts (eligible proxy: total participant universe)
FORM_5500_MAP = {
    "EIN": "SPONS_DFE_EIN",
    "active_participants": "TOT_ACTIVE_PARTCP_CNT",
    "total_eligible_employees": "TOT_ACT_RTD_SEP_BENEF_CNT",
    "sch_h_attached": "SCH_H_ATTACHED_IND",
    "sch_i_attached": "SCH_I_ATTACHED_IND",
}

# Form 5500-SF — small plan combined filing
FORM_5500_SF_MAP = {
    "EIN": "SF_SPONS_EIN",
    "active_participants": "SF_TOT_ACT_PARTCP_EOY_CNT",
    "total_eligible_employees": "SF_TOT_ACT_RTD_SEP_BENEF_CNT",
    "total_assets": "SF_TOT_ASSETS_EOY_AMT",
    "admin_expenses": "SF_ADMIN_SRVC_PROVIDERS_AMT",
    "corrective_distributions": "SF_CORRECTIVE_DEEMED_DISTR_AMT",
}

AUDIT_OUTPUT_COLUMNS = [
    "EIN",
    "schedule_type",
    "total_assets",
    "active_participants",
    "total_eligible_employees",
    "admin_expenses",
    "corrective_distributions",
    "compliance_failed",
    "participation_rate",
    "fee_ratio",
    "fee_red_flag",
    "participation_red_flag",
]


def normalize_ein(value) -> Optional[str]:
    if pd.isna(value) or value is None:
        return None
    ein = str(value).strip().replace(".0", "")
    if not ein or ein.lower() in {"nan", "none", ""}:
        return None
    return ein.zfill(9)


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _yes_indicator(value) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().upper() in {"1", "Y", "YES", "TRUE"}


def _zip_year(filename: str) -> int:
    match = _YEAR_IN_ZIP.search(filename)
    return int(match.group(1)) if match else 0


def _latest_zip_name(zip_files: list[str]) -> Optional[str]:
    if not zip_files:
        return None
    return max(zip_files, key=_zip_year)


def _columns_for_maps(*maps: dict) -> list[str]:
    cols = set()
    for mapping in maps:
        cols.update(mapping.values())
    return sorted(cols)


def _read_zip_csv(
    data_dir: str,
    zip_prefix: str,
    exclude_prefixes: tuple[str, ...] = (),
    use_columns: Optional[list[str]] = None,
) -> Optional[pd.DataFrame]:
    zip_files = [
        f
        for f in os.listdir(data_dir)
        if f.endswith(".zip")
        and f.upper().startswith(zip_prefix.upper())
        and not any(f.upper().startswith(ex.upper()) for ex in exclude_prefixes)
    ]
    latest_zip = _latest_zip_name(zip_files)
    if not latest_zip:
        return None

    zip_path = os.path.join(data_dir, latest_zip)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_files = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_files:
                return None
            with zf.open(csv_files[0]) as handle:
                if use_columns:
                    wanted = set(use_columns)
                    return pd.read_csv(
                        handle,
                        usecols=lambda col: col in wanted,
                        low_memory=False,
                    )
                return pd.read_csv(handle, low_memory=False)
    except Exception:
        return None


def _extract_columns(raw_df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    output = {}
    for target, source in column_map.items():
        if source in raw_df.columns:
            output[target] = raw_df[source]
        elif target == "EIN" and "EIN" in raw_df.columns:
            output[target] = raw_df["EIN"]
    if "EIN" not in output:
        return pd.DataFrame()
    frame = pd.DataFrame(output)
    frame["EIN"] = frame["EIN"].apply(normalize_ein)
    frame = frame[frame["EIN"].notna()]
    for col in frame.columns:
        if col != "EIN":
            frame[col] = _to_numeric(frame[col])
    return frame


def _aggregate_by_ein(df: pd.DataFrame, sum_cols: list, first_cols: list | None = None) -> pd.DataFrame:
    if df.empty:
        return df
    first_cols = first_cols or []
    agg = {}
    for col in sum_cols:
        if col in df.columns:
            agg[col] = "max"
    for col in first_cols:
        if col in df.columns:
            agg[col] = "first"
    if not agg:
        return df.drop_duplicates(subset=["EIN"], keep="first")
    return df.groupby("EIN", as_index=False).agg(agg)


def compute_audit_metrics(row: pd.Series) -> pd.Series:
    total_assets = row.get("total_assets")
    active = row.get("active_participants")
    eligible = row.get("total_eligible_employees")
    admin = row.get("admin_expenses")
    corrective = row.get("corrective_distributions")

    participation_rate = None
    if pd.notna(active) and pd.notna(eligible) and eligible > 0:
        participation_rate = float(active) / float(eligible)

    fee_ratio = None
    if pd.notna(admin) and pd.notna(total_assets) and total_assets > 0:
        fee_ratio = float(admin) / float(total_assets)

    compliance_failed = bool(pd.notna(corrective) and corrective > 0)

    fee_red_flag = bool(pd.notna(fee_ratio) and fee_ratio > FEE_RATIO_RED_THRESHOLD)
    participation_red_flag = bool(
        pd.notna(participation_rate) and participation_rate < PARTICIPATION_RATE_RED_THRESHOLD
    )

    return pd.Series(
        {
            "participation_rate": participation_rate,
            "fee_ratio": fee_ratio,
            "compliance_failed": compliance_failed,
            "fee_red_flag": fee_red_flag,
            "participation_red_flag": participation_red_flag,
        }
    )


def build_audit_dataframe(data_dir: str = ".") -> pd.DataFrame:
    """Parse DOL ZIP CSVs and return one audit row per EIN."""
    sch_h_raw = _read_zip_csv(
        data_dir, "F_SCH_H_", use_columns=_columns_for_maps(SCHEDULE_H_MAP)
    )
    sch_i_raw = _read_zip_csv(
        data_dir, "F_SCH_I_", use_columns=_columns_for_maps(SCHEDULE_I_MAP)
    )
    main_raw = _read_zip_csv(
        data_dir,
        "F_5500_",
        exclude_prefixes=("F_5500_SF_",),
        use_columns=_columns_for_maps(FORM_5500_MAP),
    )
    sf_raw = _read_zip_csv(
        data_dir, "F_5500_SF_", use_columns=_columns_for_maps(FORM_5500_SF_MAP)
    )

    sch_h = (
        _aggregate_by_ein(
            _extract_columns(sch_h_raw, SCHEDULE_H_MAP),
            sum_cols=["total_assets", "admin_expenses", "corrective_distributions"],
        )
        if sch_h_raw is not None
        else pd.DataFrame()
    )
    sch_i = (
        _aggregate_by_ein(
            _extract_columns(sch_i_raw, SCHEDULE_I_MAP),
            sum_cols=["total_assets", "admin_expenses", "corrective_distributions"],
        )
        if sch_i_raw is not None
        else pd.DataFrame()
    )

    main_frames = []
    if main_raw is not None:
        main_frames.append(_extract_columns(main_raw, FORM_5500_MAP))
    if sf_raw is not None:
        main_frames.append(_extract_columns(sf_raw, FORM_5500_SF_MAP))

    main_participants = (
        _aggregate_by_ein(
            pd.concat([f for f in main_frames if not f.empty], ignore_index=True),
            sum_cols=[],
            first_cols=[
                "active_participants",
                "total_eligible_employees",
                "sch_h_attached",
                "sch_i_attached",
                "total_assets",
                "admin_expenses",
                "corrective_distributions",
            ],
        )
        if main_frames and any(not f.empty for f in main_frames)
        else pd.DataFrame()
    )

    all_eins = set()
    for frame in (sch_h, sch_i, main_participants):
        if not frame.empty and "EIN" in frame.columns:
            all_eins.update(frame["EIN"].dropna().unique())

    if not all_eins:
        return pd.DataFrame(columns=AUDIT_OUTPUT_COLUMNS)

    records = []
    sch_h_by_ein = sch_h.set_index("EIN") if not sch_h.empty else pd.DataFrame()
    sch_i_by_ein = sch_i.set_index("EIN") if not sch_i.empty else pd.DataFrame()
    main_by_ein = main_participants.set_index("EIN") if not main_participants.empty else pd.DataFrame()

    for ein in sorted(all_eins):
        schedule_type = None
        financial = {}

        if ein in sch_h_by_ein.index:
            schedule_type = "H"
            financial = sch_h_by_ein.loc[ein].to_dict()
        elif ein in sch_i_by_ein.index:
            schedule_type = "I"
            financial = sch_i_by_ein.loc[ein].to_dict()
        elif ein in main_by_ein.index:
            main_row = main_by_ein.loc[ein]
            if pd.notna(main_row.get("total_assets")):
                schedule_type = "SF"
                financial = {
                    "total_assets": main_row.get("total_assets"),
                    "admin_expenses": main_row.get("admin_expenses"),
                    "corrective_distributions": main_row.get("corrective_distributions"),
                }
            elif _yes_indicator(main_row.get("sch_h_attached")):
                schedule_type = "H"
            elif _yes_indicator(main_row.get("sch_i_attached")):
                schedule_type = "I"

        participants = main_by_ein.loc[ein].to_dict() if ein in main_by_ein.index else {}

        row = {
            "EIN": ein,
            "schedule_type": schedule_type,
            "total_assets": financial.get("total_assets"),
            "admin_expenses": financial.get("admin_expenses"),
            "corrective_distributions": financial.get("corrective_distributions"),
            "active_participants": participants.get("active_participants"),
            "total_eligible_employees": participants.get("total_eligible_employees"),
        }

        # Fallback eligible count: use active participants if total universe missing
        if pd.isna(row["total_eligible_employees"]) and pd.notna(row["active_participants"]):
            row["total_eligible_employees"] = row["active_participants"]

        metrics = compute_audit_metrics(pd.Series(row))
        row.update(metrics.to_dict())
        records.append(row)

    audit_df = pd.DataFrame(records)
    for col in AUDIT_OUTPUT_COLUMNS:
        if col not in audit_df.columns:
            audit_df[col] = None
    return audit_df[AUDIT_OUTPUT_COLUMNS]


def get_audit_by_ein(ein: str, audit_df: Optional[pd.DataFrame] = None, data_dir: str = ".") -> dict:
    """Return audit metrics for a single EIN."""
    normalized = normalize_ein(ein)
    if not normalized:
        return {"found": False, "ein": ein}

    if audit_df is None:
        audit_df = build_audit_dataframe(data_dir=data_dir)

    if audit_df.empty:
        return {"found": False, "ein": normalized}

    matches = audit_df[audit_df["EIN"] == normalized]
    if matches.empty:
        return {"found": False, "ein": normalized}

    row = matches.iloc[0].to_dict()
    row["found"] = True
    return row


def build_advisor_pitch_script(audit: dict, employer_name: str = "your organization") -> str:
    """Generate a customized advisor pitch from audit flags."""
    name = employer_name if employer_name and str(employer_name).strip() else "your organization"
    lines = [
        f"Hi — I reviewed the latest DOL Form 5500 filing for {name} and wanted to share a few observations.",
        "",
    ]

    fee_flag = bool(audit.get("fee_red_flag"))
    part_flag = bool(audit.get("participation_red_flag"))
    compliance = bool(audit.get("compliance_failed"))

    if fee_flag:
        fee_ratio = audit.get("fee_ratio")
        fee_pct = f"{fee_ratio * 100:.2f}%" if pd.notna(fee_ratio) else "elevated"
        lines.extend(
            [
                "• **Administrative cost concern:** Total administrative expenses relative to plan assets "
                f"are running at {fee_pct} of assets — above the 60 basis-point benchmark we use for "
                "defined contribution plans. That often signals layered recordkeeping, advisory, or "
                "custodial fees that may be compressing participant net returns.",
                "",
            ]
        )

    if part_flag:
        part_rate = audit.get("participation_rate")
        part_pct = f"{part_rate * 100:.1f}%" if pd.notna(part_rate) else "below target"
        lines.extend(
            [
                "• **Participation gap:** Active participation appears to be "
                f"{part_pct} of the reported participant universe — below the 70% threshold "
                "many sponsors target. Auto-enrollment design, eligibility communication, and "
                "match structure are common levers to close that gap.",
                "",
            ]
        )

    if compliance:
        corr = audit.get("corrective_distributions")
        corr_txt = f"${corr:,.0f}" if pd.notna(corr) else "a reported amount"
        lines.extend(
            [
                "• **Compliance signal:** The filing reports corrective distributions "
                f"({corr_txt}), which can indicate ADP/ACP testing issues, missed deferrals, "
                "or operational errors. A plan operational review may reduce repeat corrections.",
                "",
            ]
        )

    if not fee_flag and not part_flag and not compliance:
        lines.extend(
            [
                "• **Overall:** Key fee and participation indicators are within common benchmark "
                "ranges on the latest filing. We would still benchmark investments and service "
                "provider economics periodically as assets and headcount change.",
                "",
            ]
        )

    schedule = audit.get("schedule_type")
    if schedule:
        sched_label = {"H": "Schedule H (large plan)", "I": "Schedule I (small plan)", "SF": "Form 5500-SF"}.get(
            schedule, schedule
        )
        lines.append(f"_Source: DOL {sched_label} financial data._")

    lines.extend(
        [
            "",
            "Would you be open to a 20-minute call to walk through a side-by-side benchmark "
            "and outline options that protect fiduciaries and participants?",
        ]
    )
    return "\n".join(lines)
