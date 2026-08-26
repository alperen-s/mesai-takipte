import streamlit as st
import streamlit.components.v1 as components

# Doğrudan erişilebilir tam URL (Görselin .png uzantılı olmasına dikkat edin)
LOGO_URL = "https://isletme.afsu.edu.tr/wp-content/uploads/sites/69/2026/08/logo-4.png"

st.set_page_config(
    page_title="AFSÜ Personel Takip",
    page_icon=LOGO_URL,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Safari ve iOS Ana Ekran İçin HTML Enjeksiyonu
pwa_html = f"""
    <script>
        // iOS Safari için Apple Touch Icon enjeksiyonu
        var link = document.createElement('link');
        link.rel = 'apple-touch-icon';
        link.href = '{LOGO_URL}';
        document.getElementsByTagName('head')[0].appendChild(link);
        
        var linkFavicon = document.createElement('link');
        linkFavicon.rel = 'icon';
        linkFavicon.href = '{LOGO_URL}';
        document.getElementsByTagName('head')[0].appendChild(linkFavicon);
    </script>
"""
components.html(pwa_html, height=0, width=0)

# Arayüz Stilleri
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

with st.sidebar:
    st.image(LOGO_URL, width=140)
    st.header("📋 Menü")
    st.write("Hoş geldiniz!")
    st.markdown("---")

st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")

st.info("👉 Sol üstteki menü butonuna basarak yan menüyü açabilirsiniz.", icon="ℹ️")
