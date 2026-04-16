import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from groq import Groq
from datetime import datetime
import smtplib, hashlib, json, re, gspread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.service_account import Credentials

# ══════════════════════════════════════════════════════════════════════════════
# SAYFA AYARI
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="ARD Finans",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg:        #060a12;
  --surface:   #0b1220;
  --card:      #0f1929;
  --card2:     #131f30;
  --border:    #1c2d47;
  --border2:   #243552;
  --accent:    #c0392b;
  --accent2:   #e74c3c;
  --accentg:   rgba(192,57,43,0.12);
  --text:      #e2e8f4;
  --text2:     #a8b8d0;
  --muted:     #4a6080;
  --green:     #10b981;
  --red:       #ef4444;
  --yellow:    #f59e0b;
  --blue:      #3b82f6;
  --mono:      'JetBrains Mono', monospace;
  --sans:      'Inter', sans-serif;
  --radius:    10px;
  --radius-lg: 14px;
  --shadow:    0 4px 24px rgba(0,0,0,0.45);
  --shadow-sm: 0 2px 10px rgba(0,0,0,0.3);
}

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
  font-family: var(--sans); background: var(--bg);
  color: var(--text); -webkit-font-smoothing: antialiased;
}
.stApp { background: var(--bg); }
.block-container { padding-top: 1.5rem !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

/* ─── SIDEBAR ─── */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* ─── METRICS ─── */
[data-testid="stMetric"] {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 18px 20px;
  transition: border-color 0.2s, transform 0.15s;
  position: relative; overflow: hidden;
}
[data-testid="stMetric"]:hover { border-color: var(--border2); transform: translateY(-1px); }
[data-testid="stMetric"]::after {
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  background: linear-gradient(90deg,var(--accent),transparent); opacity:0.6;
}
[data-testid="stMetricLabel"] {
  color: var(--muted) !important; font-size: 10px !important;
  text-transform: uppercase; letter-spacing: 1.3px; font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
  color: var(--text) !important; font-family: var(--mono) !important;
  font-size: 20px !important; font-weight: 600 !important;
}
[data-testid="stMetricDelta"] { font-family: var(--mono) !important; font-size: 11px !important; }

/* ─── TABS ─── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface); border-radius: var(--radius);
  padding: 4px; gap: 2px; border: 1px solid var(--border); margin-bottom: 6px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent; color: var(--muted);
  border-radius: 8px; font-size: 13px; font-weight: 500; padding: 8px 18px;
  transition: color 0.2s;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text2); }
.stTabs [aria-selected="true"] {
  background: var(--card) !important; color: var(--text) !important;
  border: 1px solid var(--border2) !important; font-weight: 600 !important;
  box-shadow: var(--shadow-sm) !important;
}

/* ─── BUTTONS ─── */
.stButton > button {
  background: linear-gradient(135deg,var(--accent),#a93226);
  color:#fff; border:none; border-radius:var(--radius);
  font-family:var(--sans); font-weight:600; font-size:13px;
  padding:10px 22px; transition:all 0.2s; letter-spacing:0.2px;
  box-shadow: 0 2px 12px rgba(192,57,43,0.25);
}
.stButton > button:hover {
  background: linear-gradient(135deg,var(--accent2),var(--accent));
  transform:translateY(-1px); box-shadow:0 6px 20px rgba(192,57,43,0.4);
}
.stButton > button:active { transform:translateY(0); }
.stButton > button[kind="secondary"] {
  background:var(--card); color:var(--text2);
  border:1px solid var(--border); box-shadow:none;
}
.stButton > button[kind="secondary"]:hover {
  background:var(--card2); color:var(--text);
  border-color:var(--border2); transform:none; box-shadow:none;
}

/* ─── INPUTS ─── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
  background:var(--surface) !important; border:1px solid var(--border) !important;
  border-radius:var(--radius) !important; color:var(--text) !important;
  font-family:var(--sans) !important; font-size:13px !important;
  padding:9px 12px !important; transition:border-color 0.2s,box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color:var(--accent) !important;
  box-shadow:0 0 0 3px rgba(192,57,43,0.12) !important; outline:none !important;
}
.stTextInput label,.stNumberInput label,.stSelectbox label,
.stMultiSelect label,.stTextArea label {
  color:var(--muted) !important; font-size:10px !important;
  text-transform:uppercase; letter-spacing:1.2px; font-weight:600 !important;
}
.stSelectbox > div > div,.stMultiSelect > div > div {
  background:var(--surface) !important; border:1px solid var(--border) !important;
  border-radius:var(--radius) !important; color:var(--text) !important;
}
.stSelectbox > div > div:focus-within,.stMultiSelect > div > div:focus-within {
  border-color:var(--accent) !important;
}

/* ─── MISC ─── */
hr { border:none; border-top:1px solid var(--border); margin:14px 0; }
.stAlert { background:var(--card) !important; border:1px solid var(--border) !important; border-radius:var(--radius) !important; }
.streamlit-expanderHeader {
  background:var(--card) !important; border:1px solid var(--border) !important;
  border-radius:var(--radius) !important; color:var(--text2) !important;
  font-size:13px !important; font-weight:500 !important;
}
.streamlit-expanderHeader:hover { border-color:var(--border2) !important; }
.stDataFrame { border:1px solid var(--border) !important; border-radius:var(--radius); overflow:hidden; }
[data-testid="stToast"] { background:var(--card2) !important; border:1px solid var(--border2) !important; border-radius:var(--radius) !important; }

/* ─── BADGES ─── */
.badge-buy    { background:rgba(16,185,129,0.12); color:#34d399; border:1px solid rgba(16,185,129,0.3); border-radius:6px; padding:2px 10px; font-size:11px; font-family:var(--mono); font-weight:700; white-space:nowrap; }
.badge-sell   { background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.3); border-radius:6px; padding:2px 10px; font-size:11px; font-family:var(--mono); font-weight:700; white-space:nowrap; }
.badge-neutral{ background:rgba(100,116,139,0.12); color:#94a3b8; border:1px solid rgba(100,116,139,0.25); border-radius:6px; padding:2px 10px; font-size:11px; font-family:var(--mono); font-weight:700; white-space:nowrap; }

/* ─── SIGNAL CARDS ─── */
.sig-card {
  background:var(--card); border:1px solid var(--border);
  border-radius:var(--radius); padding:14px 10px; text-align:center;
  transition:all 0.2s; height:100%;
}
.sig-card:hover { border-color:var(--border2); background:var(--card2); transform:translateY(-1px); }
.sig-label { color:var(--muted); font-size:9px; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:6px; font-weight:600; }
.sig-desc  { color:var(--muted); font-size:9px; margin-top:6px; line-height:1.4; }

/* ─── AI BOX ─── */
.ai-box {
  background:var(--card); border:1px solid var(--border);
  border-left:3px solid var(--accent); border-radius:var(--radius-lg);
  padding:22px 26px; font-size:13.5px; line-height:2;
  color:var(--text2); margin-top:14px; white-space:pre-wrap;
  box-shadow:var(--shadow-sm);
}

/* ─── ONBOARD / EMPTY STATE ─── */
.onboard-card {
  background:var(--card); border:1px solid var(--border);
  border-radius:var(--radius-lg); padding:32px 36px; margin-bottom:14px;
  text-align:center;
}
.onboard-card h4 { margin:0 0 10px; color:var(--text); font-size:16px; font-weight:700; }
.onboard-card p  { margin:0; color:var(--text2); font-size:13px; line-height:1.8; }
.onboard-card .icon { font-size:40px; margin-bottom:16px; display:block; }

/* ─── PRICE HEADER ─── */
.price-header {
  background:linear-gradient(135deg,var(--card) 0%,var(--card2) 100%);
  border:1px solid var(--border); border-radius:var(--radius-lg);
  padding:20px 24px; margin-bottom:18px;
  display:flex; flex-wrap:wrap; align-items:center; gap:20px;
  box-shadow:var(--shadow-sm);
}

/* ─── STATUS BADGES ─── */
.groq-badge {
  display:inline-flex; align-items:center; gap:7px;
  background:var(--card); border:1px solid var(--border);
  border-radius:20px; padding:4px 14px;
  font-size:11px; color:var(--text2); font-weight:500; margin-bottom:16px;
}
.groq-dot {
  width:7px; height:7px; border-radius:50%; background:var(--green);
  box-shadow:0 0 6px var(--green); animation:pulse-dot 2s infinite;
}
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.45} }

/* ─── FOOTER ─── */
.footer-bar {
  margin-top:48px; padding:18px 24px;
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--radius-lg); text-align:center;
  color:var(--muted); font-size:11px; line-height:1.8;
}

/* ─── SIDEBAR COMPONENTS ─── */
.sb-logo { padding:22px 18px 16px; border-bottom:1px solid var(--border); margin-bottom:2px; }
.sb-logo-text { font-size:20px; font-weight:800; letter-spacing:-0.8px; line-height:1; }
.sb-user {
  padding:12px 18px; display:flex; align-items:center; gap:11px;
  border-bottom:1px solid var(--border); margin-bottom:6px;
}
.sb-avatar {
  width:34px; height:34px; border-radius:50%;
  background:linear-gradient(135deg,var(--accent),#922b21);
  color:#fff; display:flex; align-items:center; justify-content:center;
  font-size:14px; font-weight:700; flex-shrink:0;
  box-shadow:0 2px 8px rgba(192,57,43,0.35);
}
.sb-section-title {
  color:var(--muted); font-size:9px; text-transform:uppercase;
  letter-spacing:2px; padding:10px 18px 5px; font-weight:700;
}

/* ─── PREDICTION CARDS ─── */
.pred-card {
  background:var(--card); border:1px solid var(--border);
  border-radius:var(--radius-lg); padding:18px 16px;
  transition:all 0.2s; height:100%;
}
.pred-card:hover { border-color:var(--border2); background:var(--card2); transform:translateY(-2px); box-shadow:var(--shadow); }
.pred-model { font-size:12px; font-weight:700; margin-bottom:12px; color:var(--text); }
.pred-price { font-family:var(--mono); font-size:17px; font-weight:700; }
.pred-label { font-size:9px; text-transform:uppercase; letter-spacing:1.2px; color:var(--muted); margin-bottom:3px; font-weight:600; }
.pred-signal-AL   { background:rgba(16,185,129,0.12); color:#34d399; border:1px solid rgba(16,185,129,0.3); border-radius:6px; padding:3px 12px; font-size:11px; font-weight:700; display:inline-block; }
.pred-signal-SAT  { background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.3); border-radius:6px; padding:3px 12px; font-size:11px; font-weight:700; display:inline-block; }
.pred-signal-NÖTR { background:rgba(100,116,139,0.12); color:#94a3b8; border:1px solid rgba(100,116,139,0.25); border-radius:6px; padding:3px 12px; font-size:11px; font-weight:700; display:inline-block; }

/* ─── CONSENSUS BOX ─── */
.consensus-box {
  background:linear-gradient(135deg,var(--card) 0%,#111e32 100%);
  border:1px solid var(--border2); border-radius:var(--radius-lg);
  padding:24px 28px; margin-bottom:22px; box-shadow:var(--shadow-sm);
  position:relative; overflow:hidden;
}
.consensus-box::before {
  content:''; position:absolute; top:0; left:0; right:0; height:3px;
  background:linear-gradient(90deg,var(--accent),var(--blue),var(--green));
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VERİTABANI (Google Sheets)
# ══════════════════════════════════════════════════════════════════════════════

def _get_sheet():
    try:
        raw = st.secrets["gcp_service_account"]
        if isinstance(raw, str):
            creds_dict = json.loads(raw)
        else:
            creds_dict = {k: v for k, v in raw.items()}
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open("ardfinans_users").sheet1
    except Exception as e:
        st.error(f"🔴 Veritabanı bağlantı hatası: {e}")
        return None

def _load_users():
    sheet = _get_sheet()
    if not sheet: return {}
    try:
        return {r["username"]: r for r in sheet.get_all_records() if r.get("username")}
    except: return {}

def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def register_user(username, email, password):
    u = username.strip().lower()
    if len(u) < 3: return False, "Kullanıcı adı en az 3 karakter olmalı."
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email): return False, "Geçerli bir e-posta girin."
    if len(password) < 6: return False, "Şifre en az 6 karakter olmalı."
    db = _load_users()
    if u in db: return False, "Bu kullanıcı adı zaten alınmış."
    if any(v.get("email","").lower()==email.lower() for v in db.values()): return False, "Bu e-posta zaten kayıtlı."
    sheet = _get_sheet()
    if not sheet: return False, "Veritabanına bağlanılamadı."
    sheet.append_row([u, email, _hash(password), datetime.now().strftime("%Y-%m-%d %H:%M")])
    return True, "Hesap oluşturuldu!"

def verify_login(username, password):
    u  = username.strip().lower()
    db = _load_users()
    if u not in db: return False, "Kullanıcı bulunamadı."
    if db[u]["password"] != _hash(password): return False, "Şifre hatalı."
    return True, db[u].get("email","")

# ══════════════════════════════════════════════════════════════════════════════
# PORTFÖY VERİTABANI (Google Sheets — 2. sayfa)
# ══════════════════════════════════════════════════════════════════════════════

def _get_portfolio_sheet():
    try:
        raw = st.secrets["gcp_service_account"]
        if isinstance(raw, str):
            creds_dict = json.loads(raw)
        else:
            creds_dict = {k: v for k, v in raw.items()}
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        wb     = client.open("ardfinans_users")
        try:
            sheet = wb.worksheet("portfolios")
        except:
            sheet = wb.add_worksheet("portfolios", rows=1000, cols=6)
            sheet.append_row(["username","ticker","qty","cost","added","asset_type"])
        return sheet
    except Exception as e:
        return None

def _get_history_sheet():
    try:
        raw = st.secrets["gcp_service_account"]
        if isinstance(raw, str):
            creds_dict = json.loads(raw)
        else:
            creds_dict = {k: v for k, v in raw.items()}
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        wb     = client.open("ardfinans_users")
        try:
            sheet = wb.worksheet("pf_history")
        except:
            sheet = wb.add_worksheet("pf_history", rows=5000, cols=4)
            sheet.append_row(["username","date","total_value","total_cost"])
        return sheet
    except:
        return None

ASSET_TYPES = ["📈 Hisse", "🪙 Kripto", "📊 ETF/Fon", "💱 Döviz"]

def load_portfolio(username):
    sheet = _get_portfolio_sheet()
    if not sheet: return []
    try:
        records = sheet.get_all_records()
        return [{"t": r["ticker"], "q": float(r["qty"]),
                 "c": float(r["cost"]),
                 "type": r.get("asset_type", "📈 Hisse")} for r in records
                if r.get("username") == username and r.get("ticker")]
    except: return []

def save_portfolio_item(username, ticker, qty, cost, asset_type="📈 Hisse"):
    sheet = _get_portfolio_sheet()
    if not sheet: return False
    try:
        sheet.append_row([username, ticker, qty, cost,
                          datetime.now().strftime("%Y-%m-%d %H:%M"), asset_type])
        return True
    except: return False

def delete_portfolio_item(username, ticker):
    sheet = _get_portfolio_sheet()
    if not sheet: return False
    try:
        records = sheet.get_all_records()
        for i, r in enumerate(records):
            if r.get("username") == username and r.get("ticker") == ticker:
                sheet.delete_rows(i + 2)
                return True
        return False
    except: return False

def save_portfolio_snapshot(username, total_value, total_cost):
    sheet = _get_history_sheet()
    if not sheet: return
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        records = sheet.get_all_records()
        for r in records:
            if r.get("username") == username and r.get("date") == today:
                return
        sheet.append_row([username, today, round(total_value, 2), round(total_cost, 2)])
    except: pass

def load_portfolio_history(username):
    sheet = _get_history_sheet()
    if not sheet: return pd.DataFrame()
    try:
        records = sheet.get_all_records()
        data = [r for r in records if r.get("username") == username]
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)[["date","total_value","total_cost"]]
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").drop_duplicates(subset="date")
        df["pl"] = df["total_value"] - df["total_cost"]
        df["pl_pct"] = (df["pl"] / df["total_cost"] * 100).round(2)
        return df
    except: return pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
DEFAULTS = dict(portfolio=[], alerts=[], groq_key="", logged_in=False,
                username="", auth_page="login", auth_msg="", auth_ok=False,
                splash_done=False, pf_loaded=False, ai_predictions={})
for k, v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

if not st.session_state.groq_key:
    try: st.session_state.groq_key = st.secrets["GROQ_API_KEY"]
    except: pass

# ══════════════════════════════════════════════════════════════════════════════
# SPLASH SCREEN
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in and not st.session_state.splash_done:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"],header[data-testid="stHeader"],#MainMenu,footer{display:none!important}
    .block-container{padding:0!important;max-width:100%!important}
    .splash{position:fixed;inset:0;background:#070b14;display:flex;flex-direction:column;
      align-items:center;justify-content:center;z-index:9999;
      animation:sFade 0.5s ease 2.9s forwards}
    @keyframes sFade{to{opacity:0;pointer-events:none}}
    .splash-bg{position:absolute;inset:0;background-image:
      linear-gradient(rgba(224,32,32,.06) 1px,transparent 1px),
      linear-gradient(90deg,rgba(224,32,32,.06) 1px,transparent 1px);
      background-size:48px 48px}
    .splash-logo{font-size:clamp(52px,10vw,92px);font-weight:800;letter-spacing:-2px;
      display:flex;align-items:center;gap:10px;
      opacity:0;animation:sLogo 0.7s cubic-bezier(.16,1,.3,1) .3s forwards}
    @keyframes sLogo{from{opacity:0;transform:scale(.88) translateY(12px)}to{opacity:1;transform:none}}
    .s-ard{color:#e02020;text-shadow:0 0 40px rgba(224,32,32,.5)}
    .s-fin{color:#e8edf5}
    .s-i{display:inline-flex;flex-direction:column;align-items:center;gap:3px;position:relative;top:2px}
    .s-dot{width:clamp(7px,1.1vw,12px);height:clamp(7px,1.1vw,12px);background:#e8edf5;border-radius:50%}
    .splash-bar-wrap{margin-top:52px;width:clamp(140px,28vw,260px);height:2px;
      background:rgba(255,255,255,.06);border-radius:2px;overflow:hidden;
      opacity:0;animation:sShow .3s ease 1.1s forwards}
    @keyframes sShow{to{opacity:1}}
    .splash-bar{height:100%;width:0%;background:linear-gradient(90deg,#e02020,#ff5555);
      border-radius:2px;animation:sBar 1.5s cubic-bezier(.4,0,.2,1) 1.2s forwards;
      box-shadow:0 0 10px rgba(224,32,32,.5)}
    @keyframes sBar{to{width:100%}}
    .splash-dots{display:flex;gap:7px;margin-top:14px;opacity:0;animation:sShow .3s ease 1.3s forwards}
    .splash-dots span{width:5px;height:5px;border-radius:50%;background:#e02020;
      animation:sDot 1s ease infinite}
    .splash-dots span:nth-child(2){animation-delay:.2s}
    .splash-dots span:nth-child(3){animation-delay:.4s}
    @keyframes sDot{0%,100%{opacity:.2;transform:scale(1)}50%{opacity:1;transform:scale(1.4)}}
    .splash-chart{position:absolute;bottom:60px;width:75%;max-width:480px;
      opacity:0;animation:sChart .9s ease .5s forwards}
    @keyframes sChart{from{opacity:0;transform:translateY(16px)}to{opacity:.15;transform:none}}
    </style>
    <div class="splash">
      <div class="splash-bg"></div>
      <svg class="splash-chart" viewBox="0 0 480 70" preserveAspectRatio="none">
        <defs><linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#e02020" stop-opacity=".4"/>
          <stop offset="100%" stop-color="#e02020" stop-opacity="0"/></linearGradient></defs>
        <polyline points="0,65 40,50 80,56 120,28 170,42 210,16 250,32 290,10 330,24 380,6 430,18 480,8"
          fill="none" stroke="#e02020" stroke-width="2.5" stroke-linejoin="round"/>
        <polyline points="0,65 40,50 80,56 120,28 170,42 210,16 250,32 290,10 330,24 380,6 430,18 480,8 480,70 0,70"
          fill="url(#cg)" stroke="none"/>
      </svg>
      <div class="splash-logo">
        <span class="s-ard">ARD</span>
        <span class="s-fin">F<span class="s-i"><span class="s-dot"></span>İ</span>NANS</span>
      </div>
      <div class="splash-bar-wrap"><div class="splash-bar"></div></div>
      <div class="splash-dots"><span></span><span></span><span></span></div>
    </div>
    """, unsafe_allow_html=True)
    import time; time.sleep(3.1)
    st.session_state.splash_done = True
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# GİRİŞ / KAYIT EKRANI
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"]{display:none!important}
    .block-container{max-width:440px!important;padding-top:48px!important}
    .stTextInput label{color:var(--muted)!important;font-size:11px!important;
      text-transform:uppercase;letter-spacing:1px}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:28px">
      <div style="font-size:36px;font-weight:800;letter-spacing:-1px;margin-bottom:6px">
        <span style="color:#e02020">ARD</span>
        <span style="color:#e8edf5"> F<span style="display:inline-flex;flex-direction:column;
          align-items:center;gap:1px;position:relative;top:1px;vertical-align:middle">
          <span style="width:5px;height:5px;background:#e8edf5;border-radius:50%;display:block"></span>İ
        </span>NANS</span>
      </div>
      <div style="color:#4a5a78;font-size:11px;letter-spacing:2px;text-transform:uppercase">
        AI Destekli Borsa Analiz Platformu
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Giriş Yap", use_container_width=True,
                     type="primary" if st.session_state.auth_page=="login" else "secondary"):
            st.session_state.auth_page="login"; st.session_state.auth_msg=""; st.rerun()
    with c2:
        if st.button("Hesap Oluştur", use_container_width=True,
                     type="primary" if st.session_state.auth_page=="register" else "secondary"):
            st.session_state.auth_page="register"; st.session_state.auth_msg=""; st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.session_state.auth_page == "login":
        u = st.text_input("Kullanıcı Adı", placeholder="kullanıcı adınız", key="l_u")
        p = st.text_input("Şifre", type="password", placeholder="••••••••", key="l_p")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Giriş Yap →", use_container_width=True, type="primary", key="do_login"):
            ok, msg = verify_login(u, p)
            if ok:
                st.session_state.logged_in = True
                st.session_state.username  = u.strip().lower()
                st.session_state.auth_msg  = ""
                st.rerun()
            else:
                st.session_state.auth_msg = msg; st.rerun()
        if st.session_state.auth_msg:
            st.error(f"❌ {st.session_state.auth_msg}")
    else:
        u  = st.text_input("Kullanıcı Adı", placeholder="en az 3 karakter", key="r_u")
        em = st.text_input("E-posta", placeholder="ornek@mail.com", key="r_e")
        p1 = st.text_input("Şifre", type="password", placeholder="en az 6 karakter", key="r_p1")
        p2 = st.text_input("Şifre (tekrar)", type="password", placeholder="••••••••", key="r_p2")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Hesap Oluştur →", use_container_width=True, type="primary", key="do_reg"):
            if p1 != p2:
                st.session_state.auth_msg="Şifreler eşleşmiyor."; st.session_state.auth_ok=False; st.rerun()
            else:
                ok, msg = register_user(u, em, p1)
                st.session_state.auth_msg=msg; st.session_state.auth_ok=ok; st.rerun()
        if st.session_state.auth_msg:
            if st.session_state.auth_ok:
                st.success(f"✅ {st.session_state.auth_msg} Şimdi giriş yapabilirsiniz.")
            else:
                st.error(f"❌ {st.session_state.auth_msg}")

    st.markdown("""
    <div style="text-align:center;color:#2a3a52;font-size:11px;margin-top:28px">
      🔒 Güvenli bağlantı · Verileriniz şifreli saklanır
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Giriş yapıldıktan sonra portföyü Sheets'ten yükle (bir kez)
if st.session_state.logged_in and not st.session_state.pf_loaded:
    with st.spinner("Portföy yükleniyor..."):
        st.session_state.portfolio = load_portfolio(st.session_state.username)
        st.session_state.pf_loaded = True

# ══════════════════════════════════════════════════════════════════════════════
# VERİ FONKSİYONLARI
# ══════════════════════════════════════════════════════════════════════════════
BIST = {"THYAO","GARAN","AKBNK","YKBNK","ISCTR","HALKB","VAKBN","SISE","EREGL","KRDMD",
        "BIMAS","MGROS","ARCLK","TOASO","FROTO","DOAS","OTKAR","KCHOL","SAHOL","PETKM",
        "TUPRS","AYGAZ","AKSA","VESBE","VESTL","TCELL","TTKOM","ASELS","KOZAL","KOZAA",
        "ENKAI","EKGYO","ISGYO","TSKB","ALARK","ALGYO","SODA","TRKCM","NETAS","LOGO",
        "INDES","DOHOL","TKFEN","TATGD","ULKER","PGSUS","TAVHL","CLEBI","MAVI","BERA",
        "BRISA","GUBRF","HEKTS","KARSAN","SASA","SOKM","QNBFL","QNBFB","SARKY","SKTAS"}

def resolve(raw):
    t = raw.upper().strip()
    if any(c in t for c in [".","-","="]): return t
    return t+".IS" if t in BIST else t

def _dl(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True, actions=False)
        if df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        cols = [c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]
        return df[cols].dropna() if len(cols)==5 else pd.DataFrame()
    except: return pd.DataFrame()

@st.cache_data(ttl=60)
def get_data(ticker, period, interval):
    df = _dl(ticker, period, interval)
    if not df.empty: return df
    if "." not in ticker:
        df2 = _dl(ticker+".IS", period, interval)
        if not df2.empty: return df2
    return pd.DataFrame()

@st.cache_data(ttl=120)
def get_info(ticker):
    try: return yf.Ticker(ticker).info
    except: return {}

# ══════════════════════════════════════════════════════════════════════════════
# İNDİKATÖRLER
# ══════════════════════════════════════════════════════════════════════════════
def calc(df):
    df = df.copy()
    c = df["Close"].squeeze().astype(float)
    h = df["High"].squeeze().astype(float)
    l = df["Low"].squeeze().astype(float)
    v = df["Volume"].squeeze().astype(float)

    g=c.diff().clip(lower=0); ls=(-c.diff()).clip(lower=0)
    df["RSI"] = 100-100/(1+g.ewm(14,adjust=False).mean()/(ls.ewm(14,adjust=False).mean()+1e-9))

    e12=c.ewm(12,adjust=False).mean(); e26=c.ewm(26,adjust=False).mean()
    df["MACD"]=e12-e26; df["MACD_S"]=df["MACD"].ewm(9,adjust=False).mean(); df["MACD_H"]=df["MACD"]-df["MACD_S"]

    s20=c.rolling(20).mean(); d20=c.rolling(20).std()
    df["BB_M"]=s20; df["BB_U"]=s20+2*d20; df["BB_L"]=s20-2*d20

    for n in [9,20,50,100,200]: df[f"EMA{n}"]=c.ewm(n,adjust=False).mean()
    for n in [20,50,200]: df[f"SMA{n}"]=c.rolling(n).mean()

    l14=l.rolling(14).min(); h14=h.rolling(14).max()
    df["StochK"]=100*(c-l14)/(h14-l14+1e-9); df["StochD"]=df["StochK"].rolling(3).mean()

    tr=pd.concat([(h-l),(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    df["ATR"]=tr.rolling(14).mean(); df["ATR%"]=df["ATR"]/(c+1e-9)*100

    obv=[0]
    for i in range(1,len(c)):
        if c.iloc[i]>c.iloc[i-1]: obv.append(obv[-1]+v.iloc[i])
        elif c.iloc[i]<c.iloc[i-1]: obv.append(obv[-1]-v.iloc[i])
        else: obv.append(obv[-1])
    df["OBV"]=obv

    df["WR"]=-100*(h14-c)/(h14-l14+1e-9)
    tp=(h+l+c)/3; st2=tp.rolling(20).mean(); md=tp.rolling(20).apply(lambda x:np.mean(np.abs(x-x.mean())))
    df["CCI"]=(tp-st2)/(0.015*md+1e-9)

    mf=tp*v
    df["MFI"]=100-100/(1+mf.where(tp>tp.shift(),0).rolling(14).sum()/(mf.where(tp<tp.shift(),0).rolling(14).sum()+1e-9))
    df["ROC"]=c.pct_change(10)*100
    df["VWAP"]=(tp*v).cumsum()/(v.cumsum()+1e-9)

    dp=(h-h.shift()).clip(lower=0); dm=(l.shift()-l).clip(lower=0)
    dp=dp.where(dp>dm,0); dm=dm.where(dm>dp,0)
    a14=tr.rolling(14).mean()
    dip=100*dp.rolling(14).mean()/(a14+1e-9); dim=100*dm.rolling(14).mean()/(a14+1e-9)
    dx=100*(dip-dim).abs()/(dip+dim+1e-9)
    df["ADX"]=dx.rolling(14).mean(); df["DI+"]=dip; df["DI-"]=dim

    clv=((c-l)-(h-c))/(h-l+1e-9)
    df["CMF"]=(clv*v).rolling(20).sum()/(v.rolling(20).sum()+1e-9)
    df["VolMA"]=v.rolling(20).mean(); df["VolR"]=v/(df["VolMA"]+1e-9)
    return df

def signals(df):
    row=df.iloc[-1]; S={}
    def s(n,b,sl,db,ds,dn=""):
        if b: S[n]=("AL",db)
        elif sl: S[n]=("SAT",ds)
        else: S[n]=("NÖTR",dn or n)

    rsi=float(row.get("RSI",50))
    s("RSI",rsi<30,rsi>70,f"RSI {rsi:.0f} — Aşırı satım",f"RSI {rsi:.0f} — Aşırı alım",f"RSI {rsi:.0f}")

    m=float(row.get("MACD",0)); ms=float(row.get("MACD_S",0)); mh=float(row.get("MACD_H",0))
    s("MACD",m>ms and mh>0,m<ms and mh<0,"Pozitif kesişim ↑","Negatif kesişim ↓","Nötr bölge")

    c2=float(row["Close"]); bu=float(row.get("BB_U",0)); bl=float(row.get("BB_L",0))
    s("Bollinger",c2<bl,c2>bu,"Alt banda yakın","Üst banda yakın","Bant ortası")

    e20=float(row.get("EMA20",0)); e50=float(row.get("EMA50",0)); e200=float(row.get("EMA200",0))
    s("EMA 20/50",e20>e50,e20<e50,"EMA20 > EMA50","EMA20 < EMA50")
    s("Golden/Death",e50>e200,e50<e200,"Golden Cross ✨","Death Cross ☠️","EMA50 ≈ EMA200")

    k=float(row.get("StochK",50)); d=float(row.get("StochD",50))
    s("Stochastic",k<20 and k>d,k>80 and k<d,f"K={k:.0f} Aşırı satım",f"K={k:.0f} Aşırı alım",f"K={k:.0f}")

    adx=float(row.get("ADX",0)); dp2=float(row.get("DI+",0)); dm2=float(row.get("DI-",0))
    s("ADX",adx>25 and dp2>dm2,adx>25 and dp2<dm2,f"ADX {adx:.0f} — Güçlü ↑",f"ADX {adx:.0f} — Güçlü ↓",f"ADX {adx:.0f} — Zayıf")

    mfi=float(row.get("MFI",50))
    s("MFI",mfi<20,mfi>80,f"MFI {mfi:.0f} — Para girişi",f"MFI {mfi:.0f} — Para çıkışı",f"MFI {mfi:.0f}")

    cmf=float(row.get("CMF",0))
    s("CMF",cmf>0.1,cmf<-0.1,f"CMF {cmf:.2f} — Boğa",f"CMF {cmf:.2f} — Ayı",f"CMF {cmf:.2f}")

    wr=float(row.get("WR",-50))
    s("Williams %R",wr<-80,wr>-20,f"%R {wr:.0f} — Dip",f"%R {wr:.0f} — Tepe",f"%R {wr:.0f}")

    cci=float(row.get("CCI",0))
    s("CCI",cci<-100,cci>100,f"CCI {cci:.0f} — Aşırı satım",f"CCI {cci:.0f} — Aşırı alım",f"CCI {cci:.0f}")

    vwap=float(row.get("VWAP",0))
    s("VWAP",c2>vwap,c2<vwap,"Fiyat VWAP üstünde","Fiyat VWAP altında","VWAP yakını")

    roc=float(row.get("ROC",0))
    s("ROC(10)",roc>2,roc<-2,f"ROC {roc:.1f}% momentum ↑",f"ROC {roc:.1f}% momentum ↓",f"ROC {roc:.1f}%")

    return S

def score(S):
    al=sum(1 for v in S.values() if v[0]=="AL")
    sat=sum(1 for v in S.values() if v[0]=="SAT")
    tot=len(S)
    return al,sat,tot-al-sat,(al-sat)/tot*100

# ══════════════════════════════════════════════════════════════════════════════
# GRAFİK
# ══════════════════════════════════════════════════════════════════════════════
def chart(df, ticker, inds):
    sub=[]; rows=1
    for x,lbl in [("RSI","RSI"),("MACD","MACD"),("Hacim","Hacim"),("ADX","ADX")]:
        if x in inds: rows+=1; sub.append(lbl)

    rh=[0.55]+[0.12]*(rows-1)
    fig=make_subplots(rows=rows,cols=1,shared_xaxes=True,
                      vertical_spacing=0.025,row_heights=rh,
                      subplot_titles=[ticker]+sub)

    fig.add_trace(go.Candlestick(
        x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],
        name="Fiyat",increasing_line_color="#22c55e",increasing_fillcolor="#052e16",
        decreasing_line_color="#ef4444",decreasing_fillcolor="#2d0707",line_width=1
    ),row=1,col=1)

    if "BB" in inds:
        for cn,col,fill in [("BB_U","#6366f1",None),("BB_M","#818cf8",None),("BB_L","#6366f1","tonexty")]:
            if cn in df.columns:
                fig.add_trace(go.Scatter(x=df.index,y=df[cn],name=cn,
                    line=dict(color=col,width=1,dash="dot"),
                    fill=fill,fillcolor="rgba(99,102,241,0.04)",showlegend=False),row=1,col=1)

    ema_c={"EMA20":"#fbbf24","EMA50":"#fb923c","EMA100":"#a78bfa","EMA200":"#f87171","EMA9":"#f472b6"}
    sma_c={"SMA20":"#34d399","SMA50":"#06b6d4","SMA200":"#818cf8"}
    for k,col in ema_c.items():
        if k in inds and k in df.columns:
            fig.add_trace(go.Scatter(x=df.index,y=df[k],name=k,line=dict(color=col,width=1.2)),row=1,col=1)
    for k,col in sma_c.items():
        if k in inds and k in df.columns:
            fig.add_trace(go.Scatter(x=df.index,y=df[k],name=k,line=dict(color=col,width=1,dash="dash")),row=1,col=1)
    if "VWAP" in inds and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["VWAP"],name="VWAP",
            line=dict(color="#38bdf8",width=1.5,dash="dot")),row=1,col=1)

    cr=2
    if "RSI" in inds and "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["RSI"],name="RSI",
            line=dict(color="#38bdf8",width=1.5),fill="tozeroy",fillcolor="rgba(56,189,248,0.04)"),row=cr,col=1)
        for y,c3 in [(70,"#ef4444"),(50,"#1e293b"),(30,"#22c55e")]:
            fig.add_hline(y=y,line_dash="dot",line_color=c3,line_width=1,row=cr,col=1)
        cr+=1
    if "MACD" in inds and "MACD" in df.columns:
        hc=["#22c55e" if v>=0 else "#ef4444" for v in df["MACD_H"]]
        fig.add_trace(go.Bar(x=df.index,y=df["MACD_H"],marker_color=hc,showlegend=False),row=cr,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["MACD"],name="MACD",line=dict(color="#3b82f6",width=1.5)),row=cr,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["MACD_S"],name="Sinyal",line=dict(color="#f59e0b",width=1.5)),row=cr,col=1)
        cr+=1
    if "Hacim" in inds and "Volume" in df.columns:
        vc=["#22c55e" if float(df["Close"].iloc[i])>=float(df["Open"].iloc[i]) else "#ef4444" for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index,y=df["Volume"],marker_color=vc,showlegend=False),row=cr,col=1)
        if "VolMA" in df.columns:
            fig.add_trace(go.Scatter(x=df.index,y=df["VolMA"],line=dict(color="#f59e0b",width=1),showlegend=False),row=cr,col=1)
        cr+=1
    if "ADX" in inds and "ADX" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["ADX"],name="ADX",line=dict(color="#c084fc",width=1.5)),row=cr,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["DI+"],name="DI+",line=dict(color="#22c55e",width=1)),row=cr,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["DI-"],name="DI-",line=dict(color="#ef4444",width=1)),row=cr,col=1)
        fig.add_hline(y=25,line_dash="dot",line_color="#1e293b",line_width=1,row=cr,col=1)

    fig.update_layout(
        paper_bgcolor="#070b14",plot_bgcolor="#0d1420",
        font=dict(color="#4a5a78",family="Sora"),
        xaxis_rangeslider_visible=False,
        legend=dict(bgcolor="#0d1420",bordercolor="#1a2840",borderwidth=1,
                    font=dict(size=10,color="#8899b0"),orientation="h",y=1.02,x=0),
        margin=dict(l=8,r=8,t=36,b=8),height=640,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#111c2e",bordercolor="#1a2840",font_color="#e8edf5")
    )
    fig.update_xaxes(gridcolor="#0f1926",zerolinecolor="#0f1926",showspikes=True,spikecolor="#e02020",spikethickness=1)
    fig.update_yaxes(gridcolor="#0f1926",zerolinecolor="#0f1926")
    for a in fig.layout.annotations: a.font=dict(color="#4a5a78",size=11)
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# GROQ AI
# ══════════════════════════════════════════════════════════════════════════════
def ai_prompt(ticker, df, info, S, al, sat, neu, sc):
    r=df.iloc[-1]
    def fv(k,f=".2f"):
        try: return f"{float(r.get(k,0)):{f}}"
        except: return "—"
    return f"""
HİSSE: {ticker} | {info.get('longName',ticker)}
Sektör: {info.get('sector','—')} | Borsa: {info.get('exchange','—')} | Para: {info.get('currency','—')}
Son Fiyat: {fv('Close')} | Piyasa Değeri: {info.get('marketCap','—')}
F/K: {info.get('trailingPE','—')} | Beta: {info.get('beta','—')}
52H: {info.get('fiftyTwoWeekLow','—')} — {info.get('fiftyTwoWeekHigh','—')}

TEKNİK:
RSI: {fv('RSI')} | MACD: {fv('MACD','.4f')} / {fv('MACD_S','.4f')}
BB: {fv('BB_U')} / {fv('BB_M')} / {fv('BB_L')}
EMA20: {fv('EMA20')} | EMA50: {fv('EMA50')} | EMA200: {fv('EMA200')}
ADX: {fv('ADX')} | DI+: {fv('DI+')} | DI-: {fv('DI-')}
ATR%: {fv('ATR%')} | CMF: {fv('CMF','.3f')} | MFI: {fv('MFI')}
Williams%R: {fv('WR')} | CCI: {fv('CCI')} | ROC: {fv('ROC')}%
VWAP: {fv('VWAP')} | Hacim/Ort: {fv('VolR','.2f')}x

SİNYAL SKORU: {sc:+.0f} (AL:{al} SAT:{sat} NÖTR:{neu})
{chr(10).join(f"• {k}: {v[0]} — {v[1]}" for k,v in S.items())}
"""

def ai_analyze(ticker, df, info, S, al, sat, neu, sc, key):
    client=Groq(api_key=key)
    sys="""Sen uzman bir borsa teknik ve temel analiz uzmanısın. Türkçe, sade ve anlaşılır yaz.

Analiz şu bölümlerden oluşsun:

📊 GENEL GÖRÜNÜM
Fiyatın durumu, trend yönü, önemli seviyeler — kısa özet.

🔍 GÜÇLÜ SİNYALLER
En dikkat çekici 4-5 indikatörü somut yorumla. Sayısal değerler kullan.

🎯 DESTEK & DİRENÇ
Net seviyeler belirt. "yaklaşık X civarında" değil, "X.XX destek" şeklinde yaz.

⚡ KISA VADE (1-5 gün)
İki senaryo: yükseliş senaryosu ve düşüş senaryosu. Koşullar neler?

📅 ORTA VADE (1-4 hafta)
Genel trend değerlendirmesi.

⚠️ DİKKAT EDİLECEKLER
Risk faktörleri ve izlenecek seviyeler.

💡 ÖZET
1-2 cümle net değerlendirme.

⚠️ Yatırım tavsiyesi değildir."""
    for m in ["llama-3.3-70b-versatile","llama-3.1-70b-versatile","llama3-70b-8192","llama3-8b-8192"]:
        try:
            r=client.chat.completions.create(model=m,
                messages=[{"role":"system","content":sys},
                          {"role":"user","content":ai_prompt(ticker,df,info,S,al,sat,neu,sc)}],
                temperature=0.65,max_tokens=1800)
            return r.choices[0].message.content
        except Exception as e:
            if any(x in str(e) for x in ["429","quota","404","model_not_found"]): continue
            raise e
    raise Exception("Groq modelleri şu an kullanılamıyor.")


AI_MODELS = [
    {"id": "llama-3.3-70b-versatile",  "name": "Llama 3.3 70B",   "icon": "🦙", "color": "#f59e0b"},
    {"id": "llama3-8b-8192",            "name": "Llama 3 8B",      "icon": "⚡", "color": "#3b82f6"},
    {"id": "gemma2-9b-it",              "name": "Gemma 2 9B",      "icon": "💎", "color": "#22c55e"},
    {"id": "mixtral-8x7b-32768",        "name": "Mixtral 8x7B",    "icon": "🔀", "color": "#a855f7"},
]

def ai_price_forecast(ticker, df, info, key, model_id):
    """Belirli bir model ile fiyat tahmini üretir."""
    client = Groq(api_key=key)
    lc = float(df["Close"].iloc[-1])
    rsi = float(df["RSI"].iloc[-1]) if "RSI" in df.columns else 50
    macd = float(df["MACD"].iloc[-1]) if "MACD" in df.columns else 0
    adx = float(df["ADX"].iloc[-1]) if "ADX" in df.columns else 0
    ema20 = float(df["EMA20"].iloc[-1]) if "EMA20" in df.columns else lc
    ema50 = float(df["EMA50"].iloc[-1]) if "EMA50" in df.columns else lc
    atr_pct = float(df["ATR%"].iloc[-1]) if "ATR%" in df.columns else 1.0

    prompt = f"""Hisse: {ticker} | Son fiyat: {lc:.4f} {info.get('currency','USD')}
RSI: {rsi:.1f} | MACD: {macd:.4f} | ADX: {adx:.1f}
EMA20: {ema20:.4f} | EMA50: {ema50:.4f} | ATR%: {atr_pct:.2f}%
52H: {info.get('fiftyTwoWeekLow','?')} — {info.get('fiftyTwoWeekHigh','?')}
Sektör: {info.get('sector','?')} | Beta: {info.get('beta','?')}

Sadece aşağıdaki JSON formatını döndür, başka hiçbir şey yazma:
{{"1gun": <sayı>, "1hafta": <sayı>, "1ay": <sayı>, "yorum": "<max 1 cümle türkçe>", "sinyal": "AL|NÖTR|SAT"}}"""

    try:
        r = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "Sen bir fiyat tahmin modelisin. Sadece istenen JSON formatında yanıt ver, markdown veya extra metin kullanma."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, max_tokens=200
        )
        import json as _json
        raw = r.choices[0].message.content.strip()
        # JSON bloğunu bul
        import re as _re
        m = _re.search(r'\{.*\}', raw, _re.DOTALL)
        if m:
            return _json.loads(m.group())
    except:
        pass
    return None

# ══════════════════════════════════════════════════════════════════════════════
# E-POSTA
# ══════════════════════════════════════════════════════════════════════════════
def send_email(to, ticker, atype, target, current):
    try:
        sender=st.secrets["EMAIL_SENDER"]; pwd=st.secrets["EMAIL_PASSWORD"]
    except: return False,"E-posta ayarları eksik."
    html=f"""<div style="font-family:sans-serif;max-width:460px;margin:0 auto;background:#070b14;
      border:1px solid #1a2840;border-radius:14px;overflow:hidden">
      <div style="background:#0d1420;padding:20px;text-align:center">
        <b style="font-size:22px"><span style="color:#e02020">ARD</span>
        <span style="color:#e8edf5"> FİNANS</span></b>
        <div style="color:#4a5a78;font-size:10px;letter-spacing:2px;margin-top:3px">ALARM BİLDİRİMİ</div>
      </div>
      <div style="padding:24px">
        <div style="background:#111c2e;border:1px solid #1a2840;border-radius:10px;padding:18px;margin-bottom:14px">
          <div style="font-size:28px;font-weight:700;color:#e8edf5;font-family:monospace">{ticker}</div>
          <div style="color:#f59e0b;font-size:16px;font-weight:700;margin:6px 0">🔔 Alarm Tetiklendi</div>
          <table style="width:100%;color:#8899b0;font-size:13px;margin-top:8px">
            <tr><td>Koşul</td><td style="color:#e8edf5;font-family:monospace">{atype}</td></tr>
            <tr><td>Hedef</td><td style="color:#f59e0b;font-family:monospace">{target:.2f}</td></tr>
            <tr><td>Güncel</td><td style="color:#22c55e;font-family:monospace;font-weight:700">{current:.2f}</td></tr>
            <tr><td>Zaman</td><td style="color:#e8edf5;font-family:monospace">{datetime.now().strftime('%d.%m.%Y %H:%M')}</td></tr>
          </table>
        </div>
        <div style="color:#2a3a52;font-size:11px;text-align:center">
          Yatırım tavsiyesi değildir · © 2026 ARD Finans
        </div>
      </div></div>"""
    try:
        msg=MIMEMultipart("alternative")
        msg["Subject"]=f"🔔 ARD Finans — {ticker} Alarm"; msg["From"]=sender; msg["To"]=to
        msg.attach(MIMEText(html,"html","utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(sender,pwd); s.sendmail(sender,to,msg.as_string())
        return True,"Gönderildi"
    except Exception as e: return False,str(e)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div class="sb-logo">
      <div class="sb-logo-text">
        <span style="color:#e02020">ARD</span>
        <span style="color:#e8edf5"> FİNANS</span>
      </div>
      <div style="color:#2a3a52;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-top:2px">
        AI Trading Platform
      </div>
    </div>
    <div class="sb-user">
      <div class="sb-avatar">{st.session_state.username[0].upper()}</div>
      <div>
        <div style="font-size:13px;font-weight:600;color:#e8edf5">{st.session_state.username}</div>
        <div style="font-size:10px;color:#2a3a52;display:flex;align-items:center;gap:4px">
          <span style="width:5px;height:5px;border-radius:50%;background:#22c55e;display:inline-block"></span>
          Aktif oturum
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Çıkış Yap", use_container_width=True, type="secondary"):
        st.session_state.logged_in=False; st.session_state.username=""; st.rerun()

    st.markdown('<div class="sb-section-title">📈 Hisse Analizi</div>', unsafe_allow_html=True)
    raw = st.text_input("Sembol", value="AAPL", placeholder="AAPL · THYAO · BTC-USD", label_visibility="visible").upper().strip()
    ticker_input = resolve(raw)
    if ticker_input != raw and raw:
        st.caption(f"🇹🇷 → **{ticker_input}** olarak aranıyor")

    c1,c2=st.columns(2)
    with c1: period=st.selectbox("Dönem",["5d","1mo","3mo","6mo","1y","2y","5y"],index=2)
    with c2: interval=st.selectbox("Aralık",["1d","1wk","1h","30m","15m","5m"],index=0)

    st.markdown('<div class="sb-section-title">📊 İndikatörler</div>', unsafe_allow_html=True)
    overlay=st.multiselect("Grafik üzeri",
        ["BB","EMA20","EMA50","EMA200","EMA9","EMA100","SMA20","SMA50","SMA200","VWAP"],
        default=["BB","EMA20","EMA50","VWAP"])
    panels=st.multiselect("Alt paneller",["RSI","MACD","Hacim","ADX"],default=["RSI","MACD","Hacim"])
    selected=overlay+panels

    st.markdown('<div class="sb-section-title">💼 Portföy</div>', unsafe_allow_html=True)
    pf_raw=st.text_input("Sembol",key="pf",placeholder="AAPL · GARAN · BTC-USD").upper().strip()
    pf_t=resolve(pf_raw)
    if pf_t!=pf_raw and pf_raw: st.caption(f"🇹🇷 → {pf_t}")
    pf_asset_type = st.selectbox("Varlık Türü", ASSET_TYPES, key="pf_type")
    pc1,pc2=st.columns(2)
    with pc1: pf_qty=st.number_input("Adet",min_value=0.0001,value=1.0,step=1.0,format="%.4f")
    with pc2: pf_cost=st.number_input("Maliyet",min_value=0.0,value=0.0,step=0.1,format="%.4f")
    if st.button("Portföye Ekle",use_container_width=True):
        if pf_t and not any(p["t"]==pf_t for p in st.session_state.portfolio):
            ok = save_portfolio_item(st.session_state.username, pf_t, pf_qty, pf_cost, pf_asset_type)
            if ok:
                st.session_state.portfolio.append({"t":pf_t,"q":pf_qty,"c":pf_cost,"type":pf_asset_type})
                st.success(f"✓ {pf_t} eklendi")
            else:
                st.error("Kaydedilemedi, tekrar deneyin.")
        elif pf_t: st.warning("Zaten portföyde!")

    st.markdown('<div class="sb-section-title">🔔 Fiyat Alarmı</div>', unsafe_allow_html=True)
    al_raw=st.text_input("Sembol",key="al",placeholder="TSLA · THYAO").upper()
    al_t=resolve(al_raw)
    ac1,ac2=st.columns(2)
    with ac1: al_price=st.number_input("Hedef fiyat",min_value=0.0,value=100.0,step=1.0)
    with ac2: al_type=st.selectbox("Koşul",["Üstüne çık","Altına in"])
    al_email=st.text_input("Bildirim e-postası",placeholder="ornek@mail.com",key="al_mail")
    if st.button("Alarm Kur",use_container_width=True):
        if al_t:
            st.session_state.alerts.append({"t":al_t,"p":al_price,"tp":al_type,"e":al_email.strip(),"fired":False})
            st.success("✓ Alarm kuruldu")

# ══════════════════════════════════════════════════════════════════════════════
# ANA İÇERİK
# ══════════════════════════════════════════════════════════════════════════════
tab1,tab2,tab3,tab4,tab5 = st.tabs(["📈 Grafik & Sinyaller","🤖 AI Analiz","🔮 AI Tahmin","💼 Portföy","🔔 Alarmlar"])

# ── TAB 1: GRAFİK ──────────────────────────────────────────────────────────────
with tab1:
    if not ticker_input:
        st.info("Sol menüden bir sembol girin.")
    else:
        with st.spinner(f"{ticker_input} yükleniyor..."):
            df=get_data(ticker_input,period,interval)
            info=get_info(ticker_input)

        if df.empty:
            st.markdown("""
            <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:16px">
              <div style="font-size:16px;font-weight:600;margin-bottom:12px">❌ Veri bulunamadı</div>
              <div style="color:var(--muted);font-size:13px;line-height:1.8">
                <b style="color:var(--text)">Desteklenen formatlar:</b><br>
                🇺🇸 ABD hisseleri: <code>AAPL</code>, <code>TSLA</code>, <code>NVDA</code><br>
                🇹🇷 BIST hisseleri: <code>THYAO</code>, <code>GARAN</code>, <code>AKBNK</code> (otomatik .IS eklenir)<br>
                ₿ Kripto: <code>BTC-USD</code>, <code>ETH-USD</code><br>
                💱 Döviz: <code>USDTRY=X</code>, <code>EURUSD=X</code><br>
                📊 Endeks: <code>^XU100</code>, <code>^GSPC</code>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            df=calc(df); S=signals(df); al,sat,neu,sc=score(S)
            lc=float(df["Close"].iloc[-1]); pc=float(df["Close"].iloc[-2]) if len(df)>1 else lc
            chg=(lc-pc)/pc*100; cc="#22c55e" if chg>=0 else "#ef4444"
            arr="▲" if chg>=0 else "▼"; sc_c="#22c55e" if sc>20 else ("#ef4444" if sc<-20 else "#f59e0b")

            st.markdown(f"""
            <div class="price-header">
              <div>
                <div style="font-size:20px;font-weight:700;color:var(--text)">{info.get('longName',ticker_input)}</div>
                <div style="color:var(--muted);font-size:11px;margin-top:2px">
                  {info.get('exchange','')} · {info.get('currency','USD')} · {ticker_input}
                </div>
              </div>
              <div style="margin-left:auto;text-align:right">
                <div style="font-family:var(--mono);font-size:24px;font-weight:700;color:{cc}">{lc:.2f}</div>
                <div style="font-family:var(--mono);font-size:13px;color:{cc}">{arr} {chg:+.2f}%</div>
              </div>
              <div style="background:var(--surface);border:1px solid {sc_c}44;border-radius:8px;padding:8px 14px;text-align:center">
                <div style="color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:1px">Sinyal Skoru</div>
                <div style="font-family:var(--mono);font-size:20px;font-weight:700;color:{sc_c}">{sc:+.0f}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            m1,m2,m3,m4,m5,m6=st.columns(6)
            m1.metric("RSI",f"{float(df['RSI'].iloc[-1]):.1f}")
            m2.metric("ADX",f"{float(df['ADX'].iloc[-1]):.1f}")
            m3.metric("MFI",f"{float(df['MFI'].iloc[-1]):.1f}")
            m4.metric("ATR %",f"{float(df['ATR%'].iloc[-1]):.2f}%")
            m5.metric("52H Yüksek",f"{info.get('fiftyTwoWeekHigh','—')}")
            m6.metric("Beta",f"{info.get('beta','—')}")

            st.plotly_chart(chart(df,ticker_input,selected),use_container_width=True,config={"displayModeBar":True})

            st.markdown("### Sinyal Panosu")
            items=list(S.items())
            for ri in range(0,len(items),6):
                chunk=items[ri:ri+6]
                cols=st.columns(len(chunk))
                for ci,(ind,(sig,desc)) in enumerate(chunk):
                    b="badge-buy" if sig=="AL" else ("badge-sell" if sig=="SAT" else "badge-neutral")
                    cols[ci].markdown(f"""
                    <div class="sig-card">
                      <div class="sig-label">{ind}</div>
                      <span class="{b}">{sig}</span>
                      <div class="sig-desc">{desc}</div>
                    </div>""",unsafe_allow_html=True)

            ap=al/len(S)*100; sp=sat/len(S)*100; np2=(len(S)-al-sat)/len(S)*100
            st.markdown(f"""
            <div style="margin:16px 0 8px;display:flex;align-items:center;gap:16px;flex-wrap:wrap">
              <span style="color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:1px">Sinyal Dağılımı</span>
              <span style="color:#22c55e;font-family:var(--mono);font-size:12px">● AL {al}</span>
              <span style="color:#ef4444;font-family:var(--mono);font-size:12px">● SAT {sat}</span>
              <span style="color:#78716c;font-family:var(--mono);font-size:12px">● NÖTR {neu}</span>
            </div>
            <div style="height:6px;background:var(--border);border-radius:3px;overflow:hidden;display:flex">
              <div style="width:{ap:.0f}%;background:linear-gradient(90deg,#16a34a,#22c55e)"></div>
              <div style="width:{np2:.0f}%;background:#1c1917"></div>
              <div style="width:{sp:.0f}%;background:linear-gradient(90deg,#ef4444,#dc2626)"></div>
            </div>
            """,unsafe_allow_html=True)

            with st.expander("Tüm İndikatör Değerleri"):
                r=df.iloc[-1]
                rows_data=[]
                for k,lbl in [("RSI","RSI(14)"),("MACD","MACD"),("MACD_S","MACD Sinyal"),
                               ("EMA20","EMA 20"),("EMA50","EMA 50"),("EMA200","EMA 200"),
                               ("ADX","ADX"),("DI+","DI+"),("DI-","DI-"),
                               ("BB_U","BB Üst"),("BB_M","BB Orta"),("BB_L","BB Alt"),
                               ("ATR%","ATR %"),("MFI","MFI"),("CMF","CMF"),
                               ("WR","Williams %R"),("CCI","CCI"),("ROC","ROC(10)"),
                               ("VWAP","VWAP"),("OBV","OBV")]:
                    try: rows_data.append({"İndikatör":lbl,"Değer":f"{float(r.get(k,0)):.3f}"})
                    except: pass
                st.dataframe(pd.DataFrame(rows_data),use_container_width=True,hide_index=True)

# ── TAB 2: AI ANALİZ ───────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="groq-badge"><span class="groq-dot"></span>Groq · Llama 3.3 70B</div>', unsafe_allow_html=True)
    st.markdown("### Yapay Zeka Analizi")
    st.markdown("<div style='color:var(--muted);font-size:13px;margin-bottom:16px'>25'den fazla teknik indikatör, sinyal skoru ve piyasa verileri birleştirilerek Türkçe analiz üretilir.</div>", unsafe_allow_html=True)

    ai_raw=st.text_input("Analiz edilecek sembol",value=ticker_input,placeholder="AAPL · THYAO · BTC-USD").upper().strip()
    ai_t=resolve(ai_raw)
    c1,c2=st.columns([2,1])
    with c1: ai_per=st.selectbox("Analiz dönemi",["1mo","3mo","6mo","1y"],index=1,key="aip")
    with c2:
        st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
        go_btn=st.button("Analiz Başlat →",use_container_width=True)

    if go_btn and ai_t:
        with st.spinner("Analiz hazırlanıyor..."):
            try:
                df_ai=get_data(ai_t,ai_per,"1d")
                if df_ai.empty: st.error("Veri alınamadı.")
                else:
                    df_ai=calc(df_ai); S_ai=signals(df_ai)
                    al_ai,sat_ai,neu_ai,sc_ai=score(S_ai)
                    info_ai=get_info(ai_t)
                    res=ai_analyze(ai_t,df_ai,info_ai,S_ai,al_ai,sat_ai,neu_ai,sc_ai,st.session_state.groq_key)
                    st.markdown(f'<div class="ai-box">{res}</div>',unsafe_allow_html=True)
            except Exception as e: st.error(f"Hata: {e}")

    st.markdown("---")
    st.markdown("### Serbest Soru")
    st.markdown("<div style='color:var(--muted);font-size:12px;margin-bottom:8px'>Borsa, teknik analiz veya hisse hakkında dilediğiniz soruyu sorun.</div>", unsafe_allow_html=True)
    q=st.text_area("",placeholder="THYAO'da yükseliş trendi devam eder mi? Altın/dolar paritesi için ne düşünürsün?",height=80,label_visibility="collapsed")
    if st.button("Gönder",use_container_width=False) and q:
        with st.spinner("Yanıt üretiliyor..."):
            try:
                client=Groq(api_key=st.session_state.groq_key)
                r=client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"system","content":"Sen borsa ve teknik analiz uzmanısın. Türkçe, net ve sade yanıt ver. Yatırım tavsiyesi olmadığını belirt."},
                              {"role":"user","content":q}],
                    temperature=0.65,max_tokens=900)
                st.markdown(f'<div class="ai-box">{r.choices[0].message.content}</div>',unsafe_allow_html=True)
            except Exception as e: st.error(f"Hata: {e}")

# ── TAB 3: AI TAHMİN ──────────────────────────────────────────────────────────
with tab3:
    st.markdown("""
    <style>
    .pred-card {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 12px; padding: 18px 20px; margin-bottom: 8px;
      transition: border-color 0.2s;
    }
    .pred-card:hover { border-color: #2d3f5e; }
    .pred-model { font-size:13px; font-weight:700; margin-bottom:10px; }
    .pred-price { font-family:var(--mono); font-size:18px; font-weight:700; }
    .pred-label { font-size:9px; text-transform:uppercase; letter-spacing:1px; color:var(--muted); margin-bottom:3px; }
    .pred-signal-AL    { background:#052e16; color:#4ade80; border:1px solid #16a34a; border-radius:5px; padding:2px 10px; font-size:11px; font-weight:700; }
    .pred-signal-SAT   { background:#2d0707; color:#f87171; border:1px solid #dc2626; border-radius:5px; padding:2px 10px; font-size:11px; font-weight:700; }
    .pred-signal-NÖTR  { background:#1c1917; color:#a8a29e; border:1px solid #44403c; border-radius:5px; padding:2px 10px; font-size:11px; font-weight:700; }
    .consensus-box {
      background: linear-gradient(135deg, #0d1420 0%, #111c2e 100%);
      border: 1px solid var(--border); border-radius: 14px;
      padding: 22px 24px; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### 🔮 Çoklu Yapay Zeka Fiyat Tahmini")
    st.markdown("<div style='color:var(--muted);font-size:13px;margin-bottom:18px'>4 farklı AI modeli bağımsız olarak fiyat tahmini yapar. Tahminler yatırım tavsiyesi değildir.</div>", unsafe_allow_html=True)

    fc1, fc2 = st.columns([3,1])
    with fc1:
        fc_raw = st.text_input("Tahmin edilecek sembol", value=ticker_input, placeholder="AAPL · THYAO · BTC-USD", key="fc_sym").upper().strip()
        fc_t = resolve(fc_raw)
    with fc2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        run_fc = st.button("🔮 Tahmin Başlat", use_container_width=True, key="run_fc")

    if run_fc and fc_t:
        with st.spinner("AI modelleri tahmin üretiyor..."):
            df_fc = get_data(fc_t, "3mo", "1d")
            if df_fc.empty:
                st.error("Veri alınamadı.")
            else:
                df_fc = calc(df_fc)
                info_fc = get_info(fc_t)
                lc_fc = float(df_fc["Close"].iloc[-1])
                predictions = {}
                for mdl in AI_MODELS:
                    result = ai_price_forecast(fc_t, df_fc, info_fc, st.session_state.groq_key, mdl["id"])
                    predictions[mdl["id"]] = result
                st.session_state.ai_predictions = {
                    "ticker": fc_t, "lc": lc_fc, "preds": predictions, "info": info_fc
                }

    if st.session_state.ai_predictions and st.session_state.ai_predictions.get("ticker") == (resolve(fc_raw) if 'fc_raw' in dir() else ""):
        pred_data = st.session_state.ai_predictions
        lc_fc = pred_data["lc"]
        curr = pred_data["info"].get("currency", "USD")

        # Konsensüs hesapla
        all_1d = []; all_1w = []; all_1m = []; signals_list = []
        for mdl in AI_MODELS:
            p = pred_data["preds"].get(mdl["id"])
            if p:
                try:
                    all_1d.append(float(p["1gun"])); all_1w.append(float(p["1hafta"]))
                    all_1m.append(float(p["1ay"])); signals_list.append(p.get("sinyal","NÖTR"))
                except: pass

        if all_1m:
            c1d = sum(all_1d)/len(all_1d); c1w = sum(all_1w)/len(all_1w); c1m = sum(all_1m)/len(all_1m)
            from collections import Counter
            top_sig = Counter(signals_list).most_common(1)[0][0]
            sig_class = f"pred-signal-{top_sig}"
            d1d = (c1d-lc_fc)/lc_fc*100; d1w = (c1w-lc_fc)/lc_fc*100; d1m = (c1m-lc_fc)/lc_fc*100
            cc1 = "#22c55e" if d1m >= 0 else "#ef4444"

            st.markdown(f"""
            <div class="consensus-box">
              <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px">🎯 Konsensüs Tahmini — {pred_data['ticker']}</div>
              <div style="display:flex;gap:32px;flex-wrap:wrap;align-items:center">
                <div>
                  <div class="pred-label">Güncel Fiyat</div>
                  <div style="font-family:var(--mono);font-size:22px;font-weight:700;color:var(--text)">{lc_fc:.4f} {curr}</div>
                </div>
                <div>
                  <div class="pred-label">1 Günlük</div>
                  <div class="pred-price" style="color:{('#22c55e' if d1d>=0 else '#ef4444')}">{c1d:.4f} <span style="font-size:13px">({d1d:+.2f}%)</span></div>
                </div>
                <div>
                  <div class="pred-label">1 Haftalık</div>
                  <div class="pred-price" style="color:{('#22c55e' if d1w>=0 else '#ef4444')}">{c1w:.4f} <span style="font-size:13px">({d1w:+.2f}%)</span></div>
                </div>
                <div>
                  <div class="pred-label">1 Aylık</div>
                  <div class="pred-price" style="color:{cc1}">{c1m:.4f} <span style="font-size:13px">({d1m:+.2f}%)</span></div>
                </div>
                <div style="margin-left:auto">
                  <div class="pred-label">Konsensüs Sinyali</div>
                  <span class="{sig_class}">{top_sig}</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Tahmin grafiği
            import numpy as np
            last_date = df_fc.index[-1]
            future_dates = pd.bdate_range(start=last_date, periods=22)[1:]
            hist_x = list(df_fc.index[-30:])
            hist_y = list(df_fc["Close"].iloc[-30:].astype(float))

            fg = go.Figure()
            fg.add_trace(go.Scatter(
                x=hist_x, y=hist_y, name="Geçmiş",
                line=dict(color="#4a5a78", width=2),
                mode="lines"
            ))
            pal_map = {m["id"]: m for m in AI_MODELS}
            for mdl in AI_MODELS:
                p = pred_data["preds"].get(mdl["id"])
                if not p: continue
                try:
                    pts_x = [last_date, future_dates[0], future_dates[4], future_dates[-1]]
                    pts_y = [lc_fc, float(p["1gun"]), float(p["1hafta"]), float(p["1ay"])]
                    fg.add_trace(go.Scatter(
                        x=pts_x, y=pts_y, name=f"{mdl['icon']} {mdl['name']}",
                        line=dict(color=mdl["color"], width=2, dash="dot"),
                        mode="lines+markers", marker=dict(size=6, color=mdl["color"])
                    ))
                except: pass
            # Konsensüs çizgisi
            pts_x_c = [last_date, future_dates[0], future_dates[4], future_dates[-1]]
            pts_y_c = [lc_fc, c1d, c1w, c1m]
            fg.add_trace(go.Scatter(
                x=pts_x_c, y=pts_y_c, name="🎯 Konsensüs",
                line=dict(color="#ffffff", width=3),
                mode="lines+markers", marker=dict(size=8, color="#ffffff")
            ))
            fg.update_layout(
                paper_bgcolor="#070b14", plot_bgcolor="#0d1420",
                font=dict(color="#4a5a78", family="Sora"),
                height=350, margin=dict(l=8,r=8,t=30,b=8),
                hovermode="x unified",
                hoverlabel=dict(bgcolor="#111c2e", bordercolor="#1a2840", font_color="#e8edf5"),
                legend=dict(bgcolor="#0d1420", bordercolor="#1a2840", borderwidth=1,
                            font=dict(size=11, color="#8899b0"), orientation="h", y=1.08),
                xaxis=dict(gridcolor="#0f1926", zerolinecolor="#0f1926",
                           showspikes=True, spikecolor="#e02020"),
                yaxis=dict(gridcolor="#0f1926", zerolinecolor="#0f1926")
            )
            st.plotly_chart(fg, use_container_width=True)

        # Model kartları
        st.markdown("### Model Tahminleri")
        cols_fc = st.columns(len(AI_MODELS))
        for i, mdl in enumerate(AI_MODELS):
            p = pred_data["preds"].get(mdl["id"])
            with cols_fc[i]:
                if p:
                    try:
                        v1d = float(p["1gun"]); v1w = float(p["1hafta"]); v1m = float(p["1ay"])
                        sig = p.get("sinyal", "NÖTR")
                        d1m = (v1m - lc_fc) / lc_fc * 100
                        cc = "#22c55e" if d1m >= 0 else "#ef4444"
                        st.markdown(f"""
                        <div class="pred-card" style="border-top:3px solid {mdl['color']}">
                          <div class="pred-model">{mdl['icon']} {mdl['name']}</div>
                          <div class="pred-label">1 Günlük</div>
                          <div class="pred-price" style="color:{('#22c55e' if v1d>=lc_fc else '#ef4444')}">{v1d:.4f}</div>
                          <div class="pred-label" style="margin-top:8px">1 Haftalık</div>
                          <div class="pred-price" style="color:{('#22c55e' if v1w>=lc_fc else '#ef4444')}">{v1w:.4f}</div>
                          <div class="pred-label" style="margin-top:8px">1 Aylık</div>
                          <div class="pred-price" style="color:{cc}">{v1m:.4f} <span style="font-size:12px">({d1m:+.1f}%)</span></div>
                          <div style="margin-top:10px"><span class="pred-signal-{sig}">{sig}</span></div>
                          <div style="color:var(--muted);font-size:10px;margin-top:8px;line-height:1.4">{p.get('yorum','')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    except:
                        st.markdown(f"<div class='pred-card'><div class='pred-model'>{mdl['icon']} {mdl['name']}</div><div style='color:var(--muted);font-size:12px'>Tahmin alınamadı</div></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='pred-card'><div class='pred-model'>{mdl['icon']} {mdl['name']}</div><div style='color:var(--muted);font-size:12px'>Tahmin bekleniyor...</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='color:#2a3a52;font-size:11px;margin-top:16px;text-align:center'>⚠️ AI tahminleri yalnızca bilgilendirme amaçlıdır. Yatırım tavsiyesi değildir.</div>", unsafe_allow_html=True)
    elif not st.session_state.ai_predictions:
        st.markdown("""
        <div class="onboard-card">
          <h4>🔮 AI Tahmin Nasıl Çalışır?</h4>
          <p>Yukarıya bir sembol girin ve <b>Tahmin Başlat</b> butonuna tıklayın.<br>
          4 farklı yapay zeka modeli (Llama 3.3 70B, Llama 3 8B, Gemma 2, Mixtral) bağımsız olarak
          1 günlük, 1 haftalık ve 1 aylık fiyat tahmini üretir.<br>
          Sonuçlar grafik üzerinde görselleştirilir ve bir konsensüs tahmini hesaplanır.</p>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 4: PORTFÖY ─────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### Portföy Takibi")
    if not st.session_state.portfolio:
        st.markdown("""
        <div class="onboard-card">
          <h4>Portföyünüz boş</h4>
          <p>Sol menüden hisse sembolü, adet ve alış maliyetini girerek portföyünüze ekleyin.
          Gerçek zamanlı fiyatlarla kar/zarar takibi yapılır. Portföyünüz kalıcı olarak saklanır.</p>
        </div>
        """,unsafe_allow_html=True)
    else:
        rows=[]
        tc=0.0
        tv=0.0
        for item in st.session_state.portfolio:
            try:
                d=get_data(item["t"],"5d","1d")
                if not d.empty:
                    pr=float(d["Close"].iloc[-1])
                    pv=float(d["Close"].iloc[-2]) if len(d)>1 else pr
                    chg=(pr-pv)/pv*100
                    cost=item["c"] if item["c"]>0 else pr
                    val=pr*item["q"]
                    pl=(pr-cost)*item["q"]
                    plp=(pr-cost)/cost*100 if cost>0 else 0
                    tc+=cost*item["q"]
                    tv+=val
                    rows.append({"t":item["t"],"q":item["q"],"c":cost,"p":pr,"chg":chg,"v":val,"pl":pl,"plp":plp,"type":item.get("type","📈 Hisse")})
            except:
                pass

        if rows:
            tpl=tv-tc
            tplp=tpl/tc*100 if tc>0 else 0

            # Günlük snapshot kaydet
            save_portfolio_snapshot(st.session_state.username, tv, tc)

            m1,m2,m3,m4=st.columns(4)
            m1.metric("Toplam Değer",f"${tv:,.2f}")
            m2.metric("Toplam Maliyet",f"${tc:,.2f}")
            m3.metric("Kar / Zarar",f"${tpl:+,.2f}",f"{tplp:+.2f}%")
            m4.metric("Pozisyon",f"{len(rows)}")
            st.markdown("---")

            # Hisse tablosu
            hcols=st.columns([0.5,1.5,0.6,0.9,0.9,0.9,1.1,1.1,1.1,0.4])
            for hc,lbl in zip(hcols,["Tür","Varlık","Adet","Alış","Güncel","Değişim","Değer","K/Z","K/Z %",""]):
                hc.markdown(f"<div style='color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:1px;padding-bottom:6px'>{lbl}</div>",unsafe_allow_html=True)

            for i,row in enumerate(rows):
                cc="#22c55e" if row["chg"]>=0 else "#ef4444"
                pc2="#22c55e" if row["pl"]>=0 else "#ef4444"
                atype = row.get('type','📈 Hisse').split()[0]  # sadece emoji
                cols=st.columns([0.5,1.5,0.6,0.9,0.9,0.9,1.1,1.1,1.1,0.4])
                vals=[
                    f"<span style='font-size:16px'>{atype}</span>",
                    f"<b style='color:var(--text)'>{row['t']}</b>",
                    f"{row['q']:.4f}",
                    f"{row['c']:.4f}",
                    f"{row['p']:.4f}",
                    f"<span style='color:{cc}'>{row['chg']:+.2f}%</span>",
                    f"{row['v']:,.2f}",
                    f"<span style='color:{pc2}'>{row['pl']:+,.2f}</span>",
                    f"<span style='color:{pc2}'>{row['plp']:+.2f}%</span>"
                ]
                for ci,v in enumerate(vals):
                    cols[ci].markdown(f"<div style='font-family:var(--mono);font-size:12px;padding:8px 0'>{v}</div>",unsafe_allow_html=True)
                if cols[9].button("✕",key=f"pd{i}"):
                    delete_portfolio_item(st.session_state.username, row["t"])
                    st.session_state.portfolio = [p for p in st.session_state.portfolio if p["t"] != row["t"]]
                    st.rerun()
                st.markdown("<hr style='margin:0;border-color:#0d1420'>",unsafe_allow_html=True)

            st.markdown("---")

            # ── PERFORMANS GRAFİĞİ ────────────────────────────────────────────
            hist_df = load_portfolio_history(st.session_state.username)

            # Bugünkü anlık değeri son nokta olarak ekle (Sheets'e kaydetmeden, sadece görsel)
            today_ts = pd.Timestamp(datetime.now().date())
            if hist_df.empty or hist_df["date"].max() < today_ts:
                today_row = pd.DataFrame([{
                    "date": today_ts,
                    "total_value": round(tv, 2),
                    "total_cost": round(tc, 2),
                    "pl": round(tv - tc, 2),
                    "pl_pct": round((tv - tc) / tc * 100, 2) if tc > 0 else 0.0
                }])
                hist_df = pd.concat([hist_df, today_row], ignore_index=True).sort_values("date").reset_index(drop=True)

            st.markdown("### Portföy Performansı")
            tab_g1, tab_g2 = st.tabs(["📈 Portföy Değeri", "💰 Kar / Zarar"])

            with tab_g1:
                fg = go.Figure()
                fg.add_trace(go.Scatter(
                    x=hist_df["date"], y=hist_df["total_value"],
                    name="Portföy Değeri",
                    line=dict(color="#3b82f6", width=2),
                    fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
                    mode="lines+markers",
                    marker=dict(size=5, color="#3b82f6"),
                    hovertemplate="<b>%{x|%d %b %Y}</b><br>Değer: $%{y:,.2f}<extra></extra>"
                ))
                fg.add_trace(go.Scatter(
                    x=hist_df["date"], y=hist_df["total_cost"],
                    name="Maliyet",
                    line=dict(color="#4a5a78", width=1.5, dash="dot"),
                    mode="lines",
                    hovertemplate="<b>%{x|%d %b %Y}</b><br>Maliyet: $%{y:,.2f}<extra></extra>"
                ))
                fg.update_layout(
                    paper_bgcolor="#070b14", plot_bgcolor="#0d1420",
                    font=dict(color="#4a5a78", family="Sora"),
                    height=300, margin=dict(l=8,r=8,t=20,b=8),
                    hovermode="x unified",
                    hoverlabel=dict(bgcolor="#111c2e", bordercolor="#1a2840", font_color="#e8edf5"),
                    legend=dict(bgcolor="#0d1420", bordercolor="#1a2840", borderwidth=1,
                                font=dict(size=11, color="#8899b0")),
                    xaxis=dict(gridcolor="#0f1926", zerolinecolor="#0f1926"),
                    yaxis=dict(gridcolor="#0f1926", zerolinecolor="#0f1926", tickprefix="$")
                )
                st.plotly_chart(fg, use_container_width=True)

            with tab_g2:
                bar_colors = ["#22c55e" if v >= 0 else "#ef4444" for v in hist_df["pl"]]
                fpl = go.Figure()
                fpl.add_trace(go.Bar(
                    x=hist_df["date"], y=hist_df["pl"],
                    name="Kar/Zarar",
                    marker_color=bar_colors,
                    hovertemplate="<b>%{x|%d %b %Y}</b><br>K/Z: $%{y:+,.2f}<extra></extra>"
                ))
                fpl.add_trace(go.Scatter(
                    x=hist_df["date"], y=hist_df["pl_pct"],
                    name="K/Z %",
                    line=dict(color="#f59e0b", width=2),
                    mode="lines+markers",
                    marker=dict(size=5),
                    yaxis="y2",
                    hovertemplate="<b>%{x|%d %b %Y}</b><br>K/Z: %{y:+.2f}%<extra></extra>"
                ))
                fpl.update_layout(
                    paper_bgcolor="#070b14", plot_bgcolor="#0d1420",
                    font=dict(color="#4a5a78", family="Sora"),
                    height=300, margin=dict(l=8,r=8,t=20,b=8),
                    hovermode="x unified",
                    hoverlabel=dict(bgcolor="#111c2e", bordercolor="#1a2840", font_color="#e8edf5"),
                    legend=dict(bgcolor="#0d1420", bordercolor="#1a2840", borderwidth=1,
                                font=dict(size=11, color="#8899b0")),
                    xaxis=dict(gridcolor="#0f1926", zerolinecolor="#0f1926"),
                    yaxis=dict(gridcolor="#0f1926", zerolinecolor="#0f1926", tickprefix="$"),
                    yaxis2=dict(overlaying="y", side="right", ticksuffix="%",
                                gridcolor="#0f1926", zerolinecolor="#1a2840")
                )
                st.plotly_chart(fpl, use_container_width=True)

            # Dağılım pasta
            if len(rows) > 1:
                st.markdown("### Dağılım")
                pal=["#e02020","#3b82f6","#22c55e","#f59e0b","#8b5cf6","#06b6d4","#f472b6","#a3e635"]
                fp=go.Figure(go.Pie(
                    labels=[r["t"] for r in rows],
                    values=[r["v"] for r in rows],
                    hole=0.68, textfont_size=12,
                    marker=dict(colors=pal[:len(rows)], line=dict(color="#070b14",width=2))
                ))
                fp.add_annotation(text=f"<b>${tv:,.0f}</b>",font=dict(size=14,color="#e8edf5"),showarrow=False)
                fp.update_layout(
                    paper_bgcolor="#070b14", plot_bgcolor="#070b14",
                    font=dict(color="#8899b0"), height=280,
                    legend=dict(bgcolor="#0d1420", bordercolor="#1a2840"),
                    margin=dict(l=0,r=0,t=20,b=0)
                )
                st.plotly_chart(fp, use_container_width=True)

# ── TAB 5: ALARMLAR ────────────────────────────────────────────────────────────
with tab5:
    st.markdown("### Fiyat Alarmları")
    st.markdown("<div style='color:var(--muted);font-size:12px;margin-bottom:14px'>Fiyat hedefine ulaştığında e-posta bildirimi gönderilir.</div>",unsafe_allow_html=True)

    if not st.session_state.alerts:
        st.markdown("""
        <div class="onboard-card">
          <h4>Alarm kurulmamış</h4>
          <p>Sol menüden sembol, hedef fiyat ve e-posta adresinizi girerek alarm kurabilirsiniz.
          Hedef gerçekleştiğinde anında bildirim alırsınız.</p>
        </div>
        """,unsafe_allow_html=True)
    else:
        fired=[]
        hcols=st.columns([1.2,0.9,0.9,1,1.6,1.8,0.4])
        for hc,lbl in zip(hcols,["Sembol","Hedef","Güncel","Koşul","Durum","E-posta",""]):
            hc.markdown(f"<div style='color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:1px;padding-bottom:6px'>{lbl}</div>",unsafe_allow_html=True)
        st.markdown("<hr style='margin:0 0 6px;border-color:var(--border)'>",unsafe_allow_html=True)

        for i,alarm in enumerate(st.session_state.alerts):
            try:
                d=get_data(alarm["t"],"1d","5m")
                cur=float(d["Close"].iloc[-1]) if not d.empty else 0.0
                hit=(alarm["tp"]=="Üstüne çık" and cur>=alarm["p"]) or (alarm["tp"]=="Altına in" and cur<=alarm["p"])
                dist=(cur-alarm["p"])/alarm["p"]*100

                if hit and not alarm.get("fired") and alarm.get("e"):
                    ok,_=send_email(alarm["e"],alarm["t"],alarm["tp"],alarm["p"],cur)
                    st.session_state.alerts[i]["fired"]=True
                    if ok: st.toast(f"📧 {alarm['t']} alarmı gönderildi!",icon="✅")

                stat=f"<span style='color:#f59e0b;font-weight:600'>🔔 Tetiklendi</span>" if hit \
                     else f"<span style='color:var(--muted)'>⏳ Bekliyor ({dist:+.1f}%)</span>"

                cols=st.columns([1.2,0.9,0.9,1,1.6,1.8,0.4])
                cols[0].markdown(f"<div style='font-family:var(--mono);font-size:13px;font-weight:600;color:var(--text);padding:6px 0'>{alarm['t']}</div>",unsafe_allow_html=True)
                cols[1].markdown(f"<div style='font-family:var(--mono);font-size:12px;color:#f59e0b;padding:6px 0'>{alarm['p']:.2f}</div>",unsafe_allow_html=True)
                cols[2].markdown(f"<div style='font-family:var(--mono);font-size:12px;color:var(--text);padding:6px 0'>{cur:.2f}</div>",unsafe_allow_html=True)
                cols[3].markdown(f"<div style='font-size:11px;color:var(--muted);padding:6px 0'>{alarm['tp']}</div>",unsafe_allow_html=True)
                cols[4].markdown(f"<div style='font-size:12px;padding:6px 0'>{stat}</div>",unsafe_allow_html=True)
                em=alarm.get("e","—"); em_s=(em[:20]+"…") if len(em)>20 else em
                cols[5].markdown(f"<div style='font-size:11px;color:var(--muted);padding:6px 0'>{'📧 '+em_s if em!='—' else '—'}</div>",unsafe_allow_html=True)
                if cols[6].button("✕",key=f"ad{i}"):
                    st.session_state.alerts.pop(i); st.rerun()

                if hit: fired.append(f"{alarm['t']} → {alarm['tp']} {alarm['p']:.2f}")
                st.markdown("<hr style='margin:0;border-color:#0d1420'>",unsafe_allow_html=True)
            except: pass

        if fired:
            st.markdown("---")
            for m in fired: st.warning(f"🔔 {m}",icon="⚠️")

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="footer-bar">
  <b style="color:#2a3a52">⚠️ Yasal Uyarı</b> — Bu platform yalnızca bilgilendirme amaçlıdır.
  Burada yer alan hiçbir içerik <b style="color:#f59e0b">yatırım tavsiyesi değildir.</b>
  Yatırım kararı vermeden önce lisanslı bir finansal danışmana başvurun.<br>
  <span style="color:#1e2d45;font-size:10px">© 2026 ARD Finans · Tüm hakları saklıdır</span>
</div>
""",unsafe_allow_html=True)
