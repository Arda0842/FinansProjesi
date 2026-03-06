import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import concurrent.futures
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime, timedelta

# TEFAS Kütüphanesi
try:
    from tefas import Crawler
except ImportError:
    st.error("Lütfen terminalde 'pip install tefas-crawler' komutunu çalıştırın.")

# ==========================================
# 0. SQL VERİTABANI VE GÜVENLİK
# ==========================================
def db_baglan():
    return sqlite3.connect('holding.db', check_same_thread=False)

def veri_tabani_kur():
    conn = db_baglan()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS portfoy (username TEXT, sembol TEXT, maliyet REAL, lot INTEGER)''')
    conn.commit()
    conn.close()

def sifre_hashle(sifre):
    return hashlib.sha256(str.encode(sifre)).hexdigest()

veri_tabani_kur()

# ==========================================
# 1. GİRİŞ VE KAYIT EKRANI
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if not st.session_state.logged_in:
    st.set_page_config(page_title=" Giriş", layout="centered")
    st.title("🔐  Güvenli Giriş")
    
    sekme_giris, sekme_kayit = st.tabs(["Giriş Yap", "Yeni Hesap Oluştur"])
    
    with sekme_giris:
        user = st.text_input("Kullanıcı Adı", key="login_user")
        pw = st.text_input("Şifre", type='password', key="login_pw")
        if st.button("Sisteme Gir"):
            conn = db_baglan()
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username=? AND password=?', (user, sifre_hashle(pw)))
            if c.fetchone():
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")
            conn.close()

    with sekme_kayit:
        new_user = st.text_input("Kullanıcı Adı Belirle", key="reg_user")
        new_pw = st.text_input("Şifre Belirle", type='password', key="reg_pw")
        if st.button("Kayıt Ol"):
            conn = db_baglan()
            c = conn.cursor()
            try:
                c.execute('INSERT INTO users VALUES (?,?)', (new_user, sifre_hashle(new_pw)))
                conn.commit()
                st.success("Hesap oluşturuldu! Giriş yapabilirsiniz.")
            except:
                st.error("Bu kullanıcı adı zaten kullanımda!")
            conn.close()

# ==========================================
# 2. ANA TERMİNAL (GİRİŞ YAPILDIKTAN SONRA)
# ==========================================
else:
    st.set_page_config(page_title="BIST Terminal", page_icon="💼", layout="wide")
    
    # --- YAN MENÜ (SIDEBAR) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2422/2422176.png", width=80)
        st.write(f"👤 **Hoş geldin, {st.session_state.user.upper()}**")
        if st.button("🚪 Oturumu Kapat"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("---")
        
        st.subheader("🛒 Portföye Ekle")
        s = st.text_input("Hisse veya Fon (örn: EREGL, HVI):").upper()
        s = s.replace("I", "I").replace("İ", "I").replace("ı", "I").replace("i", "I") 
        
        m = st.number_input("Maliyet:", min_value=0.0, format="%.4f")
        l = st.number_input("Adet / Lot:", min_value=1, step=1)
        
        if st.button("SQL'e Kaydet"):
            if s:
                if len(s) == 3:
                    st.toast(f"ℹ️ {s} TEFAS Fonu olarak algılandı.")
                elif not s.endswith(".IS"):
                    s += ".IS"
                    
                conn = db_baglan()
                c = conn.cursor()
                c.execute("INSERT INTO portfoy VALUES (?,?,?,?)", (st.session_state.user, s, m, l))
                conn.commit()
                conn.close()
                st.success(f"{s} portföye eklendi!")
                st.rerun()
        
        st.markdown("---")
        # YENİ ÖZELLİK: TEK TEK SİLME BÖLÜMÜ
        st.subheader("🗑️ Portföyden Çıkar")
        conn = db_baglan()
        df_mevcut = pd.read_sql_query("SELECT sembol FROM portfoy WHERE username=?", conn, params=(st.session_state.user,))
        conn.close()
        
        mevcut_semboller = df_mevcut['sembol'].tolist()
        
        if mevcut_semboller:
            silinecek = st.selectbox("Silmek istediğinizi seçin:", mevcut_semboller)
            if st.button("🗑️ Seçileni Sil"):
                conn = db_baglan()
                c = conn.cursor()
                # Sadece seçilen sembolü o kullanıcıdan siler
                c.execute("DELETE FROM portfoy WHERE username=? AND sembol=?", (st.session_state.user, silinecek))
                conn.commit()
                conn.close()
                st.warning(f"{silinecek} portföyden silindi!")
                st.rerun()
        else:
            st.info("Portföyünüz şu an boş.")

    # --- ANA BAŞLIK VE SEKMELER ---
    st.title(f"🚀 BIST Yönetim Terminali")
    sekme_grafik, sekme_tarayici, sekme_portfoy = st.tabs(["📈 Analiz & Grafik", "⚡ Balina Avcısı", "💼 SQL Portföyüm"])

    # ------------------------------------------
    # SEKME 1: PROFESYONEL GRAFİK VE ANALİZ
    # ------------------------------------------
    with sekme_grafik:
        aranan = st.text_input("Grafiğini görmek istediğin hisseyi yaz (Örn: ASELS):", placeholder="Sembol gir...").upper()
        if aranan:
            if len(aranan) == 3:
                st.warning("📉 TEFAS Fonları (HVI, MAC vb.) borsa gibi saniyelik mum grafikleri üretmediği için buradan çizdirilemez. Lütfen fonunuzu Portföy sekmesinden takip edin.")
            else:
                if not aranan.endswith(".IS"): aranan += ".IS"
                    
                try:
                    with st.spinner(f'{aranan} yükleniyor...'):
                        df = yf.Ticker(aranan).history(period="120d")
                        if not df.empty:
                            df['SMA20'] = ta.sma(df['Close'], length=20)
                            df['SMA50'] = ta.sma(df['Close'], length=50)
                            df['RSI'] = ta.rsi(df['Close'], length=14)
                            macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
                            df = df.join(macd)
                            
                            anlik_fiyat = df['Close'].iloc[-1]
                            degisim = ((anlik_fiyat - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                            
                            k1, k2, k3, k4 = st.columns(4)
                            k1.metric("🎯 Kapanış", f"{anlik_fiyat:.2f} TL", f"%{degisim:.2f}")
                            k2.metric("📊 Hacim", f"{int(df['Volume'].iloc[-1]):,}".replace(",", "."))
                            k3.metric("📈 RSI (14)", f"{df['RSI'].iloc[-1]:.2f}")
                            macd_durum = "🟢 AL" if df['MACD_12_26_9'].iloc[-1] > df['MACDs_12_26_9'].iloc[-1] else "🔴 SAT"
                            k4.metric("📊 MACD Sinyali", macd_durum)
                            
                            df_grafik = df.tail(90) 
                            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.05)
                            
                            fig.add_trace(go.Candlestick(x=df_grafik.index, open=df_grafik['Open'], high=df_grafik['High'], low=df_grafik['Low'], close=df_grafik['Close'], name="Fiyat", increasing_line_color='#00ff00', decreasing_line_color='#ff0000'), row=1, col=1)
                            fig.add_trace(go.Scatter(x=df_grafik.index, y=df_grafik['SMA20'], line=dict(color='orange', width=2), name='SMA 20'), row=1, col=1)
                            fig.add_trace(go.Scatter(x=df_grafik.index, y=df_grafik['SMA50'], line=dict(color='#00bfff', width=2), name='SMA 50'), row=1, col=1)
                            fig.add_trace(go.Scatter(x=df_grafik.index, y=df_grafik['RSI'], line=dict(color='yellow', width=2)), row=2, col=1)
                            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1) 
                            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1) 
                            fig.add_trace(go.Scatter(x=df_grafik.index, y=df_grafik['MACD_12_26_9'], line=dict(color='cyan', width=2)), row=3, col=1)
                            fig.add_trace(go.Scatter(x=df_grafik.index, y=df_grafik['MACDs_12_26_9'], line=dict(color='magenta', width=2)), row=3, col=1)
                            fig.add_trace(go.Bar(x=df_grafik.index, y=df_grafik['MACDh_12_26_9'], marker_color='gray'), row=3, col=1)
                            
                            fig.update_layout(xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=20, b=20), height=700, template="plotly_dark", showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)
                        else: st.warning("Veri bulunamadı.")
                except: st.error("Hata oluştu.")

    # ------------------------------------------
    # SEKME 2: IŞIK HIZINDA BALİNA TARAYICI
    # ------------------------------------------
    with sekme_tarayici:
        st.info("💡 BIST 100 Hisseleri saniyeler içinde taranır (Multithreading Motoru).")
        
        HISSELER = [
            "AEFES.IS", "AGHOL.IS", "AKBNK.IS", "AKCNS.IS", "AKFGY.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", 
            "ALBRK.IS", "ALFAS.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BERA.IS", "BIMAS.IS", "BIOEN.IS", 
            "BOBET.IS", "BRSAN.IS", "BRYAT.IS", "BUCIM.IS", "CANTE.IS", "CCOLA.IS", "CIMSA.IS", "CWENE.IS", 
            "DOAS.IS", "DOHOL.IS", "ECILC.IS", "EGEEN.IS", "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS", 
            "EUPWR.IS", "EUREN.IS", "FROTO.IS", "GARAN.IS", "GENIL.IS", "GESAN.IS", "GUBRF.IS", "GWIND.IS", 
            "HALKB.IS", "HEKTS.IS", "IPEKE.IS", "ISCTR.IS", "ISDMR.IS", "ISGYO.IS", "ISMEN.IS", "IZENR.IS", 
            "KCAER.IS", "KCHOL.IS", "KLSER.IS", "KMPUR.IS", "KONTR.IS", "KONYA.IS", "KOZAA.IS", "KOZAL.IS", 
            "KRDMD.IS", "MAVI.IS", "MIATK.IS", "MGROS.IS", "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "PETKM.IS", 
            "PGSUS.IS", "QUAGR.IS", "SAHOL.IS", "SASA.IS", "SDTTR.IS", "SISE.IS", "SKBNK.IS", "SMRTG.IS", 
            "SOKM.IS", "TABGD.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS", "TOASO.IS", "TSKB.IS", 
            "TTKOM.IS", "TTRAK.IS", "TUKAS.IS", "TUPRS.IS", "ULKER.IS", "VAKBN.IS", "VESBE.IS", "VESTL.IS", 
            "YEOTK.IS", "YKBNK.IS", "YYLGD.IS", "ZOREN.IS", "AGROT.IS", "BINHO.IS", "REEDR.IS", "KAYSE.IS","QUAGR",
            "BOSSA.IS", "KORDS.IS", "GOLTS.IS", "EBEBK.IS"
        ]

        def hisse_analiz_et(sembol):
            try:
                df = yf.Ticker(sembol).history(period="5d", interval="15m")
                if df.empty or len(df) < 15: return None
                df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)
                s_hacim, o_hacim = float(df['Volume'].dropna().iloc[-1]), float(df['Volume'].dropna().tail(11).head(10).mean())
                fiyat, s_mfi = float(df['Close'].dropna().iloc[-1]), float(df['MFI'].dropna().iloc[-1])
                if s_hacim > (o_hacim * 1.5) and s_mfi > 70:
                    return {"sembol": sembol, "fiyat": fiyat, "hacim_oran": s_hacim / o_hacim, "mfi": s_mfi}
            except: pass
            return None

        if st.button("🚀 BIST 100 Işık Hızında Tara"):
            sutunlar = st.columns(3)
            b_sayisi = 0
            with st.spinner('Motorlar tam güçte! 100 hisse taranıyor...'):
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    sonuclar = list(executor.map(hisse_analiz_et, HISSELER))
                for s in sonuclar:
                    if s:
                        with sutunlar[b_sayisi % 3]:
                            with st.container(border=True):
                                st.success(f"🔥 **{s['sembol']}**")
                                st.metric("Fiyat", f"{s['fiyat']:.2f} TL")
                                st.write(f"📊 Hacim: **{s['hacim_oran']:.1f}x kat** | 🟢 MFI: **{s['mfi']:.1f}**")
                        b_sayisi += 1
            if b_sayisi == 0: st.info("Şu an piyasa sakin.")

    # ------------------------------------------
    # SEKME 3: SQL PORTFÖY YÖNETİMİ (HİSSE + FON)
    # ------------------------------------------
    with sekme_portfoy:
        conn = db_baglan()
        df_p = pd.read_sql_query("SELECT sembol, maliyet, lot FROM portfoy WHERE username=?", conn, params=(st.session_state.user,))
        conn.close()

        if df_p.empty:
            st.info("Portföyünüz şu an boş. Sol menüden hisse veya fon ekleyebilirsiniz.")
        else:
            with st.spinner('Canlı piyasa ve TEFAS fiyatları çekiliyor...'):
                guncel_fiyatlar = []
                for sembol in df_p['sembol']:
                    # TEFAS FONU İSE (3 HARFLİ)
                    if len(sembol) == 3:
                        try:
                            crawler = Crawler()
                            bugun = datetime.now().strftime("%Y-%m-%d")
                            bas_tarih = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
                            
                            df_fon = crawler.fetch(start=bas_tarih, end=bugun, name=sembol, columns=["date", "price"])
                            
                            if not df_fon.empty:
                                df_fon['date'] = pd.to_datetime(df_fon['date'])
                                df_fon = df_fon.sort_values(by="date", ascending=True)
                                fiyat = float(df_fon['price'].iloc[-1])
                                guncel_fiyatlar.append(fiyat)
                                
                                son_tarih = df_fon['date'].iloc[-1].strftime("%d.%m.%Y")
                                st.toast(f"ℹ️ {sembol} Fonu için TEFAS tarihi: {son_tarih}")
                            else:
                                guncel_fiyatlar.append(0.0)
                        except:
                            guncel_fiyatlar.append(0.0)
                    
                    # BİST HİSSESİ İSE (.IS UZANTILI)
                    else:
                        try:
                            fiyat = yf.Ticker(sembol).history(period="1d")['Close'].iloc[-1]
                            guncel_fiyatlar.append(fiyat)
                        except:
                            guncel_fiyatlar.append(0.0)
                
                df_p['Anlık Fiyat'] = guncel_fiyatlar
                df_p['Toplam Maliyet'] = df_p['maliyet'] * df_p['lot']
                df_p['Güncel Değer'] = df_p['Anlık Fiyat'] * df_p['lot']
                df_p['Kâr / Zarar (TL)'] = df_p['Güncel Değer'] - df_p['Toplam Maliyet']
                
                df_p['Kâr / Zarar (%)'] = df_p.apply(
                    lambda row: (row['Kâr / Zarar (TL)'] / row['Toplam Maliyet'] * 100) if row['Toplam Maliyet'] > 0 else 0, axis=1
                )
                
                toplam_maliyet = df_p['Toplam Maliyet'].sum()
                toplam_deger = df_p['Güncel Değer'].sum()
                toplam_kar_zarar = toplam_deger - toplam_maliyet
                toplam_yuzde = (toplam_kar_zarar / toplam_maliyet) * 100 if toplam_maliyet > 0 else 0
                
                pk1, pk2, pk3 = st.columns(3)
                pk1.metric("💰 Toplam Maliyet", f"{toplam_maliyet:,.2f} TL".replace(",", "."))
                pk2.metric("💳 Güncel Değer", f"{toplam_deger:,.2f} TL".replace(",", "."))
                
                if toplam_kar_zarar > 0:
                    pk3.metric("🟢 Toplam Kâr / Zarar", f"+{toplam_kar_zarar:,.2f} TL".replace(",", "."), f"%{toplam_yuzde:.2f}")
                else:
                    pk3.metric("🔴 Toplam Kâr / Zarar", f"{toplam_kar_zarar:,.2f} TL".replace(",", "."), f"%{toplam_yuzde:.2f}")
                    
                st.markdown("---")
                
                col_tablo, col_grafik = st.columns([1.5, 1])
                with col_tablo:
                    st.write("📋 **Hisse ve Fon Detayları**")
                    st.dataframe(df_p.style.format({
                        "maliyet": "{:.4f} ₺", "Anlık Fiyat": "{:.4f} ₺", 
                        "Toplam Maliyet": "{:.2f} ₺", "Güncel Değer": "{:.2f} ₺",
                        "Kâr / Zarar (TL)": "{:.2f} ₺", "Kâr / Zarar (%)": "% {:.2f}"
                    }).map(lambda x: 'color: green' if x > 0 else ('color: red' if x < 0 else ''), subset=['Kâr / Zarar (TL)', 'Kâr / Zarar (%)']), 
                    use_container_width=True, hide_index=True)

                with col_grafik:
                    st.write("🍕**Portföy Dağılımı**")
                    if df_p['Güncel Değer'].sum() > 0:
                        renk_haritasi = {
                            row['sembol']: '#00cc96' if row['Kâr / Zarar (TL)'] >= 0 else '#ef553b' 
                            for index, row in df_p.iterrows()
                        }
                        
                        fig_pie = px.pie(df_p, values='Güncel Değer', names='sembol', hole=0.4, 
                                         color='sembol', color_discrete_map=renk_haritasi)
                        
                        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, template="plotly_dark")
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.info("Değer 0 olduğu için grafik çizilemiyor.")