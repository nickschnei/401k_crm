import streamlit as st
import pandas as pd
from components.metrics import render_custom_metric
from views.pipeline import format_and_style_status
from services.api_client import FiduciaryDataService

def render_discovery_view(filters):
    """Render filings and support live scraping cloud syncs inside Discovery tab."""
    
    # Cloud sync trigger
    col_sync, col_status = st.columns([1, 2])
    with col_sync:
        if st.button("☁️ Live Sync DOL Filings", key="live_sync_dol_btn", use_container_width=True, help="Trigger incremental Form 5500 background sweeps directly from Department of Labor registries."):
            import core
            sub = core.get_subscription_state()
            if sub.get("tier") != "enterprise":
                st.warning("⚡ Live Sync is an Enterprise Plan feature. Please upgrade your tier in the sidebar Panel.")
            else:
                with st.spinner("☁️ Sweeping registry directories and auditing filings..."):
                    try:
                        from services.scraper import run_nightly_dol_sync, get_sync_status
                        run_nightly_dol_sync()
                        status = get_sync_status()
                        summary = status.get("summary", {})
                        st.success(f"☁️ Sync Complete! Scanned: {summary.get('files_scanned')} · Audited: {summary.get('audits_completed')} · New records: {summary.get('new_records_added')}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as err:
                        st.error(f"Sync error: {err}")
                        
    st.markdown("<div class='section-header'>📊 Discovery Overview Metrics</div>", unsafe_allow_html=True)
    md_col1, md_col2, md_col3 = st.columns(3)
    
    discovery_filtered = FiduciaryDataService.get_discovery(filters)
    total_records_d = len(discovery_filtered)
    total_assets_d = pd.to_numeric(discovery_filtered['Total Assets'], errors='coerce').fillna(0).sum()
    avg_participants_d = pd.to_numeric(discovery_filtered['Participants'], errors='coerce').fillna(0).mean() if total_records_d > 0 else 0
    
    md_col1.markdown(render_custom_metric("DOL Filings Count", f"{total_records_d:,}"), unsafe_allow_html=True)
    md_col2.markdown(render_custom_metric("Total Filings Volume", f"${total_assets_d/1e6:,.1f}M"), unsafe_allow_html=True)
    md_col3.markdown(render_custom_metric("Avg Participants Size", f"{avg_participants_d:,.0f}"), unsafe_allow_html=True)
    
    st.markdown("<div class='section-header'>🔍 Discovery Filings Table</div>", unsafe_allow_html=True)
    if not discovery_filtered.empty:
        display_df_d = discovery_filtered.copy()
        
        standard_cols_d = [
            'Employer Name',
            'Plan Name',
            'Total Assets',
            'Participants',
            'DOL Address',
            'DOL City',
            'DOL State',
            'DOL ZIP',
            'Record ZIP',
            'Distance Miles',
            'Administrator',
            'EIN',
            'schedule_type',
            'participation_rate',
            'fee_ratio',
            'fee_red_flag',
            'participation_red_flag',
            'compliance_failed',
        ]
        
        for c in standard_cols_d:
            if c not in display_df_d.columns:
                display_df_d[c] = None
                
        display_df_d = display_df_d[standard_cols_d]
        for numeric_col in ['Total Assets', 'Participants']:
            display_df_d[numeric_col] = pd.to_numeric(display_df_d[numeric_col], errors='coerce')
        if 'Distance Miles' in display_df_d.columns:
            display_df_d['Distance Miles'] = pd.to_numeric(display_df_d['Distance Miles'], errors='coerce')
            
        column_config_d = {
            'Total Assets': st.column_config.NumberColumn('Total Assets', format="$%d"),
            'Participants': st.column_config.NumberColumn('Participants', format="%d"),
            'Distance Miles': st.column_config.NumberColumn('Distance Miles', format="%.1f mi"),
        }
        
        st.dataframe(
            format_and_style_status(display_df_d, is_prospects_table=False),
            column_config=column_config_d,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No raw Department of Labor filings match the filter parameters.")
