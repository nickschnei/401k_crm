import pandas as pd
import sqlite3
import os
import re
import zipfile
from thefuzz import process, fuzz

from dol_audit_engine import (
    AUDIT_OUTPUT_COLUMNS,
    build_audit_dataframe,
    build_advisor_pitch_script,
    get_audit_by_ein,
    normalize_ein,
)

try:
    import pgeocode
except ImportError:
    pgeocode = None

# --- CONFIGURATION & CONSTANTS ---
import config

# Parse DB file path from sqlite URI if present
DB_PATH = config.DATABASE_URL
if DB_PATH.startswith("sqlite:///"):
    DB_PATH = DB_PATH.replace("sqlite:///", "")
else:
    # If using postgresql, use a default fallback for Streamlit sqlite interface
    DB_PATH = "prospects.db"

EXCEL_FILE = config.EXCEL_PROSPECT_FILE
US_ZIP_PATTERN = re.compile(r"\b(\d{5})(?:-\d{4})?\b")
US_ZIP_AT_END_PATTERN = re.compile(r"\b(\d{5})(?:-\d{4})\s*$")
_YEAR_IN_ZIP = re.compile(r"_(\d{4})_")


def _zip_year(filename: str) -> int:
    match = _YEAR_IN_ZIP.search(filename)
    return int(match.group(1)) if match else 0


def _latest_dol_zip_files():
    """Return the newest ZIP per DOL dataset prefix to limit parse time."""
    data_dir = config.DOL_DATA_DIR
    candidates = [
        f
        for f in os.listdir(data_dir)
        if f.endswith(".zip") and (f.startswith("F_5500") or f.startswith("F_SCH"))
    ]
    grouped = {}
    for zip_name in candidates:
        if zip_name.startswith("F_5500_SF_"):
            key = "F_5500_SF_"
        elif zip_name.startswith("F_5500_"):
            key = "F_5500_"
        elif zip_name.startswith("F_SCH_H_"):
            key = "F_SCH_H_"
        elif zip_name.startswith("F_SCH_I_"):
            key = "F_SCH_I_"
        elif zip_name.startswith("F_SCH_"):
            key = "F_SCH_OTHER_"
        else:
            key = zip_name
        grouped.setdefault(key, []).append(zip_name)
    return [max(files, key=_zip_year) for files in grouped.values()]


def ensure_extracted_csvs():
    """Ensure that the CSV files from the latest DOL ZIP archives are extracted to config.EXTRACTED_DATA_DIR."""
    data_dir = config.DOL_DATA_DIR
    target_dir = config.EXTRACTED_DATA_DIR
    os.makedirs(target_dir, exist_ok=True)
    zip_files = _latest_dol_zip_files()
    extracted_paths = []
    
    for zip_name in zip_files:
        zip_path = os.path.join(data_dir, zip_name)
        if not os.path.exists(zip_path):
            continue
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for file_info in z.infolist():
                    if file_info.filename.endswith('.csv'):
                        dest_path = os.path.join(target_dir, file_info.filename)
                        # Only extract if it doesn't exist or is different size
                        if not os.path.exists(dest_path) or os.path.getsize(dest_path) != file_info.file_size:
                            z.extract(file_info, target_dir)
                        extracted_paths.append(dest_path)
        except Exception as e:
            print(f"Error extracting zip {zip_name}: {e}")
    return extracted_paths

_geo_distance = None

# --- DATABASE LOGIC ---
def get_db_connection(timeout=20):
    """Returns a sqlite3 connection with a specified timeout to prevent 'database is locked' errors."""
    return sqlite3.connect(DB_PATH, timeout=timeout)

def _ensure_audit_columns(conn):
    """Add audit tracking columns to pipeline_updates for existing databases."""
    c = conn.cursor()
    c.execute("PRAGMA table_info(pipeline_updates)")
    existing = {row[1] for row in c.fetchall()}
    audit_columns = [
        ("total_assets", "REAL"),
        ("active_participants", "INTEGER"),
        ("total_eligible_employees", "INTEGER"),
        ("admin_expenses", "REAL"),
        ("compliance_failed", "INTEGER"),
        ("contact_name", "TEXT"),
        ("contact_email", "TEXT"),
        ("contact_phone", "TEXT"),
    ]
    for column_name, column_type in audit_columns:
        if column_name not in existing:
            c.execute(
                f"ALTER TABLE pipeline_updates ADD COLUMN {column_name} {column_type}"
            )


def init_db():
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_updates (
                ein TEXT PRIMARY KEY,
                status TEXT,
                notes TEXT,
                total_assets REAL,
                active_participants INTEGER,
                total_eligible_employees INTEGER,
                admin_expenses REAL,
                compliance_failed INTEGER DEFAULT 0,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        _ensure_audit_columns(conn)
        c.execute('''
            CREATE TABLE IF NOT EXISTS form_5500_audit (
                ein TEXT PRIMARY KEY,
                schedule_type TEXT,
                total_assets REAL,
                active_participants INTEGER,
                total_eligible_employees INTEGER,
                admin_expenses REAL,
                corrective_distributions REAL,
                compliance_failed INTEGER DEFAULT 0,
                participation_rate REAL,
                fee_ratio REAL,
                fee_red_flag INTEGER DEFAULT 0,
                participation_red_flag INTEGER DEFAULT 0,
                computed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS tenant_subscription (
                tenant_id TEXT PRIMARY KEY DEFAULT 'default_tenant',
                stripe_customer_id TEXT DEFAULT '',
                subscription_tier TEXT DEFAULT 'free',
                subscription_status TEXT DEFAULT 'inactive',
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    finally:
        conn.close()

def save_update(ein, status, notes):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO pipeline_updates (ein, status, notes, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (str(ein), status, notes))
        conn.commit()
    finally:
        conn.close()

def get_updates():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM pipeline_updates", conn)
    except Exception:
        df = pd.DataFrame(columns=['ein', 'status', 'notes', 'contact_name', 'contact_email', 'contact_phone'])
    finally:
        conn.close()
    return df


def sync_audit_to_sqlite(audit_df):
    if audit_df is None or audit_df.empty:
        return
    conn = get_db_connection()
    try:
        c = conn.cursor()
        for _, row in audit_df.iterrows():
            ein = row.get("EIN")
            if not ein:
                continue
            c.execute(
                '''
                INSERT OR REPLACE INTO form_5500_audit (
                    ein, schedule_type, total_assets, active_participants,
                    total_eligible_employees, admin_expenses, corrective_distributions,
                    compliance_failed, participation_rate, fee_ratio,
                    fee_red_flag, participation_red_flag, computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''',
                (
                    str(ein),
                    row.get("schedule_type"),
                    row.get("total_assets"),
                    int(row["active_participants"]) if pd.notna(row.get("active_participants")) else None,
                    int(row["total_eligible_employees"]) if pd.notna(row.get("total_eligible_employees")) else None,
                    row.get("admin_expenses"),
                    row.get("corrective_distributions"),
                    1 if row.get("compliance_failed") else 0,
                    row.get("participation_rate"),
                    row.get("fee_ratio"),
                    1 if row.get("fee_red_flag") else 0,
                    1 if row.get("participation_red_flag") else 0,
                ),
            )
            c.execute(
                '''
                UPDATE pipeline_updates
                SET total_assets = ?,
                    active_participants = ?,
                    total_eligible_employees = ?,
                    admin_expenses = ?,
                    compliance_failed = ?
                WHERE ein = ?
                ''',
                (
                    row.get("total_assets"),
                    int(row["active_participants"]) if pd.notna(row.get("active_participants")) else None,
                    int(row["total_eligible_employees"]) if pd.notna(row.get("total_eligible_employees")) else None,
                    row.get("admin_expenses"),
                    1 if row.get("compliance_failed") else 0,
                    str(ein),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def get_audit_records():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM form_5500_audit", conn)
        if not df.empty:
            df = df.rename(columns={"ein": "EIN"})
    except Exception:
        df = pd.DataFrame(columns=["EIN"] + AUDIT_OUTPUT_COLUMNS[1:])
    finally:
        conn.close()
    return df


def merge_audit_columns(df, audit_df):
    if df.empty or audit_df is None or audit_df.empty:
        return df
    audit_merge = audit_df.copy()
    if "ein" in audit_merge.columns and "EIN" not in audit_merge.columns:
        audit_merge = audit_merge.rename(columns={"ein": "EIN"})
    suffix_cols = [c for c in audit_merge.columns if c != "EIN" and c in df.columns]
    if suffix_cols:
        audit_merge = audit_merge.rename(
            columns={col: f"{col}_audit" for col in suffix_cols}
        )
    merged = pd.merge(df, audit_merge, on="EIN", how="left")
    return merged


def get_prospect_by_ein(ein, prospects_df=None):
    normalized = normalize_ein(ein)
    if not normalized:
        return None
    if prospects_df is None:
        prospects_df, _ = load_and_merge_data()
    matches = prospects_df[prospects_df["EIN"] == normalized]
    if matches.empty:
        return None
    return matches.iloc[0]

def normalize_zip(value):
    if pd.isna(value):
        return None
    match = US_ZIP_PATTERN.search(str(value))
    if not match:
        return None
    return match.group(1)

def extract_address_zip(value):
    if pd.isna(value):
        return None
    match = US_ZIP_AT_END_PATTERN.search(str(value).strip())
    if not match:
        return None
    return match.group(1)

def extract_record_zip(row):
    for column in ['ZIP', 'DOL ZIP']:
        if column in row.index:
            zip_code = normalize_zip(row.get(column))
            if zip_code:
                return zip_code
    for column in ['Address', 'DOL Address']:
        if column in row.index:
            zip_code = extract_address_zip(row.get(column))
            if zip_code:
                return zip_code
    return None

def _get_geo_distance():
    global _geo_distance
    if pgeocode is None:
        return None
    if _geo_distance is None:
        try:
            _geo_distance = pgeocode.GeoDistance('us')
        except Exception:
            return None
    return _geo_distance

def add_distance_columns(df, origin_zip):
    origin_zip = normalize_zip(origin_zip)
    if df.empty or not origin_zip:
        return df

    geo_distance = _get_geo_distance()
    if geo_distance is None:
        return df

    output_df = df.copy()
    output_df['Record ZIP'] = output_df.apply(extract_record_zip, axis=1)
    unique_zips = sorted(output_df['Record ZIP'].dropna().unique().tolist())
    distance_by_zip = {}
    for zip_code in unique_zips:
        distance_km = geo_distance.query_postal_code(origin_zip, zip_code)
        distance_by_zip[zip_code] = distance_km * 0.621371 if pd.notna(distance_km) else None

    output_df['Distance Miles'] = output_df['Record ZIP'].map(distance_by_zip)
    return output_df

# --- DATA PROCESSING LOGIC ---
_prospects_cache = None
_discovery_cache = None
_audit_cache = None

def load_and_merge_data(force_refresh=False):
    global _prospects_cache, _discovery_cache, _audit_cache
    if _prospects_cache is not None and not force_refresh:
        return _prospects_cache, _discovery_cache

    # 1. Load Local Excel Prospect List (THE PRIMARY LIST)
    if not os.path.exists(EXCEL_FILE):
        prospects_df = pd.DataFrame(columns=['Employer Name', 'EIN', 'Total Assets', 'Participants'])
    else:
        try:
            prospects_df = pd.read_excel(EXCEL_FILE)
        except Exception as e:
            print(f"Error reading Excel: {e}")
            prospects_df = pd.DataFrame(columns=['Employer Name', 'EIN', 'Total Assets', 'Participants'])

        if 'EIN' in prospects_df.columns:
            prospects_df['EIN'] = prospects_df['EIN'].astype(str).str.replace('.0', '', regex=False).str.strip().str.zfill(9)
        else:
            prospects_df['EIN'] = None
            
        if 'Employer Name' not in prospects_df.columns:
             if 'Company' in prospects_df.columns:
                 prospects_df = prospects_df.rename(columns={'Company': 'Employer Name'})
             else:
                 prospects_df['Employer Name'] = "Unknown"
    
    # 2. Load Form 5500 Data for ENRICHMENT
    dol_data = []
    zip_files = _latest_dol_zip_files()
    
    for zip_name in zip_files:
        try:
            with zipfile.ZipFile(os.path.join(config.DOL_DATA_DIR, zip_name), 'r') as z:
                csv_files = [f for f in z.namelist() if f.endswith('.csv')]
                if csv_files:
                    with z.open(csv_files[0]) as f:
                        temp_df = pd.read_csv(f, low_memory=False)
                        
                        rename_map_dol = {
                            'SPONS_DFE_NAME': 'Employer Name DOL',
                            'SPONSOR_DFE_NAME': 'Employer Name DOL',
                            'SF_SPONSOR_NAME': 'Employer Name DOL',
                            'SPONS_DFE_MAIL_US_ADDRESS1': 'DOL Address',
                            'SPONS_DFE_MAIL_US_ADDRESS2': 'DOL Address 2',
                            'SPONS_DFE_MAIL_US_CITY': 'DOL City',
                            'SPONS_DFE_MAIL_US_STATE': 'DOL State',
                            'SPONS_DFE_MAIL_US_ZIP': 'DOL ZIP',
                            'SPONSOR_DFE_MAIL_US_ADDRESS1': 'DOL Address',
                            'SPONSOR_DFE_MAIL_US_ADDRESS2': 'DOL Address 2',
                            'SPONSOR_DFE_MAIL_US_CITY': 'DOL City',
                            'SPONSOR_DFE_MAIL_US_STATE': 'DOL State',
                            'SPONSOR_DFE_MAIL_US_ZIP': 'DOL ZIP',
                            'SF_SPONS_US_ADDRESS1': 'DOL Address',
                            'SF_SPONS_US_ADDRESS2': 'DOL Address 2',
                            'SF_SPONS_US_CITY': 'DOL City',
                            'SF_SPONS_US_STATE': 'DOL State',
                            'SF_SPONS_US_ZIP': 'DOL ZIP',
                            'PLAN_NAME': 'Plan Name',
                            'SF_PLAN_NAME': 'Plan Name',
                            'TOT_ASSETS_END_AMT': 'Total Assets',
                            'TOT_ASSETS_EOY_AMT': 'Total Assets',
                            'SF_TOT_ASSETS_EOY_AMT': 'Total Assets',
                            'SMALL_TOT_ASSETS_EOY_AMT': 'Total Assets',
                            'TOT_ACT_PARTCP_CNT': 'Participants',
                            'SF_TOT_ACT_PARTCP_EOY_CNT': 'Participants',
                            'ADMIN_NAME': 'Administrator',
                            'SF_ADMIN_NAME': 'Administrator',
                            'SPONS_DFE_EIN': 'EIN',
                            'SF_SPONS_EIN': 'EIN',
                            'SCH_H_EIN': 'EIN',
                            'SCH_I_EIN': 'EIN'
                        }
                        temp_df = temp_df.rename(columns=rename_map_dol)
                        
                        if 'EIN' in temp_df.columns:
                            temp_df['EIN'] = temp_df['EIN'].astype(str).str.replace('.0', '', regex=False).str.zfill(9)
                        
                        keep_cols = ['EIN', 'Employer Name DOL', 'Plan Name', 'Total Assets', 'Participants', 'Administrator', 'DOL Address', 'DOL City', 'DOL State', 'DOL ZIP']
                        existing_cols = [c for c in keep_cols if c in temp_df.columns]
                        if existing_cols:
                            dol_data.append(temp_df[existing_cols])
        except Exception:
            pass

    # 3. Process Data
    if not dol_data:
        merged_df = prospects_df.copy()
        discovery_df = pd.DataFrame()
        audit_df = pd.DataFrame(columns=AUDIT_OUTPUT_COLUMNS)
    else:
        dol_combined = pd.concat(dol_data, ignore_index=True)
        agg_map = {col: ('max' if col in ['Total Assets', 'Participants'] else 'first') for col in dol_combined.columns if col != 'EIN'}
        dol_aggregated = dol_combined.groupby('EIN').agg(agg_map).reset_index()
        
        try:
            audit_df = build_audit_dataframe(data_dir=config.DOL_DATA_DIR)
            _audit_cache = audit_df
        except Exception:
            audit_df = pd.DataFrame(columns=AUDIT_OUTPUT_COLUMNS)
            _audit_cache = audit_df

        # Discovery Mode: Full DOL universe enriched with audit metrics
        discovery_df = merge_audit_columns(dol_aggregated, audit_df)

        # Prospects Mode: Excel list enriched with DOL data
        if not prospects_df.empty:
            merged_df = pd.merge(prospects_df, dol_aggregated, on='EIN', how='left', suffixes=('', '_dol'))
            
            # Fill missing Excel info with DOL data
            if 'Employer Name DOL' in merged_df.columns:
                merged_df['Employer Name'] = merged_df['Employer Name'].fillna(merged_df['Employer Name DOL'])
            for col in ['Total Assets', 'Participants']:
                if f"{col}_dol" in merged_df.columns:
                    merged_df[col] = merged_df[col].fillna(merged_df[f"{col}_dol"])
            
            # Add deep audit metrics
            merged_df = merge_audit_columns(merged_df, audit_df)
        else:
            merged_df = pd.DataFrame()

    # 4. Integrate Pipeline Updates (Status, Notes)
    updates_df = get_updates()
    if not merged_df.empty:
        merged_df['match_key'] = merged_df['EIN'].fillna(merged_df['Employer Name'])
        if not updates_df.empty:
            updates_df['match_key'] = updates_df['ein']
            merged_df = pd.merge(merged_df, updates_df, on='match_key', how='left')
        
        merged_df['status'] = merged_df.get('status', pd.Series(['Lead']*len(merged_df))).fillna('Lead')
        merged_df['notes'] = merged_df.get('notes', pd.Series(['']*len(merged_df))).fillna('')

    _prospects_cache = merged_df
    _discovery_cache = discovery_df
    return merged_df, discovery_df


def get_cached_audit_dataframe(force_refresh=False):
    global _audit_cache
    if _audit_cache is None or force_refresh:
        _audit_cache = build_audit_dataframe(data_dir=config.DOL_DATA_DIR)
        sync_audit_to_sqlite(_audit_cache)
    return _audit_cache

def apply_filters(
    df,
    search_term="",
    min_assets=0,
    max_assets=None,
    min_participants=0,
    max_participants=None,
    status_filter="All",
    industry_filter="All",
    provider_filter="All",
    administrator_filter="All",
    employer_name_filter="All",
    address_filter="All",
    origin_zip="",
    max_distance_miles=None,
    data_quality_filter="All",
):
    if df.empty:
        return df
    
    filtered_df = df.copy()
    
    if search_term:
        search_columns = [
            'Employer Name',
            'Employer Name DOL',
            'EIN',
            'Plan Name',
            'Administrator',
            'Broker/Provider',
            'Industry',
            'Contact',
            'EMAIL',
            'Address',
            'DOL Address',
            'DOL City',
            'DOL State',
            'DOL ZIP',
            'schedule_type',
        ]
        existing_search_columns = [c for c in search_columns if c in filtered_df.columns]
        if existing_search_columns:
            search_mask = pd.Series(False, index=filtered_df.index)
            for col in existing_search_columns:
                search_mask = search_mask | filtered_df[col].astype(str).str.contains(
                    search_term,
                    case=False,
                    na=False,
                    regex=False,
                )
            filtered_df = filtered_df[search_mask]
        
    if 'Total Assets' in filtered_df.columns:
        assets = pd.to_numeric(filtered_df['Total Assets'], errors='coerce').fillna(0)
        if min_assets and min_assets > 0:
            filtered_df = filtered_df[assets >= min_assets]
            assets = assets.loc[filtered_df.index]
        if max_assets and max_assets > 0:
            filtered_df = filtered_df[assets <= max_assets]
        
    if 'Participants' in filtered_df.columns:
        participants = pd.to_numeric(filtered_df['Participants'], errors='coerce').fillna(0)
        if min_participants and min_participants > 0:
            filtered_df = filtered_df[participants >= min_participants]
            participants = participants.loc[filtered_df.index]
        if max_participants and max_participants > 0:
            filtered_df = filtered_df[participants <= max_participants]
        
    if status_filter != "All" and 'status' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['status'] == status_filter]

    exact_filters = {
        'Industry': industry_filter,
        'Broker/Provider': provider_filter,
        'Administrator': administrator_filter,
    }
    for column, selected_value in exact_filters.items():
        if selected_value != "All" and column in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[column].fillna("Unspecified") == selected_value]

    if employer_name_filter != "All":
        employer_name_signal = pd.Series(False, index=filtered_df.index)
        for column in ['Employer Name', 'Employer Name DOL']:
            if column in filtered_df.columns:
                employer_name_signal = employer_name_signal | filtered_df[column].notna() & filtered_df[column].astype(str).str.strip().ne("")

        if employer_name_filter == "Has employer name":
            filtered_df = filtered_df[employer_name_signal]
        elif employer_name_filter == "Missing employer name":
            filtered_df = filtered_df[~employer_name_signal]

    if address_filter != "All":
        address_signal = pd.Series(False, index=filtered_df.index)
        for column in ['Address', 'DOL Address', 'DOL ZIP']:
            if column in filtered_df.columns:
                address_signal = address_signal | filtered_df[column].notna() & filtered_df[column].astype(str).str.strip().ne("")
        zip_signal = filtered_df.apply(extract_record_zip, axis=1).notna()

        if address_filter == "Has address/ZIP":
            filtered_df = filtered_df[address_signal]
        elif address_filter == "Missing address/ZIP":
            filtered_df = filtered_df[~address_signal]
        elif address_filter == "Has ZIP code":
            filtered_df = filtered_df[zip_signal]
        elif address_filter == "Missing ZIP code":
            filtered_df = filtered_df[~zip_signal]

    if origin_zip:
        filtered_df = add_distance_columns(filtered_df, origin_zip)
        if max_distance_miles and max_distance_miles > 0 and 'Distance Miles' in filtered_df.columns:
            distances = pd.to_numeric(filtered_df['Distance Miles'], errors='coerce')
            filtered_df = filtered_df[distances.notna() & (distances <= max_distance_miles)]

    if data_quality_filter != "All":
        dol_signal = pd.Series(False, index=filtered_df.index)
        for column in ['Employer Name DOL', 'Plan Name', 'Administrator']:
            if column in filtered_df.columns:
                dol_signal = dol_signal | filtered_df[column].notna()
        if 'Total Assets' in filtered_df.columns:
            dol_signal = dol_signal | (pd.to_numeric(filtered_df['Total Assets'], errors='coerce').fillna(0) > 0)
        if 'Participants' in filtered_df.columns:
            dol_signal = dol_signal | (pd.to_numeric(filtered_df['Participants'], errors='coerce').fillna(0) > 0)

        if data_quality_filter == "Has DOL match":
            filtered_df = filtered_df[dol_signal]
        elif data_quality_filter == "Missing DOL match":
            filtered_df = filtered_df[~dol_signal]
        elif data_quality_filter == "Has administrator" and 'Administrator' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Administrator'].notna()]
        elif data_quality_filter == "Missing administrator" and 'Administrator' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Administrator'].isna()]
    return filtered_df


def get_subscription_state() -> dict:
    """Load the default tenant subscription details. Seeds a default row if empty."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT subscription_tier, subscription_status FROM tenant_subscription WHERE tenant_id = 'default_tenant'")
        row = cursor = c.fetchone()
        if not row:
            # Seed default 'free' inactive row
            c.execute("INSERT INTO tenant_subscription (tenant_id, subscription_tier, subscription_status) VALUES ('default_tenant', 'free', 'inactive')")
            conn.commit()
            return {"tier": "free", "status": "inactive"}
        return {"tier": row[0], "status": row[1]}
    except Exception as e:
        print(f"Error reading subscription: {e}")
        return {"tier": "free", "status": "inactive"}
    finally:
        conn.close()

def update_subscription_state(tier: str, status: str) -> None:
    """Upsert subscription tier and billing status stage for the default tenant."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO tenant_subscription (tenant_id, subscription_tier, subscription_status, last_updated)
            VALUES ('default_tenant', ?, ?, CURRENT_TIMESTAMP)
        ''', (tier, status))
        conn.commit()
    except Exception as e:
        print(f"Error updating subscription: {e}")
    finally:
        conn.close()
