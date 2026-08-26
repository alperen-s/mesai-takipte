import streamlit as st

# 1. Tarayıcı Sekme İkonu
st.set_page_config(
    page_title="AFSÜ Personel Takip",
    page_icon="logo.png",  # Proje klasöründeki logonun adı
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Mobil Ana Ekran ve Uygulama İkonu URL'si
LOGO_URL = "https://isletme.afsu.edu.tr/favicon.ico"  # Kendi logonun web bağlantısını yazabilirsin

# CSS içerisindeki parantezler f-string için çift {{ }} yapıldı
st.markdown(f"""
    <head>
        <link rel="apple-touch-icon" href="{LOGO_URL}">
        <link rel="shortcut icon" href="{LOGO_URL}">
    </head>
    <style>
        footer {{ visibility: hidden; }}
        #MainMenu {{ visibility: hidden; }}
        
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
            z-index: 100000 !important;
        }}
        
        [data-testid="collapsedControl"] {{
            display: flex !important;
            visibility: visible !important;
            z-index: 100001 !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
        }}
        
        .main .block-container {{
            padding-top: 3.5rem !important;
            padding-bottom: 2rem !important;
        }}
        
        .stButton > button {{
            width: 100% !important;
            height: 3.2rem !important;
            font-size: 1.1rem !important;
            border-radius: 10px !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 3. YAN MENÜ İÇERİĞİ
with st.sidebar:
    st.header("📋 Menü")
    st.write("Hoş geldiniz!")
    st.markdown("---")

# 4. ANA SAYFA İÇERİĞİ
st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")

st.info("👉 Sol üstteki menü butonuna basarak yan menüyü açabilirsiniz.", icon="ℹ️")
