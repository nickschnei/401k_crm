import streamlit as st
import pandas as pd
from components.metrics import render_custom_metric
from services.api_client import FiduciaryDataService

def format_and_style_status(df, is_prospects_table=True):
    """Format the Pipeline Status column to show emoji-badges with customized background colors."""
    if df.empty:
        return df
        
    styled_df = df.copy()
    status_map = {
        'Lead': '🔵 Lead',
        'Researching': '🟣 Researching',
        'Cold Called': '🟡 Cold Called',
        'Meeting Set': '🟢 Meeting Set',
        'Disqualified': '🔴 Disqualified'
    }
    
    if is_prospects_table and 'status' in styled_df.columns:
        styled_df['status'] = styled_df['status'].map(lambda s: status_map.get(s, f"⚪ {s}") if pd.notna(s) else '⚪ N/A')
        
    def get_status_styles(val):
        if not isinstance(val, str):
            return ''
        if 'Lead' in val:
            return 'background-color: rgba(59, 130, 246, 0.15) !important; color: #60a5fa !important; font-weight: bold !important; border-radius: 4px;'
        elif 'Researching' in val:
            return 'background-color: rgba(168, 85, 247, 0.15) !important; color: #c084fc !important; font-weight: bold !important; border-radius: 4px;'
        elif 'Cold Called' in val:
            return 'background-color: rgba(245, 158, 11, 0.15) !important; color: #fbbf24 !important; font-weight: bold !important; border-radius: 4px;'
        elif 'Meeting Set' in val:
            return 'background-color: rgba(16, 185, 129, 0.15) !important; color: #34d399 !important; font-weight: bold !important; border-radius: 4px;'
        elif 'Disqualified' in val:
            return 'background-color: rgba(239, 68, 68, 0.15) !important; color: #f87171 !important; font-weight: bold !important; border-radius: 4px;'
        return ''
        
    styler = styled_df.style
    if is_prospects_table and 'status' in styled_df.columns:
        styler = styler.map(get_status_styles, subset=['status'])
        
    return styler

def render_pipeline_view(filters):
    """Render metrics and interactive dataframe inside Prospects tab."""
    st.markdown("<div class='section-header'>📊 Prospects Overview Metrics</div>", unsafe_allow_html=True)
    m_col1, m_col2, m_col3 = st.columns(3)
    
    prospects_filtered = FiduciaryDataService.get_prospects(filters)
    total_records_p = len(prospects_filtered)
    total_assets_p = pd.to_numeric(prospects_filtered['Total Assets'], errors='coerce').fillna(0).sum()
    meetings_count_p = len(prospects_filtered[prospects_filtered['status'] == 'Meeting Set']) if 'status' in prospects_filtered.columns else 0
    
    m_col1.markdown(render_custom_metric("Total Prospects", f"{total_records_p:,}"), unsafe_allow_html=True)
    m_col2.markdown(render_custom_metric("Total Assets Under Mgmt", f"${total_assets_p/1e6:,.1f}M"), unsafe_allow_html=True)
    m_col3.markdown(render_custom_metric("Meetings Set Pipeline", f"{meetings_count_p:,}"), unsafe_allow_html=True)
    
    st.markdown("<div class='section-header'>📋 Prospects Table</div>", unsafe_allow_html=True)
    if not prospects_filtered.empty:
        display_df_p = prospects_filtered.copy()
        
        standard_cols_p = [
            'Employer Name',
            'status',
            'Industry',
            'Broker/Provider',
            'Total Assets',
            'Participants',
            'Address',
            'Record ZIP',
            'Distance Miles',
            'Administrator',
            'EIN',
            'Contact',
            'EMAIL',
            'schedule_type',
            'participation_rate',
            'fee_ratio',
            'fee_red_flag',
            'participation_red_flag',
            'compliance_failed',
        ]
        
        for c in standard_cols_p:
            if c not in display_df_p.columns:
                if c == 'status':
                    display_df_p['status'] = "Lead"
                else:
                    display_df_p[c] = None
                    
        display_df_p = display_df_p[standard_cols_p]
        for numeric_col in ['Total Assets', 'Participants']:
            display_df_p[numeric_col] = pd.to_numeric(display_df_p[numeric_col], errors='coerce')
        if 'Distance Miles' in display_df_p.columns:
            display_df_p['Distance Miles'] = pd.to_numeric(display_df_p['Distance Miles'], errors='coerce')
            
        column_config = {
            'Total Assets': st.column_config.NumberColumn('Total Assets', format="$%d"),
            'Participants': st.column_config.NumberColumn('Participants', format="%d"),
            'Distance Miles': st.column_config.NumberColumn('Distance Miles', format="%.1f mi"),
        }
        
        st.dataframe(
            format_and_style_status(display_df_p, is_prospects_table=True),
            column_config=column_config,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No prospects match the filter parameters. Broaden your live search or advanced filters.")
