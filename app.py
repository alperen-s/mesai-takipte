import streamlit as st

# --- 1. VERİ YAPISINI GÜNCELLEME (Örnek Veri) ---
# Gerçek uygulamanızda bu veriler veritabanından veya CSV'den gelebilir.
# Buradaki temel değişiklik, bir sözlük (dictionary) yapısı kullanmaktır.
personel_birim_map = {
    "Alperen Yücedağ": "AFSÜ Kafe",
    "Ahmet Taner": "Sağlık Kafe",
    "Duru Turşu": "Sağlık Kafe",
    "Enes Şenel": "Tıp Fakültesi Kafe",
    "Mehmet Murat": "AFSÜ Kafe",
    "Sinem Alçı": "AFSÜ Kafe",
    "Tarık Mengüç": "Sağlık Kafe"
}

# --- SİDEBAR (SOL MENÜ) AYARLARI ---
with st.sidebar:
    st.header("🔑 Kullanıcı Giriş Paneli")
    
    # Giriş Türü Seçimi
    giris_turu = st.radio(
        "Giriş Türünüzü Seçiniz:",
        ["Personel", "Birim Sorumlusu", "İşletme Müdürü"]
    )
    
    st.markdown("---") # Ayırıcı çizgi
    
    # Personel Giriş Bölümü
    if giris_turu == "Personel":
        st.subheader("👤 Personel Girişi")
        
        # --- 2. SİDEBAR MANTIĞINI DEĞİŞTİRME ---
        # Selectbox, sözlüğün anahtarlarını (isimleri) gösterir.
        secilen_personel = st.selectbox(
            "Adınızı Seçiniz:",
            options=list(personel_birim_map.keys()), # İsim listesi
            index=0, # Varsayılan olarak ilk ismi seç
            help="Listeden isminizi seçin."
        )
        
        # --- 3. BİRİM BİLGİSINI ALMA VE OTOMATİK ALANI EKLEME ---
        # Seçilen isme karşılık gelen birimi sözlükten çekiyoruz.
        # Eğer sözlükte yoksa varsayılan olarak "-" göster.
        ait_oldugu_birim = personel_birim_map.get(secilen_personel, "-")
        
        # Otomatik dolan ama değiştirilemeyen birim alanı
        st.text_input(
            "Bağlı Olduğunuz Birim", 
            value=ait_oldugu_birim, 
            disabled=True, # Kullanıcı bu alanı değiştiremez
            help="Bu alan isminize göre otomatik dolar."
        )
        
        # Şifre Alanı
        st.text_input("Şifreniz", type="password")
        
        # Giriş Butonu
        if st.button("Personel Girişi Yap", use_container_width=True):
            st.success(f"{secilen_personel} ({ait_oldugu_birim}) olarak giriş yapılıyor...")
            # Burada giriş doğrulama mantığınız çalışır.

# --- ANA SAYFA İÇERİĞİ ---
st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
# ... ana sayfanın geri kalanı
