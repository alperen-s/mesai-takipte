import streamlit as st

# 1. LOGO ADRESİ
# İstediğin logonun doğrudan internet bağlantısını (URL) buraya yazabilirsin
LOGO_URL = "https://isletme.afsu.edu.tr/wp-content/uploads/sites/69/2026/08/logo-4.png"

st.set_page_config(
    page_title="AFSÜ Personel Takip",
    page_icon=LOGO_URL,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. PWA Meta Etiketleri (HTML Enjeksiyonu)
st.markdown(
    '<link rel="apple-touch-icon" sizes="180x180" href="' + LOGO_URL + '">'
    '<link rel="icon" type="image/png" href="' + LOGO_URL + '">'
    '<link rel="shortcut icon" href="' + LOGO_URL + '">',
    unsafe_allow_html=True
)

# 3. Mobil Stiller ve Arayüz CSS (f-string kaldırıldı, parantez hatası vermez)
st.markdown("""
    <style>
        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 100000 !important;
        }
        
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            z-index: 100001 !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
        }
        
        .main .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 2rem !important;
        }
        
        .stButton > button {
            width: 100% !important;
            height: 3.2rem !important;
            font-size: 1.1rem !important;
            border-radius: 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 4. YAN MENÜ İÇERİĞİ
with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.header("📋 Menü")
    st.write("Hoş geldiniz!")
    st.markdown("---")

# 5. ANA SAYFA İÇERİĞİ
st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")

st.info("👉 Sol üstteki menü butonuna basarak yan menüyü açabilirsiniz.", icon="ℹ️")
