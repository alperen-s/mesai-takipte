import streamlit as st

st.set_page_config(
    page_title="AFSÜ Personel Takip",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)
# 2. Mobil Ana Ekran İkonu (PWA Meta Tag)
# PNG logonun doğrudan erişilebilir web URL'sini apple-touch-icon'a ekliyoruz
LOGO_URL = "https://isletme.afsu.edu.tr/logo.png"  # Kendi logonun web adresini yazabilirsin

st.markdown(f"""
    <head>
        <!-- Mobil Ana Ekran Uygulama İkonu -->
        <link rel="apple-touch-icon" href="{LOGO_URL}">
        <link rel="shortcut icon" href="{LOGO_URL}">
    </head>
    <style>
        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
        
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
            z-index: 100000 !important;
        }
        
        [data-testid="collapsedControl"] {{
            display: flex !important;
            visibility: visible !important;
            z-index: 100001 !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
        }
        
        .main .block-container {{
            padding-top: 3.5rem !important;
            padding-bottom: 2rem !important;
        }
        
        .stButton > button {{
            width: 100% !important;
            height: 3.2rem !important;
            font-size: 1.1rem !important;
            border-radius: 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    # Yan menünün en üstüne de kurumsal logoyu koyabilirsin
    st.image("logo.png", width=150)
    st.header("📋 Menü")
    st.write("Hoş geldiniz!")
    st.markdown("---")

st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")
# Mobil Menü ve Arayüz CSS Düzenlemeleri
st.markdown("""
    <style>
        /* Alt bilgi ve sağ üst varsayılan Streamlit menüsünü gizle */
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        
        /* Header alanını şeffaf yap */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 100000 !important;
        }
        
        /* Mobil sol açılır menü butonunu görünür yap */
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            z-index: 100001 !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
        }
        
        /* Ekran üst boşluğu */
        .main .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Buton Stilleri */
        .stButton > button {
            width: 100% !important;
            height: 3.2rem !important;
            font-size: 1.1rem !important;
            border-radius: 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 1. YAN MENÜ İÇERİĞİ
with st.sidebar:
    st.header("📋 Menü")
    st.write("Hoş geldiniz!")
    st.markdown("---")

# 2. ANA SAYFA İÇERİĞİ
st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")

st.info("👉 Sol üstteki menü butonuna basarak yan menüyü açabilirsiniz.", icon="ℹ️")
