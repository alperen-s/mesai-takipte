from datetime import datetime, date
import io
import os
import sqlite3
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
import streamlit as st

# Türkçe Karakter Destekli Font Kaydı (ReportLab)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    font_path_regular = "C:\\Windows\\Fonts\\arial.ttf"
    font_path_bold = "C:\\Windows\\Fonts\\arialbd.ttf"

    if os.path.exists(font_path_regular) and os.path.exists(font_path_bold):
        pdfmetrics.registerFont(TTFont("Arial-TR", font_path_regular))
        pdfmetrics.registerFont(TTFont("Arial-TR-Bold", font_path_bold))
        PDF_FONT_REGULAR = "Arial-TR"
        PDF_FONT_BOLD = "Arial-TR-Bold"
    else:
        PDF_FONT_REGULAR = "Helvetica"
        PDF_FONT_BOLD = "Helvetica-Bold"
except Exception:
    PDF_FONT_REGULAR = "Helvetica"
    PDF_FONT_BOLD = "Helvetica-Bold"

# Sayfa Yapılandırması
st.set_page_config(
    page_title="AFSÜ İktisadi İşletme - Mesai Takip",
    page_icon="📋",
    layout="wide",
)


# MESAİ SAATİ HESAPLAMA YARDIMCI FONKSİYONU
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


# Veritabanı Kurulumu ve Şema Güncellemesi
def init_db():
    conn = sqlite3.connect("mesai_takip.db")
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
            sifre TEXT DEFAULT '1111'
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

    # Sütun Kontrolleri ve Güncellemeler
    c.execute("PRAGMA table_info(birimler)")
    cols_b = [col[1] for col in c.fetchall()]
    if "birim_renk" not in cols_b:
        c.execute(
            "ALTER TABLE birimler ADD COLUMN birim_renk TEXT DEFAULT '#007bff'"
        )

    c.execute(
        "UPDATE personeller SET sifre = '1111' WHERE sifre IS NULL OR sifre = ''"
    )

    conn.commit()
    conn.close()


init_db()


def get_personeller_data():
    conn = sqlite3.connect("mesai_takip.db")
    c = conn.cursor()
    c.execute(
        "SELECT ad_soyad, birim_adi, is_birim_sorumlusu, sifre FROM personeller ORDER BY ad_soyad ASC"
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_birimler_data():
    conn = sqlite3.connect("mesai_takip.db")
    c = conn.cursor()
    c.execute("SELECT birim_adi, birim_renk FROM birimler ORDER BY birim_adi ASC")
    rows = c.fetchall()
    conn.close()
    return rows


def get_birim_renk_map():
    b_data = get_birimler_data()
    return {b[0]: (b[1] if b[1] else "#007bff") for b in b_data}


# PERSONEL BİLGİ ÖZET POP-UP EKRANI (DIALOG)
@st.dialog("📋 İşlem Özeti ve Onay Bilgisi")
def ozet_dialog(bilgiler, islem_turu_adi):
    st.success(
        f"✅ **{islem_turu_adi}** işleminiz başarıyla sisteme iletilmiştir."
    )
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


# PDF OLUŞTURMA FONKSİYONU
def generate_pdf(df_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15,
        leftMargin=15,
        topMargin=20,
        bottomMargin=20,
    )
    elements = []

    styles = getSampleStyleSheet()

    cell_style = ParagraphStyle(
        "CellOptionTR",
        fontName=PDF_FONT_REGULAR,
        fontSize=7.5,
        leading=9,
        alignment=1,
    )

    header_style = ParagraphStyle(
        "HeaderOptionTR",
        fontName=PDF_FONT_BOLD,
        fontSize=7.5,
        leading=9,
        alignment=1,
    )

    title_style = ParagraphStyle(
        "TitleOptionTR",
        fontName=PDF_FONT_BOLD,
        fontSize=12,
        leading=14,
        alignment=1,
    )

    summary_style = ParagraphStyle(
        "SummaryOptionTR",
        fontName=PDF_FONT_BOLD,
        fontSize=9,
        leading=11,
        alignment=2,
    )

    elements.append(
        Paragraph(
            "Afyonkarahisar Sağlık Bilimleri Üniversitesi İktisadi İşletme Müdürlüğü",
            title_style,
        )
    )
    elements.append(Paragraph("Personel Mesai Takip Çizelgesi", title_style))
    elements.append(Paragraph("<br/><br/>", styles["Normal"]))

    table_data = [[
        Paragraph("Tarih", header_style),
        Paragraph("Personel", header_style),
        Paragraph("Birimi", header_style),
        Paragraph("Mesai Başlangıç", header_style),
        Paragraph("1. Mola Çıkış", header_style),
        Paragraph("1. Mola Bitiş", header_style),
        Paragraph("Öğle Başlangıç", header_style),
        Paragraph("Öğle Bitiş", header_style),
        Paragraph("2. Mola Çıkış", header_style),
        Paragraph("2. Mola Bitiş", header_style),
        Paragraph("Mesai Bitiş", header_style),
        Paragraph("Çalışma Süresi", header_style),
        Paragraph("Fazla Mesai", header_style),
        Paragraph("İmza", header_style),
    ]]

    toplam_saat_aylik = 0.0

    for idx, row in df_data.iterrows():
        s_saat, s_metin = hesapla_calisma_suresi(
            row["mesai_baslangic"], row["mesai_bitis"]
        )
        toplam_saat_aylik += s_saat

        table_data.append([
            Paragraph(str(row["tarih"]), cell_style),
            Paragraph(str(row["personel_ad_soyad"]), cell_style),
            Paragraph(str(row["birimi"]), cell_style),
            Paragraph(str(row["mesai_baslangic"]), cell_style),
            Paragraph(str(row["mola1_cikis"]), cell_style),
            Paragraph(str(row["mola1_bitis"]), cell_style),
            Paragraph(str(row["ogle_baslangic"]), cell_style),
            Paragraph(str(row["ogle_bitis"]), cell_style),
            Paragraph(str(row["mola2_cikis"]), cell_style),
            Paragraph(str(row["mola2_bitis"]), cell_style),
            Paragraph(str(row["mesai_bitis"]), cell_style),
            Paragraph(str(s_metin), cell_style),
            Paragraph(str(row["fazla_mesai"]), cell_style),
            Paragraph("", cell_style),
        ])

    pdf_table = Table(table_data, repeatRows=1)
    pdf_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
        ])
    )

    elements.append(pdf_table)

    elements.append(Paragraph("<br/>", styles["Normal"]))
    elements.append(
        Paragraph(
            f"<b>Çizelge Dönemi Toplam Çalışma Süresi:</b> {round(toplam_saat_aylik, 2)} Saat &nbsp;&nbsp;&nbsp;&nbsp;",
            summary_style,
        )
    )

    elements.append(Paragraph("<br/><br/>", styles["Normal"]))
    onay_data = [
        [
            Paragraph("<b>Personel/Birim Sorumlusu Onayı</b>", header_style),
            Paragraph("<b>İşletme Müdürü Onayı</b>", header_style),
        ],
        [
            Paragraph("<br/><br/>...........................<br/>İmza", cell_style),
            Paragraph("<br/><br/>...........................<br/>İmza", cell_style),
        ],
    ]
    onay_table = Table(onay_data, colWidths=[350, 350])
    onay_table.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )

    elements.append(onay_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# SESSION STATE HAFIZA YÖNETİMİ
YONETICI_SIFRESI = "1234"

if "auth_role" not in st.session_state:
    st.session_state["auth_role"] = None
if "auth_unit" not in st.session_state:
    st.session_state["auth_unit"] = None
if "auth_user_name" not in st.session_state:
    st.session_state["auth_user_name"] = ""
if "sub_tab_index" not in st.session_state:
    st.session_state["sub_tab_index"] = 0

personel_raw = get_personeller_data()
personel_dict = {
    row[0]: {"birim": row[1], "is_sorumlu": row[2], "sifre": row[3]}
    for row in personel_raw
}
p_names = list(personel_dict.keys())
sorumlu_listesi = [
    p_name for p_name, data in personel_dict.items() if data["is_sorumlu"] == 1
]

# SOL MENÜ (SIDEBAR) - TÜM GİRİŞ SEÇENEKLERİ
with st.sidebar:
    st.header("🔑 Kullanıcı Giriş Paneli")

    if st.session_state["auth_role"] is None:
        login_type = st.radio(
            "Giriş Türünüzü Seçiniz:",
            ["Personel", "Birim Sorumlusu", "İşletme Müdürü"],
            key="login_type_radio",
        )

        st.divider()

        if login_type == "Personel":
            st.subheader("👤 Personel Girişi")
            secilen_p = st.selectbox(
                "Adınızı Seçiniz:",
                options=p_names if p_names else ["-"],
                index=None,
                placeholder="Listeden isminizi seçin...",
                key="side_p_select",
            )

            p_birim_auto = "-"
            if secilen_p and secilen_p in personel_dict:
                p_birim_auto = personel_dict[secilen_p]["birim"]

            st.text_input(
                "Bağlı Olduğunuz Birim",
                value=p_birim_auto,
                disabled=True,
                key="side_p_birim_disabled",
            )
            p_pass_in = st.text_input(
                "Şifreniz (Varsayılan: 1111)", type="password", key="side_p_pass"
            )

            if st.button("Personel Girişi Yap", use_container_width=True):
                if not secilen_p:
                    st.error("Lütfen adınızı seçiniz!")
                else:
                    dogru_pass = personel_dict[secilen_p]["sifre"]
                    if p_pass_in == dogru_pass:
                        st.session_state["auth_role"] = "PERSONEL"
                        st.session_state["auth_unit"] = p_birim_auto
                        st.session_state["auth_user_name"] = secilen_p
                        st.success(f"Hoş geldiniz, {secilen_p}")
                        st.rerun()
                    else:
                        st.error("Hatalı Şifre!")

        elif login_type == "Birim Sorumlusu":
            st.subheader("👔 Birim Sorumlusu Girişi")
            if not sorumlu_listesi:
                st.info("Tanımlı Birim Sorumlusu bulunmamaktadır.")
            else:
                secilen_sorumlu = st.selectbox(
                    "İsminizi Seçiniz:",
                    options=sorumlu_listesi,
                    key="sorumlu_select",
                )
                sorumlu_pass_input = st.text_input(
                    "Giriş Şifreniz", type="password", key="sorumlu_pass"
                )

                if st.button(
                    "Birim Sorumlusu Olarak Giriş Yap", use_container_width=True
                ):
                    dogru_sifre = personel_dict[secilen_sorumlu]["sifre"]
                    if sorumlu_pass_input == dogru_sifre:
                        u_birim = personel_dict[secilen_sorumlu]["birim"]
                        st.session_state["auth_role"] = "SORUMLU"
                        st.session_state["auth_unit"] = u_birim
                        st.session_state["auth_user_name"] = secilen_sorumlu
                        st.session_state["sub_tab_index"] = 0
                        st.success(f"Hoş geldiniz, {secilen_sorumlu}")
                        st.rerun()
                    else:
                        st.error("Hatalı Şifre!")

        else:  # İşletme Müdürü
            st.subheader("👑 İşletme Müdürü Girişi")
            input_pass = st.text_input(
                "Müdür Şifresi", type="password", key="mudur_pass"
            )
            if st.button(
                "Müdür Olarak Giriş Yap", use_container_width=True
            ):
                if input_pass == YONETICI_SIFRESI:
                    st.session_state["auth_role"] = "MUDUR"
                    st.session_state["auth_unit"] = "ALL"
                    st.session_state["auth_user_name"] = "İşletme Müdürü"
                    st.session_state["sub_tab_index"] = 0
                    st.success("Müdür Girişi Başarılı!")
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

# BAŞLIK
st.title("🏛️ AFSÜ İktisadi İşletme Müdürlüğü")
st.caption("Personel Mesai Takip ve Yönetim Sistemi")

# GİRİŞ YAPILMAMIŞSA VEYA ROLÜNE GÖRE SEKMELERİ OLUŞTUR
if st.session_state["auth_role"] is None:
    st.info(
        "👈 **Lütfen sağ tarafı görüntülemek için sol taraftaki menüden Personel, Birim Sorumlusu veya Müdür girişi yapınız.**"
    )

elif st.session_state["auth_role"] == "PERSONEL":
    # PERSONEL SADECE MESAİ GİRİŞ EKRANINI GÖRÜR
    st.success(
        f"👤 Hoş Geldiniz Sayın **{st.session_state['auth_user_name']}** ({st.session_state['auth_unit']})"
    )

    islem_turu = st.radio(
        "İşlem Türünü Seçiniz:",
        [
            "Yeni Günlük Mesai Kaydı",
            "Hatalı Kayıt İçin Düzeltme Talebi Gönder",
            "🔑 Kendi Şifremi Değiştir",
        ],
        horizontal=True,
    )

    st.divider()

    birimler_tuples = get_birimler_data()
    birim_listesi = [b[0] for b in birimler_tuples]
    p_ad_active = st.session_state["auth_user_name"]
    p_birim_active = st.session_state["auth_unit"]

    if islem_turu == "🔑 Kendi Şifremi Değiştir":
        st.subheader("🔑 Personel Şifre Değiştirme Ekranı")
        col_pass1, col_pass2 = st.columns(2)
        with col_pass1:
            st.write(f"**Personel:** `{p_ad_active}`")
            st.write(f"**Birim:** `{p_birim_active}`")
            p_eski_pass = st.text_input(
                "Mevcut Şifreniz", type="password", key="p_eski_pass_key_user"
            )
        with col_pass2:
            p_yeni_pass = st.text_input(
                "Yeni Şifreniz", type="password", key="p_yeni_pass_key_user"
            )
            p_yeni_pass2 = st.text_input(
                "Yeni Şifreniz (Tekrar)",
                type="password",
                key="p_yeni_pass2_key_user",
            )

        if st.button("Şifremi Güncelle"):
            dogru_mevcut = personel_dict[p_ad_active]["sifre"]
            if p_eski_pass != dogru_mevcut:
                st.error("Mevcut şifrenizi hatalı girdiniz!")
            elif not p_yeni_pass.strip():
                st.error("Yeni şifre boş bırakılamaz!")
            elif p_yeni_pass != p_yeni_pass2:
                st.error("Yeni şifreler birbiriyle uyuşmuyor!")
            else:
                conn = sqlite3.connect("mesai_takip.db")
                c = conn.cursor()
                c.execute(
                    "UPDATE personeller SET sifre = ? WHERE ad_soyad = ?",
                    (p_yeni_pass.strip(), p_ad_active),
                )
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
                tarih = st.date_input(
                    "Tarih", date.today(), max_value=date.today()
                )
                fazla_mesai = st.radio(
                    "Fazla Mesai",
                    ["Yaptım", "Yapmadım"],
                    horizontal=True,
                    index=1,
                )

            st.divider()
            st.subheader("⏰ Saat Bilgileri")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                mesai_baslangic = st.text_input(
                    "Mesai Başlangıç Saati", value="08:30"
                )
                mola1_cikis = st.text_input(
                    "1. Mola Çıkış Saati", placeholder="10:30"
                )
            with col2:
                mola1_bitis = st.text_input(
                    "1. Mola Bitiş Saati", placeholder="10:45"
                )
                ogle_baslangic = st.text_input(
                    "Öğle Tatili Başlangıç", value="12:30"
                )
            with col3:
                ogle_bitis = st.text_input("Öğle Tatili Bitiş", value="13:30")
                mola2_cikis = st.text_input(
                    "2. Mola Çıkış Saati", placeholder="14:00"
                )
            with col4:
                mola2_bitis = st.text_input(
                    "2. Mola Bitiş Saati", placeholder="14:15"
                )
                mesai_bitis = st.text_input("Mesai Bitiş Saati", value="17:30")

            btn_label = (
                " Kaydet"
                if islem_turu == "Yeni Günlük Mesai Kaydı"
                else "📩 Düzeltme Talebi Gönder"
            )
            submitted = st.form_submit_button(btn_label)

            if submitted:
                sure_saat, sure_metin = hesapla_calisma_suresi(
                    mesai_baslangic, mesai_bitis
                )

                if sure_saat <= 9.0 and fazla_mesai == "Yaptım":
                    st.error(
                        f"🛑 **GEÇERSİZ MESAİ TALEBİ:** Giriş/Çıkış saatlerinize göre hesaplanan günlük çalışma süreniz **{sure_saat} saat** ({sure_metin}). "
                        "Standart çalışma süresi 9 saattir. 9 saat ve altındaki çalışmalar için 'Fazla Mesai Yaptım' seçilemez! Lütfen 'Yapmadım' seçeneğini işaretleyiniz."
                    )
                elif sure_saat > 9.0 and fazla_mesai == "Yapmadım":
                    st.error(
                        f"🚨 **ÇALIŞMA SÜRESİ UYARISI:** Hesaplanan çalışma süreniz **{sure_saat} saat** ({sure_metin}) olarak belirlenmiştir. "
                        "Standart günlük çalışma süresi 9 saattir. 9 saat üzeri çalışmalar için lütfen Fazla Mesai seçeneğini **'Yaptım'** olarak işaretleyiniz!"
                    )
                else:
                    conn = sqlite3.connect("mesai_takip.db")
                    c = conn.cursor()

                    is_sorumlu_personel = (
                        personel_dict.get(p_ad_active, {}).get(
                            "is_sorumlu", 0
                        )
                        == 1
                    )
                    initial_bs_onay = 1 if is_sorumlu_personel else 0

                    özet_data = {
                        "personel": p_ad_active,
                        "birim": p_birim_active,
                        "tarih": str(tarih),
                        "baslangic": mesai_baslangic,
                        "bitis": mesai_bitis,
                        "sure_metin": sure_metin,
                        "m1_c": mola1_cikis or "-",
                        "m1_b": mola1_bitis or "-",
                        "o_c": ogle_baslangic or "-",
                        "o_b": ogle_bitis or "-",
                        "m2_c": mola2_cikis or "-",
                        "m2_b": mola2_bitis or "-",
                        "fazla_mesai": fazla_mesai,
                    }

                    bugun_mu = tarih == date.today()

                    if islem_turu == "Yeni Günlük Mesai Kaydı":
                        c.execute(
                            "SELECT id FROM mesai_kayitlari WHERE personel_ad_soyad = ? AND tarih = ?",
                            (p_ad_active, str(tarih)),
                        )
                        existing_record = c.fetchone()

                        if existing_record:
                            st.error(
                                f"⚠️ Sayın {p_ad_active}, {tarih} tarihi için zaten bir mesai kaydınız bulunmaktadır! "
                                "Hatalı girdiyseniz lütfen yukarıdan 'Hatalı Kayıt İçin Düzeltme Talebi Gönder' seçeneğini kullanarak düzeltme isteğinde bulununuz."
                            )
                        elif bugun_mu:
                            c.execute(
                                """
                                INSERT INTO mesai_kayitlari 
                                (personel_ad_soyad, tarih, birimi, mesai_baslangic, mola1_cikis, mola1_bitis, 
                                 ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                                 calisma_suresi_saat, calisma_suresi_metin, birim_sorumlusu_onay)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    p_ad_active,
                                    str(tarih),
                                    p_birim_active,
                                    mesai_baslangic,
                                    mola1_cikis,
                                    mola1_bitis,
                                    ogle_baslangic,
                                    ogle_bitis,
                                    mola2_cikis,
                                    mola2_bitis,
                                    mesai_bitis,
                                    fazla_mesai,
                                    sure_saat,
                                    sure_metin,
                                    initial_bs_onay,
                                ),
                            )
                            conn.commit()
                            ozet_dialog(özet_data, "Yeni Günlük Mesai Kaydı")
                        else:
                            c.execute(
                                """
                                INSERT INTO duzeltme_talepleri 
                                (mesai_id, personel_ad_soyad, tarih, birimi, mesai_baslangic, mola1_cikis, mola1_bitis, 
                                 ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                                 calisma_suresi_saat, calisma_suresi_metin)
                                VALUES (0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    p_ad_active,
                                    str(tarih),
                                    p_birim_active,
                                    mesai_baslangic,
                                    mola1_cikis,
                                    mola1_bitis,
                                    ogle_baslangic,
                                    ogle_bitis,
                                    mola2_cikis,
                                    mola2_bitis,
                                    mesai_bitis,
                                    fazla_mesai,
                                    sure_saat,
                                    sure_metin,
                                ),
                            )
                            conn.commit()
                            ozet_dialog(
                                özet_data, "Geriye Dönük Mesai Onay Talebi"
                            )

                    else:
                        c.execute(
                            "SELECT id FROM mesai_kayitlari WHERE personel_ad_soyad = ? AND tarih = ?",
                            (p_ad_active, str(tarih)),
                        )
                        target_record = c.fetchone()
                        m_id = target_record[0] if target_record else 0

                        c.execute(
                            """
                            INSERT INTO duzeltme_talepleri 
                            (mesai_id, personel_ad_soyad, tarih, birimi, mesai_baslangic, mola1_cikis, mola1_bitis, 
                             ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                             calisma_suresi_saat, calisma_suresi_metin)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                m_id,
                                p_ad_active,
                                p_birim_active,
                                mesai_baslangic,
                                mola1_cikis,
                                mola1_bitis,
                                ogle_baslangic,
                                ogle_bitis,
                                mola2_cikis,
                                mola2_bitis,
                                mesai_bitis,
                                fazla_mesai,
                                sure_saat,
                                sure_metin,
                            ),
                        )
                        conn.commit()
                        ozet_dialog(özet_data, "Düzeltme Talebi")

                    conn.close()

else:  # SORUMLU VE MÜDÜR YETKİLİ EKRANI (ÇİZELGE VE YÖNETİCİ PANELİ AÇIK)
    tab2, tab3 = st.tabs(["📊 Çizelge Görüntüle", "🔐 Yönetici Paneli"])

    # ---------------------------------------------------------
    # TAB 2: ÇİZELGE GÖRÜNTÜLEME
    # ---------------------------------------------------------
    with tab2:
        st.header("Mesai Takip Çizelgesi ve Raporlar")

        conn = sqlite3.connect("mesai_takip.db")
        df = pd.read_sql_query(
            "SELECT * FROM mesai_kayitlari ORDER BY tarih DESC", conn
        )
        conn.close()

        if st.session_state["auth_role"] == "SORUMLU":
            df = df[df["birimi"] == st.session_state["auth_unit"]]

        if not df.empty:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                secilen_personel = st.selectbox(
                    "Personel Filtrele (Tümü için boş bırakın):",
                    options=["Tüm Personeller"] + list(df["personel_ad_soyad"].unique()),
                )

            df_filtered = df.copy()
            if secilen_personel != "Tüm Personeller":
                df_filtered = df_filtered[
                    df_filtered["personel_ad_soyad"] == secilen_personel
                ]

            hesaplanan_saatler = []
            hesaplanan_metinler = []

            for idx, r in df_filtered.iterrows():
                s_saat, s_metin = hesapla_calisma_suresi(
                    r["mesai_baslangic"], r["mesai_bitis"]
                )
                hesaplanan_saatler.append(s_saat)
                hesaplanan_metinler.append(s_metin)

            df_filtered["calisma_suresi_saat"] = hesaplanan_saatler
            df_filtered["calisma_suresi_metin"] = hesaplanan_metinler

            toplam_saat = sum(hesaplanan_saatler)

            st.metric(
                label=f"📊 Listelenen Kayıtlara Ait Toplam Çalışma Süresi",
                value=f"{round(toplam_saat, 2)} Saat",
            )

            df_display = df_filtered.rename(
                columns={
                    "id": "ID",
                    "personel_ad_soyad": "Personel Adı Soyadı",
                    "tarih": "Tarih",
                    "birimi": "Birimi",
                    "mesai_baslangic": "Mesai Başlangıç",
                    "mola1_cikis": "1. Mola Çıkış",
                    "mola1_bitis": "1. Mola Bitiş",
                    "ogle_baslangic": "Öğle Başlangıç",
                    "ogle_bitis": "Öğle Bitiş",
                    "mola2_cikis": "2. Mola Çıkış",
                    "mola2_bitis": "2. Mola Bitiş",
                    "mesai_bitis": "Mesai Bitiş",
                    "calisma_suresi_metin": "Günlük Çalışma Süresi",
                    "fazla_mesai": "Fazla Mesai",
                    "birim_sorumlusu_onay": "Birim Sorumlusu Onayı",
                    "isletme_muduru_onay": "İşletme Müdürü Onayı",
                }
            )

            df_display["Birim Sorumlusu Onayı"] = df_display[
                "Birim Sorumlusu Onayı"
            ].apply(lambda x: "✅ Onaylandı" if x == 1 else "⏳ Bekliyor")
            df_display["İşletme Müdürü Onayı"] = df_display[
                "İşletme Müdürü Onayı"
            ].apply(lambda x: "✅ Onaylandı" if x == 1 else "⏳ Bekliyor")

            def highlight_fm(val):
                color = "#ffcccc" if val == "Yaptım" else ""
                weight = "bold" if val == "Yaptım" else "normal"
                return f"background-color: {color}; font-weight: {weight}"

            st.dataframe(
                df_display.style.map(highlight_fm, subset=["Fazla Mesai"]),
                use_container_width=True,
            )

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                excel_data = df_display.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 Excel / CSV Olarak İndir",
                    data=excel_data,
                    file_name="mesai_takip_cizelgesi.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col_btn2:
                pdf_buffer = generate_pdf(df_filtered)
                st.download_button(
                    label="📄 PDF Çizelgesi Olarak İndir (İmzaya Hazır)",
                    data=pdf_buffer,
                    file_name="mesai_takip_cizelgesi.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        else:
            st.info("Kayıtlı mesai verisi bulunmamaktadır.")

    # ---------------------------------------------------------
    # TAB 3: YÖNETİCİ PANELİ
    # ---------------------------------------------------------
    with tab3:
        st.header("Yönetici Kontrol Paneli")

        current_role = st.session_state["auth_role"]
        current_unit = st.session_state["auth_unit"]
        current_user = st.session_state["auth_user_name"]
        birim_renk_map = get_birim_renk_map()

        conn = sqlite3.connect("mesai_takip.db")
        c = conn.cursor()

        if current_role == "MUDUR":
            c.execute(
                "SELECT COUNT(*) FROM duzeltme_talepleri WHERE durum = 'Bekliyor'"
            )
            bekleyen_duzeltme_sayisi = c.fetchone()[0]
            c.execute(
                "SELECT COUNT(*) FROM mesai_kayitlari WHERE birim_sorumlusu_onay = 0 OR isletme_muduru_onay = 0"
            )
            bekleyen_onay_sayisi = c.fetchone()[0]
        else:
            c.execute(
                "SELECT COUNT(*) FROM duzeltme_talepleri WHERE durum = 'Bekliyor' AND birimi = ?",
                (current_unit,),
            )
            bekleyen_duzeltme_sayisi = c.fetchone()[0]

            c.execute(
                "SELECT COUNT(*) FROM mesai_kayitlari WHERE birim_sorumlusu_onay = 0 AND birimi = ? AND personel_ad_soyad != ?",
                (current_unit, current_user),
            )
            bekleyen_onay_sayisi = c.fetchone()[0]

        conn.close()

        if current_role == "MUDUR":
            available_tabs = [
                "⚙️ Personel ve Birim Yönetimi",
                f"✅ Mesai Onayları ({bekleyen_onay_sayisi})",
                f"📩 Düzeltme / Güncelleme Talepleri ({bekleyen_duzeltme_sayisi})",
            ]
        else:
            available_tabs = [
                f"✅ Mesai Onayları ({bekleyen_onay_sayisi})",
                f"📩 Düzeltme / Güncelleme Talepleri ({bekleyen_duzeltme_sayisi})",
            ]

        selected_sub_tab = st.radio(
            "İşlem Yapılacak Ekranı Seçiniz:",
            options=available_tabs,
            index=min(
                st.session_state["sub_tab_index"], len(available_tabs) - 1
            ),
            horizontal=True,
            key="sub_tab_radio_select",
        )
        st.session_state["sub_tab_index"] = available_tabs.index(
            selected_sub_tab
        )
        st.divider()

        # PERSONEL VE BİRİM YÖNETİMİ (SADECE MÜDÜR)
        if "⚙️ Personel ve Birim Yönetimi" in selected_sub_tab:
            col_admin1, col_admin2 = st.columns(2)

            birimler_tuples = get_birimler_data()
            birimler_list = [b[0] for b in birimler_tuples]

            with col_admin1:
                st.subheader("👨‍💼 Personel Tanımlama ve Şifre Yönetimi")

                yeni_p_ad = st.text_input("Yeni Personel Adı Soyadı")
                yeni_p_birim = st.selectbox(
                    "Bağlı Olduğu Birim",
                    options=birimler_list if birimler_list else ["-"],
                )
                yeni_p_sorumlu = st.checkbox("Bu Personel Birim Sorumlusudur")
                yeni_p_sifre = st.text_input(
                    "Giriş Şifresi (Boş bırakılırsa varsayılan: 1111)",
                    type="password",
                )

                if st.button("Personel Ekle"):
                    if yeni_p_ad.strip() and yeni_p_birim != "-":
                        try:
                            sifre_val = (
                                yeni_p_sifre.strip()
                                if yeni_p_sifre.strip()
                                else "1111"
                            )
                            conn = sqlite3.connect("mesai_takip.db")
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO personeller (ad_soyad, birim_adi, is_birim_sorumlusu, sifre) VALUES (?, ?, ?, ?)",
                                (
                                    yeni_p_ad.strip(),
                                    yeni_p_birim,
                                    1 if yeni_p_sorumlu else 0,
                                    sifre_val,
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"'{yeni_p_ad}' başarıyla eklendi.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Bu personel zaten kayıtlı!")
                    else:
                        st.error(
                            "Lütfen ad soyad girip geçerli bir birim seçiniz."
                        )

                st.divider()
                st.write(
                    "**Mevcut Personeller & Şifre Değiştirme / Sıfırlama:**"
                )
                p_rows = get_personeller_data()
                for p_item in p_rows:
                    p_name, p_b, p_s, p_sifre = p_item
                    s_tag = " (Birim Sorumlusu)" if p_s == 1 else ""
                    p_color = birim_renk_map.get(p_b, "#007bff")

                    st.markdown(
                        f"<div style='border-left: 5px solid {p_color}; padding-left: 8px; font-weight: bold;'>{p_name} - {p_b}{s_tag}</div>",
                        unsafe_allow_html=True,
                    )
                    with st.expander(f"⚙️ {p_name} İşlemleri"):
                        st.write(
                            f"**Mevcut Şifre:** `{p_sifre if p_sifre else '1111'}`"
                        )

                        col_up1, col_up2 = st.columns([2, 1])
                        with col_up1:
                            guncel_sifre = st.text_input(
                                "Yeni Şifre Belirle",
                                key=f"pass_field_{p_name}",
                                type="password",
                            )
                        with col_up2:
                            st.write("<br/>", unsafe_allow_html=True)
                            if st.button(
                                "Şifre Güncelle", key=f"btn_pass_{p_name}"
                            ):
                                if guncel_sifre.strip():
                                    conn = sqlite3.connect("mesai_takip.db")
                                    c = conn.cursor()
                                    c.execute(
                                        "UPDATE personeller SET sifre = ? WHERE ad_soyad = ?",
                                        (guncel_sifre.strip(), p_name),
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.success("Şifre güncellendi!")
                                    st.rerun()

                        if st.button("Personeli Sil", key=f"del_p_{p_name}"):
                            conn = sqlite3.connect("mesai_takip.db")
                            c = conn.cursor()
                            c.execute(
                                "DELETE FROM personeller WHERE ad_soyad = ?",
                                (p_name,),
                            )
                            conn.commit()
                            conn.close()
                            st.rerun()

            with col_admin2:
                st.subheader("🏢 Birim & Renk Yönetimi")
                yeni_birim = st.text_input("Yeni Birim Ekle")
                yeni_birim_renk = st.color_picker(
                    "Birim Kimlik Rengi Seçin", value="#007bff"
                )

                if st.button("Birim Ekle"):
                    if yeni_birim.strip():
                        try:
                            conn = sqlite3.connect("mesai_takip.db")
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO birimler (birim_adi, birim_renk) VALUES (?, ?)",
                                (yeni_birim.strip(), yeni_birim_renk),
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"'{yeni_birim}' başarıyla eklendi.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Bu birim zaten kayıtlı!")
                    else:
                        st.error("Lütfen geçerli bir birim adı girin.")

                st.divider()
                st.write("**Mevcut Birimler & Renkleri:**")
                for b_adi, b_renk in birimler_tuples:
                    c_b1, c_b2 = st.columns([3, 1])
                    c_b1.markdown(
                        f"<span style='color:{b_renk}; font-size:18px;'>██</span> <b>{b_adi}</b>",
                        unsafe_allow_html=True,
                    )
                    if c_b2.button("Sil", key=f"del_b_{b_adi}"):
                        conn = sqlite3.connect("mesai_takip.db")
                        c = conn.cursor()
                        c.execute(
                            "DELETE FROM birimler WHERE birim_adi = ?", (b_adi,)
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

        # MESAİ ONAYLARI
        elif "Mesai Onayları" in selected_sub_tab:
            st.subheader("Mesai Onay ve Yönetim İşlemleri")

            conn = sqlite3.connect("mesai_takip.db")
            if current_role == "MUDUR":
                query = """
                    SELECT *, 
                    (CASE WHEN birim_sorumlusu_onay = 0 OR isletme_muduru_onay = 0 THEN 0 ELSE 1 END) as onay_durum_sira
                    FROM mesai_kayitlari 
                    ORDER BY onay_durum_sira ASC, tarih DESC
                """
                df_onay = pd.read_sql_query(query, conn)
            else:
                query = """
                    SELECT *, 
                    (CASE WHEN birim_sorumlusu_onay = 0 THEN 0 ELSE 1 END) as onay_durum_sira
                    FROM mesai_kayitlari 
                    WHERE birimi = ?
                    ORDER BY onay_durum_sira ASC, tarih DESC
                """
                df_onay = pd.read_sql_query(query, conn, params=(current_unit,))
            conn.close()

            if not df_onay.empty:
                if bekleyen_onay_sayisi > 0:
                    st.warning(
                        f"⚠️ **{bekleyen_onay_sayisi} adet** onay bekleyen mesai kaydı bulunmaktadır."
                    )
                else:
                    st.success("🎉 Tüm mesai kayıtları onaylanmıştır.")

                for idx, row in df_onay.iterrows():
                    is_own_record = (
                        current_role == "SORUMLU"
                        and row["personel_ad_soyad"] == current_user
                    )

                    onay_bekliyor_mu = (
                        row["birim_sorumlusu_onay"] == 0
                        if (current_role == "SORUMLU" and not is_own_record)
                        else (
                            row["birim_sorumlusu_onay"] == 0
                            or row["isletme_muduru_onay"] == 0
                        )
                    )

                    durum_etiketi = (
                        "⏳ [ONAY BEKLİYOR]"
                        if onay_bekliyor_mu
                        else "✅ [TAMAMLANDI]"
                    )
                    fm_etiketi = (
                        "🔴 [FAZLA MESAİ VAR]"
                        if row["fazla_mesai"] == "Yaptım"
                        else ""
                    )

                    b_color = birim_renk_map.get(row["birimi"], "#007bff")
                    baslik = f"{durum_etiketi} {fm_etiketi} 📌 {row['tarih']} - {row['personel_ad_soyad']} ({row['birimi']})"

                    st.markdown(
                        f"<div style='border-left: 6px solid {b_color}; padding-left: 6px; margin-top: 10px;'><b>{row['birimi']}</b></div>",
                        unsafe_allow_html=True,
                    )

                    with st.expander(baslik, expanded=onay_bekliyor_mu):
                        if row["fazla_mesai"] == "Yaptım":
                            st.error(
                                "🚨 **FAZLA MESAİ BİLDİRİMİ:** Personel bugün fazla mesai yaptığını bildirdi."
                            )

                        s_saat, s_metin = hesapla_calisma_suresi(
                            row["mesai_baslangic"], row["mesai_bitis"]
                        )

                        st.write(
                            f"**Giriş:** {row['mesai_baslangic']} | **Çıkış:** {row['mesai_bitis']} | **Günlük Çalışma:** **{s_metin}** | **Fazla Mesai:** **{row['fazla_mesai']}**"
                        )

                        col_o1, col_o2, col_o3 = st.columns(3)

                        with col_o1:
                            bs_durum = (
                                "✅ Onaylandı"
                                if row["birim_sorumlusu_onay"] == 1
                                else "⏳ Bekliyor"
                            )
                            st.write(f"**Birim Sorumlusu Onayı:** {bs_durum}")

                            if is_own_record:
                                st.caption(
                                    "ℹ️ *Birim sorumlusu kendi kaydını onaylayamaz. Onay doğrudan İşletme Müdürüne iletilmiştir.*"
                                )
                            elif (
                                row["birim_sorumlusu_onay"] == 0
                                and st.button(
                                    "Birim Sorumlusu Olarak Onayla",
                                    key=f"bs_{row['id']}_{idx}",
                                )
                            ):
                                conn = sqlite3.connect("mesai_takip.db")
                                c = conn.cursor()
                                c.execute(
                                    "UPDATE mesai_kayitlari SET birim_sorumlusu_onay = 1 WHERE id = ?",
                                    (row["id"],),
                                )
                                conn.commit()
                                conn.close()
                                st.rerun()

                        with col_o2:
                            im_durum = (
                                "✅ Onaylandı"
                                if row["isletme_muduru_onay"] == 1
                                else "⏳ Bekliyor"
                            )
                            st.write(f"**İşletme Müdürü Onayı:** {im_durum}")
                            if current_role == "MUDUR":
                                if row["isletme_muduru_onay"] == 0:
                                    if st.button(
                                        "İşletme Müdürü Olarak Onayla",
                                        key=f"im_{row['id']}_{idx}",
                                    ):
                                        conn = sqlite3.connect(
                                            "mesai_takip.db"
                                        )
                                        c = conn.cursor()
                                        c.execute(
                                            "UPDATE mesai_kayitlari SET isletme_muduru_onay = 1 WHERE id = ?",
                                            (row["id"],),
                                        )
                                        conn.commit()
                                        conn.close()
                                        st.rerun()
                                else:
                                    if st.button(
                                        "↩️ Müdür Onayını İptal Et",
                                        key=f"im_cancel_{row['id']}_{idx}",
                                    ):
                                        conn = sqlite3.connect(
                                            "mesai_takip.db"
                                        )
                                        c = conn.cursor()
                                        c.execute(
                                            "UPDATE mesai_kayitlari SET isletme_muduru_onay = 0 WHERE id = ?",
                                            (row["id"],),
                                        )
                                        conn.commit()
                                        conn.close()
                                        st.rerun()

                        with col_o3:
                            if current_role == "MUDUR":
                                if st.button(
                                    "🗑️ Kaydı Tamamen Sil",
                                    key=f"del_m_rec_{row['id']}_{idx}",
                                ):
                                    conn = sqlite3.connect("mesai_takip.db")
                                    c = conn.cursor()
                                    c.execute(
                                        "DELETE FROM mesai_kayitlari WHERE id = ?",
                                        (row["id"],),
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.info("Mesai kaydı veritabanından silindi.")
                                    st.rerun()
            else:
                st.info("Kayıtlı mesai verisi bulunmamaktadır.")

        # DÜZELTME / GÜNCELLEME TALEPLERİ
        elif "Düzeltme" in selected_sub_tab:
            st.subheader("Gelen Düzeltme / Güncelleme Talepleri")

            if bekleyen_duzeltme_sayisi > 0:
                st.error(
                    f"🔔 **{bekleyen_duzeltme_sayisi} adet** bekleyen düzeltme / güncelleme talebi var!"
                )

            conn = sqlite3.connect("mesai_takip.db")
            c = conn.cursor()
            if current_role == "MUDUR":
                c.execute(
                    "SELECT * FROM duzeltme_talepleri WHERE durum = 'Bekliyor' ORDER BY id DESC"
                )
            else:
                c.execute(
                    "SELECT * FROM duzeltme_talepleri WHERE durum = 'Bekliyor' AND birimi = ? ORDER BY id DESC",
                    (current_unit,),
                )
            talepler = c.fetchall()
            conn.close()

            if talepler:
                for idx_t, t in enumerate(talepler):
                    t_id = t[0]
                    m_id = t[1]
                    p_ad = t[2]
                    t_tarih = t[3]
                    birim = t[4]
                    m_bas = t[5]
                    m1_c = t[6]
                    m1_b = t[7]
                    o_bas = t[8]
                    o_bit = t[9]
                    m2_c = t[10]
                    m2_b = t[11]
                    m_bit = t[12]
                    f_mesai = t[13]

                    s_saat, s_metin = hesapla_calisma_suresi(m_bas, m_bit)

                    fm_etiketi = (
                        "🔴 **[FAZLA MESAİ VAR]**" if f_mesai == "Yaptım" else ""
                    )
                    b_color = birim_renk_map.get(birim, "#007bff")

                    st.markdown(
                        f"<div style='border-left: 6px solid {b_color}; padding-left: 6px; margin-top: 10px;'><b>{birim}</b></div>",
                        unsafe_allow_html=True,
                    )

                    with st.expander(
                        f"📩 Düzeltme Talebi: {t_tarih} - {p_ad} ({birim}) {fm_etiketi}",
                        expanded=True,
                    ):
                        if f_mesai == "Yaptım":
                            st.error(
                                "🚨 **FAZLA MESAİ BİLDİRİMİ:** Düzeltme talebinde fazla mesai bildirildi."
                            )

                        st.write(
                            f"**Yeni Önerilen Giriş:** {m_bas} | **Yeni Önerilen Çıkış:** {m_bit} | **Yeni Çalışma Süresi:** **{s_metin}** | **Fazla Mesai:** **{f_mesai}**"
                        )
                        st.write(
                            f"**Mola 1:** {m1_c} - {m1_b} | **Öğle:** {o_bas} - {o_bit} | **Mola 2:** {m2_c} - {m2_b}"
                        )

                        col_dt1, col_dt2 = st.columns(2)
                        with col_dt1:
                            is_own_request = (
                                current_role == "SORUMLU"
                                and p_ad == current_user
                            )

                            if is_own_request:
                                st.caption(
                                    "ℹ️ *Birim sorumluları kendi düzeltme taleplerini onaylayamazlar. Onay İşletme Müdürü tarafından verilecektir.*"
                                )
                            else:
                                if st.button(
                                    "✅ Onayla ve Mesai Çizelgesine İşle",
                                    key=f"app_d_{t_id}_{idx_t}",
                                ):
                                    conn = sqlite3.connect("mesai_takip.db")
                                    c = conn.cursor()

                                    p_is_sorumlu = (
                                        personel_dict.get(p_ad, {}).get(
                                            "is_sorumlu", 0
                                        )
                                        == 1
                                    )
                                    req_bs_onay = 1 if p_is_sorumlu else 0

                                    if m_id == 0:
                                        c.execute(
                                            """
                                            INSERT INTO mesai_kayitlari 
                                            (personel_ad_soyad, tarih, birimi, mesai_baslangic, mola1_cikis, mola1_bitis, 
                                             ogle_baslangic, ogle_bitis, mola2_cikis, mola2_bitis, mesai_bitis, fazla_mesai,
                                             calisma_suresi_saat, calisma_suresi_metin, birim_sorumlusu_onay)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                            (
                                                p_ad,
                                                t_tarih,
                                                birim,
                                                m_bas,
                                                m1_c,
                                                m1_b,
                                                o_bas,
                                                o_bit,
                                                m2_c,
                                                m2_b,
                                                m_bit,
                                                f_mesai,
                                                s_saat,
                                                s_metin,
                                                req_bs_onay,
                                            ),
                                        )
                                    else:
                                        c.execute(
                                            """
                                            UPDATE mesai_kayitlari SET 
                                            birimi=?, mesai_baslangic=?, mola1_cikis=?, mola1_bitis=?, 
                                            ogle_baslangic=?, ogle_bitis=?, mola2_cikis=?, mola2_bitis=?, 
                                            mesai_bitis=?, fazla_mesai=?, calisma_suresi_saat=?, calisma_suresi_metin=?
                                            WHERE id=?
                                        """,
                                            (
                                                birim,
                                                m_bas,
                                                m1_c,
                                                m1_b,
                                                o_bas,
                                                o_bit,
                                                m2_c,
                                                m2_b,
                                                m_bit,
                                                f_mesai,
                                                s_saat,
                                                s_metin,
                                                m_id,
                                            ),
                                        )

                                    c.execute(
                                        "UPDATE duzeltme_talepleri SET durum = 'Onaylandi' WHERE id = ?",
                                        (t_id,),
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.success("Kayıt başarıyla işlendi!")
                                    st.rerun()

                        with col_dt2:
                            if not is_own_request:
                                if st.button(
                                    "🗑️ Talebi Reddet ve Kalıcı Olarak Sil",
                                    key=f"del_req_{t_id}_{idx_t}",
                                ):
                                    conn = sqlite3.connect("mesai_takip.db")
                                    c = conn.cursor()
                                    c.execute(
                                        "DELETE FROM duzeltme_talepleri WHERE id = ?",
                                        (t_id,),
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.info(
                                        "Talep reddedildi ve listeden silindi."
                                    )
                                    st.rerun()
            else:
                st.info(
                    "Bekleyen düzeltme veya güncelleme talebi bulunmamaktadır."
                )