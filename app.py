from datetime import datetime, date
import io
import os
import sqlite3
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
import streamlit as st

# 1. STREAMLIT SAYFA YAPILANDIRMASI
st.set_page_config(
    page_title="AFSÜ İktisadi İşletme - Mesai Takip",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. MOBİL UYUM VE PWA DÜZENLEMELERİ (CSS & METAS)
st.markdown("""
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="AFSÜ Mesai">
        <meta name="theme-color" content="#193762">
    </head>
    <style>
        /* Alt bilgi ve Streamlit varsayılan menülerini gizle */
        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        
        /* Sol üst menü butonunun üstünü kapatan katmanları düzelt */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 100000 !important;
        }
        
        /* Sol açılır menü butonunu görünür kıl */
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            z-index: 100001 !important;
            top: 0.5rem !important;
            left: 0.5rem !important;
        }
        
        /* Mobil ekran iç boşluğu */
        .main .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Butonları mobilde dokunmatik dostu yap */
        .stButton > button {
            width: 100% !important;
            height: 3.2rem !important;
            font-size: 1.05rem !important;
            border-radius: 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

# ReportLab Türkçe Karakter Dönüştürücü
def tr_to_pdf_text(text):
    if not isinstance(text, str):
        return text
    subst = {
        "ı": "i", "İ": "I", "ğ": "g", "Ğ": "G",
        "Ş": "S", "ş": "s", "Ç": "C", "ç": "c",
        "Ö": "O", "ö": "o", "Ü": "U", "ü": "u",
    }
    for search, replace in subst.items():
        text = text.replace(search, replace)
    return text

PDF_FONT_REGULAR = "Helvetica"
PDF_FONT_BOLD = "Helvetica-Bold"

def hesapla_calisma_suresi(baslangic_str, bitis_str):
    try:
        if not baslangic_str or not bitis_str:
            return 0.0, "-"
        fmt = "%H:%M"
        t_bas = datetime.strptime(str(baslangic_str).strip(), fmt)
        t_bit = datetime.strptime(str(bitis_str).strip(), fmt)

        fark = t_bit - t_bas
        toplam_dakika = int(fark.total_seconds() / 60)

        if toplam_dakika < 0:
            return 0.0, "Geçersiz Saat"

        saat = toplam_dakika // 60
        dakika = toplam_dakika % 60

        sure_saat_float = round(toplam_dakika / 60, 2)
        sure_metin = f"{saat} sa {dakika} dk" if dakika > 0 else f"{saat} sa"

        return sure_saat_float, sure_metin
    except Exception:
        return 0.0, "-"

def init_db():
    conn = sqlite3.connect("mesai_takip.db", timeout=10)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS mesai_kayitlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personel_ad_soyad TEXT,
            tarih TEXT,
            birimi TEXT,
            mesai_baslangic TEXT,
            mola1_cikis TEXT,
            mola1_bitis TEXT,
            ogle_baslangic TEXT,
            ogle_bitis TEXT,
            mola2_cikis TEXT,
            mola2_bitis TEXT,
            mesai_bitis TEXT,
            fazla_mesai TEXT,
            calisma_suresi_saat REAL DEFAULT 0.0,
            calisma_suresi_metin TEXT DEFAULT '',
            birim_sorumlusu_onay INTEGER DEFAULT 0,
            isletme_muduru_onay INTEGER DEFAULT 0,
            UNIQUE(personel_ad_soyad, tarih)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS personeller (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_soyad TEXT UNIQUE,
            birim_adi TEXT DEFAULT '',
            is_birim_sorumlusu INTEGER DEFAULT 0,
            sifre TEXT DEFAULT '1111',
            durum TEXT DEFAULT 'Aktif'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS birimler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            birim_adi TEXT UNIQUE,
            birim_renk TEXT DEFAULT '#007bff'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS duzeltme_talepleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mesai_id INTEGER,
            personel_ad_soyad TEXT,
            tarih TEXT,
            birimi TEXT,
            mesai_baslangic TEXT,
            mola1_cikis TEXT,
            mola1_bitis TEXT,
            ogle_baslangic TEXT,
            ogle_bitis TEXT,
            mola2_cikis TEXT,
            mola2_bitis TEXT,
            mesai_bitis TEXT,
            fazla_mesai TEXT,
            calisma_suresi_saat REAL DEFAULT 0.0,
            calisma_suresi_metin TEXT DEFAULT '',
            durum TEXT DEFAULT 'Bekliyor'
        )
    """)

    try:
        c.execute("ALTER TABLE personeller ADD COLUMN durum TEXT DEFAULT 'Aktif'")
    except Exception:
        pass

    try:
        c.execute("ALTER TABLE birimler ADD COLUMN birim_renk TEXT DEFAULT '#007bff'")
    except Exception:
        pass

    try:
        c.execute("UPDATE personeller SET sifre = '1111' WHERE sifre IS NULL OR sifre = ''")
    except Exception:
        pass

    conn.commit()
    conn.close()

init_db()

def get_personeller_data(only_active=False):
    conn = sqlite3.connect("mesai_takip.db", timeout=10)
    c = conn.cursor()
    if only_active:
        c.execute("SELECT ad_soyad, birim_adi, is_birim_sorumlusu, sifre, durum FROM personeller WHERE durum = 'Aktif' ORDER BY ad_soyad ASC")
    else:
        c.execute("SELECT ad_soyad, birim_adi, is_birim_sorumlusu, sifre, durum FROM personeller ORDER BY ad_soyad ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_birimler_data():
    conn = sqlite3.connect("mesai_takip.db", timeout=10)
    c = conn.cursor()
    c.execute("SELECT birim_adi, birim_renk FROM birimler ORDER BY birim_adi ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_birim_renk_map():
    b_data = get_birimler_data()
    return {b[0]: (b[1] if b[1] else "#007bff") for b in b_data}

@st.dialog("📋 İşlem Özeti ve Onay Bilgisi")
def ozet_dialog(bilgiler, islem_turu_adi):
    st.success(f"✅ **{islem_turu_adi}** işleminiz başarıyla sisteme iletilmiştir.")
    st.write("Girdiğiniz / Düzelttiğiniz bilgiler şu şekildedir:")
    st.markdown(f"""
    * **Personel:** `{bilgiler['personel']}`
    * **Birim:** `{bilgiler['birim']}`
    * **Tarih:** `{bilgiler['tarih']}`
    * **Mesai Başlangıç - Bitiş:** `{bilgiler['baslangic']}` - `{bilgiler['bitis']}`
    * **Hesaplanan Günlük Çalışma:** **`{bilgiler['sure_metin']}`**
    * **1. Mola:** `{bilgiler['m1_c']}` - `{bilgiler['m1_b']}`
    * **Öğle Tatili:** `{bilgiler['o_c']}` - `{bilgiler['o_b']}`
    * **2. Mola:** `{bilgiler['m2_c']}` - `{bilgiler['m2_b']}`
    * **Fazla Mesai Durumu:** **{bilgiler['fazla_mesai']}**
    """)
    if st.button("Anladım / Kapat"):
        st.rerun()

def generate_pdf(df_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=15, leftMargin=15, topMargin=20, bottomMargin=20
    )
    elements = []
    styles = getSampleStyleSheet()

    cell_style = ParagraphStyle("CellOptionTR", fontName=PDF_FONT_REGULAR, fontSize=7.5, leading=9, alignment=1)
    header_style = ParagraphStyle("HeaderOptionTR", fontName=PDF_FONT_BOLD, fontSize=7.5, leading=9, alignment=1)
    title_style = ParagraphStyle("TitleOptionTR", fontName=PDF_FONT_BOLD, fontSize=12, leading=14, alignment=1)
    summary_style = ParagraphStyle("SummaryOptionTR", fontName=PDF_FONT_BOLD, fontSize=9, leading=11, alignment=2)

    elements.append(Paragraph(tr_to_pdf_text("Afyonkarahisar Saglik Bilimleri Universitesi Iktisadi Isletme Mudurlugu"), title_style))
    elements.append(Paragraph(tr_to_pdf_text("Personel Mesai Takip Cizelgesi"), title_style))
    elements.append(Paragraph("<br/><br/>", styles["Normal"]))

    table_data = [[
        Paragraph(tr_to_pdf_text("Tarih"), header_style),
        Paragraph(tr_to_pdf_text("Personel"), header_style),
        Paragraph(tr_to_pdf_text("Birimi"), header_style),
        Paragraph(tr_to_pdf_text("Mesai Başlangıç"), header_style),
        Paragraph(tr_to_pdf_text("1. Mola Çıkış"), header_style),
        Paragraph(tr_to_pdf_text("1. Mola Bitiş"), header_style),
        Paragraph(tr_to_pdf_text("Öğle Başlangıç"), header_style),
        Paragraph(tr_to_pdf_text("Öğle Bitiş"), header_style),
        Paragraph(tr_to_pdf_text("2. Mola Çıkış"), header_style),
        Paragraph(tr_to_pdf_text("2. Mola Bitiş"), header_style),
        Paragraph(tr_to_pdf_text("Mesai Bitiş"), header_style),
        Paragraph(tr_to_pdf_text("Çalışma Süresi"), header_style),
        Paragraph(tr_to_pdf_text("Fazla Mesai"), header_style),
        Paragraph(tr_to_pdf_text("İmza"), header_style),
    ]]

    toplam_saat_aylik = 0.0
    for idx, row in df_data.iterrows():
        s_saat, s_metin = hesapla_calisma_suresi(row["mesai_baslangic"], row["mesai_bitis"])
        toplam_saat_aylik += s_saat
        table_data.append([
            Paragraph(tr_to_pdf_text(str(row["tarih"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["personel_ad_soyad"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["birimi"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["mesai_baslangic"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["mola1_cikis"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["mola1_bitis"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["ogle_baslangic"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["ogle_bitis"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["mola2_cikis"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["mola2_bitis"])), cell_style),
            Paragraph(tr_to_pdf_text(str(row["mesai_bitis"])), cell_style),
            Paragraph(tr_to_pdf_text(str(s_metin)), cell_style),
            Paragraph(tr_to_pdf_text(str(row["fazla_mesai"])), cell_style),
            Paragraph("", cell_style),
        ])

    pdf_table = Table(table_data, repeatRows=1)
    pdf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(pdf_table)
    elements.append(Paragraph("<br/>", styles["Normal"]))
    elements.append(Paragraph(tr_to_pdf_text(f"Cizelge Donemi Toplam Calisma Suresi: {round(toplam_saat_aylik, 2)} Saat"), summary_style))
    elements.append(Paragraph("<br/><br/>", styles["Normal"]))

    onay_data = [
        [Paragraph(tr_to_pdf_text("<b>Personel/Birim Sorumlusu Onayı</b>"), header_style), Paragraph(tr_to_pdf_text("<b>İşletme Müdürü Onayı</b>"), header_style)],
        [Paragraph("<br/><br/>...........................<br/>Imza", cell_style), Paragraph("<br/><br/>...........................<br/>Imza", cell_style)],
    ]
    onay_table = Table(onay_data, colWidths=[350, 350])
    onay_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    elements.append(onay_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

YONETICI_SIFRESI = "1234"

if "auth_role" not in st.session_state:
    st.session_state["auth_role"] = None
if "auth_unit" not in st.session_state:
    st.session_state["auth_unit"] = None
if "auth_user_name" not in st.session_state:
    st.session_state["auth_user_name"] = ""
if "sub_tab_index" not in st.session_state:
    st.session_state["sub_tab_index"] = 0

personel_raw = get_personeller_data(only_active=False)
personel_dict = {
    row[0]: {"birim": row[1], "is_sorumlu": row[2], "sifre": row[3], "durum": row[4]}
    for row in personel_raw
}

active_personel_names = [p_name for p_name, data in personel_dict.items() if data["durum"] == "Aktif"]

# TEK MERKEZİ GİRİŞ PANELİ (SOL SIDEBAR)
with st.sidebar:
    st.header("🔑 Giriş Paneli")

    if st.session_state["auth_role"] is None:
        tum_giris_secenekleri = ["İşletme Müdürü"] + active_personel_names
        
        secilen_kullanici = st.selectbox(
            "Kullanıcı Adınızı Seçiniz:",
            options=tum_giris_secenekleri,
            index=None,
            placeholder="Listeden adınızı seçin...",
            key="merkezi_giris_select"
        )

        p_birim_auto = "-"
        if secilen_kullanici:
            if secilen_kullanici == "İşletme Müdürü":
                p_birim_auto = "Genel Yönetim"
            elif secilen_kullanici in personel_dict:
                p_birim_auto = personel_dict[secilen_kullanici]["birim"]

        st.text_input("Bağlı Olduğunuz Birim", value=p_birim_auto, disabled=True, key="side_merkezi_birim")
        pass_in = st.text_input("Şifreniz", type="password", key="side_merkezi_pass")

        if st.button("Giriş Yap", use_container_width=True):
            if not secilen_kullanici:
                st.error("Lütfen adınızı seçiniz!")
            else:
                if secilen_kullanici == "İşletme Müdürü":
                    if pass_in == YONETICI_SIFRESI:
                        st.session_state["auth_role"] = "MUDUR"
                        st.session_state["auth_unit"] = "ALL"
                        st.session_state["auth_user_name"] = "İşletme Müdürü"
                        st.session_state["sub_tab_index"] = 0
                        st.success("Müdür Girişi Başarılı!")
                        st.rerun()
                    else:
                        st.error("Hatalı Müdür Şifresi!")
                else:
                    dogru_pass = personel_dict[secilen_kullanici]["sifre"]
                    if pass_in == dogru_pass:
                        is_sorumlu = personel_dict[secilen_kullanici]["is_sorumlu"] == 1
                        st.session_state["auth_role"] = "SORUMLU" if is_sorumlu else "PERSONEL"
                        st.session_state["auth_unit"] = p_birim_auto
                        st.session_state["auth_user_name"] = secilen_kullanici
                        st.session_state["sub_tab_index"] = 0
                        st.success(f"Hoş geldiniz, {secilen_kullanici}")
                        st.rerun()
                    else:
                        st.error("Hatalı Şifre!")
    else:
        role_labels = {
            "PERSONEL": "Personel",
            "SORUMLU": f"Birim Sorumlusu ({st.session_state['auth_unit']})",
            "MUDUR": "İşletme Müdürü",
        }
        st.success(f"Oturum Açık:\n**{st.session_state['auth_user_name']}**")
        st.caption(f"Yetki: {role_labels.get(st.session_state['auth_role'])}")
        if st.button("Çıkış Yap / Oturumu Kapat", use_container_width=True):
            st.session_state["auth_role"] = None
            st.session_state["auth_unit"] = None
            st.session_state["auth_user_name"] = ""
            st.session_state["sub_tab_index"] = 0
            st.rerun()

st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")

if st.session_state["auth_role"] is None:
    st.info("👈 **Lütfen sağ tarafı görüntülemek için sol taraftaki menüden kullanıcı adınız ve şifrenizle giriş yapınız.**")

elif st.session_state["auth_role"] == "PERSONEL":
    st.success(f"👤 Hoş Geldiniz Sayın **{st.session_state['auth_user_name']}** ({st.session_state['auth_unit']})")

    islem_turu = st.radio(
        "İşlem Türünü Seçiniz:",
        ["Yeni Günlük Mesai Kaydı", "Hatalı Kayıt İçin Düzeltme Talebi Gönder", "🔑 Kendi Şifremi Değiştir"],
        horizontal=True
    )
    st.divider()

    p_ad_active = st.session_state["auth_user_name"]
    p_birim_active = st.session_state["auth_unit"]

    if islem_turu == "🔑 Kendi Şifremi Değiştir":
        st.subheader("🔑 Personel Şifre Değiştirme Ekranı")
        col_pass1, col_pass2 = st.columns(2)
        with col_pass1:
            st.write(f"**Personel:** `{p_ad_active}`")
            st.write(f"**Birim:** `{p_birim_active}`")
            p_eski_pass = st.text_input("Mevcut Şifreniz", type="password", key="p_eski_pass_key_user")
        with col_pass2:
            p_yeni_pass = st.text_input("Yeni Şifreniz", type="password", key="p_yeni_pass_key_user")
            p_yeni_pass2 = st.text_input("Yeni Şifreniz (Tekrar)", type="password", key="p_yeni_pass2_key_user")

        if st.button("Şifremi Güncelle"):
            dogru_mevcut = personel_dict[p_ad_active]["sifre"]
            if p_eski_pass != dogru_mevcut:
                st.error("Mevcut şifrenizi hatalı girdiniz!")
            elif not p_yeni_pass.strip():
                st.error("Yeni şifre boş bırakılamaz!")
            elif p_yeni_pass != p_yeni_pass2:
                st.error("Yeni şifreler birbiriyle uyuşmuyor!")
            else:
                conn = sqlite3.connect("mesai_takip.db", timeout=10)
                c = conn.cursor()
                c.execute("UPDATE personeller SET sifre = ? WHERE ad_soyad = ?", (p_yeni_pass.strip(), p_ad_active))
                conn.commit()
                conn.close()
                st.success("Şifreniz başarıyla güncellenmiştir!")
                st.rerun()

    else:
        with st.form("mesai_formu_user", clear_on_submit=True):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.write(f"**Personel:** `{p_ad_active}`")
                st.write(f"**Birimi:** `{p_birim_active}`")

            with col_p2:
                tarih = st.date_input("Tarih", date.today(), max_value=date.today())
                fazla_mesai = st.radio("Fazla Mesai", ["Yaptım", "Yapmadım"], horizontal=True, index=1)

            st.divider()
            st.subheader("⏰ Saat Bilgileri")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                mesai_baslangic = st.text_input("Mesai Başlangıç Saati", value="08:30")
                mola1_cikis = st.text_input("1. Mola Çıkış Saati", placeholder="10:30")
            with col2:
                mola1_bitis = st.text_input("1. Mola Bitiş Saati", placeholder="10:45")
                ogle_baslangic = st.text_input("Öğle Tatili Başlangıç", value="12:30")
            with col3:
                ogle_bitis = st.text_input("Öğle Tatili Bitiş", value="13:30")
                mola2_cikis = st.text_input("2. Mola Çıkış Saati", placeholder="14:00")
            with col4:
                mola2_bitis = st.text_input("2. Mola Bitiş Saati", placeholder="14:15")
                mesai_bitis = st.text_input("Mesai Bitiş Saati", value="17:30")

            btn_label = " Kaydet" if islem_turu == "Yeni Günlük Mesai Kaydı" else "📩 Düzeltme Talebi Gönder"
            submitted = st.form_submit_button(btn_label)

            if submitted:
                sure_saat, sure_metin = hesapla_calisma_suresi(mesai_baslangic, mesai_bitis)

                if sure_saat <= 9.0 and fazla_mesai == "Yaptım":
                    st.error(f"🛑 **GEÇERSİZ MESAİ TALEBİ:** Giriş/Çıkış saatlerinize göre hesaplanan günlük çalışma süreniz **{sure_saat} saat** ({sure_metin}). Standart çalışma süresi 9 saattir.")
                elif sure_saat > 9.0 and fazla_mesai == "Yapmadım":
                    st.error(f"🚨 **ÇALIŞMA SÜRESİ UYARISI:** Hesaplanan çalışma süreniz **{sure_saat} saat** ({sure_metin}). Lütfen Fazla Mesai alanını 'Yaptım' seçiniz!")
                else:
                    conn = sqlite3.connect("mesai_takip.db", timeout=10)
                    c = conn.cursor()

                    is_sorumlu_personel = personel_dict.get(p_ad_active, {}).get("is_sorumlu", 0) == 1
                    initial_bs_onay = 1 if is_sorumlu_personel else 0

                    özet_data = {
                        "personel": p_ad_active, "birim": p_birim_active, "tarih": str(tarih),
                        "baslangic": mesai_baslangic, "bitis": mesai_bitis, "sure_metin": sure_metin,
                        "m1_c": mola1_cikis or "-", "m1_b": mola1_bitis or "-",
                        "o_c": ogle_baslangic or "-", "o_b": ogle_bitis or "-",
                        "m2_c": mola2_cikis or "-", "m2_b": mola2_bitis or "-",
                        "fazla_mesai": fazla_mesai,
                    }

                    bugun_mu = (tarih == date.today())

                    if islem_turu == "Yeni Günlük Mesai Kaydı":
                        c.execute("SELECT id FROM mesai_kayitlari WHERE personel_ad_soyad = ? AND tarih = ?", (p_ad_active, str(tarih)))
                        existing_record = c.fetchone()

                        if existing_record:
                            st.error(f"⚠️ Sayın {p_ad_active}, {tarih} tarihi için zaten bir mesai kaydınız bulunmaktadır!")
                        elif bugun_mu:
                            c.execute("""
                                INSERT INTO mesai_kayitlari 
                                (personel_ad_soyad, tarih, birimi, mesai_baslangic, mola1_cikis, mola1_bitis, 
                                 ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                                 calisma_suresi_saat, calisma_suresi_metin, birim_sorumlusu_onay)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (p_ad_active, str(tarih), p_birim_active, mesai_baslangic, mola1_cikis, mola1_bitis,
                                  ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                                  sure_saat, sure_metin, initial_bs_onay))
                            conn.commit()
                            ozet_dialog(özet_data, "Yeni Günlük Mesai Kaydı")
                        else:
                            c.execute("""
                                INSERT INTO duzeltme_talepleri 
                                (mesai_id, personel_ad_soyad, tarih, birimi, mesai_baslangic, mola1_cikis, mola1_bitis, 
                                 ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                                 calisma_suresi_saat, calisma_suresi_metin, durum)
                                VALUES (0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Bekliyor')
                            """, (p_ad_active, str(tarih), p_birim_active, mesai_baslangic, mola1_cikis, mola1_bitis,
                                  ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                                  sure_saat, sure_metin))
                            conn.commit()
                            ozet_dialog(özet_data, "Geriye Dönük Mesai Onay Talebi")

                    else:
                        c.execute("SELECT id FROM mesai_kayitlari WHERE personel_ad_soyad = ? AND tarih = ?", (p_ad_active, str(tarih)))
                        target_record = c.fetchone()
                        m_id = target_record[0] if target_record else 0

                        c.execute("""
                            INSERT INTO duzeltme_talepleri 
                            (mesai_id, personel_ad_soyad, tarih, birimi, mesai_baslangic, mola1_cikis, mola1_bitis, 
                             ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                             calisma_suresi_saat, calisma_suresi_metin, durum)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Bekliyor')
                        """, (m_id, p_ad_active, str(tarih), p_birim_active, mesai_baslangic, mola1_cikis, mola1_bitis,
                              ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                              sure_saat, sure_metin))
                        conn.commit()
                        ozet_dialog(özet_data, "Düzeltme Talebi")

                    conn.close()

else:  # SORUMLU VE MÜDÜR YETKİLİ EKRANLARI
    tab2, tab3 = st.tabs(["📊 Çizelge Görüntüle", "🔐 Yönetici Paneli"])

    with tab2:
        st.header("Mesai Takip Çizelgesi ve Raporlar")
        conn = sqlite3.connect("mesai_takip.db", timeout=10)
        df = pd.read_sql_query("SELECT * FROM mesai_kayitlari ORDER BY tarih DESC", conn)
        conn.close()

        if st.session_state["auth_role"] == "SORUMLU":
            df = df[df["birimi"] == st.session_state["auth_unit"]]

        cizelge_p_options = [p for p in active_personel_names if p in df["personel_ad_soyad"].unique()]

        if not df.empty:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                secilen_personel = st.selectbox(
                    "Aktif Personelleri Filtrele (Tümü için boş bırakın):",
                    options=["Tüm Personeller"] + cizelge_p_options
                )

            df_filtered = df.copy()
            if secilen_personel != "Tüm Personeller":
                df_filtered = df_filtered[df_filtered["personel_ad_soyad"] == secilen_personel]
            else:
                df_filtered = df_filtered[df_filtered["personel_ad_soyad"].isin(active_personel_names)]

            hesaplanan_saatler = []
            hesaplanan_metinler = []

            for idx, r in df_filtered.iterrows():
                s_saat, s_metin = hesapla_calisma_suresi(r["mesai_baslangic"], r["mesai_bitis"])
                hesaplanan_saatler.append(s_saat)
                hesaplanan_metinler.append(s_metin)

            df_filtered["calisma_suresi_saat"] = hesaplanan_saatler
            df_filtered["calisma_suresi_metin"] = hesaplanan_metinler
            toplam_saat = sum(hesaplanan_saatler)

            st.metric(label="📊 Listelenen Kayıtlara Ait Toplam Çalışma Süresi", value=f"{round(toplam_saat, 2)} Saat")

            df_display = df_filtered.rename(columns={
                "id": "ID", "personel_ad_soyad": "Personel Adı Soyadı", "tarih": "Tarih", "birimi": "Birimi",
                "mesai_baslangic": "Mesai Başlangıç", "mola1_cikis": "1. Mola Çıkış", "mola1_bitis": "1. Mola Bitiş",
                "ogle_baslangic": "Öğle Başlangıç", "ogle_bitis": "Öğle Bitiş", "mola2_cikis": "2. Mola Çıkış",
                "mola2_bitis": "2. Mola Bitiş", "mesai_bitis": "Mesai Bitiş", "calisma_suresi_metin": "Günlük Çalışma Süresi",
                "fazla_mesai": "Fazla Mesai", "birim_sorumlusu_onay": "Birim Sorumlusu Onayı", "isletme_muduru_onay": "İşletme Müdürü Onayı"
            })

            df_display["Birim Sorumlusu Onayı"] = df_display["Birim Sorumlusu Onayı"].apply(lambda x: "✅ Onaylandı" if x == 1 else "⏳ Bekliyor")
            df_display["İşletme Müdürü Onayı"] = df_display["İşletme Müdürü Onayı"].apply(lambda x: "✅ Onaylandı" if x == 1 else "⏳ Bekliyor")

            def highlight_fm(val):
                color = "#ffcccc" if val == "Yaptım" else ""
                weight = "bold" if val == "Yaptım" else "normal"
                return f"background-color: {color}; font-weight: {weight}"

            st.dataframe(df_display.style.map(highlight_fm, subset=["Fazla Mesai"]), use_container_width=True)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                excel_data = df_display.to_csv(index=False).encode("utf-8-sig")
                st.download_button(label="📥 Excel / CSV Olarak İndir", data=excel_data, file_name="mesai_takip_cizelgesi.csv", mime="text/csv", use_container_width=True)
            with col_btn2:
                pdf_buffer = generate_pdf(df_filtered)
                st.download_button(label="📄 PDF Çizelgesi Olarak İndir (İmzaya Hazır)", data=pdf_buffer, file_name="mesai_takip_cizelgesi.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("Kayıtlı mesai verisi bulunmamaktadır.")

    with tab3:
        st.header("Yönetici Kontrol Paneli")
        current_role = st.session_state["auth_role"]
        current_unit = st.session_state["auth_unit"]
        current_user = st.session_state["auth_user_name"]
        birim_renk_map = get_birim_renk_map()

        conn = sqlite3.connect("mesai_takip.db", timeout=10)
        c = conn.cursor()

        if current_role == "MUDUR":
            c.execute("SELECT COUNT(*) FROM duzeltme_talepleri WHERE durum = 'Bekliyor'")
            bekleyen_duzeltme_sayisi = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM mesai_kayitlari WHERE birim_sorumlusu_onay = 0 OR isletme_muduru_onay = 0")
            bekleyen_onay_sayisi = c.fetchone()[0]
        else:
            c.execute("SELECT COUNT(*) FROM duzeltme_talepleri WHERE durum = 'Bekliyor' AND birimi = ?", (current_unit,))
            bekleyen_duzeltme_sayisi = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM mesai_kayitlari WHERE birim_sorumlusu_onay = 0 AND birimi = ? AND personel_ad_soyad != ?", (current_unit, current_user))
            bekleyen_onay_sayisi = c.fetchone()[0]
        conn.close()

        if current_role == "MUDUR":
            available_tabs = [
                "⚙️ Personel ve Birim Yönetimi",
                f"✅ Mesai Onayları ({bekleyen_onay_sayisi})",
                f"📩 Düzeltme / Güncelleme Talepleri ({bekleyen_duzeltme_sayisi})"
            ]
        else:
            available_tabs = [
                f"✅ Mesai Onayları ({bekleyen_onay_sayisi})",
                f"📩 Düzeltme / Güncelleme Talepleri ({bekleyen_duzeltme_sayisi})"
            ]

        selected_sub_tab = st.radio(
            "İşlem Yapılacak Ekranı Seçiniz:",
            options=available_tabs,
            index=min(st.session_state["sub_tab_index"], len(available_tabs) - 1),
            horizontal=True,
            key="sub_tab_radio_select"
        )
        st.session_state["sub_tab_index"] = available_tabs.index(selected_sub_tab)
        st.divider()

        if "⚙️ Personel ve Birim Yönetimi" in selected_sub_tab:
            col_admin1, col_admin2 = st.columns(2)
            birimler_tuples = get_birimler_data()
            birimler_list = [b[0] for b in birimler_tuples]

            with col_admin1:
                st.subheader("👨‍💼 Personel Tanımlama ve Şifre Yönetimi")
                yeni_p_ad = st.text_input("Yeni Personel Adı Soyadı")
                yeni_p_birim = st.selectbox("Bağlı Olduğu Birim", options=birimler_list if birimler_list else ["-"])
                yeni_p_sorumlu = st.checkbox("Bu Personel Birim Sorumlusudur")
                yeni_p_sifre = st.text_input("Giriş Şifresi (Boş bırakılırsa varsayılan: 1111)", type="password")

                if st.button("Personel Ekle"):
                    if yeni_p_ad.strip() and yeni_p_birim != "-":
                        conn = sqlite3.connect("mesai_takip.db", timeout=10)
                        c = conn.cursor()
                        
                        if yeni_p_sorumlu:
                            c.execute("SELECT ad_soyad FROM personeller WHERE birim_adi = ? AND is_birim_sorumlusu = 1 AND durum = 'Aktif'", (yeni_p_birim,))
                            mevcut_sorumlu = c.fetchone()
                            if mevcut_sorumlu:
                                st.error(f"🛑 **ENGELLEME:** `{yeni_p_birim}` biriminde zaten aktif bir Birim Sorumlusu bulunmaktadır: **{mevcut_sorumlu[0]}**. Bir birime sadece 1 adet Birim Sorumlusu atanabilir!")
                                conn.close()
                                st.stop()

                        try:
                            sifre_val = yeni_p_sifre.strip() if yeni_p_sifre.strip() else "1111"
                            c.execute("INSERT INTO personeller (ad_soyad, birim_adi, is_birim_sorumlusu, sifre, durum) VALUES (?, ?, ?, ?, 'Aktif')",
                                      (yeni_p_ad.strip(), yeni_p_birim, 1 if yeni_p_sorumlu else 0, sifre_val))
                            conn.commit()
                            conn.close()
                            st.success(f"'{yeni_p_ad}' başarıyla eklendi.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            conn.close()
                            st.error("Bu personel zaten kayıtlı!")
                    else:
                        st.error("Lütfen ad soyad girip geçerli bir birim seçiniz.")

                st.divider()
                st.write("**Mevcut Personeller & Durum Yönetimi (Aktif/Pasif/Sil):**")
                p_rows = get_personeller_data(only_active=False)

                for p_item in p_rows:
                    p_name, p_b, p_s, p_sifre, p_durum = p_item
                    s_tag = " (Birim Sorumlusu)" if p_s == 1 else ""
                    p_color = birim_renk_map.get(p_b, "#007bff") if p_durum == "Aktif" else "#6c757d"
                    durum_tag = "🟢 [AKTİF]" if p_durum == "Aktif" else "🔴 [PASİF/ESKİ]"

                    st.markdown(f"<div style='border-left: 5px solid {p_color}; padding-left: 8px; font-weight: bold;'>{durum_tag} {p_name} - {p_b}{s_tag}</div>", unsafe_allow_html=True)
                    with st.expander(f"⚙️ {p_name} İşlemleri"):
                        st.write(f"**Mevcut Şifre:** `{p_sifre if p_sifre else '1111'}` | **Durum:** `{p_durum}`")

                        col_up1, col_up2 = st.columns([2, 1])
                        with col_up1:
                            guncel_sifre = st.text_input("Yeni Şifre Belirle", key=f"pass_field_{p_name}", type="password")
                        with col_up2:
                            st.write("<br/>", unsafe_allow_html=True)
                            if st.button("Şifre Güncelle", key=f"btn_pass_{p_name}"):
                                if guncel_sifre.strip():
                                    conn = sqlite3.connect("mesai_takip.db", timeout=10)
                                    c = conn.cursor()
                                    c.execute("UPDATE personeller SET sifre = ? WHERE ad_soyad = ?", (guncel_sifre.strip(), p_name))
                                    conn.commit()
                                    conn.close()
                                    st.success("Şifre güncellendi!")
                                    st.rerun()

                        col_act1, col_act2 = st.columns(2)
                        with col_act1:
                            yeni_durum_hedef = "Pasif" if p_durum == "Aktif" else "Aktif"
                            btn_text = "🔴 Personeli Pasife Al" if p_durum == "Aktif" else "🟢 Personeli Tekrar Aktif Yap"
                            if st.button(btn_text, key=f"toggle_p_{p_name}"):
                                conn = sqlite3.connect("mesai_takip.db", timeout=10)
                                c = conn.cursor()
                                c.execute("UPDATE personeller SET durum = ? WHERE ad_soyad = ?", (yeni_durum_hedef, p_name))
                                conn.commit()
                                conn.close()
                                st.rerun()

                        with col_act2:
                            if st.button("🗑️ Kalıcı Olarak Sil", key=f"del_p_{p_name}"):
                                conn = sqlite3.connect("mesai_takip.db", timeout=10)
                                c = conn.cursor()
                                c.execute("DELETE FROM personeller WHERE ad_soyad = ?", (p_name,))
                                conn.commit()
                                conn.close()
                                st.info(f"'{p_name}' silindi.")
                                st.rerun()

            with col_admin2:
                st.subheader("🏢 Birim & Renk Yönetimi")
                yeni_birim = st.text_input("Yeni Birim Ekle")
                yeni_birim_renk = st.color_picker("Birim Kimlik Rengi Seçin", value="#007bff")

                if st.button("Birim Ekle"):
                    if yeni_birim.strip():
                        try:
                            conn = sqlite3.connect("mesai_takip.db", timeout=10)
                            c = conn.cursor()
                            c.execute("INSERT INTO birimler (birim_adi, birim_renk) VALUES (?, ?)", (yeni_birim.strip(), yeni_birim_renk))
                            conn.commit()
                            conn.close()
                            st.success(f"'{yeni_birim}' eklendi.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Bu birim zaten kayıtlı!")
                    else:
                        st.error("Lütfen geçerli bir birim adı girin.")

                st.divider()
                st.write("**Mevcut Birimler & Renkleri:**")
                for b_adi, b_renk in birimler_tuples:
                    c_b1, c_b2 = st.columns([3, 1])
                    c_b1.markdown(f"<span style='color:{b_renk}; font-size:18px;'>██</span> <b>{b_adi}</b>", unsafe_allow_html=True)
                    if c_b2.button("Sil", key=f"del_b_{b_adi}"):
                        conn = sqlite3.connect("mesai_takip.db", timeout=10)
                        c = conn.cursor()
                        c.execute("DELETE FROM birimler WHERE birim_adi = ?", (b_adi,))
                        conn.commit()
                        conn.close()
                        st.rerun()

        elif "Mesai Onayları" in selected_sub_tab:
            st.subheader("Mesai Onay ve Yönetim İşlemleri")
            conn = sqlite3.connect("mesai_takip.db", timeout=10)
            if current_role == "MUDUR":
                query = """
                    SELECT *, (CASE WHEN birim_sorumlusu_onay = 0 OR isletme_muduru_onay = 0 THEN 0 ELSE 1 END) as onay_durum_sira
                    FROM mesai_kayitlari ORDER BY onay_durum_sira ASC, tarih DESC
                """
                df_onay = pd.read_sql_query(query, conn)
            else:
                query = """
                    SELECT *, (CASE WHEN birim_sorumlusu_onay = 0 THEN 0 ELSE 1 END) as onay_durum_sira
                    FROM mesai_kayitlari WHERE birimi = ? ORDER BY onay_durum_sira ASC, tarih DESC
                """
                df_onay = pd.read_sql_query(query, conn, params=(current_unit,))
            conn.close()

            if not df_onay.empty:
                if bekleyen_onay_sayisi > 0:
                    st.warning(f"⚠️ **{bekleyen_onay_sayisi} adet** onay bekleyen mesai kaydı bulunmaktadır.")
                else:
                    st.success("🎉 Tüm mesai kayıtları onaylanmıştır.")

                for idx, row in df_onay.iterrows():
                    is_own_record = (current_role == "SORUMLU" and row["personel_ad_soyad"] == current_user)
                    onay_bekliyor_mu = (row["birim_sorumlusu_onay"] == 0 if (current_role == "SORUMLU" and not is_own_record) else (row["birim_sorumlusu_onay"] == 0 or row["isletme_muduru_onay"] == 0))
                    durum_etiketi = "⏳ [ONAY BEKLİYOR]" if onay_bekliyor_mu else "✅ [TAMAMLANDI]"
                    fm_etiketi = "🔴 [FAZLA MESAİ VAR]" if row["fazla_mesai"] == "Yaptım" else ""
                    b_color = birim_renk_map.get(row["birimi"], "#007bff")

                    st.markdown(f"<div style='border-left: 6px solid {b_color}; padding-left: 6px; margin-top: 10px;'><b>{row['birimi']}</b></div>", unsafe_allow_html=True)

                    with st.expander(f"{durum_etiketi} {fm_etiketi} 📌 {row['tarih']} - {row['personel_ad_soyad']} ({row['birimi']})", expanded=onay_bekliyor_mu):
                        if row["fazla_mesai"] == "Yaptım":
                            st.error("🚨 **FAZLA MESAİ BİLDİRİMİ:** Personel bugün fazla mesai yaptığını bildirdi.")

                        s_saat, s_metin = hesapla_calisma_suresi(row["mesai_baslangic"], row["mesai_bitis"])
                        st.write(f"**Giriş:** {row['mesai_baslangic']} | **Çıkış:** {row['mesai_bitis']} | **Günlük Çalışma:** **{s_metin}** | **Fazla Mesai:** **{row['fazla_mesai']}**")

                        col_o1, col_o2, col_o3 = st.columns(3)
                        with col_o1:
                            bs_durum = "✅ Onaylandı" if row["birim_sorumlusu_onay"] == 1 else "⏳ Bekliyor"
                            st.write(f"**Birim Sorumlusu Onayı:** {bs_durum}")
                            if is_own_record:
                                st.caption("ℹ️ *Birim sorumlusu kendi kaydını onaylayamaz.*")
                            elif row["birim_sorumlusu_onay"] == 0 and st.button("Birim Sorumlusu Olarak Onayla", key=f"bs_{row['id']}_{idx}"):
                                conn = sqlite3.connect("mesai_takip.db", timeout=10)
                                c = conn.cursor()
                                c.execute("UPDATE mesai_kayitlari SET birim_sorumlusu_onay = 1 WHERE id = ?", (row["id"],))
                                conn.commit()
                                conn.close()
                                st.rerun()

                        with col_o2:
                            im_durum = "✅ Onaylandı" if row["isletme_muduru_onay"] == 1 else "⏳ Bekliyor"
                            st.write(f"**İşletme Müdürü Onayı:** {im_durum}")
                            if current_role == "MUDUR":
                                if row["isletme_muduru_onay"] == 0:
                                    if st.button("İşletme Müdürü Olarak Onayla", key=f"im_{row['id']}_{idx}"):
                                        conn = sqlite3.connect("mesai_takip.db", timeout=10)
                                        c = conn.cursor()
                                        c.execute("UPDATE mesai_kayitlari SET isletme_muduru_onay = 1 WHERE id = ?", (row["id"],))
                                        conn.commit()
                                        conn.close()
                                        st.rerun()
                                else:
                                    if st.button("↩️ Müdür Onayını İptal Et", key=f"im_cancel_{row['id']}_{idx}"):
                                        conn = sqlite3.connect("mesai_takip.db", timeout=10)
                                        c = conn.cursor()
                                        c.execute("UPDATE mesai_kayitlari SET isletme_muduru_onay = 0 WHERE id = ?", (row["id"],))
                                        conn.commit()
                                        conn.close()
                                        st.rerun()

                        with col_o3:
                            if current_role == "MUDUR":
                                if st.button("🗑️ Kaydı Tamamen Sil", key=f"del_m_rec_{row['id']}_{idx}"):
                                    conn = sqlite3.connect("mesai_takip.db", timeout=10)
                                    c = conn.cursor()
                                    c.execute("DELETE FROM mesai_kayitlari WHERE id = ?", (row["id"],))
                                    conn.commit()
                                    conn.close()
                                    st.info("Mesai kaydı veritabanından silindi.")
                                    st.rerun()
            else:
                st.info("Kayıtlı mesai verisi bulunmamaktadır.")

        elif "Düzeltme" in selected_sub_tab:
            st.subheader("Gelen Düzeltme / Güncelleme Talepleri")
            if bekleyen_duzeltme_sayisi > 0:
                st.error(f"🔔 **{bekleyen_duzeltme_sayisi} adet** bekleyen düzeltme / güncelleme talebi var!")

            conn = sqlite3.connect("mesai_takip.db", timeout=10)
            c = conn.cursor()
            if current_role == "MUDUR":
                c.execute("SELECT * FROM duzeltme_talepleri WHERE durum = 'Bekliyor' ORDER BY id DESC")
            else:
                c.execute("SELECT * FROM duzeltme_talepleri WHERE durum = 'Bekliyor' AND birimi = ? ORDER BY id DESC", (current_unit,))
            talepler = c.fetchall()
            conn.close()

            if talepler:
                for idx_t, t in enumerate(talepler):
                    t_id, m_id, p_ad, t_tarih, birim, m_bas, m1_c, m1_b, o_bas, o_bit, m2_c, m2_b, m_bit, f_mesai = t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], t[12], t[13]
                    s_saat, s_metin = hesapla_calisma_suresi(m_bas, m_bit)
                    fm_etiketi = "🔴 **[FAZLA MESAİ VAR]**" if f_mesai == "Yaptım" else ""
                    b_color = birim_renk_map.get(birim, "#007bff")

                    st.markdown(f"<div style='border-left: 6px solid {b_color}; padding-left: 6px; margin-top: 10px;'><b>{birim}</b></div>", unsafe_allow_html=True)
                    with st.expander(f"📩 Düzeltme Talebi: {t_tarih} - {p_ad} ({birim}) {fm_etiketi}", expanded=True):
                        if f_mesai == "Yaptım":
                            st.error("🚨 **FAZLA MESAİ BİLDİRİMİ:** Düzeltme talebinde fazla mesai bildirildi.")

                        st.write(f"**Yeni Önerilen Giriş:** {m_bas} | **Yeni Önerilen Çıkış:** {m_bit} | **Yeni Çalışma Süresi:** **{s_metin}** | **Fazla Mesai:** **{f_mesai}**")
                        st.write(f"**Mola 1:** {m1_c} - {m1_b} | **Öğle:** {o_bas} - {o_bit} | **Mola 2:** {m2_c} - {m2_b}")

                        col_dt1, col_dt2 = st.columns(2)
                        with col_dt1:
                            is_own_request = (current_role == "SORUMLU" and p_ad == current_user)
                            if is_own_request:
                                st.caption("ℹ️ *Birim sorumluları kendi düzeltme taleplerini onaylayamazlar.*")
                            else:
                                if st.button("✅ Onayla ve Mesai Çizelgesine İşle", key=f"app_d_{t_id}_{idx_t}"):
                                    conn = sqlite3.connect("mesai_takip.db", timeout=10)
                                    c = conn.cursor()
                                    p_is_sorumlu = personel_dict.get(p_ad, {}).get("is_sorumlu", 0) == 1
                                    req_bs_onay = 1 if p_is_sorumlu else 0

                                    if m_id == 0:
                                        c.execute("""
                                            INSERT INTO mesai_kayitlari 
                                            (personel_ad_soyad, tarih, birimi, mesai_baslangic, mola1_cikis, mola1_bitis, 
                                             ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                                             calisma_suresi_saat, calisma_suresi_metin, birim_sorumlusu_onay)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (p_ad, t_tarih, birim, m_bas, m1_c, m1_b, o_bas, o_bit, m2_c, m2_b, m_bit, f_mesai, s_saat, s_metin, req_bs_onay))
                                    else:
                                        c.execute("""
                                            UPDATE mesai_kayitlari SET 
                                            birimi=?, mesai_baslangic=?, mola1_cikis=?, mola1_bitis=?, 
                                            ogle_baslangic=?, ogle_bitis=?, mola2_cikis=?, mola2_bitis=?, 
                                            mesai_bitis=?, fazla_mesai=?, calisma_suresi_saat=?, calisma_suresi_metin=?
                                            WHERE id=?
                                        """, (birim, m_bas, m1_c, m1_b, o_bas, o_bit, m2_c, m2_b, m_bit, f_mesai, s_saat, s_metin, m_id))

                                    c.execute("UPDATE duzeltme_talepleri SET durum = 'Onaylandi' WHERE id = ?", (t_id,))
                                    conn.commit()
                                    conn.close()
                                    st.success("Kayıt işlendi!")
                                    st.rerun()

                        with col_dt2:
                            if not is_own_request:
                                if st.button("🗑️ Talebi Reddet ve Kalıcı Olarak Sil", key=f"del_req_{t_id}_{idx_t}"):
                                    conn = sqlite3.connect("mesai_takip.db", timeout=10)
                                    c = conn.cursor()
                                    c.execute("DELETE FROM duzeltme_talepleri WHERE id = ?", (t_id,))
                                    conn.commit()
                                    conn.close()
                                    st.info("Talep reddedildi ve silindi.")
                                    st.rerun()
            else:
                st.info("Bekleyen düzeltme veya güncelleme talebi bulunmamaktadır.")
