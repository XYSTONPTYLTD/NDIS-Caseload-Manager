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
# 1. CONFIG & STYLING (THE "VISUAL UPGRADE")
# ==============================================================================
st.set_page_config(page_title="XYSTON Caseload Master", layout="wide", page_icon="🛡️", initial_sidebar_state="expanded")

# Initialize Session State
if 'caseload' not in st.session_state:
    st.session_state.caseload = []

# INJECT CUSTOM CSS
st.markdown("""
<style>
    /* GLOBAL THEME */
    .stApp { background-color: #0e1117; font-family: 'Inter', sans-serif; }
    
    /* CARDS & CONTAINERS */
    .css-1r6slb0 { background-color: #161b22; border: 1px solid #30363d; }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); border-color: #58a6ff; }
    
    /* TYPOGRAPHY */
    h1, h2, h3 { color: #e6edf3 !important; font-weight: 700 !important; letter-spacing: -0.5px !important; }
    .metric-value { font-size: 28px; font-weight: 800; color: #fff; margin: 5px 0; }
    .metric-label { font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    
    /* BUTTONS */
    .stButton button {
        border-radius: 6px;
        font-weight: 600;
        border: 1px solid #30363d;
        background-color: #21262d;
        color: #c9d1d9;
        transition: all 0.2s;
    }
    .stButton button:hover {
        border-color: #8b949e;
        color: #fff;
        background-color: #30363d;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #238636;
        border-color: #2ea043;
        color: #ffffff;
    }

    /* SIDEBAR LINKS */
    .link-row a {
        text-decoration: none;
        color: #58a6ff;
        font-size: 13px;
        display: block;
        padding: 4px 0;
        transition: color 0.2s;
    }
    .link-row a:hover { color: #fff; text-decoration: underline; }
    
    /* STATUS BADGES */
    .status-good { color: #3fb950; font-weight: bold; }
    .status-warn { color: #d29922; font-weight: bold; }
    .status-bad { color: #f85149; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SIDEBAR CONTROLS
# ==============================================================================
with st.sidebar:
    # BRANDING
    st.markdown("""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <div style="font-size: 40px; margin-bottom: 10px;">🛡️</div>
            <h2 style="margin:0; color:#fff; font-size: 22px;">XYSTON</h2>
            <div style="font-size: 10px; color: #8b949e; letter-spacing: 2px; margin-top: 5px;">CASELOAD MASTER v3.0</div>
        </div>
        <div style="height: 1px; background: #30363d; margin-bottom: 20px;"></div>
    """, unsafe_allow_html=True)

    # API KEY
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        with st.expander("🔐 Activate AI Intelligence"):
            api_key = st.text_input("Google API Key", type="password")

    # 1. DATA MANAGEMENT
    st.caption("DATA PERSISTENCE")
    c1, c2 = st.columns(2)
    with c1:
        if st.session_state.caseload:
            st.download_button("💾 Save", json.dumps(st.session_state.caseload, default=str), "caseload.json", "application/json", use_container_width=True)
        else:
            st.button("💾 Save", disabled=True, use_container_width=True)
    with c2:
        uploaded = st.file_uploader("📂 Load", type=['json'], label_visibility="collapsed")
        if uploaded:
            try:
                st.session_state.caseload = json.load(uploaded)
                st.toast(f"Loaded {len(st.session_state.caseload)} participants!", icon="✅")
                # st.rerun() # Removed to prevent loop, user can just interact
            except:
                st.error("Invalid File")

    # 2. ADD CLIENT FORM (Refined Layout)
    st.caption("MANAGEMENT")
    with st.expander("➕ Add New Participant", expanded=False):
        with st.form("new_client"):
            name = st.text_input("Full Name", placeholder="e.g. John Doe")
            c_ndis, c_level = st.columns([1, 2])
            with c_ndis: ndis = st.text_input("NDIS #", placeholder="430...")
            with c_level: level = st.selectbox("Level", list(RATES.keys()), label_visibility="collapsed")
            
            c_budget, c_bal = st.columns(2)
            with c_budget: budget = st.number_input("Total Budget", 18000.0)
            with c_bal: balance = st.number_input("Current Balance", 15000.0)
            
            c_date, c_hours = st.columns(2)
            with c_date: end_date = st.date_input("Plan End")
            with c_hours: hours = st.number_input("Hrs/Week", 1.5, step=0.1)
            
            if st.form_submit_button("Create Record", type="primary"):
                new_c = {
                    "id": str(uuid.uuid4()), "name": name, "ndis_number": ndis,
                    "level": level, "rate": RATES[level], "budget": budget,
                    "balance": balance, "plan_end": str(end_date), "hours": hours, "notes": ""
                }
                st.session_state.caseload.append(new_c)
                st.success("Added!")
                st.rerun()

    # 3. COMMAND CENTRE (The Full List)
    st.markdown("---")
    st.caption("COMMAND CENTRE")
    
    with st.expander("📖 NDIS Compliance"):
        st.markdown("""
        <div class="link-row">
            <a href="https://www.ndis.gov.au/providers/pricing-arrangements" target="_blank">💰 Pricing Arrangements (Guide)</a>
            <a href="https://ourguidelines.ndis.gov.au/" target="_blank">📜 Operational Guidelines</a>
            <a href="https://www.legislation.gov.au/Details/C2013A00020" target="_blank">⚖️ NDIS Act 2013</a>
            <a href="https://www.ndiscommission.gov.au/" target="_blank">🛡️ NDIS Commission</a>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🏦 Banking & Admin"):
        st.markdown("""
        <div class="link-row">
            <a href="https://proda.humanservices.gov.au/" target="_blank">🔐 PACE / PRODA Login</a>
            <a href="https://secure.employmenthero.com/login" target="_blank">👤 Employment Hero HR</a>
            <a href="https://login.xero.com/" target="_blank">📊 Xero Accounting</a>
            <hr style="border-color: #333; margin: 5px 0;">
            <a href="https://www.commbank.com.au/" target="_blank">🏦 Commonwealth Bank</a>
            <a href="https://www.westpac.com.au/" target="_blank">🏦 Westpac</a>
            <a href="https://www.anz.com.au/" target="_blank">🏦 ANZ</a>
            <a href="https://www.nab.com.au/" target="_blank">🏦 NAB</a>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown('<div style="text-align:center"><a href="https://www.buymeacoffee.com/h0m1ez187" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" style="width:160px;"></a></div>', unsafe_allow_html=True)


# ==============================================================================
# 3. MAIN DASHBOARD LOGIC
# ==============================================================================

# ZERO STATE (When no data exists)
if not st.session_state.caseload:
    st.markdown("""
    <div style="text-align: center; padding: 50px 20px;">
        <h1 style="font-size: 3rem; margin-bottom: 10px;">Ready to Launch?</h1>
        <p style="color: #8b949e; font-size: 1.2rem; max-width: 600px; margin: 0 auto 40px auto;">
            Welcome to your new operating system. This tool replaces your spreadsheets with a compliant, AI-powered caseload manager.
        </p>
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <div class="metric-card" style="width: 200px;">
                <div style="font-size: 30px;">📂</div>
                <div style="font-weight: bold; margin-top: 10px; color: #fff;">Load Data</div>
                <div style="font-size: 12px; color: #8b949e; margin-top: 5px;">Upload your JSON backup</div>
            </div>
            <div class="metric-card" style="width: 200px;">
                <div style="font-size: 30px;">➕</div>
                <div style="font-weight: bold; margin-top: 10px; color: #fff;">Add Client</div>
                <div style="font-size: 12px; color: #8b949e; margin-top: 5px;">Use the sidebar form</div>
            </div>
            <div class="metric-card" style="width: 200px;">
                <div style="font-size: 30px;">🤖</div>
                <div style="font-weight: bold; margin-top: 10px; color: #fff;">AI Analysis</div>
                <div style="font-size: 12px; color: #8b949e; margin-top: 5px;">Generate strategy notes</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# PROCESS DATA
all_metrics = [m for m in [calculate_client_metrics(c) for c in st.session_state.caseload] if m is not None]
df = pd.DataFrame(all_metrics)

# 1. AGGREGATE METRICS ROW
total_funds = df['balance'].sum()
monthly_rev = df['weekly_cost'].sum() * 4.33
risk_count = len(df[df['status'] == 'CRITICAL SHORTFALL'])

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"<div class='metric-card'><div class='metric-val'>{len(df)}</div><div class='metric-label'>Active Participants</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-card'><div class='metric-val'>${total_funds:,.0f}</div><div class='metric-label'>Funds Under Mgmt</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='metric-card'><div class='metric-val'>${monthly_rev:,.0f}</div><div class='metric-label'>Est. Monthly Revenue</div></div>", unsafe_allow_html=True)
risk_border = "#f85149" if risk_count > 0 else "#30363d"
risk_text = "#f85149" if risk_count > 0 else "#fff"
c4.markdown(f"<div class='metric-card' style='border-color:{risk_border}'><div class='metric-val' style='color:{risk_text}'>{risk_count}</div><div class='metric-label'>Critical Risks</div></div>", unsafe_allow_html=True)

st.markdown("---")

# 2. MAIN TABS
tab1, tab2 = st.tabs(["📊 Caseload Overview", "🔍 Participant Vault"])

# --- OVERVIEW TAB ---
with tab1:
    col_viz, col_data = st.columns([1, 2])
    
    with col_viz:
        st.markdown("### Viability Radar")
        if not df.empty:
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            color_map = {"ROBUST SURPLUS": "#3fb950", "SUSTAINABLE": "#2ea043", "MONITORING REQUIRED": "#d29922", "CRITICAL SHORTFALL": "#f85149"}
            
            fig = px.pie(status_counts, values='Count', names='Status', color='Status', color_discrete_map=color_map, hole=0.6)
            fig.update_layout(showlegend=True, margin=dict(t=0,b=0,l=0,r=0), height=300, paper_bgcolor='rgba(0,0,0,0)', font_color="#c9d1d9")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Actions")
        report_bytes = generate_caseload_report(all_metrics)
        st.download_button("📄 Download Full Report (.docx)", report_bytes, f"Caseload_{datetime.date.today()}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, type="primary")

    with col_data:
        st.markdown("### Participant List")
        
        # Custom HTML Table for better styling than standard st.dataframe
        # We create a clickable-looking table
        display_df = df[['name', 'plan_end', 'status', 'runway_weeks', 'surplus']]
        
        st.dataframe(
            display_df.style.format({'surplus': "${:,.0f}", 'runway_weeks': "{:.1f}"})
            .applymap(lambda x: 'color: #f85149; font-weight: bold' if x == 'CRITICAL SHORTFALL' else 'color: #3fb950' if x == 'ROBUST SURPLUS' else '', subset=['status']),
            use_container_width=True,
            height=450,
            column_config={
                "name": "Name",
                "plan_end": "Plan Ends",
                "status": "Health Status",
                "runway_weeks": "Runway (Wks)",
                "surplus": "Outcome"
            }
        )

# --- DETAIL TAB ---
with tab2:
    c_select, c_delete = st.columns([3, 1])
    with c_select:
        selected_name = st.selectbox("Select Participant", df['name'].unique(), label_visibility="collapsed")
    
    if selected_name:
        client_metrics = next((m for m in all_metrics if m["name"] == selected_name), None)
        original_rec = next((c for c in st.session_state.caseload if c["id"] == client_metrics["id"]), None)
        
        with c_delete:
            if st.button("🗑️ Remove Participant"):
                st.session_state.caseload = [c for c in st.session_state.caseload if c['id'] != client_metrics['id']]
                st.success("Deleted.")
                st.rerun()

        # BANNER
        st.markdown(f"""
        <div style="background: {client_metrics['color']}10; border-left: 5px solid {client_metrics['color']}; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
            <h2 style="color: {client_metrics['color']}; margin:0;">{client_metrics['status']}</h2>
            <p style="margin: 5px 0 0 0; color: #c9d1d9; font-size: 14px;">
                Plan ends <b>{client_metrics['plan_end'].strftime('%d %b %Y')}</b> • 
                Runway: <b>{client_metrics['runway_weeks']:.1f} wks</b> (Buffer: {client_metrics['runway_weeks'] - client_metrics['weeks_remaining']:.1f} wks)
            </p>
        </div>
        """, unsafe_allow_html=True)

        # METRICS ROW
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Balance", f"${client_metrics['balance']:,.2f}")
        m2.metric("Burn Rate", f"${client_metrics['weekly_cost']:,.2f}", f"{client_metrics['hours']}h @ ${client_metrics['rate']:.0f}")
        m3.metric("Hours Left", f"{(client_metrics['balance']/client_metrics['rate']):.1f} hrs")
        m4.metric("End Result", f"${client_metrics['surplus']:,.0f}", "Surplus" if client_metrics['surplus'] > 0 else "Deficit")

        # CHART SECTION
        st.markdown("### 📉 Financial Trajectory")
        
        # Safe range generation
        weeks_to_show = max(int(client_metrics['weeks_remaining']), 1) + 5
        dates = [datetime.date.today() + timedelta(weeks=w) for w in range(weeks_to_show)]
        
        y_act = [max(0, client_metrics['balance'] - (w * client_metrics['weekly_cost'])) for w in range(len(dates))]
        
        # Ideal burn (prevent divide by zero)
        rem = client_metrics['weeks_remaining']
        ideal_wk = client_metrics['balance'] / rem if rem > 0 else 0
        y_opt = [max(0, client_metrics['balance'] - (w * ideal_wk)) for w in range(len(dates))]
        
        chart_df = pd.DataFrame({
            "Date": dates*2, 
            "Balance": y_act + y_opt, 
            "Type": ["Actual Trajectory"]*len(dates) + ["Ideal Path"]*len(dates)
        })
        
        fig = px.line(chart_df, x="Date", y="Balance", color="Type", 
                      color_discrete_map={"Actual Trajectory": client_metrics['color'], "Ideal Path": "#6e7681"})
        fig.update_traces(patch={"line": {"dash": "dot"}}, selector={"legendgroup": "Ideal Path"})
        
        try:
            fig.add_vline(x=client_metrics['plan_end'], line_dash="dash", line_color="#c9d1d9", annotation_text="End Date")
        except: pass
        
        fig.update_layout(
            height=350, 
            hovermode="x unified", 
            margin=dict(t=30,b=0,l=0,r=0), 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#8b949e'),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#30363d')
        )
        st.plotly_chart(fig, use_container_width=True)

        # AI & NOTES SECTION
        st.markdown("### 📝 Strategy & File Notes")
        c_gen, c_txt = st.columns([1, 2])
        
        with c_gen:
            st.info("Generate a professional file note for this client.")
            if st.button("✨ Generate Strategy Note", use_container_width=True):
                if api_key:
                    with st.spinner("Consulting AI..."):
                        try:
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel('gemini-2.0-flash')
                            prompt = f"Write a strategic NDIS file note for {selected_name}. Status: {client_metrics['status']}. Balance: ${client_metrics['balance']}. Burn: ${client_metrics['weekly_cost']}/wk. Outcome: ${client_metrics['surplus']}. Tone: Professional Australian NDIS."
                            response = model.generate_content(prompt)
                            original_rec['notes'] = response.text
                            st.success("Generated!")
                            st.rerun()
                        except Exception as e: st.error(f"AI Error: {e}")
                else: st.error("API Key missing.")
            
            # Email Button
            subject = f"Update: {selected_name} - {datetime.date.today()}"
            body = f"Status: {client_metrics['status']}%0ABalance: ${client_metrics['balance']}%0A{original_rec.get('notes', '')}"
            st.link_button("📧 Draft Email", f"mailto:?subject={subject}&body={body}", use_container_width=True)

        with c_txt:
            notes = st.text_area("Client Notes / AI Output", value=original_rec.get('notes', ''), height=250)
            if notes != original_rec.get('notes', ''):
                original_rec['notes'] = notes
