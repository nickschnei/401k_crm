import streamlit as st

def display_threat_alert(class_name: str, icon: str, title: str, message: str) -> None:
    """Render animated custom HTML threat containers."""
    html_content = f"""
    <div class="threat-alert {class_name}">
        <span class="threat-icon">{icon}</span>
        <div class="threat-content">
            <strong>{title}</strong>: {message}
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

def display_empty_state() -> None:
    """Render gorgeous custom vector SVG empty state."""
    html_empty = """
    <div class="empty-state-container">
        <svg class="empty-state-icon" viewBox="0 0 24 24" width="64" height="64" style="color: #3b82f6;">
            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
        </svg>
        <h3>Select a Prospect to Begin Audit</h3>
        <p>Choose an employer or DOL filing from the sidebar controls to run a comprehensive 401(k) fiduciary health diagnostic and review active Form 5500 filings.</p>
    </div>
    """
    st.markdown(html_empty, unsafe_allow_html=True)
