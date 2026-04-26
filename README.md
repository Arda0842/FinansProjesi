# 📈 ARD FİNANS | AI Destekli Borsa Analiz ve Portföy Platformu

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ardfinanss8.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ARD Finans, yatırımcılar ve traderlar için geliştirilmiş; teknik analiz, yapay zeka (AI) tabanlı piyasa yorumları, makine öğrenmesi (ML) ile fiyat projeksiyonları ve detaylı portföy yönetimi sunan kapsamlı bir web uygulamasıdır.

### 🚀 Canlı Demo: [ardfinanss8.streamlit.app](https://ardfinanss8.streamlit.app/)

---

## ✨ Öne Çıkan Özellikler

* **📊 Kapsamlı Teknik Analiz:** Yahoo Finance (`yfinance`) entegrasyonu ile BIST, ABD Hisseleri, Kripto ve Döviz çiftleri için anlık veri çekimi. 25'ten fazla indikatör (RSI, MACD, Bollinger Bantları, ADX, VWAP vb.) ile otomatik "AL/SAT/NÖTR" sinyal skorlaması ve interaktif Plotly grafikleri.
* **🤖 Groq AI Entegrasyonu:** Llama 3 ve Mixtral gibi gelişmiş dil modelleri kullanılarak; teknik verilere dayalı otomatik, anlaşılır, Türkçe piyasa analiz raporları. Ayrıca 1 günlük, 1 haftalık ve 1 aylık konsensüs fiyat tahminleri.
* **📉 Makine Öğrenmesi (ML) ile Regresyon:** `scikit-learn` kullanılarak eğitilen 6 farklı regresyon modeli (Doğrusal, Polinom, Ridge, SVR, Random Forest) ile 22 iş gününü kapsayan gelecek fiyat projeksiyonu. Tarayıcı üzerinden anında eğitilip sonuç veren yerel modeller.
* **💼 Portföy Takibi:** Hisse, kripto, fon ve döviz yatırımlarının anlık değer, ortalama maliyet ve Kar/Zarar (P&L) takibi. Google Sheets entegrasyonu ile verilerin bulutta güvenle saklanması ve portföyün tarihsel büyüme grafiği.
* **🔔 Fiyat Alarmları:** Belirlenen fiyat hedeflerine ulaşıldığında anında tetiklenen otomatik e-posta (SMTP) bildirim sistemi.
* **🔐 Güvenli Kullanıcı Yönetimi:** Hesap oluşturma, şifreli oturum açma, benzersiz cüzdan ID'si (ARD-XXXX) oluşturma ve e-posta doğrulama kodu ile şifre sıfırlama özellikleri.

## 🛠️ Kullanılan Teknolojiler

* **Arayüz & Backend:** Python, Streamlit
* **Finansal Veri İşleme:** `yfinance`, Pandas, NumPy
* **Veri Görselleştirme:** Plotly (`plotly.graph_objects`)
* **Makine Öğrenmesi:** `scikit-learn` (LinearRegression, Ridge, SVR, RandomForest)
* **Yapay Zeka (LLM):** Groq API (Llama 3.3 70B, Gemma 2, Mixtral)
* **Veritabanı:** Google Sheets API (`gspread`, `google-auth`)
* **Bildirim Sistemi:** Python `smtplib`, `email.mime`
<img width="1904" height="737" alt="image" src="https://github.com/user-attachments/assets/5b3956e0-acb2-4398-b592-8e61f8b94f87" />

## 📂 Proje Yapısı

```text
├── .devcontainer/       # Geliştirme ortamı (Codespaces) yapılandırmaları
├── app.py               # Ana Streamlit uygulama kodu ve UI bileşenleri
├── requirements.txt     # Gerekli Python kütüphaneleri ve versiyonları
└── README.md            # Proje dokümantasyonu
