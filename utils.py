import datetime
from datetime import timedelta
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# --- CONSTANTS ---
RATES = {
    "Level 2: Coordination of Supports": 100.14,
    "Level 3: Specialist Support Coordination": 190.41
}

# --- MATH ENGINE ---
def calculate_client_metrics(client):
    """Calculates runway, surplus, and status for a single client."""
    # Safe defaults
    balance = float(client.get('balance', 0))
    hours = float(client.get('hours_per_week', 0))
    rate = float(client.get('hourly_rate', 100.14))
    
    # Time calc
    try:
        end_date = datetime.datetime.strptime(client.get('plan_end', ''), "%Y-%m-%d").date()
    except:
        end_date = datetime.date.today() + timedelta(weeks=40) # Fallback
        
    today = datetime.date.today()
    weeks_remaining = max(0, (end_date - today).days / 7)
    
    # Financials
    weekly_cost = hours * rate
    if weekly_cost > 0:
        runway_weeks = balance / weekly_cost
    else:
        runway_weeks = 999
        
    required = weekly_cost * weeks_remaining
    surplus = balance - required
    
    # Status Logic (Strict NDIS Terminology)
    if runway_weeks >= weeks_remaining * 1.2:
        status = "ROBUST SURPLUS"
        color = "#10b981" # Green
    elif runway_weeks >= weeks_remaining:
        status = "SUSTAINABLE"
        color = "#22c55e" # Light Green
    elif runway_weeks >= max(0, weeks_remaining - 4):
        status = "MONITORING REQUIRED"
        color = "#eab308" # Yellow
    else:
        status = "CRITICAL SHORTFALL"
        color = "#ef4444" # Red

    return {
        "name": client.get('name', 'Unknown'),
        "ndis_number": client.get('ndis_number', ''),
        "support_level": client.get('support_level', ''),
        "balance": balance,
        "hours": hours,
        "rate": rate,
        "plan_end": end_date,
        "weeks_remaining": weeks_remaining,
        "weekly_cost": weekly_cost,
        "runway_weeks": runway_weeks,
        "surplus": surplus,
        "status": status,
        "color": color
    }

# --- WORD DOC GENERATOR ---
def generate_caseload_report(clients_data):
    """Generates a formatted .docx report for the whole caseload."""
    doc = Document()
    
    # Style Helper
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(10)

    # 1. TITLE PAGE
    doc.add_heading('XYSTON | Caseload Viability Report', 0)
    doc.add_paragraph(f"Generated: {datetime.date.today().strftime('%d %B %Y')}")
    doc.add_paragraph("Confidential: For Internal Use Only")
    doc.add_page_break()

    # 2. EXECUTIVE SUMMARY
    doc.add_heading('Executive Summary', 1)
    
    # Aggregate Data
    total_funds = sum(c['balance'] for c in clients_data)
    total_revenue = sum(c['weekly_cost'] for c in clients_data)
    critical_count = sum(1 for c in clients_data if "CRITICAL" in c['status'])
    
    p = doc.add_paragraph()
    p.add_run(f"Total Participants: {len(clients_data)}\n").bold = True
    p.add_run(f"Funds Under Management: ${total_funds:,.2f}\n")
    p.add_run(f"projected Weekly Revenue: ${total_revenue:,.2f}\n")
    
    if critical_count > 0:
        risk_run = doc.add_paragraph().add_run(f"⚠️ CRITICAL RISK ALERT: {critical_count} participant(s) require immediate review.")
        risk_run.font.color.rgb = RGBColor(255, 0, 0)
        risk_run.bold = True

    # Summary Table
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text = 'Participant'
    hdr[1].text = 'Status'
    hdr[2].text = 'Plan Ends'
    hdr[3].text = 'Outcome'
    
    for c in clients_data:
        row = table.add_row().cells
        row[0].text = c['name']
        row[1].text = c['status']
        row[2].text = c['plan_end'].strftime('%d/%m/%y')
        outcome = f"${c['surplus']:,.0f}"
        row[3].text = f"+{outcome}" if c['surplus'] > 0 else outcome

    doc.add_page_break()

    # 3. INDIVIDUAL DETAILS
    for c in clients_data:
        doc.add_heading(f"{c['name']} ({c['ndis_number']})", 1)
        doc.add_paragraph(f"Support Level: {c['support_level']}")
        
        # Status Banner Logic in Text
        p = doc.add_paragraph()
        run = p.add_run(f"PLAN HEALTH: {c['status']}")
        run.bold = True
        run.font.size = Pt(14)
        
        # Metrics Grid
        doc.add_heading('Financial Position', 2)
        p = doc.add_paragraph()
        p.add_run(f"Current Balance: ${c['balance']:,.2f}\n")
        p.add_run(f"Weekly Burn: ${c['weekly_cost']:,.2f} ({c['hours']} hrs/wk)\n")
        p.add_run(f"Runway: {c['runway_weeks']:.1f} weeks (Buffer: {c['runway_weeks'] - c['weeks_remaining']:.1f} wks)")
        
        # AI Strategy Note (if saved in JSON)
        if c.get('ai_strategy'):
            doc.add_heading('Strategic Note', 2)
            doc.add_paragraph(c.get('ai_strategy'))
            
        doc.add_page_break()

    # Save to memory
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()
