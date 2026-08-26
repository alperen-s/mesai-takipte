import streamlit as st

st.set_page_config(
    page_title="AFSÜ Personel Takip",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
