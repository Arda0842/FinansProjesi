import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from groq import Groq
from datetime import datetime, timedelta
import math
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─── SAYFA AYARLARI ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BorsaRobot AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS STİLLER ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background-color: #0a0e1a; color: #e0e6f0; }
  .stApp { background-color: #0a0e1a; }

  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1225 0%, #0a0e1a 100%);
    border-right: 1px solid #1e2a45;
  }

  [data-testid="stMetric"] {
    background: #111827; border: 1px solid #1e2a45; border-radius: 12px;
    padding: 16px; transition: border-color 0.2s;
  }
  [data-testid="stMetric"]:hover { border-color: #3b82f6; }
  [data-testid="stMetricLabel"] { color: #6b7a99 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 1px; }
  [data-testid="stMetricValue"] { color: #e0e6f0 !important; font-family: 'Space Mono', monospace; font-size: 20px !important; }
  [data-testid="stMetricDelta"] { font-family: 'Space Mono', monospace; font-size: 12px !important; }

  .main-header {
    font-family: 'Space Mono', monospace; font-size: 26px; font-weight: 700;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -1px; margin-bottom: 2px;
  }
  .sub-header { color: #4b5a75; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 20px; }

  .ai-response {
    background: linear-gradient(135deg, #0f1e38, #111827);
    border: 1px solid #2563eb44; border-left: 3px solid #10b981;
    border-radius: 12px; padding: 20px; font-size: 14px;
    line-height: 1.85; color: #c8d3e8; margin-top: 12px;
    white-space: pre-wrap;
  }

  .signal-buy   { background:#064e3b; color:#34d399; border:1px solid #059669; border-radius:6px; padding:2px 10px; font-size:11px; font-family:'Space Mono',monospace; font-weight:700; }
  .signal-sell  { background:#450a0a; color:#f87171; border:1px solid #dc2626; border-radius:6px; padding:2px 10px; font-size:11px; font-family:'Space Mono',monospace; font-weight:700; }
  .signal-neutral{ background:#1c1917; color:#a8a29e; border:1px solid #44403c; border-radius:6px; padding:2px 10px; font-size:11px; font-family:'Space Mono',monospace; font-weight:700; }

  .stTabs [data-baseweb="tab-list"] { background:#0d1225; border-radius:10px; padding:4px; gap:4px; border:1px solid #1e2a45; }
  .stTabs [data-baseweb="tab"] { background:transparent; color:#6b7a99; border-radius:8px; font-size:13px; font-weight:500; padding:8px 18px; }
  .stTabs [aria-selected="true"] { background:#1e2a45 !important; color:#e0e6f0 !important; }

  .stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #2563eb); color:white; border:none;
    border-radius:10px; font-family:'DM Sans',sans-serif; font-weight:600;
    padding:10px 24px; transition:all 0.2s;
  }
  .stButton > button:hover { background:linear-gradient(135deg,#2563eb,#3b82f6); transform:translateY(-1px); box-shadow:0 4px 12px #2563eb44; }

  .stTextInput > div > div > input { background:#0d1225 !important; border:1px solid #1e2a45 !important; border-radius:10px !important; color:#e0e6f0 !important; }
  .stTextInput > div > div > input:focus { border-color:#3b82f6 !important; }

  hr { border-color:#1e2a45; margin:16px 0; }
  ::-webkit-scrollbar { width:5px; height:5px; }
  ::-webkit-scrollbar-track { background:#0a0e1a; }
  ::-webkit-scrollbar-thumb { background:#1e2a45; border-radius:3px; }
  .stAlert { background:#111827; border:1px solid #1e2a45; border-radius:10px; }

  .ind-card {
    text-align:center; padding:14px 10px; background:#0d1225;
    border:1px solid #1e2a45; border-radius:10px;
  }
  .ind-card:hover { border-color:#3b82f6; }
  .ind-label { color:#6b7a99; font-size:10px; text-transform:uppercase; letter-spacing:1px; margin-bottom:5px; }
  .ind-value { font-family:'Space Mono',monospace; font-size:15px; color:#e0e6f0; margin-bottom:5px; }

  .gemini-badge {
    display:inline-flex; align-items:center; gap:6px;
    background:linear-gradient(135deg,#1a2e4a,#162038);
    border:1px solid #1e4a6e; border-radius:20px;
    padding:4px 12px; font-size:11px; color:#60a5fa; font-weight:600;
    letter-spacing:0.5px; margin-bottom:12px;
  }
</style>
""", unsafe_allow_html=True)

import hashlib, json, os, re, gspread
from pathlib import Path
from google.oauth2.service_account import Credentials

# ─── KULLANICI VERİTABANI (Google Sheets — kalıcı) ─────────────────────────────

def _get_sheet():
    """Google Sheets bağlantısı."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet  = client.open("ardfinans_users").sheet1
        return sheet
    except Exception as e:
        st.error(f"🔴 Google Sheets bağlantı hatası: {e}")
        return None

def _load_users() -> dict:
    sheet = _get_sheet()
    if sheet is None:
        return {}
    try:
        records = sheet.get_all_records()
        return {r["username"]: {"email": r["email"], "password": r["password"], "created": r.get("created","")}
                for r in records if r.get("username")}
    except Exception as e:
        st.error(f"🔴 Kullanıcı okuma hatası: {e}")
        return {}

def _save_user_row(username: str, email: str, pw_hash: str):
    sheet = _get_sheet()
    if sheet is None:
        return False
    try:
        from datetime import datetime as dt
        sheet.append_row([username, email, pw_hash, dt.now().strftime("%Y-%m-%d %H:%M")])
        return True
    except Exception as e:
        st.error(f"🔴 Kayıt yazma hatası: {e}")
        return False

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()
    if not username or not email or not password:
        return False, "Tüm alanlar zorunludur."
    if len(username) < 3:
        return False, "Kullanıcı adı en az 3 karakter olmalı."
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Geçerli bir e-posta girin."
    if len(password) < 6:
        return False, "Şifre en az 6 karakter olmalı."
    db = _load_users()
    if username in db:
        return False, "Bu kullanıcı adı zaten alınmış."
    if any(v.get("email","").lower() == email.lower() for v in db.values()):
        return False, "Bu e-posta zaten kayıtlı."
    ok = _save_user_row(username, email, _hash(password))
    if not ok:
        return False, "Kayıt sırasında hata oluştu. Lütfen tekrar deneyin."
    return True, "Kayıt başarılı!"

def verify_login(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()
    db = _load_users()
    if username not in db:
        return False, "Kullanıcı bulunamadı."
    if db[username]["password"] != _hash(password):
        return False, "Şifre hatalı."
    return True, db[username].get("email", "")

# ─── SESSION STATE ──────────────────────────────────────────────────────────────
for key, default in [("portfolio",[]),("alerts",[]),("groq_key",""),
                     ("logged_in", False), ("username", ""), ("auth_page", "login"),
                     ("auth_msg", ""), ("auth_ok", False), ("splash_done", False)]:
    if key not in st.session_state:
        st.session_state[key] = default

# Secrets'tan Groq key oku
if not st.session_state.groq_key:
    try:
        st.session_state.groq_key = st.secrets["GROQ_API_KEY"]
    except:
        pass

# ─── SPLASH SCREEN ─────────────────────────────────────────────────────────────
if not st.session_state.logged_in and not st.session_state.splash_done:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display:none !important; }
    header[data-testid="stHeader"]   { display:none !important; }
    #MainMenu, footer                { display:none !important; }
    .block-container { padding:0 !important; max-width:100% !important; }

    /* Splash arka plan — JS ile toggle edilir */
    .splash {
        position: fixed; inset: 0;
        background: #05080f;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        z-index: 9999;
        transition: background 0.4s;
        animation: splashFadeOut 0.6s ease 2.8s forwards;
    }
    .splash.light { background: #f0f2f5; }
    @keyframes splashFadeOut { to { opacity: 0; pointer-events: none; } }

    /* Grid arka plan */
    .splash-grid {
        position: absolute; inset: 0; overflow: hidden;
        background-image:
            linear-gradient(#e02020 1px, transparent 1px),
            linear-gradient(90deg, #e02020 1px, transparent 1px);
        background-size: 60px 60px;
        transition: opacity 0.4s;
        opacity: 0.07;
    }
    .splash.light .splash-grid { opacity: 0.04; }

    /* Tema toggle butonu */
    .splash-theme-btn {
        position: absolute; top: 20px; right: 20px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 50%; width: 40px; height: 40px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 18px;
        transition: background 0.3s, transform 0.3s;
        color: #e0e6f0; user-select: none;
    }
    .splash.light .splash-theme-btn {
        background: rgba(0,0,0,0.06);
        border-color: rgba(0,0,0,0.12);
        color: #333;
    }
    .splash-theme-btn:hover { transform: scale(1.15) rotate(20deg); background: rgba(255,255,255,0.15); }
    .splash.light .splash-theme-btn:hover { background: rgba(0,0,0,0.1); }

    /* Borsa grafik */
    .splash-chart {
        position: absolute; bottom: 80px; width: 80%; max-width: 500px;
        opacity: 0;
        animation: chartRise 1s ease 0.5s forwards;
    }
    @keyframes chartRise {
        from { opacity:0; transform: translateY(20px); }
        to   { opacity:0.18; transform: translateY(0); }
    }

    /* Logo */
    .splash-logo {
        font-size: clamp(48px, 10vw, 88px);
        font-weight: 900; letter-spacing: -2px; line-height: 1;
        display: flex; align-items: center; gap: 12px;
        opacity: 0;
        animation: logoAppear 0.8s cubic-bezier(0.16,1,0.3,1) 0.3s forwards;
    }
    @keyframes logoAppear {
        from { opacity:0; transform: scale(0.85) translateY(10px); }
        to   { opacity:1; transform: scale(1) translateY(0); }
    }
    .sl-ard {
        color: #e02020;
        text-shadow: 0 0 40px rgba(224,32,32,0.6), 0 0 80px rgba(224,32,32,0.3);
    }
    .sl-fin { color: #ffffff; transition: color 0.4s; }
    .splash.light .sl-fin { color: #111; }
    .splash.light .sl-i-dot { background: #111 !important; }

    /* İ harfi */
    .sl-i-wrap {
        display: inline-flex; flex-direction: column;
        align-items: center; line-height: 1;
        gap: 3px; position: relative; top: 2px;
    }
    .sl-i-dot {
        width: clamp(7px,1.2vw,13px); height: clamp(7px,1.2vw,13px);
        background: #ffffff; border-radius: 50%; transition: background 0.4s;
    }
    .sl-i-stem { font-weight: 900; line-height: 1; }

    /* Yükleme çubuğu */
    .splash-bar-wrap {
        margin-top: 48px;
        width: clamp(160px, 30vw, 280px); height: 2px;
        background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;
        opacity: 0; animation: barShow 0.3s ease 1.2s forwards;
        transition: background 0.4s;
    }
    .splash.light .splash-bar-wrap { background: rgba(0,0,0,0.08); }
    @keyframes barShow { to { opacity:1; } }
    .splash-bar {
        height: 100%;
        background: linear-gradient(90deg, #e02020, #ff6060);
        border-radius: 2px; width: 0%;
        animation: barFill 1.4s cubic-bezier(0.4,0,0.2,1) 1.3s forwards;
        box-shadow: 0 0 8px rgba(224,32,32,0.6);
    }
    @keyframes barFill { to { width: 100%; } }

    /* Noktalar */
    .splash-dots {
        display: flex; gap: 8px; margin-top: 16px;
        opacity: 0; animation: barShow 0.3s ease 1.4s forwards;
    }
    .splash-dots span {
        width: 5px; height: 5px; border-radius: 50%;
        background: #e02020; opacity: 0.3;
        animation: dotPulse 1s ease infinite;
    }
    .splash-dots span:nth-child(1) { animation-delay: 0s; }
    .splash-dots span:nth-child(2) { animation-delay: 0.2s; }
    .splash-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dotPulse {
        0%,100% { opacity:0.2; transform:scale(1); }
        50%      { opacity:1;   transform:scale(1.4); }
    }
    </style>

    <div class="splash" id="splashEl">
      <div class="splash-grid"></div>

      <!-- Tema toggle butonu -->
      <div class="splash-theme-btn" id="splashThemeBtn" onclick="toggleSplashTheme()" title="Tema değiştir">
        🌙
      </div>

      <!-- Arka plan grafik -->
      <svg class="splash-chart" viewBox="0 0 500 80" preserveAspectRatio="none">
        <polyline points="0,70 40,55 80,62 130,30 180,45 220,18 270,35 310,12 360,28 410,8 460,20 500,10"
          fill="none" stroke="#e02020" stroke-width="2.5" stroke-linejoin="round"/>
        <polyline points="0,70 40,55 80,62 130,30 180,45 220,18 270,35 310,12 360,28 410,8 460,20 500,10 500,80 0,80"
          fill="url(#splashGrad)" stroke="none"/>
        <defs>
          <linearGradient id="splashGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#e02020" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="#e02020" stop-opacity="0"/>
          </linearGradient>
        </defs>
      </svg>

      <!-- Ana logo -->
      <div class="splash-logo">
        <span class="sl-ard">ARD</span>
        <span class="sl-fin">
          F<span class="sl-i-wrap"><span class="sl-i-dot"></span><span class="sl-i-stem">İ</span></span>NANS
        </span>
      </div>

      <div class="splash-bar-wrap"><div class="splash-bar"></div></div>
      <div class="splash-dots"><span></span><span></span><span></span></div>
    </div>

    <script>
    // Önceki tema tercihi varsa uygula
    const saved = localStorage.getItem('ardfinans-theme');
    const splash = document.getElementById('splashEl');
    const btn    = document.getElementById('splashThemeBtn');
    let isLight  = saved === 'light';
    if (isLight) { splash.classList.add('light'); btn.textContent = '☀️'; }

    function toggleSplashTheme() {
        isLight = !isLight;
        if (isLight) {
            splash.classList.add('light');
            btn.textContent = '☀️';
            localStorage.setItem('ardfinans-theme','light');
        } else {
            splash.classList.remove('light');
            btn.textContent = '🌙';
            localStorage.setItem('ardfinans-theme','dark');
        }
    }
    </script>
    """, unsafe_allow_html=True)

    import time
    time.sleep(3.2)
    st.session_state.splash_done = True
    st.rerun()

# ─── AUTH EKRANI ───────────────────────────────────────────────────────────────
if not st.session_state.logged_in:

    st.markdown("""
    <style>
    section[data-testid="stSidebar"]   { display:none !important; }
    header[data-testid="stHeader"]     { background:transparent; }
    .block-container { max-width:480px !important; padding-top:40px !important; padding-bottom:40px !important; }

    /* Kart */
    .auth-card {
        background: linear-gradient(160deg,#0d1427,#111827);
        border: 1px solid #1e2a45;
        border-radius: 20px;
        padding: 36px 36px 28px;
        box-shadow: 0 20px 60px rgba(0,0,0,.55);
        margin-bottom: 0;
    }
    /* Logo */
    .ard-logo {
        text-align:center;
        font-size: 38px;
        font-weight: 900;
        letter-spacing: -1px;
        line-height: 1;
        margin-bottom: 4px;
    }
    .ard-red   { color: #e02020; }
    .ard-black { color: #e0e6f0; }
    .ard-dot   { display:inline-block; width:8px; height:8px; background:#e0e6f0;
                 border-radius:50%; vertical-align:super; margin-left:1px; }
    .auth-sub  { text-align:center; color:#4b5a75; font-size:11px;
                 letter-spacing:2.5px; text-transform:uppercase; margin-bottom:28px; }
    /* Tab seçici */
    .tab-row   { display:flex; gap:0; border:1px solid #1e2a45; border-radius:10px; overflow:hidden; margin-bottom:24px; }
    .tab-btn   { flex:1; padding:9px; text-align:center; font-size:13px; font-weight:600;
                 cursor:pointer; transition:background .2s; }
    .tab-active{ background:#1e2a45; color:#e0e6f0; }
    .tab-idle  { background:transparent; color:#4b5a75; }
    /* Footer */
    .auth-footer { text-align:center; color:#253350; font-size:11px; margin-top:20px; }
    /* Input label */
    .stTextInput label { color:#6b7a99 !important; font-size:12px !important;
                         text-transform:uppercase; letter-spacing:1px; }
    </style>
    """, unsafe_allow_html=True)

    # ── LOGO ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="auth-card">
      <div class="ard-logo">
        <span class="ard-red">ARD</span>
        <span class="ard-black"> FİNANS</span>
      </div>
      <div class="auth-sub">AI · Powered Trading Platform</div>
    </div>
    """, unsafe_allow_html=True)

    # ── SEKME SEÇİCİ ──────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        if st.button("🔑 Giriş Yap", use_container_width=True,
                     type="primary" if st.session_state.auth_page=="login" else "secondary"):
            st.session_state.auth_page = "login"
            st.session_state.auth_msg  = ""
            st.rerun()
    with col_r:
        if st.button("📝 Kayıt Ol", use_container_width=True,
                     type="primary" if st.session_state.auth_page=="register" else "secondary"):
            st.session_state.auth_page = "register"
            st.session_state.auth_msg  = ""
            st.rerun()

    st.markdown("---")

    # ── GİRİŞ FORMU ───────────────────────────────────────────────────────────
    if st.session_state.auth_page == "login":
        login_user = st.text_input("👤 Kullanıcı Adı", placeholder="kullanıcı adınız", key="l_user")
        login_pass = st.text_input("🔒 Şifre", placeholder="••••••••", type="password", key="l_pass")
        st.markdown(" ")
        if st.button("Giriş Yap →", use_container_width=True, key="do_login", type="primary"):
            ok, msg = verify_login(login_user, login_pass)
            if ok:
                st.session_state.logged_in = True
                st.session_state.username  = login_user.strip().lower()
                st.session_state.auth_msg  = ""
                st.rerun()
            else:
                st.session_state.auth_msg = msg
                st.rerun()
        if st.session_state.auth_msg:
            st.error(f"❌ {st.session_state.auth_msg}")

    # ── KAYIT FORMU ───────────────────────────────────────────────────────────
    else:
        reg_user  = st.text_input("👤 Kullanıcı Adı", placeholder="en az 3 karakter", key="r_user")
        reg_email = st.text_input("📧 E-posta",        placeholder="ornek@mail.com",   key="r_email")
        reg_pass  = st.text_input("🔒 Şifre",          placeholder="en az 6 karakter", type="password", key="r_pass")
        reg_pass2 = st.text_input("🔒 Şifre (tekrar)", placeholder="••••••••",          type="password", key="r_pass2")
        st.markdown(" ")
        if st.button("Hesap Oluştur →", use_container_width=True, key="do_register", type="primary"):
            if reg_pass != reg_pass2:
                st.session_state.auth_msg = "Şifreler eşleşmiyor."
                st.session_state.auth_ok  = False
                st.rerun()
            else:
                ok, msg = register_user(reg_user, reg_email, reg_pass)
                st.session_state.auth_msg = msg
                st.session_state.auth_ok  = ok
                st.rerun()
        if st.session_state.auth_msg:
            if st.session_state.auth_ok:
                st.success(f"✅ {st.session_state.auth_msg} Giriş yapabilirsiniz.")
            else:
                st.error(f"❌ {st.session_state.auth_msg}")

    st.markdown("""
    <div class="auth-footer">🔒 Güvenli bağlantı · ARD Finans v2.0 · Tüm hakları saklıdır</div>
    """, unsafe_allow_html=True)

    st.stop()

# ─── VERİ FONKSİYONLARI ────────────────────────────────────────────────────────

# Bilinen BIST hisseleri — .IS otomatik eklenir
BIST_TICKERS = {
    "THYAO","GARAN","AKBNK","YKBNK","ISCTR","HALKB","VAKBN","SISE","EREGL","KRDMD",
    "BIMAS","MGROS","MIGRS","ARCLK","TOASO","FROTO","DOAS","OTKAR","KCHOL","SAHOL",
    "PETKM","TUPRS","AYGAZ","AKSA","VESBE","VESTL","TCELL","TTKOM","ASELS","KOZAL",
    "KOZAA","GOLD","ENKAI","EKGYO","ISGYO","TSKB","ALARK","ALGYO","SODA","TRKCM",
    "NETAS","LOGO","INDES","DOHOL","TKFEN","ISMEN","TATGD","ULKER","PGSUS","THYAO",
    "TAVHL","CLEBI","MAVI","LCWAI","BERA","BRISA","GUBRF","HEKTS","KARSAN","KLNMA",
    "KMPUR","KONTR","KONYA","KORDS","KURTOSAN","LINK","LMKDC","LREDY","MAALT",
    "MAKTK","MEGAP","MERIT","METRO","MIPAZ","MPARK","NTHOL","NTTUR","NUHCM",
    "ODAS","ONCSM","ORGE","OSMEN","OYAKC","OYLUM","OZGYO","OZKGY","PAPIL",
    "PARSN","PCILT","PENGD","PKENT","PRKAB","PRKME","PRZMA","QNBFL","QNBFB",
    "RAYSG","RGYAS","RNPOL","RTALB","RUBNS","RYSAS","SAMAT","SARKY","SASA",
    "SDTTR","SEGYO","SEKFK","SEKUR","SELEC","SELGD","SERVE","SKTAS","SMART",
    "SNKRN","SODSN","SOKM","SRVGY","SUWEN","TCKRC","TGSAS","THYAO","TIRE",
    "TKURU","TLMAN","TMSN","TNZTP","TRGYO","TRILC","TSPOR","TTRAK","TUCLK",
    "TUKAS","TURGZ","TURSG","UFUK","ULUFA","ULUSE","ULUUN","UMPAS","UNLU",
    "USAK","USDTR","VANGD","VERUS","VKFYO","VKGYO","VKTUR","YAPRK","YATAS",
    "YESIL","YGGYO","YKGYO","YKSLN","YUNSA","ZEDUR","ZOREN"
}

def resolve_ticker(raw: str) -> str:
    """Girilen hisse sembolünü akıllıca çözer. BIST hisselerine .IS ekler."""
    t = raw.upper().strip()
    # Zaten uzantı var
    if "." in t or "=" in t or "-" in t:
        return t
    # Bilinen BIST listesinde var mı?
    if t in BIST_TICKERS:
        return t + ".IS"
    # Yahoo Finance'de direkt dene, bulamazsa .IS ile dene
    return t

def _download(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Tek ticker için yfinance download, sütunları düzeltir."""
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True, actions=False)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        needed = [c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]
        if len(needed) < 5:
            return pd.DataFrame()
        return df[needed].dropna()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_stock_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Ticker'ı dener; bulamazsa .IS ekleyerek tekrar dener."""
    df = _download(ticker, period, interval)
    if not df.empty:
        return df
    # .IS ekleyerek tekrar dene (BIST)
    if "." not in ticker and "=" not in ticker and "-" not in ticker:
        df2 = _download(ticker + ".IS", period, interval)
        if not df2.empty:
            return df2
    return pd.DataFrame()

@st.cache_data(ttl=60)
def get_ticker_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info
    except:
        return {}

# ─── İNDİKATÖR HESAPLAMA ───────────────────────────────────────────────────────

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["Close"].squeeze().astype(float)
    high  = df["High"].squeeze().astype(float)
    low   = df["Low"].squeeze().astype(float)
    vol   = df["Volume"].squeeze().astype(float)

    # RSI
    gain = close.diff().clip(lower=0)
    loss = (-close.diff()).clip(lower=0)
    avg_g = gain.ewm(span=14, adjust=False).mean()
    avg_l = loss.ewm(span=14, adjust=False).mean()
    df["RSI"] = 100 - 100 / (1 + avg_g / (avg_l + 1e-9))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"]        = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]

    # Bollinger Bands
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    df["BB_Mid"]   = sma20
    df["BB_Upper"] = sma20 + 2*std20
    df["BB_Lower"] = sma20 - 2*std20
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / (df["BB_Mid"] + 1e-9)

    # EMAs
    for span in [9, 20, 50, 100, 200]:
        df[f"EMA_{span}"] = close.ewm(span=span, adjust=False).mean()

    # SMAs
    for w in [10, 20, 50, 200]:
        df[f"SMA_{w}"] = close.rolling(w).mean()

    # Stochastic
    low14  = low.rolling(14).min()
    high14 = high.rolling(14).max()
    df["Stoch_K"] = 100*(close - low14) / (high14 - low14 + 1e-9)
    df["Stoch_D"] = df["Stoch_K"].rolling(3).mean()

    # ATR
    tr = pd.concat([(high-low), (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
    df["ATR"]     = tr.rolling(14).mean()
    df["ATR_pct"] = df["ATR"] / (close + 1e-9) * 100

    # OBV
    obv = [0]
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:   obv.append(obv[-1] + vol.iloc[i])
        elif close.iloc[i] < close.iloc[i-1]: obv.append(obv[-1] - vol.iloc[i])
        else:                                  obv.append(obv[-1])
    df["OBV"] = obv

    # Williams %R
    df["WilliamsR"] = -100*(high14 - close) / (high14 - low14 + 1e-9)

    # CCI
    tp       = (high + low + close) / 3
    sma_tp   = tp.rolling(20).mean()
    mean_dev = tp.rolling(20).apply(lambda x: np.mean(np.abs(x - x.mean())))
    df["CCI"] = (tp - sma_tp) / (0.015 * mean_dev + 1e-9)

    # MFI
    mf  = tp * vol
    pos = mf.where(tp > tp.shift(), 0).rolling(14).sum()
    neg = mf.where(tp < tp.shift(), 0).rolling(14).sum()
    df["MFI"] = 100 - 100 / (1 + pos / (neg + 1e-9))

    # ROC
    df["ROC_10"] = close.pct_change(10) * 100
    df["ROC_20"] = close.pct_change(20) * 100

    # VWAP
    cum_vol = vol.cumsum()
    cum_tp  = (tp * vol).cumsum()
    df["VWAP"] = cum_tp / (cum_vol + 1e-9)

    # ADX
    dm_plus  = (high - high.shift()).clip(lower=0)
    dm_minus = (low.shift() - low).clip(lower=0)
    dm_plus  = dm_plus.where(dm_plus > dm_minus, 0)
    dm_minus = dm_minus.where(dm_minus > dm_plus, 0)
    atr14    = tr.rolling(14).mean()
    di_plus  = 100 * dm_plus.rolling(14).mean() / (atr14 + 1e-9)
    di_minus = 100 * dm_minus.rolling(14).mean() / (atr14 + 1e-9)
    dx       = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus + 1e-9)
    df["ADX"]      = dx.rolling(14).mean()
    df["DI_Plus"]  = di_plus
    df["DI_Minus"] = di_minus

    # Parabolic SAR
    af = 0.02; max_af = 0.2
    psar = [float(close.iloc[0])]; bull = True
    ep = float(high.iloc[0]); cur_af = af
    for i in range(1, len(close)):
        prev_sar = psar[-1]
        if bull:
            new_sar = prev_sar + cur_af * (ep - prev_sar)
            new_sar = min(new_sar, float(low.iloc[i-1]), float(low.iloc[max(0,i-2)]))
            if float(low.iloc[i]) < new_sar:
                bull = False; new_sar = ep; ep = float(low.iloc[i]); cur_af = af
            else:
                if float(high.iloc[i]) > ep: ep = float(high.iloc[i]); cur_af = min(cur_af+af, max_af)
        else:
            new_sar = prev_sar + cur_af * (ep - prev_sar)
            new_sar = max(new_sar, float(high.iloc[i-1]), float(high.iloc[max(0,i-2)]))
            if float(high.iloc[i]) > new_sar:
                bull = True; new_sar = ep; ep = float(high.iloc[i]); cur_af = af
            else:
                if float(low.iloc[i]) < ep: ep = float(low.iloc[i]); cur_af = min(cur_af+af, max_af)
        psar.append(new_sar)
    df["PSAR"] = psar

    # Donchian Channel
    df["Donchian_High"] = high.rolling(20).max()
    df["Donchian_Low"]  = low.rolling(20).min()
    df["Donchian_Mid"]  = (df["Donchian_High"] + df["Donchian_Low"]) / 2

    # Ichimoku
    df["Ichimoku_Conversion"] = (high.rolling(9).max()  + low.rolling(9).min())  / 2
    df["Ichimoku_Base"]       = (high.rolling(26).max() + low.rolling(26).min()) / 2
    df["Ichimoku_SpanA"]      = ((df["Ichimoku_Conversion"] + df["Ichimoku_Base"]) / 2).shift(26)
    df["Ichimoku_SpanB"]      = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)

    # Chaikin Money Flow
    clv = ((close - low) - (high - close)) / (high - low + 1e-9)
    df["CMF"] = (clv * vol).rolling(20).sum() / (vol.rolling(20).sum() + 1e-9)

    # Elder Ray
    ema13 = close.ewm(span=13, adjust=False).mean()
    df["Bull_Power"] = high - ema13
    df["Bear_Power"] = low  - ema13

    # Hacim Ortalaması
    df["Vol_SMA_20"] = vol.rolling(20).mean()
    df["Vol_Ratio"]  = vol / (df["Vol_SMA_20"] + 1e-9)

    return df

# ─── SİNYAL ÜRETİCİ ───────────────────────────────────────────────────────────

def generate_signals(df: pd.DataFrame) -> dict:
    last = df.iloc[-1]
    signals = {}

    def s(name, cond_buy, cond_sell, desc_buy, desc_sell, desc_neu=""):
        if cond_buy:    signals[name] = ("AL",   desc_buy)
        elif cond_sell: signals[name] = ("SAT",  desc_sell)
        else:           signals[name] = ("NÖTR", desc_neu or name)

    rsi = float(last.get("RSI", 50))
    s("RSI", rsi < 30, rsi > 70,
      f"RSI={rsi:.1f} Aşırı satım", f"RSI={rsi:.1f} Aşırı alım", f"RSI={rsi:.1f}")

    macd = float(last.get("MACD",0)); sig_l = float(last.get("MACD_Signal",0))
    hist = float(last.get("MACD_Hist",0))
    s("MACD", macd > sig_l and hist > 0, macd < sig_l and hist < 0,
      "Pozitif kesişim ↑", "Negatif kesişim ↓", "Nötr")

    close = float(last["Close"])
    bb_u = float(last.get("BB_Upper",0)); bb_l = float(last.get("BB_Lower",0))
    s("BB", close < bb_l, close > bb_u, "Alt banda yakın", "Üst banda yakın", "Band içinde")

    ema20 = float(last.get("EMA_20",0)); ema50 = float(last.get("EMA_50",0))
    s("EMA 20/50", ema20 > ema50, ema20 < ema50, "EMA20>EMA50 ↑", "EMA20<EMA50 ↓")

    ema50_ = float(last.get("EMA_50",0)); ema200 = float(last.get("EMA_200",0))
    s("Golden/Death", ema50_ > ema200, ema50_ < ema200,
      "Golden Cross ↑", "Death Cross ↓", "EMA50≈EMA200")

    k = float(last.get("Stoch_K",50)); d = float(last.get("Stoch_D",50))
    s("Stoch", k < 20 and k > d, k > 80 and k < d,
      f"K={k:.0f} Aşırı satım", f"K={k:.0f} Aşırı alım", f"K={k:.0f}")

    adx = float(last.get("ADX",0)); di_p = float(last.get("DI_Plus",0)); di_m = float(last.get("DI_Minus",0))
    s("ADX", adx > 25 and di_p > di_m, adx > 25 and di_p < di_m,
      f"ADX={adx:.0f} Güçlü ↑", f"ADX={adx:.0f} Güçlü ↓", f"ADX={adx:.0f} Zayıf trend")

    mfi = float(last.get("MFI",50))
    s("MFI", mfi < 20, mfi > 80,
      f"MFI={mfi:.0f} Aşırı satım", f"MFI={mfi:.0f} Aşırı alım", f"MFI={mfi:.0f}")

    cmf = float(last.get("CMF",0))
    s("CMF", cmf > 0.1, cmf < -0.1,
      f"CMF={cmf:.2f} Para girişi", f"CMF={cmf:.2f} Para çıkışı", f"CMF={cmf:.2f}")

    wr = float(last.get("WilliamsR",-50))
    s("Williams%R", wr < -80, wr > -20,
      f"%R={wr:.0f} Aşırı satım", f"%R={wr:.0f} Aşırı alım", f"%R={wr:.0f}")

    cci = float(last.get("CCI",0))
    s("CCI", cci < -100, cci > 100,
      f"CCI={cci:.0f} Aşırı satım", f"CCI={cci:.0f} Aşırı alım", f"CCI={cci:.0f}")

    vwap = float(last.get("VWAP",0))
    s("VWAP", close > vwap, close < vwap, "Fiyat>VWAP ↑", "Fiyat<VWAP ↓", "≈VWAP")

    psar = float(last.get("PSAR",0))
    s("PSAR", close > psar, close < psar, "Fiyat>PSAR Boğa", "Fiyat<PSAR Ayı")

    bull_p = float(last.get("Bull_Power",0)); bear_p = float(last.get("Bear_Power",0))
    s("Elder Ray", bull_p > 0 and bear_p > -0.5, bear_p < 0 and bull_p < 0.5,
      "Bull Power pozitif", "Bear Power negatif", "Karma güç")

    roc10 = float(last.get("ROC_10",0))
    s("ROC(10)", roc10 > 2, roc10 < -2,
      f"ROC={roc10:.1f}% ↑", f"ROC={roc10:.1f}% ↓", f"ROC={roc10:.1f}%")

    return signals

def compute_score(signals: dict) -> tuple:
    al = sum(1 for v in signals.values() if v[0] == "AL")
    sat = sum(1 for v in signals.values() if v[0] == "SAT")
    total = len(signals)
    score = (al - sat) / total * 100
    return al, sat, total - al - sat, score

# ─── GRAFİK ────────────────────────────────────────────────────────────────────

def build_chart(df: pd.DataFrame, ticker: str, indicators: list) -> go.Figure:
    rows = 1
    sub_panels = []
    if "RSI"   in indicators: rows += 1; sub_panels.append("RSI (14)")
    if "MACD"  in indicators: rows += 1; sub_panels.append("MACD")
    if "Hacim" in indicators: rows += 1; sub_panels.append("Hacim")
    if "ADX"   in indicators: rows += 1; sub_panels.append("ADX")

    row_heights = [0.55] + [0.12] * (rows - 1)
    subplot_titles = [ticker] + sub_panels

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.03, row_heights=row_heights,
        subplot_titles=subplot_titles
    )

    # Mum grafik
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Fiyat",
        increasing_line_color="#34d399", increasing_fillcolor="#064e3b",
        decreasing_line_color="#f87171", decreasing_fillcolor="#450a0a",
        line_width=1
    ), row=1, col=1)

    # Bollinger
    if "BB" in indicators:
        for col_nm, color, fill in [("BB_Upper","#6366f1",None),("BB_Mid","#a78bfa",None),("BB_Lower","#6366f1","tonexty")]:
            if col_nm in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col_nm], name=col_nm,
                    line=dict(color=color, width=1, dash="dot"),
                    fill=fill, fillcolor="rgba(99,102,241,0.04)", showlegend=False
                ), row=1, col=1)

    # EMAs
    ema_colors = {"EMA_9":"#f472b6","EMA_20":"#fbbf24","EMA_50":"#fb923c","EMA_100":"#a78bfa","EMA_200":"#f87171"}
    for ema, color in ema_colors.items():
        if ema in indicators and ema in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ema], name=ema.replace("_"," "),
                line=dict(color=color, width=1.2), showlegend=True
            ), row=1, col=1)

    # SMAs
    sma_colors = {"SMA_10":"#67e8f9","SMA_20":"#4ade80","SMA_50":"#fde68a","SMA_200":"#fca5a5"}
    for sma, color in sma_colors.items():
        if sma in indicators and sma in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[sma], name=sma.replace("_"," "),
                line=dict(color=color, width=1, dash="dash"), showlegend=True
            ), row=1, col=1)

    # VWAP
    if "VWAP" in indicators and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["VWAP"], name="VWAP",
            line=dict(color="#38bdf8", width=1.5, dash="dot"), showlegend=True
        ), row=1, col=1)

    # PSAR
    if "PSAR" in indicators and "PSAR" in df.columns:
        close_arr = df["Close"].squeeze()
        psar_colors = ["#34d399" if float(df["PSAR"].iloc[i]) < float(close_arr.iloc[i]) else "#f87171" for i in range(len(df))]
        fig.add_trace(go.Scatter(
            x=df.index, y=df["PSAR"], name="PSAR", mode="markers",
            marker=dict(color=psar_colors, size=3), showlegend=True
        ), row=1, col=1)

    # Donchian
    if "Donchian" in indicators and "Donchian_High" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Donchian_High"], name="Donchian H",
            line=dict(color="#0891b2",width=1), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Donchian_Low"], name="Donchian L",
            line=dict(color="#0891b2",width=1), fill="tonexty",
            fillcolor="rgba(8,145,178,0.05)", showlegend=True), row=1, col=1)

    # Ichimoku
    if "Ichimoku" in indicators and "Ichimoku_SpanA" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_Conversion"], name="Tenkan",
            line=dict(color="#f59e0b",width=1), showlegend=True), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_Base"], name="Kijun",
            line=dict(color="#ec4899",width=1), showlegend=True), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_SpanA"], name="Span A",
            line=dict(color="#34d399",width=1,dash="dot"), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichimoku_SpanB"], name="Span B",
            line=dict(color="#f87171",width=1,dash="dot"), fill="tonexty",
            fillcolor="rgba(52,211,153,0.04)", showlegend=False), row=1, col=1)

    current_row = 2

    # RSI
    if "RSI" in indicators and "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
            line=dict(color="#38bdf8",width=1.5),
            fill="tozeroy", fillcolor="rgba(56,189,248,0.04)"), row=current_row, col=1)
        for lvl, clr in [(70,"#f87171"),(50,"#374151"),(30,"#34d399")]:
            fig.add_hline(y=lvl, line_dash="dot", line_color=clr, line_width=1, row=current_row, col=1)
        current_row += 1

    # MACD
    if "MACD" in indicators and "MACD" in df.columns:
        hist_colors = ["#34d399" if v >= 0 else "#f87171" for v in df["MACD_Hist"]]
        fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="Histogram",
            marker_color=hist_colors, showlegend=False), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
            line=dict(color="#3b82f6",width=1.5)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], name="Sinyal",
            line=dict(color="#f59e0b",width=1.5)), row=current_row, col=1)
        current_row += 1

    # Hacim
    if "Hacim" in indicators and "Volume" in df.columns:
        vol_colors = ["#34d399" if float(df["Close"].iloc[i]) >= float(df["Open"].iloc[i]) else "#f87171" for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Hacim",
            marker_color=vol_colors, showlegend=False), row=current_row, col=1)
        if "Vol_SMA_20" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["Vol_SMA_20"], name="Hacim Ort.",
                line=dict(color="#f59e0b",width=1), showlegend=False), row=current_row, col=1)
        current_row += 1

    # ADX
    if "ADX" in indicators and "ADX" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["ADX"], name="ADX",
            line=dict(color="#c084fc",width=1.5)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["DI_Plus"], name="DI+",
            line=dict(color="#34d399",width=1)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["DI_Minus"], name="DI-",
            line=dict(color="#f87171",width=1)), row=current_row, col=1)
        fig.add_hline(y=25, line_dash="dot", line_color="#374151", line_width=1, row=current_row, col=1)

    fig.update_layout(
        paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1225",
        font=dict(color="#6b7a99", family="DM Sans"),
        xaxis_rangeslider_visible=False,
        legend=dict(bgcolor="#0d1225", bordercolor="#1e2a45", borderwidth=1,
                    font=dict(size=10, color="#9ca3af"), orientation="h", y=1.02, x=0),
        margin=dict(l=10, r=10, t=40, b=10),
        height=650, hovermode="x unified",
        hoverlabel=dict(bgcolor="#111827", bordercolor="#1e2a45", font_color="#e0e6f0"),
    )
    fig.update_xaxes(gridcolor="#1e2a45", zerolinecolor="#1e2a45",
                     showspikes=True, spikecolor="#3b82f6", spikethickness=1)
    fig.update_yaxes(gridcolor="#1e2a45", zerolinecolor="#1e2a45")
    for ann in fig.layout.annotations:
        ann.font = dict(color="#4b5a75", size=11)
    return fig

# ─── GEMİNİ AI ANALİZ ──────────────────────────────────────────────────────────

def build_prompt(ticker, df, info, signals, al, sat, neutral, score):
    last = df.iloc[-1]
    def fv(k, fmt=".2f"):
        try: return f"{float(last.get(k,0)):{fmt}}"
        except: return "N/A"
    return f"""
HİSSE: {ticker}
Şirket: {info.get('longName', ticker)}
Sektör: {info.get('sector','N/A')} | Endüstri: {info.get('industry','N/A')}
Borsa: {info.get('exchange','N/A')} | Para: {info.get('currency','N/A')}
Son Fiyat: {fv('Close')}
Piyasa Değeri: {info.get('marketCap','N/A')}
F/K: {info.get('trailingPE','N/A')} | PD/DD: {info.get('priceToBook','N/A')}
52H Max: {info.get('fiftyTwoWeekHigh','N/A')} | 52H Min: {info.get('fiftyTwoWeekLow','N/A')}
Temettü: {info.get('dividendYield','N/A')} | Beta: {info.get('beta','N/A')}

─── TEKNİK DEĞERLER ───
RSI(14): {fv('RSI')}
MACD: {fv('MACD','.4f')} | Signal: {fv('MACD_Signal','.4f')} | Hist: {fv('MACD_Hist','.4f')}
BB Üst: {fv('BB_Upper')} | Orta: {fv('BB_Mid')} | Alt: {fv('BB_Lower')} | Genişlik: {fv('BB_Width','.3f')}
EMA9: {fv('EMA_9')} | EMA20: {fv('EMA_20')} | EMA50: {fv('EMA_50')} | EMA200: {fv('EMA_200')}
SMA20: {fv('SMA_20')} | SMA50: {fv('SMA_50')} | SMA200: {fv('SMA_200')}
Stoch K: {fv('Stoch_K')} | D: {fv('Stoch_D')}
ADX: {fv('ADX')} | DI+: {fv('DI_Plus')} | DI-: {fv('DI_Minus')}
ATR: {fv('ATR','.4f')} | ATR%: {fv('ATR_pct')}
OBV: {fv('OBV',',.0f')} | CMF: {fv('CMF','.3f')} | MFI: {fv('MFI')}
Williams%R: {fv('WilliamsR')} | CCI: {fv('CCI')} | ROC10: {fv('ROC_10')}%
VWAP: {fv('VWAP')} | PSAR: {fv('PSAR')}
Donchian H: {fv('Donchian_High')} | L: {fv('Donchian_Low')}
Ichimoku Tenkan: {fv('Ichimoku_Conversion')} | Kijun: {fv('Ichimoku_Base')}
Bull Power: {fv('Bull_Power','.3f')} | Bear Power: {fv('Bear_Power','.3f')}
Hacim/Ort: {fv('Vol_Ratio','.2f')}x

─── SİNYAL SKORU: {score:+.0f} ───
AL: {al} | SAT: {sat} | NÖTR: {neutral}
{chr(10).join(f"• {k}: {v[0]} — {v[1]}" for k,v in signals.items())}
"""

def ai_analyze_groq(ticker, df, info, signals, al, sat, neutral, score, api_key):
    client = Groq(api_key=api_key)

    system_prompt = """Sen uzman bir borsa teknik ve temel analiz uzmanısın. Türkçe yanıt ver.
Analizin bu bölümlerden oluşsun (emojili başlıklar kullan):

📊 TEKNİK GENEL BAKIŞ
🔍 KRİTİK İNDİKATÖR ANALİZİ (en önemli 5-6 indikatörü yorumla, somut yorumla)
🎯 DESTEK ve DİRENÇ SEVİYELERİ (hesaplayarak belirt)
📈 TREND ANALİZİ (kısa/orta/uzun vadeli)
⚡ KISA VADE SENARYO (1-5 gün)
📅 ORTA VADE SENARYO (1-4 hafta)
⚠️ RİSKLER ve UYARILAR
💡 ÖZET ve STRATEJİ ÖNERİSİ

Her bölüm somut ve sayısal olsun. Yatırım tavsiyesi olmadığını belirt."""

    prompt = build_prompt(ticker, df, info, signals, al, sat, neutral, score)

    # Model öncelik sırası — Groq'ta mevcut
    GROQ_MODELS = [
        "llama-3.3-70b-versatile",   # En iyi analiz kalitesi
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "llama3-70b-8192",
        "llama3-8b-8192",
    ]

    last_err = None
    for model_name in GROQ_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return f"*{model_name}*\n\n" + response.choices[0].message.content
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "model_not_found" in err_str.lower() or "404" in err_str:
                continue
            raise e

    raise Exception(f"Groq hatası: {last_err}")

# ─── E-POSTA ALARM FONKSİYONU ──────────────────────────────────────────────────
def send_alarm_email(to_email: str, ticker: str, alarm_type: str,
                     target_price: float, current_price: float):
    """Gmail SMTP ile alarm e-postası gönderir."""
    try:
        sender    = st.secrets["EMAIL_SENDER"]
        password  = st.secrets["EMAIL_PASSWORD"]
    except:
        return False, "E-posta ayarları Secrets'ta tanımlı değil."

    subject = f"🔔 ARD Finans Alarm: {ticker} {alarm_type}!"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;
                background:#0a0e1a;border:1px solid #1e2a45;border-radius:16px;overflow:hidden">
      <div style="background:linear-gradient(135deg,#1e2a45,#0d1225);padding:24px;text-align:center">
        <span style="font-size:28px;font-weight:900">
          <span style="color:#e02020">ARD</span>
          <span style="color:#e0e6f0"> FİNANS</span>
        </span>
        <div style="color:#4b5a75;font-size:11px;letter-spacing:2px;margin-top:4px">ALARM BİLDİRİMİ</div>
      </div>
      <div style="padding:28px">
        <div style="background:#111827;border:1px solid #1e2a45;border-radius:12px;padding:20px;margin-bottom:16px">
          <div style="font-size:32px;font-weight:700;color:#e0e6f0;font-family:monospace">{ticker}</div>
          <div style="color:#f59e0b;font-size:18px;font-weight:700;margin:8px 0">🔥 ALARM TETİKLENDİ</div>
          <table style="width:100%;color:#9ca3af;font-size:14px">
            <tr><td style="padding:4px 0">Koşul:</td>
                <td style="color:#e0e6f0;font-family:monospace">{alarm_type}</td></tr>
            <tr><td style="padding:4px 0">Hedef Fiyat:</td>
                <td style="color:#f59e0b;font-family:monospace">{target_price:.2f}</td></tr>
            <tr><td style="padding:4px 0">Güncel Fiyat:</td>
                <td style="color:#34d399;font-family:monospace;font-weight:700">{current_price:.2f}</td></tr>
            <tr><td style="padding:4px 0">Tarih/Saat:</td>
                <td style="color:#e0e6f0;font-family:monospace">{datetime.now().strftime("%d.%m.%Y %H:%M")}</td></tr>
          </table>
        </div>
        <div style="color:#4b5a75;font-size:11px;text-align:center;margin-top:16px">
          ⚠️ Bu bildirim yalnızca bilgilendirme amaçlıdır. Yatırım tavsiyesi değildir.<br>
          © 2026 ARD Finans
        </div>
      </div>
    </div>
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True, "E-posta gönderildi!"
    except Exception as e:
        return False, str(e)

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; margin-bottom:4px">
      <span style="font-size:26px; font-weight:900; letter-spacing:-1px; line-height:1">
        <span style="color:#e02020">ARD</span>
        <span style="color:#e0e6f0"> FİNANS</span>
      </span>
    </div>
    <div style="text-align:center; color:#4b5a75; font-size:10px; letter-spacing:2px; text-transform:uppercase; margin-bottom:16px;">
      AI · Powered Trading Platform
    </div>
    """, unsafe_allow_html=True)

    # Kullanıcı bilgisi
    st.markdown(f"""
    <div style="background:#0d1225;border:1px solid #1e2a45;border-radius:10px;padding:10px 14px;margin-bottom:16px;display:flex;align-items:center;gap:10px">
      <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#3b82f6,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:white;flex-shrink:0">
        {st.session_state.username[0].upper()}
      </div>
      <div>
        <div style="font-size:13px;font-weight:600;color:#e0e6f0">{st.session_state.username}</div>
        <div style="font-size:10px;color:#4b5a75;display:flex;align-items:center;gap:4px">
          <span style="width:6px;height:6px;border-radius:50%;background:#22c55e;display:inline-block"></span>
          Oturum açık
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username  = ""
        st.rerun()

    st.divider()

    st.markdown("#### 🔍 Hisse")
    _raw_ticker = st.text_input("Sembol", value="AAPL",
                                 placeholder="AAPL / THYAO / BTC-USD").upper().strip()
    ticker_input = resolve_ticker(_raw_ticker)
    if ticker_input != _raw_ticker and _raw_ticker:
        st.caption(f"🇹🇷 BIST: **{ticker_input}** olarak aranıyor")
    col1, col2 = st.columns(2)
    with col1: period   = st.selectbox("Dönem",  ["5d","1mo","3mo","6mo","1y","2y","5y"], index=2)
    with col2: interval = st.selectbox("Aralık", ["1d","1wk","1h","30m","15m","5m"],      index=0)

    st.markdown("#### 📊 İndikatörler")
    overlay_inds = st.multiselect(
        "Grafik Üzeri (Overlay)",
        ["BB","EMA_9","EMA_20","EMA_50","EMA_100","EMA_200",
         "SMA_10","SMA_20","SMA_50","SMA_200",
         "VWAP","PSAR","Donchian","Ichimoku"],
        default=["BB","EMA_20","EMA_50","VWAP"]
    )
    sub_inds = st.multiselect(
        "Alt Paneller",
        ["RSI","MACD","Hacim","ADX"],
        default=["RSI","MACD","Hacim"]
    )
    selected_inds = overlay_inds + sub_inds

    st.divider()
    st.markdown("#### ➕ Portföy")
    _pf_raw = st.text_input("Sembol", key="pf_ticker", placeholder="AAPL / THYAO").upper().strip()
    pf_ticker = resolve_ticker(_pf_raw)
    if pf_ticker != _pf_raw and _pf_raw:
        st.caption(f"🇹🇷 {pf_ticker}")
    c3, c4 = st.columns(2)
    with c3: pf_qty  = st.number_input("Adet",    min_value=1,   value=10,  step=1)
    with c4: pf_cost = st.number_input("Maliyet", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    if st.button("Portföye Ekle", use_container_width=True):
        if pf_ticker and not any(p["ticker"]==pf_ticker for p in st.session_state.portfolio):
            st.session_state.portfolio.append({"ticker":pf_ticker,"qty":pf_qty,"cost":pf_cost})
            st.success(f"✓ {pf_ticker} eklendi")
        elif pf_ticker:
            st.warning("Zaten portföyde!")

    st.divider()
    st.markdown("#### 🔔 Fiyat Alarmı")
    _alrm_raw = st.text_input("Sembol", key="alrm_t", placeholder="TSLA / GARAN").upper()
    alrm_ticker = resolve_ticker(_alrm_raw)
    c5, c6 = st.columns(2)
    with c5: alarm_price = st.number_input("Hedef",  min_value=0.0, value=100.0, step=1.0)
    with c6: alarm_type  = st.selectbox("Tip", ["Üstüne çık","Altına in"])
    alarm_email = st.text_input("📧 Bildirim E-postası", placeholder="ornek@mail.com", key="alrm_email")
    if st.button("Alarm Ekle", use_container_width=True):
        if alrm_ticker:
            st.session_state.alerts.append({
                "ticker": alrm_ticker,
                "price":  alarm_price,
                "type":   alarm_type,
                "email":  alarm_email.strip(),
                "fired":  False
            })
            st.success("✓ Alarm eklendi")

# ─── ANA İÇERİK ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 Grafik & Sinyaller","🤖 Groq AI Analiz","💼 Portföy","🔔 Alarmlar"])

# ══ TAB 1: GRAFİK ══════════════════════════════════════════════════════════════
with tab1:
    if not ticker_input:
        st.info("Sol menüden bir sembol girin.")
    else:
        with st.spinner(f"⏳ {ticker_input} yükleniyor..."):
            df   = get_stock_data(ticker_input, period, interval)
            info = get_ticker_info(ticker_input)

        if df.empty:
            st.error("❌ Veri bulunamadı. Sembolü kontrol edin. (Örn: AAPL, THYAO, GARAN, BTC-USD)")
        else:
            df = calculate_indicators(df)
            signals  = generate_signals(df)
            al, sat, neutral, score = compute_score(signals)

            last_close = float(df["Close"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2]) if len(df)>1 else last_close
            daily_chg  = (last_close - prev_close) / prev_close * 100
            arrow      = "▲" if daily_chg >= 0 else "▼"
            chg_color  = "#34d399" if daily_chg >= 0 else "#f87171"
            score_color = "#34d399" if score>20 else ("#f87171" if score<-20 else "#f59e0b")

            company = info.get("longName", ticker_input)
            st.markdown(f"""
            <div style="display:flex;flex-wrap:wrap;align-items:baseline;gap:14px;margin-bottom:14px">
              <span style="font-family:'Space Mono';font-size:21px;font-weight:700;color:#e0e6f0">{company}</span>
              <span style="font-family:'Space Mono';font-size:19px;color:{chg_color};font-weight:700">{last_close:.2f}</span>
              <span style="font-family:'Space Mono';font-size:14px;color:{chg_color}">{arrow} {daily_chg:+.2f}%</span>
              <span style="font-size:11px;color:#4b5a75;background:#0d1225;border:1px solid #1e2a45;border-radius:6px;padding:2px 8px">{info.get('currency','USD')} · {info.get('exchange','')}</span>
              <span style="font-family:'Space Mono';font-size:12px;color:{score_color};background:#0d1225;border:1px solid {score_color}33;border-radius:6px;padding:3px 10px">⚡ Skor: {score:+.0f}</span>
            </div>
            """, unsafe_allow_html=True)

            c1,c2,c3,c4,c5,c6 = st.columns(6)
            c1.metric("RSI (14)",  f"{float(df['RSI'].iloc[-1]):.1f}")
            c2.metric("ADX",       f"{float(df['ADX'].iloc[-1]):.1f}")
            c3.metric("MFI",       f"{float(df['MFI'].iloc[-1]):.1f}")
            c4.metric("ATR %",     f"{float(df['ATR_pct'].iloc[-1]):.2f}%")
            c5.metric("52H Yüksek",f"{info.get('fiftyTwoWeekHigh','—')}")
            c6.metric("Beta",      f"{info.get('beta','—')}")

            st.plotly_chart(build_chart(df, ticker_input, selected_inds),
                            use_container_width=True, config={"displayModeBar":True})

            # Sinyal kartları (6'lı ızgara)
            st.markdown("### ⚡ İndikatör Sinyalleri")
            sig_items = list(signals.items())
            for row_i in range(0, len(sig_items), 6):
                chunk = sig_items[row_i:row_i+6]
                cols  = st.columns(len(chunk))
                for ci, (ind, (sig, desc)) in enumerate(chunk):
                    badge = "signal-buy" if sig=="AL" else ("signal-sell" if sig=="SAT" else "signal-neutral")
                    cols[ci].markdown(f"""
                    <div class="ind-card">
                      <div class="ind-label">{ind}</div>
                      <span class="{badge}">{sig}</span>
                      <div style="color:#4b5a75;font-size:10px;margin-top:5px;line-height:1.4">{desc}</div>
                    </div>""", unsafe_allow_html=True)

            # Skor barı
            al_pct  = al  / len(signals) * 100
            sat_pct = sat / len(signals) * 100
            neu_pct = (len(signals)-al-sat) / len(signals) * 100
            st.markdown(f"""
            <div style="margin:14px 0 6px;display:flex;align-items:center;gap:14px">
              <span style="color:#6b7a99;font-size:12px">Sinyal Dağılımı:</span>
              <span style="color:#34d399;font-family:Space Mono;font-size:13px">● AL: {al}</span>
              <span style="color:#f87171;font-family:Space Mono;font-size:13px">● SAT: {sat}</span>
              <span style="color:#a8a29e;font-family:Space Mono;font-size:13px">● NÖTR: {neutral}</span>
              <span style="color:{score_color};font-family:Space Mono;font-size:13px">Skor: {score:+.0f}/100</span>
            </div>
            <div style="height:7px;background:#1e2a45;border-radius:4px;overflow:hidden;display:flex">
              <div style="width:{al_pct:.0f}%;background:linear-gradient(90deg,#059669,#34d399)"></div>
              <div style="width:{neu_pct:.0f}%;background:#374151"></div>
              <div style="width:{sat_pct:.0f}%;background:linear-gradient(90deg,#f87171,#dc2626)"></div>
            </div>
            """, unsafe_allow_html=True)

            # Detay tablosu
            with st.expander("📋 Tüm İndikatör Değerleri (Genişlet)"):
                last_row = df.iloc[-1]
                table_data = {
                    "Grup": ["Momentum"]*5 + ["Trend"]*7 + ["Volatilite"]*3 + ["Hacim"]*3 + ["Diğer"]*6,
                    "İndikatör": [
                        "RSI(14)","MACD","MACD Hist","Stoch K","Stoch D",
                        "EMA20","EMA50","EMA200","SMA20","SMA50","ADX","PSAR",
                        "BB Üst","BB Orta","ATR%",
                        "OBV","MFI","CMF",
                        "Williams%R","CCI","ROC(10)","VWAP","Donchian H","Donchian L"
                    ],
                    "Değer": [
                        f"{float(last_row.get('RSI',0)):.2f}",
                        f"{float(last_row.get('MACD',0)):.4f}",
                        f"{float(last_row.get('MACD_Hist',0)):.4f}",
                        f"{float(last_row.get('Stoch_K',0)):.1f}",
                        f"{float(last_row.get('Stoch_D',0)):.1f}",
                        f"{float(last_row.get('EMA_20',0)):.2f}",
                        f"{float(last_row.get('EMA_50',0)):.2f}",
                        f"{float(last_row.get('EMA_200',0)):.2f}",
                        f"{float(last_row.get('SMA_20',0)):.2f}",
                        f"{float(last_row.get('SMA_50',0)):.2f}",
                        f"{float(last_row.get('ADX',0)):.1f}",
                        f"{float(last_row.get('PSAR',0)):.2f}",
                        f"{float(last_row.get('BB_Upper',0)):.2f}",
                        f"{float(last_row.get('BB_Mid',0)):.2f}",
                        f"{float(last_row.get('ATR_pct',0)):.2f}%",
                        f"{float(last_row.get('OBV',0)):,.0f}",
                        f"{float(last_row.get('MFI',0)):.1f}",
                        f"{float(last_row.get('CMF',0)):.3f}",
                        f"{float(last_row.get('WilliamsR',0)):.1f}",
                        f"{float(last_row.get('CCI',0)):.1f}",
                        f"{float(last_row.get('ROC_10',0)):.1f}%",
                        f"{float(last_row.get('VWAP',0)):.2f}",
                        f"{float(last_row.get('Donchian_High',0)):.2f}",
                        f"{float(last_row.get('Donchian_Low',0)):.2f}",
                    ]
                }
                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

# ══ TAB 2: AI ANALİZ ═══════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="gemini-badge">⚡ Powered by Groq · Llama 3.3 70B</div>', unsafe_allow_html=True)
    st.markdown("### 🤖 Yapay Zeka Teknik Analiz")

    ai_ticker_raw = st.text_input("Analiz Edilecek Sembol", value=ticker_input,
                               placeholder="AAPL, THYAO, BTC-USD...").upper().strip()
    ai_ticker = resolve_ticker(ai_ticker_raw)
    c_b, c_c = st.columns([1, 1])
    with c_b:
        ai_period = st.selectbox("Dönem", ["1mo","3mo","6mo","1y"], index=1, key="ai_period")
    with c_c:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("🔍 Analiz Et", use_container_width=True)

    if analyze_btn and ai_ticker:
        with st.spinner("🤖 Groq Llama 3.3 analiz yapıyor..."):
            try:
                df_ai = get_stock_data(ai_ticker, ai_period, "1d")
                if df_ai.empty:
                    st.error("Veri alınamadı.")
                else:
                    df_ai   = calculate_indicators(df_ai)
                    sigs_ai = generate_signals(df_ai)
                    al_ai, sat_ai, neu_ai, score_ai = compute_score(sigs_ai)
                    info_ai = get_ticker_info(ai_ticker)
                    result  = ai_analyze_groq(ai_ticker, df_ai, info_ai, sigs_ai,
                                              al_ai, sat_ai, neu_ai, score_ai,
                                              st.session_state.groq_key)
                    st.markdown(f'<div class="ai-response">{result}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"AI hatası: {e}")

    st.markdown("---")
    st.markdown("### 💬 Serbest Borsa Sorusu")
    custom_q = st.text_area("", placeholder="Örn: THYAO'da golden cross oluştu mu? RSI ve MACD birlikte AL sinyali veriyor mu? Bollinger sıkışması var mı?", height=90, label_visibility="collapsed")
    if st.button("Gönder 🚀") and custom_q:
        with st.spinner("Yanıt üretiliyor..."):
            try:
                client = Groq(api_key=st.session_state.groq_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Sen uzman bir borsa analisti ve teknik analiz uzmanısın. Türkçe, net ve somut yanıt ver. Her zaman 'yatırım tavsiyesi değildir' notunu ekle."},
                        {"role": "user",   "content": custom_q}
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                )
                resp_text = response.choices[0].message.content
                st.markdown(f'<div class="ai-response">{resp_text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Hata: {e}")

# ══ TAB 3: PORTFÖY ═════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 💼 Portföy Takibi")

    if not st.session_state.portfolio:
        st.info("Henüz portföyde hisse yok. Sol menüden ekleyin.")
    else:
        rows = []
        total_cost = total_value = 0.0

        for item in st.session_state.portfolio:
            try:
                d = get_stock_data(item["ticker"], "5d", "1d")
                if not d.empty:
                    price = float(d["Close"].iloc[-1])
                    prev  = float(d["Close"].iloc[-2]) if len(d)>1 else price
                    chg   = (price-prev)/prev*100
                    cost  = item["cost"] if item["cost"]>0 else price
                    val   = price * item["qty"]
                    pl    = (price-cost) * item["qty"]
                    pl_p  = (price-cost)/cost*100 if cost>0 else 0
                    total_cost  += cost * item["qty"]
                    total_value += val
                    rows.append({"ticker":item["ticker"],"qty":item["qty"],"cost":cost,
                                 "price":price,"chg":chg,"val":val,"pl":pl,"pl_p":pl_p})
            except:
                pass

        if rows:
            total_pl  = total_value - total_cost
            total_plp = total_pl / total_cost * 100 if total_cost > 0 else 0

            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Toplam Değer",   f"${total_value:,.2f}")
            m2.metric("Toplam Maliyet", f"${total_cost:,.2f}")
            m3.metric("Toplam K/Z",     f"${total_pl:+,.2f}", f"{total_plp:+.2f}%")
            m4.metric("Pozisyon Sayısı",f"{len(rows)}")

            st.markdown("---")
            # Tablo başlığı
            hcols = st.columns([1.4,0.7,0.9,0.9,1,1.1,1.1,1.1,0.4])
            for hc, lbl in zip(hcols,["Sembol","Adet","Maliyet","Fiyat","Günlük","Değer","K/Z","K/Z %",""]):
                hc.markdown(f"<span style='color:#4b5a75;font-size:11px;text-transform:uppercase;letter-spacing:1px'>{lbl}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:4px 0;border-color:#1e2a45'>", unsafe_allow_html=True)

            for i, row in enumerate(rows):
                chg_c = "#34d399" if row["chg"]>=0 else "#f87171"
                pl_c  = "#34d399" if row["pl"]>=0 else "#f87171"
                cols  = st.columns([1.4,0.7,0.9,0.9,1,1.1,1.1,1.1,0.4])
                data  = [
                    f"<b>{row['ticker']}</b>",
                    str(row['qty']),
                    f"{row['cost']:.2f}",
                    f"{row['price']:.2f}",
                    f"<span style='color:{chg_c}'>{row['chg']:+.2f}%</span>",
                    f"{row['val']:,.2f}",
                    f"<span style='color:{pl_c}'>{row['pl']:+,.2f}</span>",
                    f"<span style='color:{pl_c}'>{row['pl_p']:+.2f}%</span>",
                ]
                for ci, v in enumerate(data):
                    cols[ci].markdown(f"<span style='font-family:Space Mono;font-size:13px'>{v}</span>", unsafe_allow_html=True)
                if cols[8].button("✕", key=f"del_{i}"):
                    st.session_state.portfolio.pop(i)
                    st.rerun()
                st.markdown("<hr style='margin:3px 0;border-color:#111827'>", unsafe_allow_html=True)

            # Pasta grafik
            if len(rows) > 1:
                palette = ["#3b82f6","#8b5cf6","#06b6d4","#34d399","#f59e0b","#f87171","#a78bfa","#67e8f9","#4ade80","#fca5a5"]
                fig_pie = go.Figure(go.Pie(
                    labels=[r["ticker"] for r in rows],
                    values=[r["val"] for r in rows],
                    hole=0.65, textfont_size=12,
                    marker=dict(colors=palette[:len(rows)], line=dict(color="#0a0e1a",width=2))
                ))
                fig_pie.add_annotation(text=f"<b>${total_value:,.0f}</b>",
                                       font=dict(size=15, color="#e0e6f0"), showarrow=False)
                fig_pie.update_layout(
                    paper_bgcolor="#0a0e1a", plot_bgcolor="#0a0e1a",
                    font=dict(color="#9ca3af"), height=300,
                    legend=dict(bgcolor="#0d1225",bordercolor="#1e2a45"),
                    margin=dict(l=0,r=0,t=30,b=0),
                    title=dict(text="Portföy Dağılımı", font=dict(color="#6b7a99",size=13))
                )
                st.plotly_chart(fig_pie, use_container_width=True)

# ══ TAB 4: ALARMLAR ════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🔔 Fiyat Alarmları")
    st.caption("Alarm tetiklendiğinde belirtilen e-posta adresine otomatik bildirim gönderilir.")

    if not st.session_state.alerts:
        st.info("Henüz alarm yok. Sol menüden ekleyin.")
    else:
        fired_list = []
        hcols = st.columns([1.2, 0.9, 0.9, 0.8, 1.4, 1.6, 0.4])
        for hc, lbl in zip(hcols, ["Sembol","Hedef","Güncel","Tür","Durum","E-posta",""]):
            hc.markdown(f"<span style='color:#4b5a75;font-size:11px;text-transform:uppercase;letter-spacing:1px'>{lbl}</span>",
                        unsafe_allow_html=True)
        st.markdown("<hr style='margin:4px 0;border-color:#1e2a45'>", unsafe_allow_html=True)

        for i, alarm in enumerate(st.session_state.alerts):
            try:
                d = get_stock_data(alarm["ticker"], "1d", "5m")
                current = float(d["Close"].iloc[-1]) if not d.empty else 0.0
                fired = (alarm["type"] == "Üstüne çık" and current >= alarm["price"]) or \
                        (alarm["type"] == "Altına in"  and current <= alarm["price"])
                dist  = (current - alarm["price"]) / alarm["price"] * 100

                # E-posta gönder (sadece ilk tetiklenişte)
                if fired and not alarm.get("fired", False) and alarm.get("email"):
                    ok, msg = send_alarm_email(
                        alarm["email"], alarm["ticker"],
                        alarm["type"], alarm["price"], current
                    )
                    st.session_state.alerts[i]["fired"] = True
                    if ok:
                        st.toast(f"📧 {alarm['ticker']} alarmı {alarm['email']} adresine gönderildi!", icon="✅")
                    else:
                        st.toast(f"E-posta gönderilemedi: {msg}", icon="⚠️")

                status_html = "🔥 <span style='color:#f59e0b;font-weight:700'>TETİKLENDİ</span>" if fired \
                              else f"⏳ <span style='color:#6b7a99'>Bekliyor ({dist:+.1f}%)</span>"

                cols = st.columns([1.2, 0.9, 0.9, 0.8, 1.4, 1.6, 0.4])
                cols[0].markdown(f"<b style='font-family:Space Mono;color:#e0e6f0'>{alarm['ticker']}</b>", unsafe_allow_html=True)
                cols[1].markdown(f"<span style='font-family:Space Mono;color:#f59e0b'>{alarm['price']:.2f}</span>", unsafe_allow_html=True)
                cols[2].markdown(f"<span style='font-family:Space Mono;color:#e0e6f0'>{current:.2f}</span>", unsafe_allow_html=True)
                cols[3].markdown(f"<span style='font-size:11px;color:#9ca3af'>{alarm['type']}</span>", unsafe_allow_html=True)
                cols[4].markdown(status_html, unsafe_allow_html=True)
                email_disp = alarm.get("email","—")
                email_short = email_disp[:18] + "…" if len(email_disp) > 18 else email_disp
                cols[5].markdown(f"<span style='font-size:11px;color:#4b5a75'>{'📧 ' + email_short if email_disp != '—' else '—'}</span>", unsafe_allow_html=True)

                if cols[6].button("✕", key=f"adel_{i}"):
                    st.session_state.alerts.pop(i)
                    st.rerun()

                if fired:
                    fired_list.append(f"{alarm['ticker']} → {alarm['type']} {alarm['price']:.2f} (Güncel: {current:.2f})")

                st.markdown("<hr style='margin:4px 0;border-color:#111827'>", unsafe_allow_html=True)
            except:
                pass

        if fired_list:
            st.markdown("---")
            for msg in fired_list:
                st.warning(f"🔔 ALARM: {msg}", icon="⚠️")

# ─── YASAL UYARI FOOTER ────────────────────────────────────────────────────────
st.markdown("""
<div style="
  margin-top: 48px;
  padding: 14px 20px;
  background: #0d1225;
  border-top: 1px solid #1e2a45;
  border-radius: 10px;
  text-align: center;
">
  <span style="color:#4b5a75; font-size:12px; letter-spacing:0.3px;">
    ⚠️ <strong style="color:#6b7a99">Yasal Uyarı:</strong>
    Bu platform yalnızca bilgilendirme ve eğitim amaçlıdır.
    Burada yer alan hiçbir içerik <strong style="color:#f59e0b">yatırım tavsiyesi değildir.</strong>
    Yatırım kararlarınızı vermeden önce lisanslı bir finansal danışmana başvurmanız tavsiye edilir.
    ARD Finans, kullanıcıların aldığı yatırım kararlarından sorumlu tutulamaz.
  </span>
  <br><br>
  <span style="color:#2d3f5e; font-size:11px;">© 2026 ARD Finans · Tüm hakları saklıdır</span>
</div>
""", unsafe_allow_html=True)
