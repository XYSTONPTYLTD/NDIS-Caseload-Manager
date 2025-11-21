import datetime
from datetime import timedelta
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor
import io

# --- CONSTANTS ---
RATES = {
    "Level 2: Coordination of Supports": 100.14,
    "Level 3: Specialist Support Coordination": 190.41
}

# --- MATH ENGINE ---
def calculate_client_metrics(c):
    """Calculates runway, surplus, and status for a single client dictionary."""
    try:
        balance = float(c.get('balance', 0))
        hours = float(c.get('hours', 0))
        rate = float(c.get('rate', 100.14))
        total_budget = float(c.get('budget', 0))
        
        # Handle Date Parsing safely (JSON stores dates as strings)
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

    # Time Calculations
    today = datetime.date.today()
    weeks_remaining = max(0, (plan_end - today).days / 7)
    
    # Financial Calculations
    weekly_cost = hours * rate
    runway_weeks = balance / weekly_cost if weekly_cost > 0 else 999
    required_to_finish = weekly_cost * weeks_remaining
    surplus = balance - required_to_finish
    depletion_date = today + timedelta(days=int(runway_weeks * 7))
    
    # NDIS Status Logic (Audit-Safe)
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
        "id": c.get('id'),
        "name": c.get('name', 'Unknown'),
        "ndis_number": c.get('ndis_number', ''),
        "level": c.get('level'),
        "rate": rate,
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
        "notes": c.get('notes', '')
    }

# --- REPORT GENERATOR ---
def generate_caseload_report(caseload_data):
    """Generates a professional Word doc for the whole caseload."""
    doc = Document()
    
    # Title Page
    doc.add_heading('XYSTON | Caseload Master Report', 0)
    doc.add_paragraph(f"Date: {datetime.date.today().strftime('%d %B %Y')}")
    doc.add_paragraph("Confidential: Internal Use Only")
    doc.add_page_break()
    
    # Executive Summary
    doc.add_heading('Executive Summary', 1)
    total_funds = sum(c['balance'] for c in caseload_data)
    monthly_rev = sum(c['weekly_cost'] for c in caseload_data) * 4.33
    critical_clients = [c for c in caseload_data if "CRITICAL" in c['status']]
    
    p = doc.add_paragraph()
    p.add_run(f"Total Participants: {len(caseload_data)}\n").bold = True
    p.add_run(f"Funds Under Management: ${total_funds:,.2f}\n")
    p.add_run(f"Projected Monthly Revenue: ${monthly_rev:,.2f}\n")
    
    if critical_clients:
        doc.add_heading('⚠️ Critical Risk Watchlist', 3)
        for c in critical_clients:
            doc.add_paragraph(f"• {c['name']}: Runs out on {c['depletion_date'].strftime('%d/%m/%y')} (${abs(c['surplus']):,.0f} shortfall)")
            
    doc.add_page_break()
    
    # Individual Files
    for c in caseload_data:
        doc.add_heading(f"{c['name']} ({c['ndis_number']})", 1)
        
        p = doc.add_paragraph()
        run = p.add_run(f"PLAN HEALTH: {c['status']}")
        run.bold = True
        run.font.color.rgb = RGBColor(0xEF, 0x44, 0x44) if "CRITICAL" in c['status'] else RGBColor(0x10, 0xB9, 0x81)
        
        p = doc.add_paragraph()
        p.add_run(f"Current Balance: ${c['balance']:,.2f}\n")
        p.add_run(f"Weekly Burn: ${c['weekly_cost']:,.2f} ({c['hours']} hrs/wk)\n")
        p.add_run(f"Plan Ends: {c['plan_end'].strftime('%d/%m/%y')} ({c['weeks_remaining']:.1f} wks left)\n")
        p.add_run(f"Projected Outcome: ${c['surplus']:,.2f}\n")
        
        if c['notes']:
            doc.add_heading('Strategy Notes', 2)
            doc.add_paragraph(c['notes'])
            
        doc.add_page_break()
        
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()
