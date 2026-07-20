import streamlit as st
import pandas as pd
import core
import sqlite3
import config
from dol_audit_engine import build_advisor_pitch_script, get_audit_by_ein

# Component and View Imports (SaaS Split Structure)
from components.metrics import render_custom_metric, get_participation_color, get_fee_color
from components.threats import display_threat_alert, display_empty_state
from views.pipeline import render_pipeline_view
from views.discovery import render_discovery_view

def get_prospect_audit_from_db(ein: str, db_path: str = 'prospects.db') -> dict | None:
    """Extract the newly added schema rows from the prospects database table for a given EIN."""
    if not ein:
        return None
    # Normalize EIN
    digits = "".join(character for character in str(ein) if character.isdigit())
    if not digits:
        return None
    normalized_ein = digits[-9:].zfill(9)
    
    # Parse DB file path from sqlite URI if present
    db_file = config.DATABASE_URL
    if db_file.startswith("sqlite:///"):
        db_file = db_file.replace("sqlite:///", "")
    else:
        db_file = db_path
        
    conn = sqlite3.connect(db_file, timeout=20)
    try:
        cursor = conn.cursor()
        # Verify prospects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prospects'")
        if not cursor.fetchone():
            return None
            
        cursor.execute("PRAGMA table_info(prospects)")
        columns = [row[1] for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM prospects WHERE ein = ?", (normalized_ein,))
        row = cursor.fetchone()
        if row:
            return dict(zip(columns, row))
    except Exception as e:
        print(f"Error querying prospects DB: {e}")
    finally:
        conn.close()
    return None

def build_custom_outreach_pitch(record: dict | None, employer_name: str) -> str:
    """Programmatically customize the pitch value based on which specific threshold flags are active."""
    name = employer_name if employer_name and str(employer_name).strip() else "your organization"
    
    if not record:
        return f"""Subject: Strategic 401(k) Fiduciary Review for {name}

Dear Plan Sponsor at {name},

I am reaching out to introduce our specialized 401(k) fiduciary advisory services. We assist companies like yours in optimizing plan design, reducing administrative friction, and ensuring fee competitiveness.

We would be glad to run a complimentary plan diagnostic and benchmark report comparing your plan with peer sponsors. This review focuses on:
• Fiduciary oversight and fee validation
• Modernized participant education and auto-enrollment design
• Investment menu optimization and risk management

Are you available for a brief 15-minute introductory conversation next week to see if we can uncover efficiency gains for your plan?

Best regards,
[Your Name]
[Your Fiduciary Advisory Firm]
[Contact Details]"""

    fee_flag = bool(record.get("fee_flag"))
    part_flag = bool(record.get("participation_flag"))
    compliance_failed = bool(record.get("compliance_failed"))
    
    fee_ratio = record.get("fee_ratio", 0.0)
    participation_rate = record.get("participation_rate", 0.0)
    fee_bps = int(fee_ratio * 10000)
    
    subject = f"Fiduciary Health & Fee Diagnostic for {name} 401(k) Plan"
    
    lines = [
        f"Subject: {subject}",
        "",
        f"Dear Plan Sponsor at {name},",
        "",
        "I recently conducted a comprehensive fiduciary health audit of the Department of Labor Form 5500 filings "
        f"for the {name} 401(k) plan. Based on our analysis, we identified key opportunities to optimize "
        "your plan design, enhance participant returns, and insulate your committee from regulatory risk.",
        "",
    ]
    
    if fee_flag or part_flag or compliance_failed:
        lines.append("Specifically, our analysis flagged the following areas for immediate review:")
        
        if fee_flag:
            lines.extend([
                f"• **Excessive Plan Fees**: Your plan administrative fee ratio is currently running at {fee_ratio * 100:.2f}% ({fee_bps} bps), which exceeds the 60 basis points industry threshold. As fiduciaries, plan sponsors are legally required to verify that recordkeeping, advisory, and administrative costs are reasonable. We can help execute a fee compression audit to reduce vendor drag and boost employee savings.",
            ])
            
        if part_flag:
            lines.extend([
                f"• **Participation Gap**: The plan's active employee participation rate is {participation_rate * 100:.1f}%, falling below the 70% target. Low participation often triggers discrimination testing limits and restricts executive savings. We specialize in auto-enrollment designs and streamlined education plans to drive engagement.",
            ])
            
        if compliance_failed:
            lines.extend([
                "• **Historic Compliance Alert**: The filing records historic corrective distributions. Compliance testing failures are costly and administratively intensive. We can structure safe harbor provisions or restructure matching parameters to prevent future non-discrimination failures.",
            ])
            
        lines.append("")
    else:
        lines.extend([
            "Your plan's primary indicators currently align well with benchmark thresholds. However, periodic fee validation and fiduciary structural checks are highly recommended to ensure you continue to receive institutional pricing as your assets grow.",
            "",
        ])
        
    lines.extend([
        "We would love to offer your committee a complimentary, side-by-side benchmarking report that details actionable steps to minimize fiduciary risk and elevate employee retirement success.",
        "",
        "Are you open to a brief 15-minute call next Tuesday or Thursday to walk through our findings?",
        "",
        "Best regards,",
        "[Your Name]",
        "[Your Fiduciary Advisory Firm]",
        "[Contact Details]"
    ])
    
    return "\n".join(lines)

# --- CONFIGURATION & CONSTANTS ---
st.set_page_config(
    page_title="401(k) Prospecting CRM",
    layout="wide",
    page_icon="💼"
)

# --- MODERN PREMIUM CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* Apply modern typography globally */
html, body, [class*="css"], .stApp {
    font-family: 'Outfit', sans-serif;
    background-color: #0f172a; /* Slate 900 */
    color: #e2e8f0; /* Slate 200 */
}

/* Force Outfit on all headers */
h1, h2, h3, h4, h5, h6, .section-header {
    font-family: 'Outfit', sans-serif !important;
}

/* Gradient Title */
.gradient-title {
    background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 50%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.8rem;
    margin-bottom: 5px;
    letter-spacing: -0.5px;
}

.subtitle-text {
    color: #94a3b8; /* Slate 400 */
    font-size: 1.1rem;
    margin-bottom: 30px;
    font-weight: 400;
}

/* Premium Card Metrics styling (Glassmorphism Overhaul) */
div[data-testid="stMetric"] {
    background: rgba(30, 41, 59, 0.5) !important; /* Glassmorphism background */
    border: 1px solid rgba(255, 255, 255, 0.1) !important; /* Thin premium border */
    border-radius: 16px !important;
    padding: 20px 24px !important;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5) !important;
    backdrop-filter: blur(10px) !important; /* Backdrop filter blur */
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-4px) !important;
    border-color: rgba(99, 102, 241, 0.4) !important; /* Indigo accent hover border */
    box-shadow: 0 20px 40px -15px rgba(99, 102, 241, 0.2) !important;
}

div[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #94a3b8 !important;
    font-weight: 600 !important;
}

div[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Custom premium-styled metric cards (for dynamic coloring) */
.custom-metric {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 16px;
}

.custom-metric:hover {
    transform: translateY(-4px);
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 20px 40px -15px rgba(99, 102, 241, 0.2);
}

.custom-metric-label {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #94a3b8;
    font-weight: 600;
    margin-bottom: 8px;
}

.custom-metric-value {
    font-size: 2rem;
    font-weight: 700;
}

/* Subheaders style with increased letter spacing */
.section-header {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f1f5f9;
    border-left: 4px solid #3b82f6;
    padding-left: 12px;
    margin-top: 30px;
    margin-bottom: 20px;
    letter-spacing: 1.5px !important; /* Increased letter spacing */
    text-transform: uppercase;
}

/* Custom styles for selectbox/inputs label */
label[data-testid="stWidgetLabel"] {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: #cbd5e1 !important;
}

/* Make Dataframe beautiful and blend in */
div[data-testid="stDataFrame"] {
    background: rgba(30, 41, 59, 0.4);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 8px;
}

/* Threat Alert custom components CSS */
@keyframes pulse-amber {
    0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.5); }
    70% { box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); }
    100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
}

@keyframes glow-red {
    0% { border-color: rgba(239, 68, 68, 0.4); box-shadow: 0 0 8px rgba(239, 68, 68, 0.2); }
    50% { border-color: rgba(239, 68, 68, 0.8); box-shadow: 0 0 16px rgba(239, 68, 68, 0.5); }
    100% { border-color: rgba(239, 68, 68, 0.4); box-shadow: 0 0 8px rgba(239, 68, 68, 0.2); }
}

.threat-alert {
    padding: 16px 20px;
    border-radius: 12px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    font-size: 0.95rem;
    backdrop-filter: blur(8px);
    line-height: 1.5;
}

.threat-alert.excessive-fees {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #fca5a5;
    animation: glow-red 3s infinite ease-in-out; /* Glowing red border */
}

.threat-alert.participation-gaps {
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.4);
    color: #fde047;
    animation: pulse-amber 2s infinite ease-in-out; /* Amber pulse shadow */
}

.threat-alert.compliance-failed {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #fca5a5;
    animation: glow-red 3s infinite ease-in-out;
}

.threat-icon {
    font-size: 1.4rem;
}

.threat-content {
    flex-grow: 1;
}

/* Sidebar text area (Activity log/Notes) - keep it dark mode */
section[data-testid="stSidebar"] div[data-testid="stTextArea"] {
    background: rgba(15, 23, 42, 0.6) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] div[data-testid="stTextArea"] textarea {
    color: #e2e8f0 !important;
}

/* Main drafting desk outreach pitch - White premium letterhead paper style */
div.letterhead-container div[data-testid="stTextArea"] {
    background: #faf8f5 !important; /* Premium warm white/cream paper */
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3), inset 0 0 40px rgba(0, 0, 0, 0.05) !important;
    padding: 24px !important;
    border-top: 10px solid #3b82f6 !important; /* Elegant blue header accent line */
}

div.letterhead-container div[data-testid="stTextArea"] textarea {
    color: #1e293b !important; /* Slate 800 for high contrast readability */
    font-size: 1.05rem !important;
    line-height: 1.65 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Custom empty state CSS */
.empty-state-container {
    background: rgba(30, 41, 59, 0.3);
    border: 2px dashed rgba(59, 130, 246, 0.3);
    border-radius: 16px;
    padding: 48px 24px;
    text-align: center;
    backdrop-filter: blur(10px);
    margin: 20px 0;
    transition: all 0.3s ease;
}

.empty-state-container:hover {
    border-color: rgba(59, 130, 246, 0.6);
    background: rgba(30, 41, 59, 0.4);
}

.empty-state-icon {
    color: #3b82f6;
    margin-bottom: 18px;
    filter: drop-shadow(0 0 12px rgba(59, 130, 246, 0.4));
}

.empty-state-container h3 {
    color: #f1f5f9;
    font-size: 1.3rem;
    margin-bottom: 10px;
    font-weight: 600;
}

.empty-state-container p {
    color: #94a3b8;
    font-size: 0.95rem;
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.5;
}

</style>
""", unsafe_allow_html=True)

# --- DATABASE & DATA CACHING ---
core.init_db()

@st.cache_data
def load_crm_data(force=False):
    return core.load_and_merge_data(force_refresh=force)

try:
    prospects_df, discovery_df = load_crm_data()
except Exception as e:
    st.error(f"Error loading CRM data: {e}")
    prospects_df = pd.DataFrame(columns=['Employer Name', 'EIN', 'Total Assets', 'Participants', 'status', 'notes', 'match_key'])
    discovery_df = pd.DataFrame(columns=['Employer Name DOL', 'EIN', 'Total Assets', 'Participants', 'Plan Name', 'Administrator'])

def option_list(df, column, limit=75):
    if column not in df.columns:
        return ["All"]
    values = (
        df[column]
        .fillna("Unspecified")
        .astype(str)
        .str.strip()
    )
    values = values[values.ne("")]
    ranked_values = values.value_counts().head(limit).index.tolist()
    return ["All"] + sorted(ranked_values)

def parse_minimum_filter(selected_value, thresholds):
    return thresholds.get(selected_value, 0)

def parse_maximum_filter(selected_value, thresholds):
    return thresholds.get(selected_value)

def parse_zip_input(value):
    return core.normalize_zip(value)

def format_currency(value):
    if pd.isna(value) or value is None:
        return "N/A"
    return f"${float(value):,.0f}"

def format_percent(value, decimals=2):
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{float(value) * 100:.{decimals}f}%"

def audit_dict_from_row(row):
    if row is None:
        return {"found": False}
    keys = [
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
    audit = {key: row.get(key) for key in keys if key in row.index}
    audit["found"] = pd.notna(audit.get("EIN")) or pd.notna(row.get("total_assets"))
    return audit

def render_health_audit_panel(audit, employer_name):
    with st.expander("401(k) Health Audit", expanded=True):
        if not audit.get("found"):
            st.info(
                "No DOL audit data found for this EIN. Confirm Schedule H or I (or 5500-SF) "
                "filings are present in the DOL ZIP files."
            )
            return

        schedule_label = {
            "H": "Schedule H (large plan)",
            "I": "Schedule I (small plan)",
            "SF": "Form 5500-SF",
        }.get(audit.get("schedule_type"), "Unknown")
        st.caption(f"Filing source: **{schedule_label}** · EIN `{audit.get('EIN', 'N/A')}`")

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(render_custom_metric("Total Assets (EOY)", format_currency(audit.get("total_assets"))), unsafe_allow_html=True)
        
        act_part = audit.get("active_participants")
        m2.markdown(render_custom_metric(
            "Active Participants", 
            f"{int(act_part):,}" if pd.notna(act_part) else "N/A"
        ), unsafe_allow_html=True)
        
        elig = audit.get("total_eligible_employees")
        m3.markdown(render_custom_metric(
            "Eligible / Total Participants", 
            f"{int(elig):,}" if pd.notna(elig) else "N/A"
        ), unsafe_allow_html=True)
        
        m4.markdown(render_custom_metric("Admin Expenses", format_currency(audit.get("admin_expenses"))), unsafe_allow_html=True)

        m5, m6, m7 = st.columns(3)
        part_rate = audit.get("participation_rate")
        m5.markdown(render_custom_metric(
            "Participation Rate", 
            format_percent(part_rate, 1),
            get_participation_color(part_rate)
        ), unsafe_allow_html=True)
        
        fee_ratio = audit.get("fee_ratio")
        m6.markdown(render_custom_metric(
            "Fee Ratio (Admin / Assets)", 
            format_percent(fee_ratio, 2),
            get_fee_color(fee_ratio)
        ), unsafe_allow_html=True)
        
        corr_dist = audit.get("corrective_distributions")
        m7.markdown(render_custom_metric(
            "Corrective Distributions", 
            format_currency(corr_dist),
            "#ef4444" if pd.notna(corr_dist) and corr_dist > 0 else None
        ), unsafe_allow_html=True)

        # Threat Alert Boxes
        has_alerts = False
        if audit.get("fee_red_flag"):
            display_threat_alert(
                "excessive-fees", "🚨", "Excessive Fees Flagged",
                f"Administrative expenses exceed 60 basis points of plan assets ({format_percent(audit.get('fee_ratio'), 2)})."
            )
            has_alerts = True
        if audit.get("participation_red_flag"):
            display_threat_alert(
                "participation-gaps", "⚠️", "Participation Gap Flagged",
                f"Active employee participation is below 70% ({format_percent(audit.get('participation_rate'), 1)})."
            )
            has_alerts = True
        if audit.get("compliance_failed"):
            display_threat_alert(
                "compliance-failed", "🚨", "Historic Compliance Failure",
                "Corrective distributions were reported on the filing — review ADP/ACP testing and operational compliance."
            )
            has_alerts = True
        if not has_alerts:
            st.markdown("""
            <div class="threat-alert" style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.4); color: #a7f3d0;">
                <span class="threat-icon">✨</span>
                <div class="threat-content">
                    <strong>Fiduciary Standard Maintained</strong>: No active fee, participation, or compliance red flags are detected on this filing.
                </div>
            </div>
            """, unsafe_allow_html=True)

        pitch = build_advisor_pitch_script(audit, employer_name=employer_name)
        st.markdown("**Advisor Pitch Script**")
        st.text_area(
            "Advisor Pitch Script",
            value=pitch,
            height=280,
            label_visibility="collapsed",
        )

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.markdown("""
<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 20px;'>
    <span style='font-size: 2rem;'>💼</span>
    <h2 style='margin: 0; font-weight: 700; color: #f1f5f9;'>CRM Panel</h2>
</div>
""", unsafe_allow_html=True)

# Build unified employer/filing search indexing for sidebar audit selectbox
all_plans_dict = {} # Name -> EIN
ein_to_name = {} # EIN -> Name

# Index from prospects
for _, r in prospects_df.iterrows():
    name = r.get('Employer Name')
    ein = r.get('EIN')
    if pd.notna(name) and str(name).strip():
        n_str = str(name).strip()
        all_plans_dict[n_str] = ein
        if pd.notna(ein):
            ein_to_name[str(ein).zfill(9)] = n_str

# Index from discovery
if not discovery_df.empty:
    for _, r in discovery_df.iterrows():
        name = r.get('Employer Name DOL', r.get('Employer Name'))
        ein = r.get('EIN')
        if pd.notna(name) and str(name).strip():
            n_str = str(name).strip()
            if n_str not in all_plans_dict:
                all_plans_dict[n_str] = ein
            if pd.notna(ein):
                ein_to_name[str(ein).zfill(9)] = n_str

sorted_plans = sorted(all_plans_dict.keys())

st.sidebar.subheader("🩺 Fiduciary Plan Audit")
if sorted_plans:
    # Initialize session state for selected employer
    if 'selected_audit_employer' not in st.session_state:
        st.session_state['selected_audit_employer'] = sorted_plans[0]
        
    selected_audit_employer = st.sidebar.selectbox(
        "Select Plan to Audit:",
        sorted_plans,
        key="selected_audit_employer_widget",
        help="Select a plan from the combined database to execute a deep fiduciary diagnostic and review Form 5500 metrics."
    )
    st.session_state['selected_audit_employer'] = selected_audit_employer
    active_company_name = selected_audit_employer
    active_ein = all_plans_dict.get(selected_audit_employer)
else:
    st.sidebar.info("No plans available to audit.")
    active_company_name = None
    active_ein = None

# Sidebar Operations
st.sidebar.markdown("---")
st.sidebar.subheader("💳 Subscription Suite")

sub_state = core.get_subscription_state()
tier = sub_state.get("tier", "free")
st.sidebar.markdown(f"Current Tier: **⚡ {tier.upper()}**")

new_tier = st.sidebar.selectbox(
    "Change Subscription Tier (Demo):",
    ["Free", "Pro", "Enterprise"],
    index=["free", "pro", "enterprise"].index(tier),
    help="Demo subscription billing tier selector."
)
if new_tier.lower() != tier:
    core.update_subscription_state(new_tier.lower(), "active")
    st.sidebar.success(f"Upgraded to {new_tier} Plan!")
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Operations")

# Reload data button
if st.sidebar.button("🔄 Force Reload (Clear Cache)", use_container_width=True):
    st.cache_data.clear()
    prospects_df, discovery_df = load_crm_data(force=True)
    st.sidebar.success("Data reloaded from source!")
    st.rerun()

# --- MAIN APP LAYOUT ---
st.markdown("<h1 class='gradient-title'>401(k) Prospecting CRM</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle-text'>Enterprise lead retirement plan diagnostic & Form 5500 filings workspace</p>", unsafe_allow_html=True)

# Placeholder for premium active audit metrics panel
top_panel_placeholder = st.empty()

# Main Filter Bar
st.markdown("<div class='section-header'>🔍 Live Search & Filtering</div>", unsafe_allow_html=True)
f_col1, f_col2, f_col3, f_col4 = st.columns([2.1, 1, 1, 1])

with f_col1:
    search_query = st.text_input(
        "Search",
        placeholder="Employer, EIN, plan, admin, provider, contact...",
        value="",
        help="Enter any keyword to perform a global search across employer name, plan name, EIN, administrator, or service provider."
    )

with f_col2:
    min_asset_filter = st.selectbox(
        "Min Assets",
        ["$0", "$1M+", "$5M+", "$10M+", "$50M+"],
        help="Plans over $5M often require Schedule H audits. Plans between $1M and $5M represent prime targets for recordkeeping fee optimizations."
    )

with f_col3:
    part_filter = st.selectbox(
        "Min Participants",
        ["0", "100+", "500+", "1,000+", "5,000+"],
        help="Plans with over 100 participants generally trigger large plan filing requirements (Schedule H), demanding stricter fiduciary oversight."
    )

with f_col4:
    status_options = ["All", "Lead", "Researching", "Cold Called", "Meeting Set", "Disqualified"]
    status_filter = st.selectbox(
        "Pipeline Status", 
        status_options,
        index=0,
        help="Track and organize your outreach stages to prioritize active pipelines or focus on fresh research leads."
    )

# Use discovery_df (having full schema) for filter indexing values
df_filter_base = discovery_df.copy() if not discovery_df.empty else prospects_df.copy()

with st.expander("Advanced filters", expanded=True):
    af_col1, af_col2, af_col3, af_col4 = st.columns(4)
    with af_col1:
        max_asset_filter = st.selectbox(
            "Max Assets",
            ["No max", "Under $1M", "Under $5M", "Under $10M", "Under $50M"],
            help="Cap assets to target mid-market or small businesses where advisors can easily compress high retail fee structures."
        )
    with af_col2:
        max_part_filter = st.selectbox(
            "Max Participants",
            ["No max", "Under 100", "Under 500", "Under 1,000", "Under 5,000"],
            help="Limit participant counts to match your servicing capacity or focus on high-efficiency small-plan markets."
        )
    with af_col3:
        industry_filter = st.selectbox(
            "Industry",
            option_list(df_filter_base, "Industry"),
            disabled="Industry" not in df_filter_base.columns,
            help="Target specific high-margin industries or build sector-specific prospecting campaigns."
        )
    with af_col4:
        provider_filter = st.selectbox(
            "Provider",
            option_list(df_filter_base, "Broker/Provider"),
            disabled="Broker/Provider" not in df_filter_base.columns,
            help="Filter by existing broker/provider to target legacy competitors with outdated, expensive fee arrangements."
        )

    af_col5, af_col6, af_col7, af_col8 = st.columns(4)
    with af_col5:
        administrator_filter = st.selectbox(
            "Administrator",
            option_list(df_filter_base, "Administrator"),
            disabled="Administrator" not in df_filter_base.columns,
            help="Filter by Third Party Administrator (TPA) to identify plans using administrative platforms with known fee compression opportunities."
        )
    with af_col6:
        data_quality_filter = st.selectbox(
            "DOL Data",
            ["All", "Has DOL match", "Missing DOL match", "Has administrator", "Missing administrator"],
            help="Segment prospects by the availability of rich Department of Labor filing details to prioritize data-backed outreach."
        )
    with af_col7:
        sort_options = ["Total Assets", "Participants", "Employer Name", "Industry", "Broker/Provider", "Administrator"]
        sort_options = [opt for opt in sort_options if opt in df_filter_base.columns]
        sort_by = st.selectbox("Sort By", sort_options or ["Employer Name"], help="Sort records to prioritize by scale of potential assets or size of participant base.")
    with af_col8:
        sort_direction = st.selectbox("Sort", ["Descending", "Ascending"], help="Order ascending or descending to focus on top-tier prospects or small, fast-growth plans.")

    af_col9, af_col10, af_col11, _ = st.columns(4)
    with af_col9:
        employer_name_filter = st.selectbox(
            "Employer Name",
            ["All", "Has employer name", "Missing employer name"],
            help="Ensure records contain valid legal employer names for accurate outreach and corporate profiling."
        )
    with af_col10:
        address_filter = st.selectbox(
            "Address",
            ["All", "Has ZIP code", "Missing ZIP code", "Has address/ZIP", "Missing address/ZIP"],
            help="Verify address completeness for mail campaigns or regional geographic filtering."
        )
    with af_col11:
        origin_zip_input = st.text_input(
            "Current ZIP",
            placeholder="46220",
            max_chars=10,
            help="Enter your ZIP code to establish a reference point for proximity-based prospecting and local visits."
        )

    af_col12, _, _, _ = st.columns(4)
    with af_col12:
        max_distance_miles = st.number_input(
            "Max Distance (miles)",
            min_value=0,
            max_value=3000,
            value=0,
            step=25,
            help="Filter prospects close to your location to optimize travel time and schedule in-person coffee meetings."
        )

asset_min_thresholds = {
    "$1M+": 1000000,
    "$5M+": 5000000,
    "$10M+": 10000000,
    "$50M+": 50000000,
}
asset_max_thresholds = {
    "Under $1M": 1000000,
    "Under $5M": 5000000,
    "Under $10M": 10000000,
    "Under $50M": 50000000,
}
participant_min_thresholds = {
    "100+": 100,
    "500+": 500,
    "1,000+": 1000,
    "5,000+": 5000,
}
participant_max_thresholds = {
    "Under 100": 99,
    "Under 500": 499,
    "Under 1,000": 999,
    "Under 5,000": 4999,
}

min_assets_val = parse_minimum_filter(min_asset_filter, asset_min_thresholds)
max_assets_val = parse_maximum_filter(max_asset_filter, asset_max_thresholds)
min_parts_val = parse_minimum_filter(part_filter, participant_min_thresholds)
max_parts_val = parse_maximum_filter(max_part_filter, participant_max_thresholds)
origin_zip = parse_zip_input(origin_zip_input)

if origin_zip_input and not origin_zip:
    st.warning("Enter a valid 5-digit ZIP code for the distance filter.")

# Compile state dictionary for view parameters
filters_state = {
    "search": search_query,
    "min_assets": min_assets_val,
    "max_assets": max_assets_val,
    "min_participants": min_parts_val,
    "max_participants": max_parts_val,
    "status": status_filter,
    "industry": industry_filter,
    "provider": provider_filter,
    "administrator": administrator_filter,
    "employer_name_filter": employer_name_filter,
    "address_filter": address_filter,
    "origin_zip": origin_zip,
    "max_distance_miles": max_distance_miles,
    "data_quality": data_quality_filter,
    "sort_by": sort_by,
    "sort_direction": sort_direction
}

# --- ACTIVE FIDUCIARY AUDIT CALCULATION ---
audit_row = None
if active_company_name:
    match_p = prospects_df[prospects_df['Employer Name'] == active_company_name]
    if not match_p.empty:
        audit_row = match_p.iloc[0]
    else:
        match_d = discovery_df[discovery_df['Employer Name DOL'] == active_company_name] if not discovery_df.empty else pd.DataFrame()
        if not match_d.empty:
            audit_row = match_d.iloc[0]

# EIN search routing
clean_search = "".join(c for c in search_query if c.isdigit())
if len(clean_search) == 9:
    active_ein = clean_search
    active_company_name = ein_to_name.get(active_ein, f"Plan EIN {active_ein}")
elif audit_row is not None and pd.notna(audit_row.get("EIN")):
    active_ein = str(audit_row.get("EIN"))

prospect_audit_record = None
if active_ein:
    clean_ein = "".join(c for c in str(active_ein) if c.isdigit())[-9:].zfill(9)
    prospect_audit_record = get_prospect_audit_from_db(clean_ein)
    
    if not prospect_audit_record or pd.isna(prospect_audit_record.get("total_assets")):
        try:
            from utils.audit_engine import run_plan_audit
            extract_dir = core.ensure_extracted_csvs()
            run_plan_audit(clean_ein, extract_dir)
            prospect_audit_record = get_prospect_audit_from_db(clean_ein)
        except Exception as e:
            print(f"Error running plan audit for EIN {clean_ein}: {e}")

# Render Active Prospect Intelligence panel
if prospect_audit_record:
    total_assets_val = prospect_audit_record.get("total_assets", 0.0)
    participation_rate_val = prospect_audit_record.get("participation_rate", 0.0)
    fee_ratio_val = prospect_audit_record.get("fee_ratio", 0.0)
    
    participation_flag_val = bool(prospect_audit_record.get("participation_flag"))
    fee_flag_val = bool(prospect_audit_record.get("fee_flag"))
    compliance_failed_val = bool(prospect_audit_record.get("compliance_failed"))
    
    with top_panel_placeholder.container():
        st.markdown(f"<div class='section-header'>🚨 Fiduciary Intelligence & Health Audit: {active_company_name}</div>", unsafe_allow_html=True)
        
        part_color = get_participation_color(participation_rate_val)
        fee_color = get_fee_color(fee_ratio_val)
        fee_bps = int(fee_ratio_val * 10000)
        
        metrics_list = [
            ("Total Plan Assets", format_currency(total_assets_val), None),
            ("Plan Participation Rate", format_percent(participation_rate_val, 1), part_color),
            ("Plan Fee Ratio", f"{fee_ratio_val * 100:.2f}% ({fee_bps} bps)", fee_color)
        ]
        
        cols = st.columns(3)
        for col, m_data in zip(cols, metrics_list):
            label, value, color = m_data
            with col:
                st.markdown(render_custom_metric(label, value, color), unsafe_allow_html=True)
        
        # Threat Alert Boxes
        has_flags = False
        if participation_flag_val:
            display_threat_alert(
                "participation-gaps", "⚠️", "Low Participation Flagged",
                f"Active employee participation is {participation_rate_val * 100:.1f}%, which is below the 70.0% target threshold."
            )
            has_flags = True
        if fee_flag_val:
            display_threat_alert(
                "excessive-fees", "🚨", "Excessive Fees Flagged",
                f"Administrative expenses exceed 60 basis points of plan assets ({fee_ratio_val * 100:.2f}% or {fee_bps} bps)."
            )
            has_flags = True
        if compliance_failed_val:
            display_threat_alert(
                "compliance-failed", "🚨", "Historic Compliance Failure",
                "Corrective distributions were reported on the filing. Testing failures or operational non-compliance have occurred."
            )
            has_flags = True
        if not has_flags:
            st.markdown("""
            <div class="threat-alert" style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.4); color: #a7f3d0;">
                <span class="threat-icon">✨</span>
                <div class="threat-content">
                    <strong>Fiduciary Standard Maintained</strong>: No active fee, participation, or compliance red flags are detected on this filing.
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
else:
    with top_panel_placeholder.container():
        display_empty_state()

# --- SIDEBAR RECORD UPDATES (Prospects Only) ---
is_selected_prospect = active_company_name in prospects_df['Employer Name'].values if active_company_name else False
if is_selected_prospect:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📝 Update Pipeline Record")
    
    firm_row = prospects_df[prospects_df['Employer Name'] == active_company_name].iloc[0]
    match_key = firm_row.get('match_key', firm_row.get('EIN', active_company_name))
    
    st.sidebar.markdown(f"**Employer:** `{active_company_name}`")
    st.sidebar.markdown(f"**EIN:** `{firm_row.get('EIN', 'N/A')}`")
    
    # Render Contact Card
    contact_name = firm_row.get('contact_name')
    contact_email = firm_row.get('contact_email')
    contact_phone = firm_row.get('contact_phone')
    
    if pd.notna(contact_name) and str(contact_name).strip():
        st.sidebar.markdown(f"👤 **HR Contact:** {contact_name}")
        if pd.notna(contact_email):
            st.sidebar.markdown(f"✉️ **Email:** {contact_email}")
        if pd.notna(contact_phone):
            st.sidebar.markdown(f"📞 **Phone:** {contact_phone}")
    else:
        st.sidebar.markdown("👤 **HR Contact:** None on file")
        
    sub_state = core.get_subscription_state()
    current_tier = sub_state.get("tier", "free")
    
    if st.sidebar.button("🔍 Enrich Contact Info", use_container_width=True):
        if current_tier == "free":
            st.sidebar.warning("⭐ Contact Enrichment is a Pro/Enterprise feature. Please upgrade your plan in the Panel below.")
        else:
            with st.spinner("Searching local Excel database..."):
                from services.enrichment import enrich_prospect_contact
                res = enrich_prospect_contact(firm_row.get('EIN'), active_company_name)
                st.sidebar.success(f"Enriched: {res['contact_name']}")
                st.cache_data.clear()
                st.rerun()
                
    st.sidebar.markdown("---")
    
    status_options = ["Lead", "Researching", "Cold Called", "Meeting Set", "Disqualified"]
    current_status = firm_row.get('status', 'Lead')
    if current_status not in status_options:
        current_status = "Lead"
        
    new_status = st.sidebar.selectbox(
        "Pipeline Status",
        status_options,
        index=status_options.index(current_status),
        help="Update the outreach progression stage for this corporate prospect."
    )
    
    current_notes = firm_row.get('notes', '')
    new_notes = st.sidebar.text_area(
        "Prospect Notes / Activity Log",
        value=current_notes if pd.notna(current_notes) else "",
        height=120,
        help="Log communication history, meeting outcomes, or plan design analysis notes."
    )
    
    if st.sidebar.button("💾 Save Pipeline Update", use_container_width=True, type="primary"):
        core.save_update(match_key, new_status, new_notes)
        st.sidebar.success(f"Updated '{active_company_name}' status to {new_status}!")
        st.cache_data.clear()
        st.rerun()
else:
    st.sidebar.markdown("---")
    st.sidebar.info("ℹ️ The selected plan is currently in raw Discovery Mode. Register it in your pipeline excel sheet to unlock CRM pipeline updates.")

# --- MAIN TABS NAVIGATOR ---
tab1, tab2 = st.tabs(["📋 Prospects Pipeline", "🔍 Discovery Mode"])

with tab1:
    render_pipeline_view(filters_state)

with tab2:
    render_discovery_view(filters_state)

# --- 401(k) HEALTH AUDIT REPORTING SECTION ---
st.markdown("<div class='section-header'>🩺 Plan Health Audit</div>", unsafe_allow_html=True)
if audit_row is not None:
    audit_payload = audit_dict_from_row(audit_row)
    if not audit_payload.get("found") and pd.notna(audit_row.get("EIN")):
        audit_payload = get_prospect_audit_from_db(audit_row.get("EIN"))
        if not audit_payload or not audit_payload.get("found"):
            audit_payload = get_audit_by_ein(audit_row.get("EIN"))
            
    render_health_audit_panel(audit_payload, employer_name=active_company_name or "this plan")
else:
    display_empty_state()

# --- BASE PANEL: CUSTOMIZED FIDUCIARY COLD-OUTREACH PITCH ---
st.markdown("<div class='section-header'>📨 Customized Fiduciary Cold-Outreach Pitch</div>", unsafe_allow_html=True)
pitch_company_name = active_company_name or "your prospect"
custom_pitch = build_custom_outreach_pitch(prospect_audit_record, pitch_company_name)

st.markdown("<div class='letterhead-container'>", unsafe_allow_html=True)
st.text_area(
    "Fiduciary Cold-Outreach Pitch (Copy & Customize)",
    value=custom_pitch,
    height=320,
    help="This script is dynamically customized based on the active prospect's Form 5500 health red flags.",
    key="customized_cold_outreach_pitch_textarea",
    label_visibility="collapsed"
)
st.markdown("</div>", unsafe_allow_html=True)

# Expose ReportLab client PDF download button (Pro/Enterprise feature)
if prospect_audit_record:
    st.markdown(" ")
    sub_state = core.get_subscription_state()
    current_tier = sub_state.get("tier", "free")
    
    if current_tier == "free":
        st.button("🔒 Download Plan Fiduciary Diagnostic PDF (Pro)", key="download_pdf_locked_btn", help="Upgrade to a Pro or Enterprise plan in the sidebar to download client-facing PDFs.", use_container_width=True)
    else:
        try:
            from utils.pdf_generator import compile_diagnostic_pdf, compile_short_form_pdf
            pdf_payload = {
                "employer_name": active_company_name,
                "plan_name": prospect_audit_record.get("plan_name", "401(k) Plan"),
                "ein": clean_ein,
                "total_assets": prospect_audit_record.get("total_assets"),
                "active_participants": prospect_audit_record.get("active_participants"),
                "total_eligible_employees": prospect_audit_record.get("total_eligible_employees"),
                "admin_expenses": prospect_audit_record.get("admin_expenses"),
                "corrective_distributions": prospect_audit_record.get("corrective_distributions"),
                "schedule_type": prospect_audit_record.get("schedule_type", "SF"),
                "participation_rate": prospect_audit_record.get("participation_rate"),
                "fee_ratio": prospect_audit_record.get("fee_ratio"),
                "compliance_failed": bool(prospect_audit_record.get("compliance_failed")),
                "fee_red_flag": bool(prospect_audit_record.get("fee_flag")),
                "participation_red_flag": bool(prospect_audit_record.get("participation_flag")),
                "administrator_name": prospect_audit_record.get("administrator", "Sponsor Managed")
            }
            pdf_buffer = compile_diagnostic_pdf(pdf_payload, custom_pitch)
            short_pdf_buffer = compile_short_form_pdf(pdf_payload, custom_pitch)
            
            pdf_col1, pdf_col2 = st.columns(2)
            with pdf_col1:
                st.download_button(
                    label="📄 Download Short Form PDF (1-Page Summary)",
                    data=short_pdf_buffer.getvalue(),
                    file_name=f"fiduciary_short_form_{clean_ein}.pdf",
                    mime="application/pdf",
                    key="download_short_pdf_btn",
                    use_container_width=True
                )
            with pdf_col2:
                st.download_button(
                    label="📄 Download Plan Fiduciary Diagnostic PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"fiduciary_diagnostic_{clean_ein}.pdf",
                    mime="application/pdf",
                    key="download_pdf_btn",
                    use_container_width=True
                )
        except Exception as pdf_err:
            st.error(f"Error compiling PDF: {pdf_err}")
