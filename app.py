import streamlit as st
import pandas as pd
import plotly.express as px
import json
import datetime
from datetime import timedelta
import uuid
import requests
import pytz
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
    
    /* METRIC CARDS (Active Dashboard) */
    .metric-card {
        background-color: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .metric-val { font-size: 24px; font-weight: 800; color: #ffffff; }
    .metric-lbl { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }
    
    /* WEATHER CARDS */
    .weather-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        transition: transform 0.2s;
    }
    .weather-card:hover { border-color: #58a6ff; transform: translateY(-2px); }
    .city-name { font-size: 14px; font-weight: 700; color: #fff; text-transform: uppercase; letter-spacing: 1px; }
    .city-time { font-size: 20px; font-weight: 300; color: #58a6ff; font-family: monospace; margin: 5px 0; }
    .weather-row { display: flex; justify-content: space-between; font-size: 12px; color: #c9d1d9; margin-top: 8px; padding-top: 8px; border-top: 1px solid #30363d; }
    .weather-temp { font-weight: bold; color: #fff; }
    
    /* SIDEBAR LINKS */
    .link-row a {
        text-decoration: none; color: #58a6ff; font-size: 13px; display: block;
        padding: 6px 8px; margin: 2px 0; border-radius: 4px; background: #161b22;
        border: 1px solid #30363d; transition: all 0.2s;
    }
    .link-row a:hover { background: #238636; color: white; border-color: #2ea043; padding-left: 15px; }
    
    /* GUIDE BOXES */
    .guide-box { background-color: #161b22; border-left: 4px solid #238636; padding: 15px; margin-bottom: 15px; border-radius: 4px; }
    .guide-title { font-weight: bold; color: #fff; margin-bottom: 5px; font-size: 1.1em; }
    .guide-text { color: #8b949e; font-size: 0.9em; line-height: 1.5; }
    
    .disclaimer-text { font-size: 0.75em; color: #484f58; text-align: center; margin-top: 30px; }
    .stButton button { width: 100%; border-radius: 6px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. WEATHER UTILITIES
# ==============================================================================
CAPITALS = {
    "Canberra": {"lat": -35.28, "lng": 149.13, "tz": "Australia/Canberra"},
    "Sydney": {"lat": -33.86, "lng": 151.20, "tz": "Australia/Sydney"},
    "Melbourne": {"lat": -37.81, "lng": 144.96, "tz": "Australia/Melbourne"},
    "Brisbane": {"lat": -27.47, "lng": 153.02, "tz": "Australia/Brisbane"},
    "Perth": {"lat": -31.95, "lng": 115.86, "tz": "Australia/Perth"},
    "Adelaide": {"lat": -34.92, "lng": 138.60, "tz": "Australia/Adelaide"},
    "Hobart": {"lat": -42.88, "lng": 147.32, "tz": "Australia/Hobart"},
    "Darwin": {"lat": -12.46, "lng": 130.84, "tz": "Australia/Darwin"},
}

def get_weather_icon(code):
    if code <= 1: return "☀️"
    if code <= 3: return "⛅"
    if code <= 48: return "🌫️"
    if code <= 67: return "🌧️"
    if code <= 77: return "🌨️"
    if code <= 82: return "⛈️"
    return "🌦️"

@st.cache_data(ttl=3600) # Cache for 1 hour
def fetch_weather():
    weather_data = {}
    for city, coords in CAPITALS.items():
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lng']}&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto"
            res = requests.get(url).json()
            
            # Current
            curr_temp = round(res['current']['temperature_2m'])
            curr_code = res['current']['weather_code']
            
            # Tomorrow
            tmrw_max = round(res['daily']['temperature_2m_max'][1])
            tmrw_code = res['daily']['weather_code'][1]
            
            # Time
            tz = pytz.timezone(coords['tz'])
            local_time = datetime.datetime.now(tz).strftime("%I:%M %p")
            
            weather_data[city] = {
                "time": local_time,
                "curr_temp": curr_temp,
                "curr_icon": get_weather_icon(curr_code),
                "tmrw_temp": tmrw_max,
                "tmrw_icon": get_weather_icon(tmrw_code)
            }
        except:
            weather_data[city] = None
    return weather_data

# ==============================================================================
# 3. SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("<div style='text-align:center; padding:15px 0;'><h1 style='margin:0; font-size:40px;'>🛡️</h1><h3 style='margin:0; color:white; letter-spacing:2px;'>XYSTON</h3><p style='color:#8b949e; font-size:10px; letter-spacing:1px;'>CASELOAD MASTER v6.0</p></div>", unsafe_allow_html=True)
    
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
                    # No rerun loop
                except: st.error("Error loading JSON")

        with tab_csv:
            csv_template = generate_csv_template()
            st.download_button("📄 Get CSV Template", csv_template, "client_template.csv", "text/csv", use_container_width=True)
            
            with st.form("csv_upload_form", clear_on_submit=True):
                uploaded_csv = st.file_uploader("Import CSV", type=['csv'], label_visibility="collapsed")
                submitted = st.form_submit_button("Import Data")
                if submitted and uploaded_csv:
                    new_data = process_csv_upload(uploaded_csv)
                    if new_data:
                        st.session_state.caseload.extend(new_data)
                        st.success(f"Imported {len(new_data)} clients!")
                        st.rerun()
                    else: st.error("Format Error.")

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

    # COMMAND CENTRE (SIDEBAR ONLY)
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
# 3. MAIN DASHBOARD (ZERO STATE)
# ==============================================================================

if not st.session_state.caseload:
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px 20px 20px;">
        <h1 style="font-size: 50px; margin-bottom: 10px;">🛡️</h1>
        <h1 style="margin-bottom: 10px;">Xyston Caseload Master</h1>
        <p style="color: #8b949e; font-size: 18px; max-width: 700px; margin: 0 auto;">
            The operating system for independent Support Coordinators.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- WEATHER DASHBOARD ---
    st.markdown("### 🇦🇺 National Dashboard")
    weather = fetch_weather()
    
    # Create 2 Rows of 4 Capitals
    row1 = st.columns(4)
    cities_1 = ["Canberra", "Sydney", "Melbourne", "Brisbane"]
    for i, city in enumerate(cities_1):
        w = weather.get(city)
        if w:
            row1[i].markdown(f"""
            <div class="weather-card">
                <div class="city-name">{city}</div>
                <div class="city-time">{w['time']}</div>
                <div class="weather-row">
                    <div>TODAY<br><span class="weather-temp">{w['curr_icon']} {w['curr_temp']}°</span></div>
                    <div style="border-left:1px solid #30363d;"></div>
                    <div>TOMORROW<br><span class="weather-temp">{w['tmrw_icon']} {w['tmrw_temp']}°</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    row2 = st.columns(4)
    cities_2 = ["Perth", "Adelaide", "Hobart", "Darwin"]
    for i, city in enumerate(cities_2):
        w = weather.get(city)
        if w:
            row2[i].markdown(f"""
            <div class="weather-card">
                <div class="city-name">{city}</div>
                <div class="city-time">{w['time']}</div>
                <div class="weather-row">
                    <div>TODAY<br><span class="weather-temp">{w['curr_icon']} {w['curr_temp']}°</span></div>
                    <div style="border-left:1px solid #30363d;"></div>
                    <div>TOMORROW<br><span class="weather-temp">{w['tmrw_icon']} {w['tmrw_temp']}°</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # DONATION & FOOTER
    st.markdown("---")
    c_empty1, c_donate, c_empty2 = st.columns([1, 1, 1]) 
    with c_donate:
        st.markdown("""
        <div style="display: flex; justify-content: center; margin: 20px 0;">
            <a href="https://www.buymeacoffee.com/h0m1ez187" target="_blank">
                <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 50px !important; width: 180px !important;" >
            </a>
        </div>
        """, unsafe_allow_html=True)

    # GUIDES
    c_how, c_safe = st.columns(2)
    with c_how:
        st.markdown('<div class="guide-box"><div class="guide-title">🚀 Get Started</div><div class="guide-text">1. <b>Load Data:</b> Upload a JSON backup or CSV.<br>2. <b>Add Manual:</b> Use "Add Single Client".<br>3. <b>Analyse:</b> Dashboard activates automatically.</div></div>', unsafe_allow_html=True)
    with c_safe:
        st.markdown('<div class="guide-box" style="border-left-color: #58a6ff;"><div class="guide-title">🔒 Privacy First</div><div class="guide-text">Data is stored locally on your device. No participant data touches our servers. You own your JSON database file.</div></div>', unsafe_allow_html=True)
    
    st.stop()

# ==============================================================================
# ACTIVE DASHBOARD (DATA LOADED)
# ==============================================================================

all_metrics = [m for m in [calculate_client_metrics(c) for c in st.session_state.caseload] if m is not None]
df = pd.DataFrame(all_metrics)

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

        # Chart
        st.markdown("### Financial Trajectory")
        weeks_show = max(int(client_metrics['weeks_remaining']), 1) + 5
        dates = [datetime.date.today() + timedelta(weeks=w) for w in range(weeks_show)]
        y_act = [max(0, client_metrics['balance'] - (w * client_metrics['weekly_cost'])) for w in range(len(dates))]
        rem = client_metrics['weeks_remaining']
        ideal_wk = client_metrics['balance'] / rem if rem > 0 else 0
        y_opt = [max(0, client_metrics['balance'] - (w * ideal_wk)) for w in range(len(dates))]
        chart_df = pd.DataFrame({"Date": dates*2, "Balance": y_act + y_opt, "Type": ["Actual Trajectory"]*len(dates) + ["Ideal Path"]*len(dates)})
        fig = px.line(chart_df, x="Date", y="Balance", color="Type", color_discrete_map={"Actual Trajectory": client_metrics['color'], "Ideal Path": "#6e7681"})
        fig.update_traces(patch={"line": {"dash": "dot"}}, selector={"legendgroup": "Ideal Path"})
        try: fig.add_vline(x=client_metrics['plan_end'], line_dash="dash", line_color="#c9d1d9")
        except: pass
        fig.update_layout(height=350, hovermode="x unified", margin=dict(t=30,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        # AI
        st.markdown("---")
        c_ai, c_note = st.columns(2)
        with c_ai:
            st.markdown("### 🤖 Strategy")
            if st.button("Generate Note ✨", use_container_width=True):
                if api_key:
                    with st.spinner("Consulting AI..."):
                        try:
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel('gemini-2.0-flash')
                            prompt = f"Write a strategic NDIS file note for {selected_name}. Status: {client_metrics['status']}. Balance: ${client_metrics['balance']}. Burn: ${client_metrics['weekly_cost']}/wk. Outcome: ${client_metrics['surplus']}. Tone: Professional Australian NDIS."
                            response = model.generate_content(prompt)
                            original_rec['notes'] = response.text
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                else: st.error("No API Key.")
        
        with c_note:
            st.markdown("### 📝 Notes")
            new_note = st.text_area("Editor", value=original_rec.get('notes', ''), height=150, label_visibility="collapsed")
            if new_note != original_rec.get('notes', ''): original_rec['notes'] = new_note
