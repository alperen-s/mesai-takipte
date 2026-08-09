import streamlit as st

# --- 1. SESSION STATE BAŞLANGIÇ AYARLARI ---
# Uygulama ilk açıldığında giriş yapılmadı olarak işaretle
if 'giris_basarili' not in st.session_state:
    st.session_state['giris_basarili'] = False
if 'kullanici_adi' not in st.session_state:
    st.session_state['kullanici_adi'] = ""
if 'kullanici_birimi' not in st.session_state:
    st.session_state['kullanici_birimi'] = ""

# Örnek Veri (Önceki adımda oluşturduğumuz harita)
personel_birim_map = {
    "Alperen Yücedağ": "AFSÜ Kafe",
    "Ahmet Taner": "Sağlık Kafe",
    "Duru Turşu": "Sağlık Kafe"
}
# Örnek basit şifre
DOGRU_SIFRE = "1234" 

# --- 2. ANA MANTIK: GİRİŞ KONTROLÜ ---
# Eğer giriş yapılmadıysa giriş ekranını göster
if not st.session_state['giris_basarili']:
    
    # --- SİDEBAR (SOL MENÜ) GİRİŞ EKRANI ---
    with st.sidebar:
        st.header("🔑 Kullanıcı Giriş Paneli")
        st.subheader("👤 Personel Girişi")
        
        # 1. İsim Seçimi
        secilen_personel = st.selectbox(
            "Adınızı Seçiniz:",
            options=list(personel_birim_map.keys()),
            index=0
        )
        
        # 2. Otomatik Birim (Değiştirilemez)
        ait_oldugu_birim = personel_birim_map.get(secilen_personel, "-")
        st.text_input("Bağlı Olduğunuz Birim", value=ait_oldugu_birim, disabled=True)
        
        # 3. Şifre Girişi
        girilen_sifre = st.text_input("Şifreniz", type="password")
        
        # 4. Giriş Butonu
        # NOT: use_container_width=True sadece görsel genişlik içindir, mantığı etkilemez.
        if st.button("Personel Girişi Yap", use_container_width=True):
            # --- 3. GİRİŞ KONTROLÜ VE SESSION STATE GÜNCELLEME ---
            if girilen_sifre == DOGRU_SIFRE:
                # Giriş başarılı, durumları güncelle
                st.session_state['giris_basarili'] = True
                st.session_state['kullanici_adi'] = secilen_personel
                st.session_state['kullanici_birimi'] = ait_oldugu_birim
                # *** KRİTİK ADIM ***
                # Sayfayı hemen yeni durumla (giriş yapılmış haliyle) yenilemeye zorla.
                st.rerun() 
            else:
                st.error("Hatalı şifre girdiniz!")

    # Giriş yapılmadığında ana ekranda görünecek mesaj
    st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
    st.info("👈 Lütfen sol taraftaki menüden giriş yapınız.")

# --- 4. GİRİŞ BAŞARILIYSA GÖSTERİLECEK EKRAN ---
else:
    # Giriş ekranını gizlemek için sidebar'ı temizle veya boş bırak
    st.sidebar.success(f"Oturum Açık: {st.session_state['kullanici_adi']}")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state['giris_basarili'] = False
        st.rerun()

    # --- ESAS PROGRAM EKRANI BURAYA GELECEK ---
    st.title(f"👋 Hoş Geldiniz, {st.session_state['kullanici_adi']}")
    st.subheader(f"Biriminiz: {st.session_state['kullanici_birimi']}")
    
    st.markdown("---")
    st.write("Personel Mesai Takip ve Yönetim Sistemi ana ekranı yüklendi.")
    # Mesai giriş formları, tablolar vb. buraya kodlanacak.
