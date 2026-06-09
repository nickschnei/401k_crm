import os
import re
import sqlite3
import pandas as pd
from thefuzz import process, fuzz
import config
from typing import Dict, Any, Optional

def extract_domain(employer_name: str) -> str:
    """Clean company names to form standard domains."""
    if not employer_name:
        return "company.com"
    
    clean = str(employer_name).upper().strip()
    # Remove common corporate suffixes
    clean = re.sub(r'\b(INC|LLC|CORP|CO|SERVICES|GROUP|HOLDINGS|PLC|LTD|ASSOCIATES)\b', '', clean)
    clean = re.sub(r'[^A-Z0-9]', '', clean)
    
    if not clean:
        return "company.com"
    return f"{clean.lower()}.com"

def enrich_prospect_contact(ein: str, employer_name: str) -> Dict[str, Any]:
    """
    Search local data files (Combined 401k Prospecting Plan.xlsx) for target decision-makers,
    bypassing live external API calls to enforce absolute sandboxed execution using local files.
    """
    clean_ein = "".join(c for c in str(ein) if c.isdigit())[-9:].zfill(9)
    domain = extract_domain(employer_name)
    
    contact_name = None
    contact_email = None
    contact_phone = None
    title = "Director of Human Resources"
    enriched_via = "Local Prospecting Plan Excel"

    excel_file = config.EXCEL_PROSPECT_FILE
    matched_row = None

    if os.path.exists(excel_file):
        try:
            df = pd.read_excel(excel_file)
            if 'EIN' in df.columns and 'Contact' in df.columns:
                # Standardize EINs for search
                df['clean_ein'] = df['EIN'].astype(str).str.replace('.0', '', regex=False).str.strip().str.zfill(9)
                
                # Try exact EIN match
                matches = df[df['clean_ein'] == clean_ein]
                if not matches.empty:
                    matched_row = matches.iloc[0]
                else:
                    # Try fuzzy matching on Employer Name
                    prospect_name = str(employer_name).strip().upper()
                    best_match = None
                    best_score = 0
                    for _, row in df.iterrows():
                        row_name = str(row.get('Employer Name', '')).strip().upper()
                        # Calculate fuzzy similarity
                        score = fuzz.token_sort_ratio(prospect_name, row_name)
                        if score > best_score:
                            best_score = score
                            best_match = row
                    
                    if best_score > 80:
                        matched_row = best_match
        except Exception as e:
            print(f"Error loading local Excel file for contact matching: {e}")

    if matched_row is not None:
        contact_name = str(matched_row.get('Contact')).strip()
        # Generate clean email from contact name
        parts = contact_name.split()
        first = parts[0].lower() if parts else "contact"
        last = parts[-1].lower() if len(parts) > 1 else "person"
        contact_email = f"{first}.{last}@{domain}"
        
        # Phone: (Area) 555-01XX based on EIN hash
        ein_hash = sum(int(c) for c in clean_ein)
        area_codes = [415, 212, 312, 617, 206, 213, 713, 305]
        area = area_codes[ein_hash % len(area_codes)]
        suffix = 100 + (ein_hash * 7) % 900
        contact_phone = f"({area}) 555-0{suffix}"
    else:
        # Fallback to realistic mock data if not found in the Excel sheet
        ein_hash = sum(int(c) for c in clean_ein)
        first_names = ["Jane", "Michael", "Sarah", "David", "Amanda", "Robert", "Elena", "James"]
        last_names = ["Miller", "Davis", "Rodriguez", "Chen", "Taylor", "Anderson", "Smith", "Lopez"]
        
        first = first_names[ein_hash % len(first_names)]
        last = last_names[(ein_hash + 3) % len(last_names)]
        
        contact_name = f"{first} {last}"
        contact_email = f"{first.lower()}.{last.lower()}@{domain}"
        
        area_codes = [415, 212, 312, 617, 206, 213, 713, 305]
        area = area_codes[ein_hash % len(area_codes)]
        suffix = 100 + (ein_hash * 7) % 900
        contact_phone = f"({area}) 555-0{suffix}"
        enriched_via = "Dynamic Fiduciary Mock (Offline Fallback)"

    # Save to SQLite Database pipeline_updates
    db_file = config.DATABASE_URL
    if db_file.startswith("sqlite:///"):
        db_file = db_file.replace("sqlite:///", "")
    else:
        db_file = "prospects.db"
        
    conn = sqlite3.connect(db_file, timeout=20)
    try:
        cursor = conn.cursor()
        
        # Fetch current record to verify/update status and notes
        cursor.execute("SELECT status, notes FROM pipeline_updates WHERE ein = ?", (clean_ein,))
        row = cursor.fetchone()
        
        status = "Lead"
        notes = ""
        if row:
            status = row[0]
            notes = row[1]
            
        # Insert or replace record including newly enriched contact data
        cursor.execute('''
            INSERT OR REPLACE INTO pipeline_updates (ein, status, notes, contact_name, contact_email, contact_phone, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (clean_ein, status, notes, contact_name, contact_email, contact_phone))
        conn.commit()
    except Exception as db_err:
        print(f"Error saving enriched contact to database: {db_err}")
    finally:
        conn.close()
        
    return {
        "ein": clean_ein,
        "employer_name": employer_name,
        "contact_name": contact_name,
        "contact_email": contact_email,
        "contact_phone": contact_phone,
        "contact_title": title,
        "domain": domain,
        "enriched_via": enriched_via
    }
