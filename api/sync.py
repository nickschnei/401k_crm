import os
import zipfile
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from api.models import Prospect, Form5500Audit, Tenant
import config
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

def normalize_ein(value) -> str | None:
    if pd.isna(value) or value is None:
        return None
    ein = str(value).strip().replace(".0", "")
    ein = "".join(c for c in ein if c.isdigit())
    if not ein:
        return None
    return ein.zfill(9)

def _yes_indicator(value) -> bool:
    if pd.isna(value) or value is None:
        return False
    return str(value).strip().upper() in {"1", "Y", "YES", "TRUE"}

def bulk_upsert_audits(db: Session, records: list[dict], file_type: str):
    """Perform high-performance bulk upserts in Postgres or SQLite based on active dialect."""
    if not records:
        return
        
    dialect_name = db.bind.dialect.name
    
    if dialect_name == "postgresql":
        stmt = pg_insert(Form5500Audit).values(records)
        
        if file_type == "main":
            update_cols = {
                "employer_name": stmt.excluded.employer_name,
                "plan_name": stmt.excluded.plan_name,
                "active_participants": stmt.excluded.active_participants,
                "total_eligible_employees": stmt.excluded.total_eligible_employees,
                "participation_rate": stmt.excluded.participation_rate,
                "participation_red_flag": stmt.excluded.participation_red_flag,
                "dol_address": stmt.excluded.dol_address,
                "dol_city": stmt.excluded.dol_city,
                "dol_state": stmt.excluded.dol_state,
                "dol_zip": stmt.excluded.dol_zip,
                "schedule_type": text("COALESCE(EXCLUDED.schedule_type, form_5500_audits.schedule_type)")
            }
        elif file_type in ["sch_h", "sch_i"]:
            update_cols = {
                "total_assets": stmt.excluded.total_assets,
                "admin_expenses": stmt.excluded.admin_expenses,
                "corrective_distributions": stmt.excluded.corrective_distributions,
                "fee_ratio": stmt.excluded.fee_ratio,
                "fee_red_flag": stmt.excluded.fee_red_flag,
                "compliance_failed": stmt.excluded.compliance_failed,
                "schedule_type": stmt.excluded.schedule_type
            }
        elif file_type == "sf":
            update_cols = {
                "employer_name": stmt.excluded.employer_name,
                "plan_name": stmt.excluded.plan_name,
                "active_participants": stmt.excluded.active_participants,
                "total_eligible_employees": stmt.excluded.total_eligible_employees,
                "participation_rate": stmt.excluded.participation_rate,
                "participation_red_flag": stmt.excluded.participation_red_flag,
                "total_assets": stmt.excluded.total_assets,
                "admin_expenses": stmt.excluded.admin_expenses,
                "corrective_distributions": stmt.excluded.corrective_distributions,
                "fee_ratio": stmt.excluded.fee_ratio,
                "fee_red_flag": stmt.excluded.fee_red_flag,
                "compliance_failed": stmt.excluded.compliance_failed,
                "dol_address": stmt.excluded.dol_address,
                "dol_city": stmt.excluded.dol_city,
                "dol_state": stmt.excluded.dol_state,
                "dol_zip": stmt.excluded.dol_zip,
                "administrator_name": stmt.excluded.administrator_name,
                "schedule_type": stmt.excluded.schedule_type
            }
        else:
            return
            
        stmt = stmt.on_conflict_do_update(
            index_elements=["ein"],
            set_=update_cols
        )
        db.execute(stmt)
        
    elif dialect_name == "sqlite":
        stmt = sqlite_insert(Form5500Audit).values(records)
        
        if file_type == "main":
            update_cols = {
                "employer_name": stmt.excluded.employer_name,
                "plan_name": stmt.excluded.plan_name,
                "active_participants": stmt.excluded.active_participants,
                "total_eligible_employees": stmt.excluded.total_eligible_employees,
                "participation_rate": stmt.excluded.participation_rate,
                "participation_red_flag": stmt.excluded.participation_red_flag,
                "dol_address": stmt.excluded.dol_address,
                "dol_city": stmt.excluded.dol_city,
                "dol_state": stmt.excluded.dol_state,
                "dol_zip": stmt.excluded.dol_zip,
                "schedule_type": text("COALESCE(excluded.schedule_type, form_5500_audits.schedule_type)")
            }
        elif file_type in ["sch_h", "sch_i"]:
            update_cols = {
                "total_assets": stmt.excluded.total_assets,
                "admin_expenses": stmt.excluded.admin_expenses,
                "corrective_distributions": stmt.excluded.corrective_distributions,
                "fee_ratio": stmt.excluded.fee_ratio,
                "fee_red_flag": stmt.excluded.fee_red_flag,
                "compliance_failed": stmt.excluded.compliance_failed,
                "schedule_type": stmt.excluded.schedule_type
            }
        elif file_type == "sf":
            update_cols = {
                "employer_name": stmt.excluded.employer_name,
                "plan_name": stmt.excluded.plan_name,
                "active_participants": stmt.excluded.active_participants,
                "total_eligible_employees": stmt.excluded.total_eligible_employees,
                "participation_rate": stmt.excluded.participation_rate,
                "participation_red_flag": stmt.excluded.participation_red_flag,
                "total_assets": stmt.excluded.total_assets,
                "admin_expenses": stmt.excluded.admin_expenses,
                "corrective_distributions": stmt.excluded.corrective_distributions,
                "fee_ratio": stmt.excluded.fee_ratio,
                "fee_red_flag": stmt.excluded.fee_red_flag,
                "compliance_failed": stmt.excluded.compliance_failed,
                "dol_address": stmt.excluded.dol_address,
                "dol_city": stmt.excluded.dol_city,
                "dol_state": stmt.excluded.dol_state,
                "dol_zip": stmt.excluded.dol_zip,
                "administrator_name": stmt.excluded.administrator_name,
                "schedule_type": stmt.excluded.schedule_type
            }
        else:
            return
            
        stmt = stmt.on_conflict_do_update(
            index_elements=["ein"],
            set_=update_cols
        )
        db.execute(stmt)
        
    else:
        # Fallback ORM merge in batches (for database backends without ON CONFLICT support)
        for r in records:
            db.merge(Form5500Audit(**r))
            
    db.commit()

def clean_and_map_chunk(df: pd.DataFrame, mapping: dict, file_type: str) -> list[dict]:
    """Perform data cleaning, typing normalization, and flag computations on a pandas chunk."""
    # 1. Rename columns to standardized keys based on case-insensitive mapping
    rename_map = {}
    for target, sources in mapping.items():
        for src in sources:
            match_cols = [c for c in df.columns if c.upper() == src.upper()]
            if match_cols:
                rename_map[match_cols[0]] = target
                break
                
    df_renamed = df.rename(columns=rename_map)
    
    # 2. Identify target key
    ein_key = None
    for k in ["SPONS_DFE_EIN", "SCH_H_EIN", "SCH_I_EIN", "SF_SPONS_EIN"]:
        if k in df_renamed.columns:
            ein_key = k
            break
            
    if not ein_key:
        return []
        
    df_renamed = df_renamed.dropna(subset=[ein_key])
    
    records = []
    for _, row in df_renamed.iterrows():
        ein = normalize_ein(row.get(ein_key))
        if not ein:
            continue
            
        record = {"ein": ein}
        
        if file_type == "main":
            record["employer_name"] = str(row.get("SPONS_DFE_NAME", "Unknown")).strip()[:255]
            record["plan_name"] = str(row.get("PLAN_NAME", "401(k) Plan")).strip()[:255] if pd.notna(row.get("PLAN_NAME")) else None
            
            active = pd.to_numeric(row.get("TOT_ACTIVE_PARTCP_CNT"), errors="coerce")
            eligible = pd.to_numeric(row.get("TOT_ACT_RTD_SEP_BENEF_CNT"), errors="coerce")
            active = int(active) if pd.notna(active) else 0
            eligible = int(eligible) if pd.notna(eligible) else 0
            if eligible <= 0:
                eligible = active
                
            record["active_participants"] = active
            record["total_eligible_employees"] = eligible
            
            part_rate = float(active) / float(eligible) if eligible > 0 else 1.0
            record["participation_rate"] = part_rate
            record["participation_red_flag"] = bool(part_rate < 0.70)
            
            record["dol_address"] = str(row.get("SPONS_DFE_MAIL_US_ADDRESS1")).strip()[:255] if pd.notna(row.get("SPONS_DFE_MAIL_US_ADDRESS1")) else None
            record["dol_city"] = str(row.get("SPONS_DFE_MAIL_US_CITY")).strip()[:150] if pd.notna(row.get("SPONS_DFE_MAIL_US_CITY")) else None
            record["dol_state"] = str(row.get("SPONS_DFE_MAIL_US_STATE")).strip()[:50] if pd.notna(row.get("SPONS_DFE_MAIL_US_STATE")) else None
            record["dol_zip"] = str(row.get("SPONS_DFE_MAIL_US_ZIP")).strip()[:20] if pd.notna(row.get("SPONS_DFE_MAIL_US_ZIP")) else None
            
            sch_h = _yes_indicator(row.get("SCH_H_ATTACHED_IND"))
            sch_i = _yes_indicator(row.get("SCH_I_ATTACHED_IND"))
            record["schedule_type"] = "H" if sch_h else "I" if sch_i else None
            
        elif file_type == "sch_h":
            assets = pd.to_numeric(row.get("TOT_ASSETS_EOY_AMT"), errors="coerce")
            admin = pd.to_numeric(row.get("TOT_ADMIN_EXPENSES_AMT"), errors="coerce")
            corrective = pd.to_numeric(row.get("TOT_CORRECTIVE_DISTRIB_AMT"), errors="coerce")
            
            assets = float(assets) if pd.notna(assets) else 0.0
            admin = float(admin) if pd.notna(admin) else 0.0
            corrective = float(corrective) if pd.notna(corrective) else 0.0
            
            fee_ratio = assets > 0 and (admin / assets) or 0.0
            record["total_assets"] = assets
            record["admin_expenses"] = admin
            record["corrective_distributions"] = corrective
            record["fee_ratio"] = fee_ratio
            record["fee_red_flag"] = bool(fee_ratio > 0.0060)
            record["compliance_failed"] = bool(corrective > 0)
            record["schedule_type"] = "H"
            record["employer_name"] = "Unknown"
            
        elif file_type == "sch_i":
            assets = pd.to_numeric(row.get("SMALL_TOT_ASSETS_EOY_AMT"), errors="coerce")
            admin = pd.to_numeric(row.get("SMALL_ADMIN_SRVC_PROVIDERS_AMT"), errors="coerce")
            corrective = pd.to_numeric(row.get("SMALL_CORRECTIVE_DISTRIB_AMT"), errors="coerce")
            
            assets = float(assets) if pd.notna(assets) else 0.0
            admin = float(admin) if pd.notna(admin) else 0.0
            corrective = float(corrective) if pd.notna(corrective) else 0.0
            
            fee_ratio = assets > 0 and (admin / assets) or 0.0
            record["total_assets"] = assets
            record["admin_expenses"] = admin
            record["corrective_distributions"] = corrective
            record["fee_ratio"] = fee_ratio
            record["fee_red_flag"] = bool(fee_ratio > 0.0060)
            record["compliance_failed"] = bool(corrective > 0)
            record["schedule_type"] = "I"
            record["employer_name"] = "Unknown"
            
        elif file_type == "sf":
            record["employer_name"] = str(row.get("SF_SPONSOR_NAME", "Unknown")).strip()[:255]
            record["plan_name"] = str(row.get("SF_PLAN_NAME", "401(k) Plan")).strip()[:255] if pd.notna(row.get("SF_PLAN_NAME")) else None
            
            active = pd.to_numeric(row.get("SF_TOT_ACT_PARTCP_EOY_CNT"), errors="coerce")
            eligible = pd.to_numeric(row.get("SF_TOT_ACT_RTD_SEP_BENEF_CNT"), errors="coerce")
            active = int(active) if pd.notna(active) else 0
            eligible = int(eligible) if pd.notna(eligible) else 0
            if eligible <= 0:
                eligible = active
                
            record["active_participants"] = active
            record["total_eligible_employees"] = eligible
            
            part_rate = float(active) / float(eligible) if eligible > 0 else 1.0
            record["participation_rate"] = part_rate
            record["participation_red_flag"] = bool(part_rate < 0.70)
            
            assets = pd.to_numeric(row.get("SF_TOT_ASSETS_EOY_AMT"), errors="coerce")
            admin = pd.to_numeric(row.get("SF_ADMIN_SRVC_PROVIDERS_AMT"), errors="coerce")
            corrective = pd.to_numeric(row.get("SF_CORRECTIVE_DEEMED_DISTR_AMT"), errors="coerce")
            
            assets = float(assets) if pd.notna(assets) else 0.0
            admin = float(admin) if pd.notna(admin) else 0.0
            corrective = float(corrective) if pd.notna(corrective) else 0.0
            
            fee_ratio = assets > 0 and (admin / assets) or 0.0
            record["total_assets"] = assets
            record["admin_expenses"] = admin
            record["corrective_distributions"] = corrective
            record["fee_ratio"] = fee_ratio
            record["fee_red_flag"] = bool(fee_ratio > 0.0060)
            record["compliance_failed"] = bool(corrective > 0)
            
            record["dol_address"] = str(row.get("SF_SPONS_US_ADDRESS1")).strip()[:255] if pd.notna(row.get("SF_SPONS_US_ADDRESS1")) else None
            record["dol_city"] = str(row.get("SF_SPONS_US_CITY")).strip()[:150] if pd.notna(row.get("SF_SPONS_US_CITY")) else None
            record["dol_state"] = str(row.get("SF_SPONS_US_STATE")).strip()[:50] if pd.notna(row.get("SF_SPONS_US_STATE")) else None
            record["dol_zip"] = str(row.get("SF_SPONS_US_ZIP")).strip()[:20] if pd.notna(row.get("SF_SPONS_US_ZIP")) else None
            record["administrator_name"] = str(row.get("SF_ADMIN_NAME")).strip()[:255] if pd.notna(row.get("SF_ADMIN_NAME")) else None
            record["schedule_type"] = "SF"
            
        records.append(record)
    return records

def sync_dol_data(db: Session, force_refresh: bool = False, target_tenant_id: str = "default_tenant"):
    """
    Highly optimized, memory-efficient incremental sync.
    Reads large DOL ZIP files in chunks and performs bulk database inserts/upserts.
    """
    print(f"[Sync] Initiating database sync sweep for tenant {target_tenant_id}...")
    
    # 1. Ensure target tenant exists
    tenant = db.query(Tenant).filter_by(id=target_tenant_id).first()
    if not tenant:
        if target_tenant_id == "default_tenant":
            tenant = Tenant(
                id="default_tenant",
                company_name="Default Advisory Firm",
                subscription_tier="free",
                subscription_status="active"
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print("[Sync] Created default tenant.")
        else:
            tenant = Tenant(
                id=target_tenant_id,
                company_name="Advisory Firm",
                subscription_tier="free",
                subscription_status="active"
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"[Sync] Created tenant {target_tenant_id}.")
    else:
        print(f"[Sync] Found existing tenant {target_tenant_id}.")

    # 2. Extract ZIPs and parse DOL data using chunking
    audit_count = db.query(Form5500Audit).count()
    
    if audit_count > 0 and not force_refresh:
        print(f"[Sync] form_5500_audits already contains {audit_count} filings. Skipping heavy DOL extraction.")
    else:
        data_dir = config.DOL_DATA_DIR
        
        candidates = [
            f
            for f in os.listdir(data_dir)
            if f.endswith(".zip") and (f.startswith("F_5500") or f.startswith("F_SCH"))
        ]
        
        grouped = {}
        for zip_name in candidates:
            if zip_name.startswith("F_5500_SF_"):
                key = "sf"
            elif zip_name.startswith("F_5500_"):
                key = "main"
            elif zip_name.startswith("F_SCH_H_"):
                key = "sch_h"
            elif zip_name.startswith("F_SCH_I_"):
                key = "sch_i"
            else:
                continue
            grouped.setdefault(key, []).append(zip_name)
            
        def _zip_year(filename: str) -> int:
            import re
            match = re.search(r"_(\d{4})_", filename)
            return int(match.group(1)) if match else 0
            
        latest_zips = {k: max(v, key=_zip_year) for k, v in grouped.items()}
        
        processing_order = ["main", "sch_h", "sch_i", "sf"]
        
        for file_type in processing_order:
            if file_type not in latest_zips:
                continue
                
            zip_name = latest_zips[file_type]
            zip_path = os.path.join(data_dir, zip_name)
            print(f"[Sync] Parsing {file_type.upper()} archives: {zip_name}")
            
            if file_type == "main":
                mapping = {
                    "SPONS_DFE_EIN": ["SPONS_DFE_EIN", "SPONSOR_DFE_EIN", "EIN"],
                    "SPONS_DFE_NAME": ["SPONS_DFE_NAME", "SPONSOR_DFE_NAME", "SF_SPONSOR_NAME"],
                    "PLAN_NAME": ["PLAN_NAME", "SF_PLAN_NAME"],
                    "TOT_ACTIVE_PARTCP_CNT": ["TOT_ACTIVE_PARTCP_CNT", "SF_TOT_ACT_PARTCP_EOY_CNT"],
                    "TOT_ACT_RTD_SEP_BENEF_CNT": ["TOT_ACT_RTD_SEP_BENEF_CNT", "SF_TOT_ACT_RTD_SEP_BENEF_CNT"],
                    "SCH_H_ATTACHED_IND": ["SCH_H_ATTACHED_IND"],
                    "SCH_I_ATTACHED_IND": ["SCH_I_ATTACHED_IND"],
                    "SPONS_DFE_MAIL_US_ADDRESS1": ["SPONS_DFE_MAIL_US_ADDRESS1", "SPONSOR_DFE_MAIL_US_ADDRESS1", "SF_SPONS_US_ADDRESS1"],
                    "SPONS_DFE_MAIL_US_CITY": ["SPONS_DFE_MAIL_US_CITY", "SPONSOR_DFE_MAIL_US_CITY", "SF_SPONS_US_CITY"],
                    "SPONS_DFE_MAIL_US_STATE": ["SPONS_DFE_MAIL_US_STATE", "SPONSOR_DFE_MAIL_US_STATE", "SF_SPONS_US_STATE"],
                    "SPONS_DFE_MAIL_US_ZIP": ["SPONS_DFE_MAIL_US_ZIP", "SPONSOR_DFE_MAIL_US_ZIP", "SF_SPONS_US_ZIP"]
                }
            elif file_type == "sch_h":
                mapping = {
                    "SCH_H_EIN": ["SCH_H_EIN", "EIN"],
                    "TOT_ASSETS_EOY_AMT": ["TOT_ASSETS_EOY_AMT"],
                    "TOT_ADMIN_EXPENSES_AMT": ["TOT_ADMIN_EXPENSES_AMT"],
                    "TOT_CORRECTIVE_DISTRIB_AMT": ["TOT_CORRECTIVE_DISTRIB_AMT"]
                }
            elif file_type == "sch_i":
                mapping = {
                    "SCH_I_EIN": ["SCH_I_EIN", "EIN"],
                    "SMALL_TOT_ASSETS_EOY_AMT": ["SMALL_TOT_ASSETS_EOY_AMT"],
                    "SMALL_ADMIN_SRVC_PROVIDERS_AMT": ["SMALL_ADMIN_SRVC_PROVIDERS_AMT"],
                    "SMALL_CORRECTIVE_DISTRIB_AMT": ["SMALL_CORRECTIVE_DISTRIB_AMT"]
                }
            elif file_type == "sf":
                mapping = {
                    "SF_SPONS_EIN": ["SF_SPONS_EIN", "EIN"],
                    "SF_SPONSOR_NAME": ["SF_SPONSOR_NAME"],
                    "SF_PLAN_NAME": ["SF_PLAN_NAME"],
                    "SF_TOT_ACT_PARTCP_EOY_CNT": ["SF_TOT_ACT_PARTCP_EOY_CNT"],
                    "SF_TOT_ACT_RTD_SEP_BENEF_CNT": ["SF_TOT_ACT_RTD_SEP_BENEF_CNT"],
                    "SF_TOT_ASSETS_EOY_AMT": ["SF_TOT_ASSETS_EOY_AMT"],
                    "SF_ADMIN_SRVC_PROVIDERS_AMT": ["SF_ADMIN_SRVC_PROVIDERS_AMT"],
                    "SF_CORRECTIVE_DEEMED_DISTR_AMT": ["SF_CORRECTIVE_DEEMED_DISTR_AMT"],
                    "SF_SPONS_US_ADDRESS1": ["SF_SPONS_US_ADDRESS1"],
                    "SF_SPONS_US_CITY": ["SF_SPONS_US_CITY"],
                    "SF_SPONS_US_STATE": ["SF_SPONS_US_STATE"],
                    "SF_SPONS_US_ZIP": ["SF_SPONS_US_ZIP"],
                    "SF_ADMIN_NAME": ["SF_ADMIN_NAME"]
                }
                
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    csv_files = [n for n in z.namelist() if n.lower().endswith(".csv")]
                    if not csv_files:
                        continue
                        
                    # Pre-scan headers to dynamically build usecols constraint list
                    sample_df = pd.read_csv(z.open(csv_files[0]), nrows=5, low_memory=False)
                    use_cols = []
                    for target, sources in mapping.items():
                        for src in sources:
                            match_col = [c for c in sample_df.columns if c.upper() == src.upper()]
                            if match_col:
                                use_cols.append(match_col[0])
                                break
                                
                    with z.open(csv_files[0]) as handle:
                        chunk_idx = 0
                        chunk_size = 20000
                        # Read and upsert in chunks of 20,000 records
                        for chunk in pd.read_csv(handle, usecols=use_cols, chunksize=chunk_size, low_memory=False):
                            chunk_idx += 1
                            records = clean_and_map_chunk(chunk, mapping, file_type)
                            if records:
                                bulk_upsert_audits(db, records, file_type)
                                
                            if chunk_idx % 10 == 0:
                                print(f"  Processed {chunk_idx * chunk_size} filings...")
                                
            except Exception as zip_err:
                print(f"[Sync] Error processing ZIP {zip_name}: {zip_err}")

    # 3. Sync Excel Prospects (OneDrive prioritized)
    onedrive_excel = "C:\\Users\\nicks\\OneDrive\\Documents\\Combined 401k Prospecting Plan.xlsx"
    local_excel = config.EXCEL_PROSPECT_FILE
    excel_file = onedrive_excel if os.path.exists(onedrive_excel) else local_excel
    
    if os.path.exists(excel_file):
        try:
            print(f"[Sync] Syncing Excel prospects from: {excel_file}")
            prospects_df = pd.read_excel(excel_file, header=5)
            
            # Normalize column names (the Excel file uses 'Company', 'Contact', etc.)
            prospects_df = prospects_df.rename(columns={
                'Company': 'Employer Name',
                'Contact': 'Contact Name',
                'EMAIL': 'EMAIL'
            })
            
            if 'Employer Name' not in prospects_df.columns:
                if 'Company' in prospects_df.columns:
                    prospects_df = prospects_df.rename(columns={'Company': 'Employer Name'})
                else:
                    prospects_df['Employer Name'] = "Unknown"

            prospects_df = prospects_df.dropna(subset=['Employer Name'])
            
            db.query(Prospect).filter_by(tenant_id=tenant.id).delete()
            db.commit()

            print(f"[Sync] Mapping {len(prospects_df)} excel contacts to system pipeline...")
            seen_prospects = {}
            for _, row in prospects_df.iterrows():
                employer_name = str(row.get('Employer Name')).strip()
                if not employer_name or employer_name.lower() in ["nan", "none", "company"]:
                    continue
                
                ein = None
                if 'EIN' in row.index and pd.notna(row.get('EIN')):
                    ein = normalize_ein(row.get('EIN'))
                
                if not ein:
                    # Optimized lookup from Form5500Audit database
                    # 1. Try exact match (sub-millisecond, uses index)
                    audit_match = db.query(Form5500Audit).filter(Form5500Audit.employer_name == employer_name).first()
                    if not audit_match:
                        # 2. Try exact uppercase match
                        audit_match = db.query(Form5500Audit).filter(Form5500Audit.employer_name == employer_name.upper()).first()
                    if not audit_match:
                        # 3. Try prefix match (fast, uses index)
                        audit_match = db.query(Form5500Audit).filter(Form5500Audit.employer_name.like(f"{employer_name}%")).first()
                    
                    if audit_match:
                        ein = audit_match.ein
                    else:
                        import hashlib
                        hash_obj = hashlib.md5(employer_name.encode('utf-8'))
                        ein = "".join(c for c in hash_obj.hexdigest() if c.isdigit())[:9].zfill(9)

                contact_name = str(row.get('Contact Name', row.get('Contact'))).strip() if pd.notna(row.get('Contact Name', row.get('Contact'))) else None
                contact_email = str(row.get('EMAIL')).strip() if 'EMAIL' in row.index and pd.notna(row.get('EMAIL')) else None
                
                if not contact_email and 'Phone#/Email' in row.index and pd.notna(row.get('Phone#/Email')):
                    val = str(row.get('Phone#/Email')).strip()
                    if "@" in val:
                        contact_email = val

                total_assets = None
                if 'Assets' in row.index and pd.notna(row.get('Assets')):
                    try:
                        total_assets = float(row.get('Assets'))
                    except Exception:
                        pass

                active_participants = None
                if 'Active Participants' in row.index and pd.notna(row.get('Active Participants')):
                    try:
                        clean_part = "".join(c for c in str(row.get('Active Participants')) if c.isdigit())
                        if clean_part:
                            active_participants = int(clean_part)
                    except Exception:
                        pass

                provider = str(row.get('Provider')).strip() if 'Provider' in row.index and pd.notna(row.get('Provider')) else None
                industry = str(row.get('Industry')).strip() if 'Industry' in row.index and pd.notna(row.get('Industry')) else None

                contact_phone = None
                if 'Phone#/Email' in row.index and pd.notna(row.get('Phone#/Email')):
                    val = str(row.get('Phone#/Email')).strip()
                    if "@" not in val:
                        contact_phone = val

                if ein in seen_prospects:
                    existing = seen_prospects[ein]
                    if not existing.contact_name and contact_name:
                        existing.contact_name = contact_name
                    if not existing.contact_email and contact_email:
                        existing.contact_email = contact_email
                    if not existing.contact_phone and contact_phone:
                        existing.contact_phone = contact_phone
                    continue

                prospect = Prospect(
                    tenant_id=tenant.id,
                    ein=ein,
                    employer_name=employer_name,
                    status="Lead",
                    notes="",
                    contact_name=contact_name,
                    contact_email=contact_email,
                    contact_phone=contact_phone,
                    total_assets=total_assets,
                    active_participants=active_participants,
                    provider=provider,
                    industry=industry
                )
                db.add(prospect)
                seen_prospects[ein] = prospect
            db.commit()
        except Exception as e:
            print(f"[Sync] Excel prospects mapping error: {e}")

    # 4. Migrate status changes from legacy update table (if present)
    try:
        legacy_table_query = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='pipeline_updates'")).fetchone()
        if legacy_table_query:
            print(f"[Sync] Migration: Syncing pipeline updates status history...")
            legacy_updates = db.execute(text("SELECT * FROM pipeline_updates")).fetchall()
            col_query = db.execute(text("PRAGMA table_info(pipeline_updates)")).fetchall()
            col_names = [c[1] for c in col_query]
            
            for row_tuple in legacy_updates:
                row = dict(zip(col_names, row_tuple))
                ein = normalize_ein(row.get("ein"))
                if not ein:
                    continue
                
                prospect = db.query(Prospect).filter_by(tenant_id=tenant.id, ein=ein).first()
                if prospect:
                    if row.get("status"):
                        prospect.status = row.get("status")
                    if row.get("notes"):
                        prospect.notes = row.get("notes")
            db.commit()
    except Exception:
        pass

    print("[Sync] Background registry sweep completed successfully!")
