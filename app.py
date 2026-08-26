import streamlit as st

# 1. Sayfa Yapılandırması (Dosyada SADECE BİR KEZ olmalı)
st.set_page_config(
    page_title="AFSÜ Personel Takip",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Mobil Stiller ve Görsel Düzenlemeler
st.markdown("""
    <style>
        /* Streamlit varsayılan üst/alt boşlukları ve menüleri gizle */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Ekranın en üstündeki gereksiz boşluğu azalt */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Butonları mobil dostu yap */
        .stButton > button {
            width: 100% !important;
            height: 3.2rem !important;
            font-size: 1.1rem !important;
            border-radius: 10px !important;
        }
        
        /* Form alanını düzenle */
        div[data-testid="stForm"] {
            border-radius: 12px;
            padding: 1.2rem;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Ana Sayfa İçeriği
st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")

st.info("👉 Lütfen sol taraftaki menüden veya aşağıdaki formdan giriş yapınız.")

# --- BURADAN SONRA KENDİ ESKİ MESAİ/GİRİŞ KODLARINI EKLEYEBİLİRSİN ---
