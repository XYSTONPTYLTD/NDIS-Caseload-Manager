import datetime
from datetime import timedelta
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor
import io

RATES = {
    "Level 2: Coordination of Supports": 100.14,
    "Level 3: Specialist Support Coordination": 190.41
}

def calculate_client_metrics(c):
    """Calculates metrics with UI-ready colors and risk scores."""
    try:
        balance = float(c.get('balance', 0))
        hours = float(c.get('hours', 0))
        rate = float(c.get('rate', 100.14))
        budget = float(c.get('budget', 0))
        
        plan_end_str = c.get('plan_end')
        if isinstance(plan_end_str, (datetime.date, datetime.datetime)):
            plan_end = plan_end_str
        else:
            try:
                plan_end = datetime.datetime.strptime(str(plan_end_str), "%Y-%m-%d").date()
            except:
                plan_end = datetime.date.today() + timedelta(weeks=40)
            
    except Exception:
        return None

    today = datetime.date.today()
    weeks_remaining = max(0, (plan_end - today).days / 7)
    
    weekly_cost = hours * rate
    runway_weeks = balance / weekly_cost if weekly_cost > 0 else 999
    surplus = balance - (weekly_cost * weeks_remaining)
    depletion_date = today + timedelta(days=int(runway_weeks * 7))
    
    # STATUS LOGIC & VISUALS
    if runway_weeks >= weeks_remaining * 1.2:
        status = "ROBUST SURPLUS"
        color = "#3fb950" # Bright Green
        badge_class = "status-good"
    elif runway_weeks >= weeks_remaining:
        status = "SUSTAINABLE"
        color = "#2ea043" # Green
        badge_class = "status-good"
    elif runway_weeks >= max(0, weeks_remaining - 4):
        status = "MONITORING REQUIRED"
        color = "#d29922" # Yellow
        badge_class = "status-warn"
    else:
        status = "CRITICAL SHORTFALL"
        color = "#f85149" # Red
        badge_class = "status-bad"

    return {
        "id": c.get('id'),
        "name": c.get('name', 'Unknown'),
        "ndis_number": c.get('ndis_number', ''),
        "level": c.get('level'),
        "rate": rate,
        "budget": budget,
        "balance": balance,
        "hours": hours,
        "plan_end": plan_end,
        "weeks_remaining": weeks_remaining,
        "weekly_cost": weekly_cost,
        "runway_weeks": runway_weeks,
        "depletion_date": depletion_date,
        "surplus": surplus,
        "status": status,
        "color": color,
        "badge_class": badge_class,
        "notes": c.get('notes', '')
    }

def generate_caseload_report(caseload_data):
    doc = Document()
    doc.add_heading('XYSTON | Caseload Master Report', 0)
    doc.add_paragraph(f"Date: {datetime.date.today().strftime('%d %B %Y')}")
    
    total_funds = sum(c['balance'] for c in caseload_data)
    critical = [c for c in caseload_data if "CRITICAL" in c['status']]
    
    doc.add_heading('Executive Summary', 1)
    doc.add_paragraph(f"Total Clients: {len(caseload_data)}")
    doc.add_paragraph(f"Funds Under Management: ${total_funds:,.2f}")
    
    if critical:
        p = doc.add_paragraph()
        run = p.add_run(f"CRITICAL ALERT: {len(critical)} clients require review.")
        run.font.color.rgb = RGBColor(255, 0, 0)
        run.bold = True

    for c in caseload_data:
        doc.add_page_break()
        doc.add_heading(f"{c['name']}", 1)
        doc.add_paragraph(f"Status: {c['status']}")
        doc.add_paragraph(f"Balance: ${c['balance']:,.2f}")
        doc.add_paragraph(f"Outcome: ${c['surplus']:,.2f}")
        if c['notes']:
            doc.add_heading('Strategy', 2)
            doc.add_paragraph(c['notes'])
            
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()
