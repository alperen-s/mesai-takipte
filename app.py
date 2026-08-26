import streamlit as st

st.set_page_config(
    page_title="AFSÜ Personel Takip",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="expanded"  # Mobilde menünün açık gelmesini sağlar
)

st.markdown("""
    <style>
        /* Alt bilgi ve sağ üstteki Streamlit menüsünü gizle */
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        
        /* Sol üstteki Yan Menü (Sidebar) Açma/Kapama Butonunu Göster */
        [data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 99999;
        }
        
        /* Ekran üst boşluğunu hizala */
        .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Buton ve Form stilleri */
        .stButton > button {
            width: 100% !important;
            height: 3.2rem !important;
            font-size: 1.1rem !important;
            border-radius: 10px !important;
        }
        
        div[data-testid="stForm"] {
            border-radius: 12px;
            padding: 1.2rem;
        }
    </style>
""", unsafe_allow_html=True)

# Ana sayfa içeriği
st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")

st.info("👉 Lütfen sol taraftaki menüden veya aşağıdaki formdan giriş yapınız.")
