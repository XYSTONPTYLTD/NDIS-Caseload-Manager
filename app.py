import streamlit as st
import pandas as pd
import plotly.express as px
import json
import datetime
from datetime import timedelta # <--- This was the missing key
import uuid
import google.generativeai as genai
from utils import calculate_client_metrics, generate_caseload_report, RATES

# ==============================================================================
# CONFIG & STATE
# ==============================================================================
st.set_page_config(page_title="XYSTON Caseload", layout="wide", page_icon="🛡️", initial_sidebar_state="expanded")

# Load Session State
if 'caseload' not in st.session_state:
    st.session_state.caseload = [] # List of Client Dictionaries

# CSS Styling
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-card { background: #1e2129; border: 1px solid #333; padding: 15px; border-radius: 8px; text-align: center; }
    .metric-val { font-size: 26px; font-weight: 800; color: #fff; margin-bottom: 5px; }
    .metric-lbl { font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; }
    .status-badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; color: #000; }
    div[data-testid="stExpander"] { border: 1px solid #333; border-radius: 8px; background: #161b22; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR: NAVIGATION & ACTIONS
# ==============================================================================
with st.sidebar:
    st.markdown("<h1 style='text-align:center; margin-bottom:0;'>🛡️</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; margin-top:0; letter-spacing:2px;'>XYSTON</h2>", unsafe_allow_html=True)
    st.caption("Caseload Manager v2.1")
    
    # API Key Input
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        with st.expander("🔐 AI Key"):
            api_key = st.text_input("Google Key", type="password")

    st.markdown("---")
    
    # --- DATA MANAGER ---
    with st.expander("💾 Database (Load/Save)", expanded=True):
        # Save
        if st.session_state.caseload:
            json_str = json.dumps(st.session_state.caseload, default=str)
            st.download_button("⬇️ Backup to PC", json_str, "ndis_caseload.json", "application/json", use_container_width=True)
        
        # Load
        uploaded = st.file_uploader("⬆️ Restore Backup", type=['json'])
        if uploaded:
            try:
                data = json.load(uploaded)
                st.session_state.caseload = data
                st.success(f"Restored {len(data)} clients!")
                st.rerun()
            except:
                st.error("Bad file.")

    # --- ADD CLIENT FORM ---
    with st.expander("➕ Add Participant"):
        with st.form("new_client"):
            name = st.text_input("Full Name")
            ndis = st.text_input("NDIS Number")
            level = st.selectbox("Support Level", list(RATES.keys()))
            budget = st.number_input("Total Budget ($)", 18000.0)
            balance = st.number_input("Current Balance ($)", 15000.0)
            end_date = st.date_input("Plan End Date")
            hours = st.number_input("Hours/Week", 1.5, step=0.1)
            
            if st.form_submit_button("Create File"):
                # Get rate safely
                rate = RATES.get(level, 100.14)
                new_c = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "ndis_number": ndis,
                    "level": level,
                    "rate": rate,
                    "budget": budget,
                    "balance": balance,
                    "plan_end": str(end_date),
                    "hours": hours,
                    "notes": ""
                }
                st.session_state.caseload.append(new_c)
                st.success("Added!")
                st.rerun()

    # --- LINKS ---
    st.markdown("---")
    with st.expander("⚡ Quick Links"):
        st.markdown("• [💰 Price Guide](https://www.ndis.gov.au/providers/pricing-arrangements)")
        st.markdown("• [🔐 PRODA](https://proda.humanservices.gov.au/)")
        st.markdown("• [⚖️ NDIS Commission](https://www.ndiscommission.gov.au/)")

# ==============================================================================
# MAIN DASHBOARD LOGIC
# ==============================================================================

# 1. Process All Data
if not st.session_state.caseload:
    st.info("👋 Welcome to **Xyston Caseload Master**.")
    st.markdown("To get started, use the sidebar to **Add a Participant** or **Load a Backup File**.")
    st.stop()

# Calculate metrics for everyone (Filter out any None results from bad data)
all_metrics = [m for m in [calculate_client_metrics(c) for c in st.session_state.caseload] if m is not None]
df = pd.DataFrame(all_metrics)

# 2. Dashboard Header (Aggregate Stats)
total_funds = df['balance'].sum()
monthly_rev = df['weekly_cost'].sum() * 4.33
risk_count = len(df[df['status'] == 'CRITICAL SHORTFALL'])

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"<div class='metric-card'><div class='metric-val'>{len(df)}</div><div class='metric-lbl'>Active Participants</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-card'><div class='metric-val'>${total_funds:,.0f}</div><div class='metric-lbl'>Funds Managed</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='metric-card'><div class='metric-val'>${monthly_rev:,.0f}</div><div class='metric-lbl'>Proj. Monthly Rev</div></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='metric-card' style='border-color:{'#ef4444' if risk_count > 0 else '#333'}'><div class='metric-val' style='color:{'#ef4444' if risk_count > 0 else '#fff'}'>{risk_count}</div><div class='metric-lbl'>Critical Risks</div></div>", unsafe_allow_html=True)

# ==============================================================================
# TABS: OVERVIEW vs DETAIL
# ==============================================================================
st.markdown("---")
tab_overview, tab_detail = st.tabs(["📊 Caseload Overview", "🔍 Client Vault"])

# --- TAB 1: OVERVIEW ---
with tab_overview:
    col_chart, col_list = st.columns([1, 2])
    
    with col_chart:
        st.markdown("#### Viability Distribution")
        # Pie Chart of Status
        if not df.empty:
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            color_map = {"ROBUST SURPLUS": "#10b981", "SUSTAINABLE": "#22c55e", "MONITORING REQUIRED": "#eab308", "CRITICAL SHORTFALL": "#ef4444"}
            fig = px.pie(status_counts, values='Count', names='Status', color='Status', color_discrete_map=color_map, hole=0.6)
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=200)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("#### Download Reports")
        report_bytes = generate_caseload_report(all_metrics)
        st.download_button("📄 Download Full Caseload Report (.docx)", report_bytes, f"Caseload_Report_{datetime.date.today()}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, type="primary")

    with col_list:
        st.markdown("#### Active Participants")
        # Clean Table for Display
        display_df = df[['name', 'plan_end', 'status', 'runway_weeks', 'surplus']]
        display_df.columns = ['Name', 'Plan End', 'Status', 'Runway (Wks)', 'Outcome ($)']
        
        st.dataframe(
            display_df.style.format({'Outcome ($)': "${:,.0f}", 'Runway (Wks)': "{:.1f}"})
            .applymap(lambda x: 'color: #ef4444; font-weight: bold' if x == 'CRITICAL SHORTFALL' else 'color: #10b981' if x == 'ROBUST SURPLUS' else '', subset=['Status']),
            use_container_width=True, 
            height=400
        )

# --- TAB 2: CLIENT VAULT (Drill Down) ---
with tab_detail:
    c_sel, c_del = st.columns([3, 1])
    with c_sel:
        client_names = df['name'].unique()
        if len(client_names) > 0:
            selected_name = st.selectbox("Select Participant to Manage", client_names)
            
            # Get selected client data safely
            metrics = next((item for item in all_metrics if item["name"] == selected_name), None)
            
            # Get original record for updates
            if metrics:
                original_record = next((item for item in st.session_state.caseload if item["id"] == metrics["id"]), None)
    
    with c_del:
        st.write("") # Spacing
        st.write("") 
        if st.button("🗑️ Delete Client", key="del_btn"):
            if metrics:
                st.session_state.caseload = [c for c in st.session_state.caseload if c['id'] != metrics['id']]
                st.success("Deleted.")
                st.rerun()

    if metrics:
        # --- CLIENT DASHBOARD ---
        st.markdown(f"""
        <div style="background: {metrics['color']}15; border: 1px solid {metrics['color']}; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <h2 style="color: {metrics['color']}; margin:0;">{metrics['status']}</h2>
            <p style="margin:5px 0 0 0; color: #ccc;">Plan ends {metrics['plan_end'].strftime('%d %b %Y')} • {metrics['weeks_remaining']:.1f} weeks remaining</p>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Balance", f"${metrics['balance']:,.2f}")
        m2.metric("Burn Rate", f"${metrics['weekly_cost']:,.2f}", f"{metrics['hours']}h @ ${metrics['rate']:.0f}")
        m3.metric("Runway", f"{metrics['runway_weeks']:.1f} wks", f"{metrics['runway_weeks'] - metrics['weeks_remaining']:.1f} vs Plan")
        m4.metric("Outcome", f"${metrics['surplus']:,.0f}", "Surplus" if metrics['surplus'] > 0 else "Deficit")

        # Burn Down Chart
        st.markdown("### 📉 Financial Trajectory")
        
        # Safe range for chart (prevent negative range errors)
        chart_weeks = int(metrics['weeks_remaining']) + 5
        if chart_weeks < 1: chart_weeks = 5
            
        dates = [datetime.date.today() + timedelta(weeks=w) for w in range(chart_weeks)]
        y_actual = [max(0, metrics['balance'] - (w * metrics['weekly_cost'])) for w in range(len(dates))]
        
        # Ideal line logic
        ideal_burn = metrics['balance'] / metrics['weeks_remaining'] if metrics['weeks_remaining'] > 0 else 0
        y_ideal = [max(0, metrics['balance'] - (w * ideal_burn)) for w in range(len(dates))]
        
        chart_df = pd.DataFrame({
            "Date": dates * 2,
            "Balance": y_actual + y_ideal,
            "Type": ["Projected"] * len(dates) + ["Ideal"] * len(dates)
        })
        
        fig = px.line(chart_df, x="Date", y="Balance", color="Type", 
                      color_discrete_map={"Projected": metrics['color'], "Ideal": "#555"})
        fig.update_traces(patch={"line": {"dash": "dot"}}, selector={"legendgroup": "Ideal"})
        
        # Only add Plan End line if valid date
        try:
            fig.add_vline(x=metrics['plan_end'], line_dash="dash", line_color="white", annotation_text="Plan End")
        except:
            pass
            
        fig.update_layout(height=350, hovermode="x unified", margin=dict(t=20,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        # --- AI STRATEGY & NOTES ---
        st.markdown("---")
        col_ai, col_notes = st.columns([1, 1])
        
        with col_ai:
            st.subheader("🤖 AI Strategy Generator")
            if st.button("Generate File Note ✨"):
                if api_key:
                    with st.spinner("Thinking..."):
                        try:
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel('gemini-2.0-flash')
                            prompt = f"Write a short, strategic NDIS file note for {selected_name}. Status: {metrics['status']}. Balance: ${metrics['balance']}. Burn: ${metrics['weekly_cost']}/wk. Outcome: ${metrics['surplus']}. Tone: Professional Australian NDIS."
                            response = model.generate_content(prompt)
                            original_record['notes'] = response.text
                            st.success("Note generated and saved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"AI Error: {e}")
                else:
                    st.error("No API Key.")
        
        with col_notes:
            st.subheader("📝 Strategy Notes")
            # Text area updates the session state in real time
            new_notes = st.text_area("Client Notes", value=original_record.get('notes', ''), height=200)
            if new_notes != original_record.get('notes', ''):
                original_record['notes'] = new_notes
