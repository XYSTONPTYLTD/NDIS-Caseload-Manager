import streamlit as st
import pandas as pd
import plotly.express as px
import json
import datetime
from datetime import timedelta
import uuid
import google.generativeai as genai
from utils import calculate_client_metrics, generate_caseload_report, RATES

# ==============================================================================
# CONFIG & ACCESS CONTROL
# ==============================================================================
st.set_page_config(page_title="XYSTON Caseload", layout="wide", page_icon="🛡️")

# ACCESS CODE LOCK
REQUIRED_CODE = st.secrets.get("ACCESS_CODE", None)
def check_password():
    if not REQUIRED_CODE: return True
    if st.session_state.get('authenticated', False): return True
    st.markdown("### 🛡️ Xyston Master Access")
    if st.text_input("Access Code", type="password") == REQUIRED_CODE:
        st.session_state['authenticated'] = True
        st.rerun()
    return False

if not check_password(): st.stop()

# Initialize Session
if 'caseload' not in st.session_state:
    st.session_state.caseload = []

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-card { background: #1e2129; border: 1px solid #333; padding: 15px; border-radius: 8px; text-align: center; }
    .metric-val { font-size: 26px; font-weight: 800; color: #fff; margin-bottom: 5px; }
    .metric-lbl { font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; }
    .quick-link a { display: block; padding: 6px 10px; margin: 3px 0; background: #1e2129; border: 1px solid #333; border-radius: 6px; color: #ccc; text-decoration: none; font-size: 0.8rem; transition: all 0.2s; }
    .quick-link a:hover { background: #2d3342; border-color: #555; color: #fff; padding-left: 15px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("<h1 style='text-align:center; margin-bottom:0;'>🛡️</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; margin-top:0; letter-spacing:2px;'>XYSTON</h2>", unsafe_allow_html=True)
    st.caption("Caseload Master v3.0")
    
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        with st.expander("🔐 AI Key"):
            api_key = st.text_input("Google Key", type="password")

    st.markdown("---")
    
    # DATA MANAGER
    with st.expander("💾 Database (Load/Save)", expanded=True):
        if st.session_state.caseload:
            st.download_button("⬇️ Backup (JSON)", json.dumps(st.session_state.caseload, default=str), "caseload.json", "application/json", use_container_width=True)
        
        uploaded = st.file_uploader("⬆️ Restore", type=['json'])
        if uploaded:
            try:
                st.session_state.caseload = json.load(uploaded)
                st.success("Restored!")
                st.rerun()
            except: st.error("Bad file.")

    # ADD PARTICIPANT
    with st.expander("➕ Add Participant"):
        with st.form("new_client"):
            name = st.text_input("Name")
            ndis = st.text_input("NDIS Number")
            level = st.selectbox("Level", list(RATES.keys()))
            budget = st.number_input("Budget ($)", 18000.0)
            balance = st.number_input("Balance ($)", 15000.0)
            end_date = st.date_input("Plan End")
            hours = st.number_input("Hours/Week", 1.5, step=0.1)
            
            if st.form_submit_button("Add"):
                new_c = {"id": str(uuid.uuid4()), "name": name, "ndis_number": ndis, "level": level, "rate": RATES[level], "budget": budget, "balance": balance, "plan_end": str(end_date), "hours": hours, "notes": ""}
                st.session_state.caseload.append(new_c)
                st.success("Added!")
                st.rerun()

    # COMMAND CENTRE
    st.markdown("---")
    st.markdown("### ⚡ Command Centre")
    with st.expander("📖 Rules & Legislation", expanded=True):
        st.markdown('<div class="quick-link"><a href="https://www.ndis.gov.au/providers/pricing-arrangements" target="_blank">💰 Pricing Guide</a><a href="https://ourguidelines.ndis.gov.au/" target="_blank">📜 Operational Guidelines</a><a href="https://www.ndiscommission.gov.au/" target="_blank">🛡️ Commission</a></div>', unsafe_allow_html=True)
    with st.expander("🛠️ Admin Tools"):
        st.markdown('<div class="quick-link"><a href="https://proda.humanservices.gov.au/" target="_blank">🔐 PRODA Login</a><a href="https://login.xero.com/" target="_blank">Xero</a></div>', unsafe_allow_html=True)

# ==============================================================================
# DASHBOARD LOGIC
# ==============================================================================
if not st.session_state.caseload:
    st.info("👋 Welcome. Use the sidebar to **Add a Participant** or **Load a Backup**.")
    st.stop()

all_metrics = [m for m in [calculate_client_metrics(c) for c in st.session_state.caseload] if m is not None]
df = pd.DataFrame(all_metrics)

# 1. TOP STATS
total_funds = df['balance'].sum()
monthly_rev = df['weekly_cost'].sum() * 4.33
risk_count = len(df[df['status'] == 'CRITICAL SHORTFALL'])

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"<div class='metric-card'><div class='metric-val'>{len(df)}</div><div class='metric-lbl'>Participants</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-card'><div class='metric-val'>${total_funds:,.0f}</div><div class='metric-lbl'>Funds Managed</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='metric-card'><div class='metric-val'>${monthly_rev:,.0f}</div><div class='metric-lbl'>Proj. Monthly Rev</div></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='metric-card' style='border-color:{'#ef4444' if risk_count > 0 else '#333'}'><div class='metric-val' style='color:{'#ef4444' if risk_count > 0 else '#fff'}'>{risk_count}</div><div class='metric-lbl'>Critical Risks</div></div>", unsafe_allow_html=True)

# ==============================================================================
# MAIN TABS
# ==============================================================================
st.markdown("---")
tab1, tab2 = st.tabs(["📊 Overview", "🔍 Client Vault"])

# --- OVERVIEW TAB ---
with tab1:
    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.markdown("#### Viability")
        if not df.empty:
            fig = px.pie(df, names='status', color='status', hole=0.6, color_discrete_map={"ROBUST SURPLUS": "#10b981", "SUSTAINABLE": "#22c55e", "MONITORING REQUIRED": "#eab308", "CRITICAL SHORTFALL": "#ef4444"})
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=200)
            st.plotly_chart(fig, use_container_width=True)
        
        report_bytes = generate_caseload_report(all_metrics)
        st.download_button("📄 Download Word Report", report_bytes, f"Caseload_Report_{datetime.date.today()}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, type="primary")

    with c_right:
        st.markdown("#### Active Participants")
        disp_df = df[['name', 'plan_end', 'status', 'runway_weeks', 'surplus']]
        disp_df.columns = ['Name', 'Plan End', 'Status', 'Runway (Wks)', 'Outcome ($)']
        st.dataframe(disp_df.style.format({'Outcome ($)': "${:,.0f}", 'Runway (Wks)': "{:.1f}"}).applymap(lambda x: 'color:#ef4444' if x=='CRITICAL SHORTFALL' else 'color:#10b981' if x=='ROBUST SURPLUS' else '', subset=['Status']), use_container_width=True, height=400)

# --- CLIENT VAULT TAB ---
with tab2:
    c_sel, c_act = st.columns([3, 1])
    with c_sel:
        selected_name = st.selectbox("Select Participant", df['name'].unique())
        client_metrics = next((m for m in all_metrics if m["name"] == selected_name), None)
        original_rec = next((c for c in st.session_state.caseload if c["id"] == client_metrics["id"]), None)
    
    with c_act:
        st.write("")
        st.write("")
        if st.button("🗑️ Delete"):
            st.session_state.caseload = [c for c in st.session_state.caseload if c['id'] != client_metrics['id']]
            st.success("Deleted.")
            st.rerun()

    if client_metrics:
        # Banner
        st.markdown(f"<div style='background:{client_metrics['color']}15; border:1px solid {client_metrics['color']}; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;'><h2 style='color:{client_metrics['color']}; margin:0;'>{client_metrics['status']}</h2><p style='margin:5px 0 0 0; color:#ccc;'>Runs out {client_metrics['depletion_date'].strftime('%d %b %Y')} • {client_metrics['weeks_remaining']:.1f} wks left</p></div>", unsafe_allow_html=True)

        # Cards
        m1, m2, m3 = st.columns(3)
        m1.metric("Balance", f"${client_metrics['balance']:,.2f}")
        m2.metric("Burn", f"${client_metrics['weekly_cost']:,.2f}/wk", f"{client_metrics['hours']}h/wk")
        m3.metric("Outcome", f"${client_metrics['surplus']:,.0f}", "Surplus" if client_metrics['surplus'] > 0 else "Deficit")

        # Chart
        dates = [datetime.date.today() + timedelta(weeks=w) for w in range(int(client_metrics['weeks_remaining']) + 5)]
        y_act = [max(0, client_metrics['balance'] - (w * client_metrics['weekly_cost'])) for w in range(len(dates))]
        y_opt = [max(0, client_metrics['balance'] - (w * (client_metrics['balance']/client_metrics['weeks_remaining'] if client_metrics['weeks_remaining']>0 else 0))) for w in range(len(dates))]
        
        fig = px.line(pd.DataFrame({"Date": dates*2, "Balance": y_act + y_opt, "Type": ["Actual"]*len(dates) + ["Ideal"]*len(dates)}), x="Date", y="Balance", color="Type", color_discrete_map={"Actual": client_metrics['color'], "Ideal": "#555"})
        fig.update_traces(patch={"line": {"dash": "dot"}}, selector={"legendgroup": "Ideal"})
        fig.add_vline(x=client_metrics['plan_end'], line_dash="dash", line_color="white")
        fig.update_layout(height=300, margin=dict(t=10,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        # AI & Email
        st.markdown("---")
        c_note, c_email = st.columns(2)
        
        with c_note:
            st.subheader("🤖 AI Strategy")
            if st.button("Generate Note ✨"):
                if api_key:
                    with st.spinner("Thinking..."):
                        try:
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel('gemini-2.0-flash')
                            prompt = f"Write a strategic NDIS file note for {selected_name}. Status: {client_metrics['status']}. Balance: ${client_metrics['balance']}. Burn: ${client_metrics['weekly_cost']}/wk. Outcome: ${client_metrics['surplus']}. Tone: Professional."
                            response = model.generate_content(prompt)
                            original_rec['notes'] = response.text
                            st.rerun()
                        except Exception as e: st.error(f"AI Error: {e}")
                else: st.error("No API Key.")
            
            new_note = st.text_area("Notes", value=original_rec.get('notes', ''), height=200)
            if new_note != original_rec.get('notes', ''): original_rec['notes'] = new_note

        with c_email:
            st.subheader("📧 Quick Actions")
            subject = f"NDIS Update: {selected_name} - {datetime.date.today().strftime('%d/%m/%Y')}"
            body = f"Hi Team,%0A%0ACurrent Status: {client_metrics['status']}%0ABalance: ${client_metrics['balance']:,.2f}%0APlan Ends: {client_metrics['plan_end']}%0A%0A{original_rec.get('notes', '')}"
            st.link_button("Draft Email to Plan Manager", f"mailto:?subject={subject}&body={body}")
