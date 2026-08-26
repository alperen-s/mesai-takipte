import streamlit as st

st.set_page_config(
    page_title="AFSÜ Personel Takip",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Temiz CSS Enjeksiyonu (iframe veya JS olmadan)
st.markdown("""
    <style>
        /* Streamlit varsayılan üst/alt boşlukları ve menüleri gizle */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Mobil görünüm için üst boşluğu sıfırla */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Butonları mobilde daha kullanışlı yap */
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
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="AFSÜ Personel Takip",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 1. PWA Meta Etiketlerini Gizli HTML Enjeksiyonu ile Ekleme
components.html(
    """
    <script>
        const metaViewport = document.createElement('meta');
        metaViewport.name = "viewport";
        metaViewport.content = "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no";
        document.getElementsByTagName('head')[0].appendChild(metaViewport);

        const metaApp = document.createElement('meta');
        metaApp.name = "apple-mobile-web-app-capable";
        metaApp.content = "yes";
        document.getElementsByTagName('head')[0].appendChild(metaApp);

        const metaTitle = document.createElement('meta');
        metaTitle.name = "apple-mobile-web-app-title";
        metaTitle.content = "AFSÜ Mesai";
        document.getElementsByTagName('head')[0].appendChild(metaTitle);

        const metaTheme = document.createElement('meta');
        metaTheme.name = "theme-color";
        metaTheme.content = "#193762";
        document.getElementsByTagName('head')[0].appendChild(metaTheme);
    </script>
    """,
    height=0,
    width=0
)

# 2. Sadece Görsel CSS Düzenlemeleri (Ekranda Kod Görünmez)
st.markdown("""
    <style>
        /* Streamlit üst ve alt bilgi alanlarını gizleme */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Butonları mobil dostu geniş yapma */
        .stButton > button {
            width: 100% !important;
            height: 3.2rem !important;
            font-size: 1.1rem !important;
            border-radius: 10px !important;
        }
        
        /* Form kutusunu düzenleme */
        div[data-testid="stForm"] {
            border-radius: 12px;
            padding: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)
