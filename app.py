import streamlit as st
import pandas as pd
import plotly.express as px
import json
import datetime
from datetime import timedelta  # <--- This was the missing import causing the crash
import uuid
import google.generativeai as genai
from utils import calculate_client_metrics, generate_caseload_report, generate_csv_template, process_csv_upload, RATES

# ==============================================================================
# 1. CONFIG & STYLING
# ==============================================================================
st.set_page_config(page_title="XYSTON Caseload Master", layout="wide", page_icon="🛡️", initial_sidebar_state="expanded")

if 'caseload' not in st.session_state:
    st.session_state.caseload = []

st.markdown("""
<style>
    .stApp { background-color: #0d1117; font-family: 'Segoe UI', sans-serif; }
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
    .link-row a {
        text-decoration: none; color: #58a6ff; font-size: 13px; display: block;
        padding: 6px 8px; margin: 2px 0; border-radius: 4px; background: #161b22;
        border: 1px solid #30363d; transition: all 0.2s;
    }
    .link-row a:hover { background: #238636; color: white; border-color: #2ea043; padding-left: 15px; }
    .stButton button { width: 100%; border-radius: 6px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("<div style='text-align:center; padding:15px 0;'><h1 style='margin:0; font-size:40px;'>🛡️</h1><h3 style='margin:0; color:white; letter-spacing:2px;'>XYSTON</h3><p style='color:#8b949e; font-size:10px; letter-spacing:1px;'>CASELOAD MASTER v3.6</p></div>", unsafe_allow_html=True)
    
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        with st.expander("🔐 AI Settings"):
            api_key = st.text_input("Google API Key", type="password")

    # DATA TOOLS
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
                except: st.error("Error loading JSON")

        with tab_csv:
            csv_template = generate_csv_template()
            st.download_button("📄 Get CSV Template", csv_template, "client_template.csv", "text/csv", use_container_width=True)
            uploaded_csv = st.file_uploader("Import CSV", type=['csv'], label_visibility="collapsed", key="csv_up")
            if uploaded_csv:
                new_data = process_csv_upload(uploaded_csv)
                if new_data:
                    st.session_state.caseload.extend(new_data)
                    st.success(f"Imported {len(new_data)} clients!")
                    st.rerun()

    # ADD CLIENT
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

    # COMMAND CENTRE
    st.markdown("---")
    with st.expander("⚡ Quick Access"):
        st.markdown("""
        <div class="link-row">
            <a href="https://proda.humanservices.gov.au/" target="_blank">🔐 PACE / PRODA Login</a>
            <a href="https://secure.employmenthero.com/login" target="_blank">👤 Employment Hero HR</a>
            <a href="https://login.xero.com/" target="_blank">📊 Xero Accounting</a>
            <a href="https://www.ndis.gov.au/providers/pricing-arrangements" target="_blank">💰 Pricing Arrangements</a>
            <a href="https://ourguidelines.ndis.gov.au/" target="_blank">📜 Operational Guidelines</a>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; margin-top:10px;"><a href="https://www.buymeacoffee.com/h0m1ez187" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" style="width:140px;"></a></div>', unsafe_allow_html=True)

# ==============================================================================
# 3. DASHBOARD LOGIC
# ==============================================================================

# HERO SCREEN (Zero State)
if not st.session_state.caseload:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <h1 style="font-size: 60px; margin-bottom: 10px;">🛡️</h1>
        <h1>Welcome to Caseload Master</h1>
        <p style="color: #8b949e; font-size: 18px;">Your compliant, secure NDIS operating system.</p>
        <div style="margin-top: 30px; padding: 20px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; display: inline-block; text-align: left;">
            <p style="color:#fff;"><strong>👉 Get Started:</strong></p>
            <ol style="color: #c9d1d9;">
                <li>Open the sidebar <b>(Import / Export)</b>.</li>
                <li>Click <b>Add Single Client</b> to start manually.</li>
                <li>Or upload a JSON backup if you have one.</li>
            </ol>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Process Data
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
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=250, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        
        report_doc = generate_caseload_report(all_metrics)
        st.download_button("📄 Download Full Report (.docx)", report_doc, f"Caseload_Report_{datetime.date.today()}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, type="primary")

    with c_data:
        st.markdown("### Participant List")
        display_df = df[['name', 'plan_end', 'status', 'runway_weeks', 'surplus']]
        display_df.columns = ['Name', 'End Date', 'Health', 'Runway', 'Outcome']
        st.dataframe(
            display_df.style.format({'Outcome': "${:,.0f}", 'Runway': "{:.1f}"})
            .applymap(lambda x: 'color:#f85149; font-weight:bold' if x=='CRITICAL SHORTFALL' else 'color:#3fb950' if x=='ROBUST SURPLUS' else '', subset=['Health']),
            use_container_width=True, height=400
        )

with tab2:
    c_sel, c_act = st.columns([3, 1])
    with c_sel:
        selected_name = st.selectbox("Select Participant", df['name'].unique(), label_visibility="collapsed")
    
    if selected_name:
        client_metrics = next((m for m in all_metrics if m["name"] == selected_name), None)
        original_rec = next((c for c in st.session_state.caseload if c["id"] == client_metrics["id"]), None)
        
        with c_act:
            if st.button("🗑️ Remove Participant"):
                st.session_state.caseload = [c for c in st.session_state.caseload if c['id'] != client_metrics['id']]
                st.success("Deleted.")
                st.rerun()

        st.markdown(f"<div style='background:{client_metrics['color']}10; border-left:5px solid {client_metrics['color']}; padding:15px; border-radius:4px; margin-bottom:20px;'><h2 style='margin:0; color:{client_metrics['color']};'>{client_metrics['status']}</h2><p style='margin:5px 0 0 0; color:#8b949e;'>Plan ends {client_metrics['plan_end'].strftime('%d %b %Y')} • {client_metrics['weeks_remaining']:.1f} wks left</p></div>", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Balance", f"${client_metrics['balance']:,.2f}")
        m2.metric("Burn", f"${client_metrics['weekly_cost']:,.2f}/wk", f"{client_metrics['hours']}h/wk")
        m3.metric("Outcome", f"${client_metrics['surplus']:,.0f}", "Surplus" if client_metrics['surplus'] > 0 else "Deficit")

        # Chart (Fixed for Crash)
        st.markdown("### 📉 Financial Trajectory")
        weeks_to_show = max(int(client_metrics['weeks_remaining']), 1) + 5
        dates = [datetime.date.today() + timedelta(weeks=w) for w in range(weeks_to_show)]
        
        y_act = [max(0, client_metrics['balance'] - (w * client_metrics['weekly_cost'])) for w in range(len(dates))]
        
        rem = client_metrics['weeks_remaining']
        ideal_wk = client_metrics['balance'] / rem if rem > 0 else 0
        y_opt = [max(0, client_metrics['balance'] - (w * ideal_wk)) for w in range(len(dates))]
        
        chart_df = pd.DataFrame({
            "Date": dates*2, 
            "Balance": y_act + y_opt, 
            "Type": ["Actual Trajectory"]*len(dates) + ["Ideal Path"]*len(dates)
        })
        
        fig = px.line(chart_df, x="Date", y="Balance", color="Type", color_discrete
