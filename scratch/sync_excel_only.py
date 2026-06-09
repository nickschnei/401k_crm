import sys
import os
import hashlib
sys.path.append(os.getcwd())

import pandas as pd
from sqlalchemy.orm import Session
from api.database import SessionLocal
from api.models import Prospect, Form5500Audit, Tenant
from dol_audit_engine import normalize_ein

def sync_excel_only():
    db = SessionLocal()
    try:
        print("[Sync] Running Excel-only sync with curated fields...")
        
        # 1. Ensure default tenant exists
        tenant = db.query(Tenant).filter_by(id="default_tenant").first()
        if not tenant:
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
            print("[Sync] Found existing default tenant.")

        # 2. Path to OneDrive spreadsheet or fallback local spreadsheet
        onedrive_excel = "C:\\Users\\nicks\\OneDrive\\Documents\\Combined 401k Prospecting Plan.xlsx"
        local_excel = "Combined 401k Prospecting Plan.xlsx"
        
        excel_file = onedrive_excel if os.path.exists(onedrive_excel) else local_excel
        print(f"[Sync] Using excel file: {excel_file}")
        
        is_onedrive = (excel_file == onedrive_excel)
        header_row = 5 if is_onedrive else 0
        
        prospects_df = pd.read_excel(excel_file, header=header_row)
        print(f"[Sync] Loaded {len(prospects_df)} raw rows from excel sheet.")
        
        # Map columns to target fields
        if is_onedrive:
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
        
        # Clean and filter empty rows
        prospects_df = prospects_df.dropna(subset=['Employer Name'])
        print(f"[Sync] Cleaned prospects count: {len(prospects_df)}")
        
        # Empty old prospects list to re-sync fresh OneDrive data
        deleted_count = db.query(Prospect).filter_by(tenant_id=tenant.id).delete()
        db.commit()
        print(f"[Sync] Cleared {deleted_count} existing prospects from the pipeline.")

        print(f"[Sync] Ingesting prospects into pipeline_prospects...")
        matched_count = 0
        hashed_count = 0
        
        for index, row in prospects_df.iterrows():
            employer_name = str(row.get('Employer Name')).strip()
            if not employer_name or employer_name.lower() in ["nan", "none", "company"]:
                continue
            
            # Check for EIN column, otherwise perform fuzzy match against DOL database
            ein = None
            if 'EIN' in row.index and pd.notna(row.get('EIN')):
                ein = normalize_ein(row.get('EIN'))
            
            if not ein:
                # Search DB audits for matches
                # Let's clean the name slightly to improve matching
                clean_name = employer_name.replace("INC", "").replace("Inc", "").replace("CO", "").replace("Co", "").replace("LLC", "").replace("Llc", "").strip()
                audit_match = db.query(Form5500Audit).filter(Form5500Audit.employer_name.ilike(f"%{clean_name}%")).first()
                if audit_match:
                    ein = audit_match.ein
                    matched_count += 1
                else:
                    # Fallback deterministic hash
                    hash_obj = hashlib.md5(employer_name.encode('utf-8'))
                    ein = "".join(c for c in hash_obj.hexdigest() if c.isdigit())[:9].zfill(9)
                    hashed_count += 1

            contact_name = str(row.get('Contact Name', row.get('Contact'))).strip() if pd.notna(row.get('Contact Name', row.get('Contact'))) else None
            contact_email = str(row.get('EMAIL')).strip() if 'EMAIL' in row.index and pd.notna(row.get('EMAIL')) else None
            
            # If email is missing, check Phone#/Email column
            if not contact_email and 'Phone#/Email' in row.index and pd.notna(row.get('Phone#/Email')):
                val = str(row.get('Phone#/Email')).strip()
                if "@" in val:
                    contact_email = val

            contact_phone = None
            if 'Phone#/Email' in row.index and pd.notna(row.get('Phone#/Email')):
                val = str(row.get('Phone#/Email')).strip()
                # Extract phone number if it has digits and no @
                if "@" not in val:
                    contact_phone = val
            
            # Curated columns from Excel
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
            
        db.commit()
        print(f"[Sync] Completed! Ingested {len(prospects_df)} prospects. (Matched to DOL: {matched_count}, Hashed fallback: {hashed_count})")
        
        # Verify db count
        total_in_db = db.query(Prospect).count()
        print(f"[Sync] Total prospects in database now: {total_in_db}")
        
    except Exception as e:
        db.rollback()
        print(f"[Sync] Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    sync_excel_only()
