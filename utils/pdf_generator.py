import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from typing import Dict, Any

def compile_diagnostic_pdf(record: Dict[str, Any], pitch_text: str) -> BytesIO:
    """
    Programmatically compile a branded, client-ready 1-page PDF diagnostic report
    using ReportLab Platypus. Fits perfectly on a single Letter page.
    """
    buffer = BytesIO()
    
    # Page setup - 0.5 inch margins for exact 1-page fit
    margin = 36 # 0.5 inch in points (72 points = 1 inch)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom Brand Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e3a8a'), # Brand Royal Blue
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#64748b'), # Slate Gray
        spaceAfter=15,
        textTransform='uppercase'
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#0f172a'), # Deep Dark Slate
        spaceBefore=10,
        spaceAfter=6,
        borderPadding=2
    )
    
    body_style = ParagraphStyle(
        'BodyTextDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'), # Charcoal
        spaceAfter=4
    )
    
    mono_style = ParagraphStyle(
        'MonoText',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        textColor=colors.HexColor('#475569')
    )
    
    # 1. Header Banner & Title Block
    title_p = Paragraph("401(k) FIDUCIARY PLAN DIAGNOSTIC", title_style)
    sub_p = Paragraph("Department of Labor Form 5500 Compliance & Fee Audit", subtitle_style)
    story.append(title_p)
    story.append(sub_p)
    
    # 2. Plan Metadata Table
    emp_name = record.get("employer_name") or "Your Client Organization"
    plan_name = record.get("plan_name") or "401(k) Plan"
    ein = record.get("ein") or "—"
    assets = record.get("total_assets")
    assets_str = f"${assets:,.2f}" if assets else "—"
    participants = record.get("active_participants")
    part_str = f"{participants:,}" if participants else "—"
    admin_name = record.get("administrator_name") or "Sponsor Managed"
    
    meta_data = [
        [
            Paragraph("<b>Employer Sponsor:</b>", body_style), Paragraph(emp_name, body_style),
            Paragraph("<b>Active Participants:</b>", body_style), Paragraph(part_str, body_style)
        ],
        [
            Paragraph("<b>Plan Name:</b>", body_style), Paragraph(plan_name, body_style),
            Paragraph("<b>Fiduciary Assets:</b>", body_style), Paragraph(assets_str, body_style)
        ],
        [
            Paragraph("<b>Employer EIN:</b>", body_style), Paragraph(ein, mono_style),
            Paragraph("<b>Plan Administrator:</b>", body_style), Paragraph(admin_name, body_style)
        ]
    ]
    
    # Total printable width is 8.5" * 72 - 2 * 36 = 540 points
    meta_table = Table(meta_data, colWidths=[110, 180, 110, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#f1f5f9')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    
    story.append(meta_table)
    story.append(Spacer(1, 10))
    
    # 3. Fiduciary Scorecard Section
    story.append(Paragraph("Fiduciary Scorecard & Performance Indicators", h2_style))
    
    # Calculations
    fee_ratio = record.get("fee_ratio") or 0.0
    fee_bps = int(fee_ratio * 10000)
    fee_val = f"{fee_ratio * 100:.2f}% ({fee_bps} bps)" if fee_ratio else "—"
    part_rate = record.get("participation_rate") or 0.0
    part_val = f"{part_rate * 100:.1f}%" if part_rate else "—"
    admin_exp = record.get("admin_expenses")
    admin_str = f"${admin_exp:,.2f}" if admin_exp else "$0.00"
    corr_dist = record.get("corrective_distributions")
    corr_str = f"${corr_dist:,.2f}" if corr_dist else "$0.00"
    
    # Threshold checks
    fee_status = "RED FLAG (EXCESSIVE)" if record.get("fee_red_flag") else "SAFE / INSTITUTIONAL"
    fee_color = "#e11d48" if record.get("fee_red_flag") else "#16a34a" # Crimson vs Emerald
    
    part_status = "RED FLAG (LOW)" if record.get("participation_red_flag") else "SAFE / TARGET MET"
    part_color = "#e11d48" if record.get("participation_red_flag") else "#16a34a"
    
    comp_status = "RED FLAG (FAILURE)" if record.get("compliance_failed") else "SAFE / PASSED"
    comp_color = "#e11d48" if record.get("compliance_failed") else "#16a34a"
    
    scorecard_data = [
        [
            Paragraph("<b>Fiduciary Metric</b>", body_style),
            Paragraph("<b>Filing Value</b>", body_style),
            Paragraph("<b>Threshold Benchmark</b>", body_style),
            Paragraph("<b>Fiduciary Status</b>", body_style)
        ],
        [
            Paragraph("Plan Fee Ratio (bps)", body_style),
            Paragraph(fee_val, body_style),
            Paragraph("&lt; 60 bps (0.60%)", body_style),
            Paragraph(f"<b><font color='{fee_color}'>{fee_status}</font></b>", body_style)
        ],
        [
            Paragraph("Active Employee Participation", body_style),
            Paragraph(part_val, body_style),
            Paragraph("&gt; 70% Target", body_style),
            Paragraph(f"<b><font color='{part_color}'>{part_status}</font></b>", body_style)
        ],
        [
            Paragraph("Corrective Compliance Refunds", body_style),
            Paragraph(corr_str, body_style),
            Paragraph("$0.00 (No Testing Failures)", body_style),
            Paragraph(f"<b><font color='{comp_color}'>{comp_status}</font></b>", body_style)
        ],
        [
            Paragraph("Total Administrative Expenses", body_style),
            Paragraph(admin_str, body_style),
            Paragraph("Value Validation Required", body_style),
            Paragraph("<b>AUDIT INDICATOR</b>", body_style)
        ]
    ]
    
    score_table = Table(scorecard_data, colWidths=[160, 110, 130, 140])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('LEFTPADDING', (0,0), (-1,0), 8),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
        ('LEFTPADDING', (0,1), (-1,-1), 8),
        ('RIGHTPADDING', (0,1), (-1,-1), 8),
    ]))
    
    # Quick fix for headers text color inside the Royal Blue header row
    header_style = ParagraphStyle(
        'ScorecardHeader',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )
    for col_idx in range(4):
        scorecard_data[0][col_idx] = Paragraph(scorecard_data[0][col_idx].text, header_style)
        
    story.append(score_table)
    story.append(Spacer(1, 10))
    
    # 4. Fiduciary Fiduciary Red Flags & Recommendations
    story.append(Paragraph("Fiduciary Risk Assessment & Key Recommendations", h2_style))
    
    recommendations = []
    if record.get("fee_red_flag"):
        recommendations.append(
            "<b>• Excessive Fee Exposure:</b> The plan fee ratio exceeds standard benchmarks. As fiduciaries, plan sponsors are legally required to verify that recordkeeping, advisory, and administrative costs are reasonable. We recommend executing an institutional fee compression audit."
        )
    if record.get("participation_red_flag"):
        recommendations.append(
            "<b>• Employee Savings Gap:</b> Participation falls below the 70% baseline target. Low participation often triggers discrimination testing limits and restricts executive savings. We recommend restructuring matching criteria and structuring safe-harbor options."
        )
    if record.get("compliance_failed"):
        recommendations.append(
            "<b>• Regulatory Compliance Failure:</b> Filing records show historic testing failure refunds. This incurs costly admin friction. Restructuring core parameters is recommended to prevent future testing deficiencies."
        )
        
    if not recommendations:
        recommendations.append(
            "<b>• Fiduciary Oversight Safe:</b> All checked indicators reside within healthy guidelines. We recommend completing periodic vendor benchmarks every 3 years to maintain institutional pricing structures as plan assets expand."
        )
        
    for rec in recommendations:
        story.append(Paragraph(rec, body_style))
        story.append(Spacer(1, 3))
        
    story.append(Spacer(1, 10))
    
    # 5. Customized Advisor Pitch outreach block
    story.append(Paragraph("Advisor Fiduciary Assessment Outreach Proposal", h2_style))
    
    # Styled Pitch Box - Warm Cream/Tan background
    pitch_style = ParagraphStyle(
        'PitchText',
        parent=body_style,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )
    
    # Format pitch_text beautifully
    formatted_pitch = pitch_text.replace("\n", "<br/>")
    pitch_p = Paragraph(formatted_pitch, pitch_style)
    
    pitch_table = Table([[pitch_p]], colWidths=[540])
    pitch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fafaf9')), # Cream
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    
    story.append(pitch_table)
    
    # Build Document
    doc.build(story)
    
    buffer.seek(0)
    return buffer
