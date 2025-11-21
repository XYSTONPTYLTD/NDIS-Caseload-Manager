import streamlit as st
import pandas as pd
import plotly.express as px
import json
import datetime
from utils import calculate_client_metrics, generate_caseload_report, RATES
import google.generativeai as genai

# ==============================================================================
# CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="NDIS Caseload Master", layout="wide", page_icon="🛡️")

# CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-box { background: #1e2129; padding: 15px; border-radius: 8px; border: 1px solid #333; text-align: center; }
    .metric-val { font-size: 24px; font-weight: bold; color: #fff; }
    .metric-lbl { font-size: 12px; color: #aaa; text-transform: uppercase; }
    .status-badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SESSION STATE (The Database)
# ==============================================================================
if 'clients' not in st.session_state:
    st.session_state.clients = []

# Helper to calculate all metrics for display
def get_all_metrics():
    return [calculate_client_metrics(c) for c in st.session_state.clients]

# ==============================================================================
# SIDEBAR - DATA & ACTIONS
# ==============================================================================
with st.sidebar:
    st.markdown("## 🛡️ XYSTON Caseload")
    st.caption("NDIS Master Manager v1.0")
    
    # 1. DATA MANAGER (Load/Save)
    with st.expander("💾 Data Manager", expanded=True):
        # SAVE
        if st.session_state.clients:
            json_str = json.dumps(st.session_state.clients, default=str)
            st.download_button(
                "⬇️ Save Database (JSON)",
                data=json_str,
                file_name="ndis_caseload.json",
                mime="application/json",
                use_container_width=True
            )
        
        # LOAD
        uploaded_file = st.file_uploader("⬆️ Load Database", type=['json'])
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                st.session_state.clients = data
                st.success(f"Loaded {len(data)} clients!")
            except:
                st.error("Invalid JSON file.")

    # 2. ADD NEW CLIENT
    st.markdown("### ➕ Add Participant")
    with st.form("add_client_form", clear_on_submit=True):
        name = st.text_input("Name")
        ndis_num = st.text_input("NDIS Number")
        level = st.selectbox("Level", list(RATES.keys()))
        rate = RATES[level]
        budget = st.number_input("Total Budget ($)", value=18000.0)
        balance = st.number_input("Current Balance ($)", value=15000.0)
        end_date = st.date_input("Plan End Date")
        hours = st.number_input("Hours/Week", value=1.5, step=0.1)
        
        if st.form_submit_button("Add to Caseload"):
            new_client = {
                "id": datetime.datetime.now().strftime("%f"), # Simple unique ID
                "name": name,
                "ndis_number": ndis_num,
                "support_level": level,
                "hourly_rate": rate,
                "total_budget": budget,
                "balance": balance,
                "plan_end": str(end_date),
                "hours_per_week": hours,
                "ai_strategy": "" # Placeholder for AI notes
            }
            st.session_state.clients.append(new_client)
            st.rerun()

    # 3. LINKS
    st.markdown("---")
    with st.expander("⚡ Command Centre"):
        st.markdown("[💰 Price Guide](https://www.ndis.gov.au/providers/pricing-arrangements)")
        st.markdown("[🔐 PRODA Login](https://proda.humanservices.gov.au/)")
        st.markdown("[⚖️ NDIS Commission](https://www.ndiscommission.gov.au/)")

# ==============================================================================
# MAIN DASHBOARD
# ==============================================================================

if not st.session_state.clients:
    st.info("👋 Welcome! Use the sidebar to **Add a Participant** or **Load a Database file**.")
    st.stop()

# Calculate Real-time Metrics
all_metrics = get_all_metrics()
df = pd.DataFrame(all_metrics)

# 1. TOP METRICS ROW
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"<div class='metric-box'><div class='metric-val'>{len(df)}</div><div class='metric-lbl'>Participants</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-box'><div class='metric-val'>${df['balance'].sum():,.0f}</div><div class='metric-lbl'>Funds Managed</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='metric-box'><div class='metric-val'>${df['weekly_cost'].sum():,.0f}</div><div class='metric-lbl'>Weekly Revenue</div></div>", unsafe_allow_html=True)
risk_count = len(df[df['status'] == "CRITICAL SHORTFALL"])
risk_color = "#ff4444" if risk_count > 0 else "#00cc66"
c4.markdown(f"<div class='metric-box' style='border-color:{risk_color}'><div class='metric-val' style='color:{risk_color}'>{risk_count}</div><div class='metric-lbl'>Critical Risks</div></div>", unsafe_allow_html=True)

# 2. CASELOAD TABLE
st.markdown("### 📋 Caseload Overview")
# Create a clean display dataframe
display_df = df[['name', 'status', 'runway_weeks', 'surplus', 'plan_end']]
display_df.columns = ['Participant', 'Status', 'Runway (Wks)', 'Outcome ($)', 'Plan End']

# Custom formatting isn't supported in standard st.dataframe easily, so we rely on clean data
st.dataframe(
    display_df.style.map(lambda x: 'color: #ff4444' if x == 'CRITICAL SHORTFALL' else 'color: #00cc66' if x == 'ROBUST SURPLUS' else '', subset=['Status']),
    use_container_width=True,
    hide_index=True
)

# 3. EXPORT REPORT BUTTON
st.markdown("---")
col_rep1, col_rep2 = st.columns([3,1])
with col_rep1:
    st.markdown("### 📄 Generate Reports")
    st.caption("Creates a full Word Document analysis of your entire caseload.")
with col_rep2:
    doc_bytes = generate_caseload_report(all_metrics)
    st.download_button(
        "⬇️ Download Word Report",
        data=doc_bytes,
        file_name=f"Caseload_Report_{datetime.date.today()}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
        use_container_width=True
    )

# ==============================================================================
# 4. DRILL DOWN (CLIENT DETAIL VIEW)
# ==============================================================================
st.markdown("---")
st.markdown("### 🔍 Participant Drill-Down")

selected_name = st.selectbox("Select Participant", df['name'].tolist())
client_data = next((item for item in st.session_state.clients if item["name"] == selected_name), None)
metrics = calculate_client_metrics(client_data)

if client_data:
    # Metric Cards for Individual
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Balance", f"${metrics['balance']:,.2f}")
    m2.metric("Runway", f"{metrics['runway_weeks']:.1f} weeks", f"{metrics['runway_weeks'] - metrics['weeks_remaining']:.1f} vs Plan")
    m3.metric("Outcome", f"${metrics['surplus']:,.2f}", "Surplus" if metrics['surplus'] > 0 else "Deficit")

    # Burn Down Chart
    dates = [datetime.date.today() + timedelta(weeks=w) for w in range(int(metrics['weeks_remaining']) + 5)]
    y_val = [max(0, metrics['balance'] - (w * metrics['weekly_cost'])) for w in range(len(dates))]
    
    fig = px.line(x=dates, y=y_val, title=f"{selected_name} - Financial Trajectory")
    fig.update_traces(line_color=metrics['color'], line_width=3)
    fig.add_vline(x=metrics['plan_end'], line_dash="dash", line_color="white", annotation_text="Plan End")
    st.plotly_chart(fig, use_container_width=True)

    # AI Strategy Generator (Individual)
    with st.expander("🤖 Generate AI Strategy Note"):
        api_key = st.secrets.get("GEMINI_API_KEY", None)
        if not api_key: api_key = st.text_input("Google API Key", type="password")
        
        if st.button("Generate Strategy"):
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    prompt = f"Write a short, strategic NDIS file note for {selected_name}. Status: {metrics['status']}. Balance: ${metrics['balance']}. Burn: ${metrics['weekly_cost']}/wk. Outcome: ${metrics['surplus']}. Tone: Professional."
                    response = model.generate_content(prompt)
                    
                    # Save to session state so it exports to JSON/Word later
                    client_data['ai_strategy'] = response.text
                    st.success("Strategy Generated & Saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("No API Key found.")
        
        if client_data.get('ai_strategy'):
            st.text_area("Current Strategy Note", value=client_data['ai_strategy'], height=200)
