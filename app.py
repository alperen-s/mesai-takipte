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
        
        /* Header alanını şeffaf yap ve tıklanabilirliği sağla */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 100000 !important;
        }
        
        /* Yan menü ikonunu/butonunu mobilde görünür yap */
        [data-testid="stSidebarNavSeparator"],
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            z-index: 100001 !important;
        }
        
        /* Ekran üst boşluğu */
        .main .block-container {
            padding-top: 3rem !important;
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

# 1. YAN MENÜ İÇERİĞİ (Streamlit menü butonunu bu blok sayesinde oluşturur)
with st.sidebar:
    st.header("📋 Menü")
    st.markdown("---")
    # Sayfalar arası geçiş veya giriş menüsü elemanları buraya gelecek
    st.page_link("app.py", label="Ana Sayfa", icon="🏠")

# 2. ANA SAYFA İÇERİĞİ
st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")

st.info("👉 Lütfen sol taraftaki menüden veya aşağıdaki formdan giriş yapınız.")
