import streamlit as st
import pandas as pd
import plotly.express as px
import json
import datetime
from datetime import timedelta # Fixed the crash error
import uuid
import google.generativeai as genai
from utils import calculate_client_metrics, generate_caseload_report, generate_csv_template, process_csv_upload, RATES

# ==============================================================================
# 1. CONFIG & STYLING
# ==============================================================================
st.set_page_config(page_title="XYSTON Caseload Master", layout="wide", page_icon="🛡️", initial_sidebar_state="expanded")

if 'caseload' not in st.session_state:
    st.session_state.caseload = []

# INJECT CUSTOM CSS
st.markdown("""
<style>
    /* GLOBAL THEME */
    .stApp { background-color: #0d1117; font-family: 'Segoe UI', sans-serif; }
    
    /* CARDS */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .metric-val { font-size: 24px; font-weight: 800; color: #ffffff; }
    .metric-lbl { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }
    
    /* LINKS & BUTTONS */
    .link-row a {
        text-decoration: none;
        color: #58a6ff;
        font-size: 13px;
        display: block;
        padding: 6px 8px;
        margin: 2px 0;
        border-radius: 4px;
        background: #161b22;
        border: 1px solid #30363d;
        transition: all 0.2s;
    }
    .link-row a:hover { background: #238636; color: white; border-color: #2ea043; padding-left: 15px; }
    
    .stButton button {
        width: 100%;
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton button:hover { color: #fff; border-color: #8b949e; }
    div[data-testid="stButton"] button[kind="primary"] { background-color: #238636; border-color: #2ea043; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("<div style='text-align:center; padding:15px 0;'><h1 style='margin:0; font-size:40px;'>🛡️</h1><h3 style='margin:0; color:white; letter-spacing:2px;'>XYSTON</h3><p style='color:#8b949e; font-size:10px; letter-spacing:1px;'>CASELOAD MASTER v3.7</p></div>", unsafe_allow_html=True)
    
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        with st.expander("🔐 AI Settings"):
            api_key = st.text_input("Google API Key", type="password")

    # --- DATA & TEMPLATES ---
    with st.expander("📂 Import / Export", expanded=True):
        tab_json, tab_csv = st.tabs(["Backup", "Bulk Import"])
        
        with tab_json:
            if st.session_state.caseload:
                st.download_button("💾 Save Database", json.dumps(st.session_state.caseload, default=str), "caseload_backup.json", "application/json", use_container_width=True)
            uploaded_json = st.file_uploader("Load Backup", type=['json'], label_visibility="collapsed", key="json_up")
            if uploaded_json:
                try:
                    st.session_state.caseload = json.load(uploaded_json)
                    st.success(f"Loaded {len(st.session_state.caseload)} clients!")
                    st.rerun()
                except: st.error("Error")

        with tab_csv:
            st.caption("Use this for Excel editing")
            csv_template = generate_csv_template()
            st.download_button("📄 Get CSV Template", csv_template, "client_template.csv", "text/csv", use_container_width=True)
            uploaded_csv = st.file_uploader("Import CSV", type=['csv'], label_visibility="collapsed", key="csv_up")
            if uploaded_csv:
                new_data = process_csv_upload(uploaded_csv)
                if new_data:
                    st.session_state.caseload.extend(new_data)
                    st.success(f"Imported {len(new_data)} clients!")
                    st.rerun()
                else: st.error("Check format.")

    # --- ADD SINGLE ---
    with st.expander("➕ Add Single Client", expanded=False):
        with st.form("add_form"):
            name = st.text_input("Name")
            ndis = st.text_input("NDIS #")
            level = st.selectbox("Level", list(RATES.keys()))
            budget = st.number_input("Total Budget", 18000.0)
            balance = st.number_input("Current Balance", 15000.0)
            end = st.date_input("Plan End")
            hours = st.number_input("Hours/Week", 1.5, step=0.1)
            if st.form_submit_button("Create Record", type="primary"):
                new_c = {"id": str(uuid.uuid4()), "name": name, "ndis_number": ndis, "level": level, "rate": RATES[level], "budget": budget, "balance": balance, "plan_end": str(end), "hours": hours, "notes": ""}
                st.session_state.caseload.append(new_c)
                st.rerun()

    # --- COMMAND CENTRE (The Full Link List) ---
    st.markdown("---")
    st.caption("COMMAND CENTRE")
    
    with st.expander("⚡ Admin & Banking"):
        st.markdown("""
        <div class="link-row">
            <a href="https://secure.employmenthero.com/login" target="_blank">👤 Employment Hero HR</a>
            <a href="https://login.xero.com/" target="_blank">📊 Xero Accounting</a>
            <hr style="border-color:#333; margin:5px 0;">
            <a href="https://www.commbank.com.au/" target="_blank">🏦 Commonwealth Bank</a>
            <a href="https://www.westpac.com.au/" target="_blank">🏦 Westpac</a>
            <a href="https://www.anz.com.au/" target="_blank">🏦 ANZ</a>
            <a href="https://www.nab.com.au/" target="_blank">🏦 NAB</a>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🏛️ NDIS Compliance"):
        st.markdown("""
        <div class="link-row">
            <a href="https://proda.humanservices.gov.au/" target="_blank">🔐 PACE / PRODA Login</a>
            <a href="https://www.ndis.gov.au/providers/pricing-arrangements" target="_blank">💰 Pricing Arrangements</a>
            <a href="https://ourguidelines.ndis.gov.au/" target="_blank">📜 Operational Guidelines</a>
            <a href="https://www.legislation.gov.au/Details/C2013A00020" target="_blank">⚖️ NDIS Act 2013</a>
            <a href="https://www.ndiscommission.gov.au/" target="_blank">🛡️ NDIS Commission</a>
            <a href="https://www.ndis.gov.au/news" target="_blank">📰 News & Reviews</a>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown('<div style="text-align:center"><a href="https://www.buymeacoffee.com/h0m1ez187" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" style="width:160px;"></a></div>', unsafe_allow_html=True)

# ==============================================================================
# 3. DASHBOARD
# ==============================================================================

# HERO SCREEN
if not st.session_state.caseload:
    st.markdown("""
    <div style="text-align: center; padding: 40px;">
        <h1 style="font-size: 50px; margin-bottom: 10px;">🛡️</h1>
        <h1>Xyston Caseload Master</h1>
        <p style="color: #8b949e; font-size: 18px;">The operating system for independent coordinators.</p>
        <br>
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <div class="metric-card" style="width: 250px; text-align:left;">
                <div style="font-size: 20px;">📂 <b>Bulk Import</b></div>
                <div style="color: #8b949e; font-size: 14px; margin-top:5px;">Download the CSV template, fill it in Excel, and upload it to populate your dashboard instantly.</div>
            </div>
            <div class="metric-card" style="width: 250px; text-align:left;">
                <div style="font-size: 20px;">💾 <b>Secure Backup</b></div>
                <div style="color: #8b949e; font-size: 14px; margin-top:5px;">Your data stays on your device. Save and Load your full database securely via JSON.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# CALC METRICS
all_metrics = [m for m in [calculate_client_metrics(c) for c in st.session_state.caseload] if m is not None]
df = pd.DataFrame(all_metrics)

# TOP STATS
total_funds = df['balance'].sum()
monthly_rev = df['weekly_cost'].sum() * 4.33
risk_count = len(df[df['status'] == 'CRITICAL SHORTFALL'])

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"<div class='metric-card'><div class='metric-val'>{len(df)}</div><div class='metric-lbl'>Active Participants</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-card'><div class='metric-val'>${total_funds:,.0f}</div><div class='metric-lbl'>Funds Managed</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='metric-card'><div class='metric-val'>${monthly_rev:,.0f}</div><div class='metric-lbl'>Est. Monthly Revenue</div></div>", unsafe_allow_html=True)
risk_col = "#f85149" if risk_count > 0 else "#238636"
c4.markdown(f"<div class='metric-card' style='border-color:{risk_col}'><div class='metric-val' style='color:{risk_col}'>{risk_count}</div><div class='metric-lbl'>Critical Risks</div></div>", unsafe_allow_html=True)

st.markdown("---")

# TABS
tab1, tab2 = st.tabs(["📊 Caseload Overview", "🔍 Participant Vault"])

with tab1:
    c_viz, c_data = st.columns([1, 2])
    with c_viz:
        st.markdown("### Viability Radar")
        if not df.empty:
            color_map = {"ROBUST SURPLUS": "#3fb950", "SUSTAINABLE": "#2ea043", "MONITORING REQUIRED": "#d29922", "CRITICAL SHORTFALL": "#f85149"}
            fig = px.pie(df, names='status', color='status', color_discrete_map=color_map, hole=0.6)
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=250, paper_bgcolor='rgba(0,0,0,0)', font_color="#c9d1d9")
            st.plotly_chart(fig, use_container_width=True)
        
        report_doc = generate_caseload_report(all_metrics)
        st.download_button("📄 Download Full Report (.docx)", report_doc, f"Report_{datetime.date.today()}.docx", "application/msword", use_container_width=True, type="primary")

    with c_data:
        st.markdown("### Participant List")
        display_df = df[['name
