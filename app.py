import streamlit as st

# Sayfa genişliği ayarı (Opsiyonel ama formlar için daha iyi görünür)
st.set_page_config(layout="wide")

# --- 1. SESSION STATE (OTURUM DURUMU) BAŞLANGIÇ AYARLARI ---
# Uygulama ilk açıldığında bu değişkenler tanımlanır.
# Amaç: Giriş yapılıp yapılmadığını ve kimin yaptığını hafızada tutmak.
if 'giris_basarili' not in st.session_state:
    st.session_state['giris_basarili'] = False
if 'kullanici_adi' not in st.session_state:
    st.session_state['kullanici_adi'] = ""
if 'kullanici_birimi' not in st.session_state:
    st.session_state['kullanici_birimi'] = ""

# --- 2. VERİ YAPISI (Personel - Birim Eşleştirmesi) ---
# Gerçek uygulamada veritabanından gelebilir.
personel_birim_map = {
    "Alperen Yücedağ": "AFSÜ Kafe",
    "Ahmet Taner": "Sağlık Kafe",
    "Duru Turşu": "Sağlık Kafe",
    "Enes Şenel": "Tıp Fakültesi Kafe",
    "Mehmet Murat": "AFSÜ Kafe",
    "Sinem Alçı": "AFSÜ Kafe",
    "Tarık Mengüç": "Sağlık Kafe"
}

# Örnek basit şifre (Gerçek uygulamada her personelin şifresi farklı ve veritabanında olmalı)
DOGRU_SIFRE = "1234"

# --- ANA BAŞLIK (Her zaman görünür) ---
st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.markdown("---")


# --- 3. ANA MANTIK: GİRİŞ KONTROLÜ ---

# EĞER GİRİŞ YAPILMADIYSA (Oturum kapalıysa)
if not st.session_state['giris_basarili']:
    
    # --- SİDEBAR (SOL MENÜ) AYARLARI ---
    with st.sidebar:
        st.header("🔑 Kullanıcı Giriş Paneli")
        
        # Giriş Türü Seçimi
        giris_turu = st.radio(
            "Giriş Türünüzü Seçiniz:",
            ["Personel", "Birim Sorumlusu", "İşletme Müdürü"]
        )
        
        st.markdown("---") # Ayırıcı çizgi
        
        # Sadece "Personel" seçiliyse giriş formunu göster
        if giris_turu == "Personel":
            st.subheader("👤 Personel Girişi")
            
            # Selectbox: İsim listesi
            secilen_personel = st.selectbox(
                "Adınızı Seçiniz:",
                options=list(personel_birim_map.keys()), 
                index=0, 
                help="Listeden isminizi seçin."
            )
            
            # Otomatik birim çekme
            ait_oldugu_birim = personel_birim_map.get(secilen_personel, "-")
            
            # Otomatik dolan değiştirilemez birim alanı
            st.text_input(
                "Bağlı Olduğunuz Birim", 
                value=ait_oldugu_birim, 
                disabled=True,
                help="Bu alan isminize göre otomatik dolar."
            )
            
            # Şifre Alanı
            girilen_sifre = st.text_input("Şifreniz", type="password")
            
            # Giriş Butonu
            if st.button("Personel Girişi Yap", use_container_width=True):
                # --- GİRİŞ DOĞRULAMA MANTIĞI ---
                if girilen_sifre == DOGRU_SIFRE:
                    # BAŞARILI: Oturum bilgilerini hafızaya (Session State) kaydet
                    st.session_state['giris_basarili'] = True
                    st.session_state['kullanici_adi'] = secilen_personel
                    st.session_state['kullanici_birimi'] = ait_oldugu_birim
                    st.sidebar.success("Giriş başarılı!")
                    # Sayfayı hemen yenileyerek ana içeriği göster
                    st.rerun()
                else:
                    # BAŞARISIZ: Hata mesajı göster
                    st.error("Hatalı şifre girdiniz. Lütfen tekrar deneyin.")
        
        elif giris_turu in ["Birim Sorumlusu", "İşletme Müdürü"]:
            st.info(f"{giris_turu} girişi henüz aktif değildir.")

    # Giriş yapılmadığında ana ekranda görünecek bilgilendirme
    st.subheader("Hoş Geldiniz")
    st.info("👈 İşlem yapmak için lütfen sol taraftaki panelden giriş yapınız.")


# EĞER GİRİŞ BAŞARILIYSA (Oturum açık ise)
else:
    # --- YENİ SİDEBAR İÇERİĞİ (Giriş yapıldıktan sonra) ---
    with st.sidebar:
        st.header("👤 Kullanıcı Paneli")
        st.success(f"Oturum Açık: {st.session_state['kullanici_adi']}")
        st.write(f"Birim: {st.session_state['kullanici_birimi']}")
        st.markdown("---")
        
        # Çıkış Butonu
        if st.button("Güvenli Çıkış", use_container_width=True):
            # Hafızadaki oturum bilgilerini sıfırla
            st.session_state['giris_basarili'] = False
            st.session_state['kullanici_adi'] = ""
            st.session_state['kullanici_birimi'] = ""
            # Sayfayı yenileyerek giriş ekranına dön
            st.rerun()

    # --- ANA SAYFA İÇERİĞİ (Giriş yapıldıktan sonra görünecek kısım) ---
    st.subheader(f"👋 Hoş Geldiniz, {st.session_state['kullanici_adi']}")
    
    # Buradan itibaren ana program kodları (formlar, tablolar vb.) yer alır.
    with st.expander("Mesai Giriş Formu", expanded=True):
        st.write("Biriminiz için mesai kaydı oluşturun.")
        st.date_input("Tarih")
        st.time_input("Giriş Saati")
        st.time_input("Çıkış Saati")
        st.button("Kaydet")
