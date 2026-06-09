import pandas as pd

def render_custom_metric(label: str, value: str, color: str = None) -> str:
    """Compile custom premium HTML markup for glassmorphic metric cards."""
    color_style = f"color: {color} !important; -webkit-text-fill-color: {color} !important;" if color else ""
    return f"""
    <div class="custom-metric">
        <div class="custom-metric-label">{label}</div>
        <div class="custom-metric-value" style="{color_style}">{value}</div>
    </div>
    """

def get_participation_color(rate) -> str:
    """Evaluate participation percentage against fiduciary thresholds."""
    if pd.isna(rate) or rate is None:
        return None
    if rate > 0.80:
        return "#10b981" # Green
    elif rate >= 0.70:
        return "#f59e0b" # Yellow
    else:
        return "#ef4444" # Red

def get_fee_color(ratio) -> str:
    """Evaluate recordkeeping fee ratio against industry 60bps standard."""
    if pd.isna(ratio) or ratio is None:
        return None
    if ratio > 0.0060:
        return "#ef4444" # Red
    else:
        return "#10b981" # Green
