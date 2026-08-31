from datetime import datetime, date
import io
import sqlite3
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
import streamlit as st

# 1. STREAMLIT SAYFA YAPILANDIRMASI
st.set_page_config(
    page_title="AFSÜ Mesai & İzin",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. GÖRSELDEKİ MODERN MOBİL TEMA VE CSS YAPI
st.markdown("""
    <style>
        /* Genel Arka Plan ve Tipografi */
        .stApp {
            background-color: #f6f8fa !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Header / Footer / Varsayılan Öğeleri Gizle */
        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 100000 !important;
        }
        .main .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 5rem !important;
            max-width: 500px !important; /* Mobil Ekran Genişliği Limiti */
            margin: 0 auto;
        }

        /* 🟢 CANLI MESAİ KARTI (Lacivert Card) */
        .live-card {
            background: linear-gradient(135deg, #0f3458 0%, #164370 100%);
            border-radius: 24px;
            padding: 24px;
            color: white;
            box-shadow: 0 10px 25px rgba(15, 52, 88, 0.15);
            margin-bottom: 20px;
            position: relative;
        }
        .live-status-badge {
            background-color: rgba(255, 255, 255, 0.15);
            color: #4cd964;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
        }
        .live-time-title {
            color: #a0b2c6;
            font-size: 13px;
            margin-top: 18px;
            margin-bottom: 2px;
        }
        .live-time-clock {
            font-size: 42px;
            font-weight: 800;
            letter-spacing: -1px;
            line-height: 1;
            margin-bottom: 12px;
        }
        .live-elapsed {
            position: absolute;
            right: 24px;
            top: 65px;
            text-align: right;
        }
        .live-elapsed-val {
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
        }

        /* BEYAZ KART YAPISI (Plan & Özet Kartları) */
        .white-card {
            background: #ffffff;
            border-radius: 20px;
            padding: 18px 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
            border: 1px solid #eaeaea;
        }
        .card-title {
            font-size: 18px;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 12px;
        }
        .plan-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .plan-item:last-child { border-bottom: none; }

        /* MOBİL TURUNCU BUTON */
        .stButton > button {
            background-color: #e85d35 !important;
            color: white !important;
            border: none !important;
            border-radius: 14px !important;
            height: 3.4rem !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            box-shadow: 0 6px 15px rgba(232, 93, 53, 0.25) !important;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #d44c26 !important;
            transform: translateY(-1px);
        }

        /* METRİK VE STAT KARTLARI (Raporlar Sayfası) */
        .stat-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 15px;
        }
        .stat-box {
            background: #ffffff;
            border-radius: 18px;
            padding: 16px;
            border: 1px solid #eaeaea;
        }
        .stat-number {
            font-size: 28px;
            font-weight: 800;
            color: #0f3458;
        }
        .stat-label {
            font-size: 12px;
            color: #7a8b9e;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- VERİTABANI VE YARDIMCI MANTIKLAR -----------------
def tr_to_pdf_text(text):
    if not isinstance(text, str): return text
    subst = {"ı": "i", "İ": "I", "ğ": "g", "Ğ": "G", "Ş": "S", "ş": "s", "Ç": "C", "ç": "c", "Ö": "O", "ö": "o", "Ü": "U", "ü": "u"}
    for search, replace in subst.items(): text = text.replace(search, replace)
    return text

def hesapla_calisma_suresi(baslangic_str, bitis_str):
    try:
        if not baslangic_str or not bitis_str: return 0.0, "-"
        fmt = "%H:%M"
        t_bas = datetime.strptime(str(baslangic_str).strip(), fmt)
        t_bit = datetime.strptime(str(bitis_str).strip(), fmt)
        fark = t_bit - t_bas
        toplam_dakika = int(fark.total_seconds() / 60)
        if toplam_dakika < 0: return 0.0, "Geçersiz"
        saat = toplam_dakika // 60
        dakika = toplam_dakika % 60
        return round(toplam_dakika / 60, 2), f"{saat}s {dakika}dk" if dakika > 0 else f"{saat}s"
    except Exception: return 0.0, "-"

def init_db():
    conn = sqlite3.connect("mesai_takip.db", timeout=10)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mesai_kayitlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT, personel_ad_soyad TEXT, tarih TEXT, birimi TEXT,
            mesai_baslangic TEXT, mola1_cikis TEXT, mola1_bitis TEXT, ogle_baslangic TEXT, ogle_bitis TEXT,
            mola2_cikis TEXT, mola2_bitis TEXT, mesai_bitis TEXT, fazla_mesai TEXT, calisma_suresi_saat REAL DEFAULT 0.0,
            calisma_suresi_metin TEXT DEFAULT '', birim_sorumlusu_onay INTEGER DEFAULT 0, isletme_muduru_onay INTEGER DEFAULT 0,
            UNIQUE(personel_ad_soyad, tarih)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS personeller (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT UNIQUE, birim_adi TEXT DEFAULT '',
            is_birim_sorumlusu INTEGER DEFAULT 0, sifre TEXT DEFAULT '1111', durum TEXT DEFAULT 'Aktif'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS duzeltme_talepleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT, mesai_id INTEGER, personel_ad_soyad TEXT, tarih TEXT, birimi TEXT,
            mesai_baslangic TEXT, mola1_cikis TEXT, mola1_bitis TEXT, ogle_baslangic TEXT, ogle_bitis TEXT,
            mola2_cikis TEXT, mola2_bitis TEXT, mesai_bitis TEXT, fazla_mesai TEXT, calisma_suresi_saat REAL DEFAULT 0.0,
            calisma_suresi_metin TEXT DEFAULT '', durum TEXT DEFAULT 'Bekliyor'
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_personeller_data():
    conn = sqlite3.connect("mesai_takip.db", timeout=10)
    c = conn.cursor()
    c.execute("SELECT ad_soyad, birim_adi, is_birim_sorumlusu, sifre, durum FROM personeller ORDER BY ad_soyad ASC")
    rows = c.fetchall()
    conn.close()
    return rows

# SESSION STATE İLKLEME
if "auth_role" not in st.session_state: st.session_state["auth_role"] = None
if "auth_unit" not in st.session_state: st.session_state["auth_unit"] = None
if "auth_user_name" not in st.session_state: st.session_state["auth_user_name"] = ""
if "current_nav" not in st.session_state: st.session_state["current_nav"] = "Ana Sayfa"

personel_raw = get_personeller_data()
personel_dict = {row[0]: {"birim": row[1], "is_sorumlu": row[2], "sifre": row[3], "durum": row[4]} for row in personel_raw}
active_personel_names = [p for p, d in personel_dict.items() if d["durum"] == "Aktif"]

# ----------------- ÜST BAŞLIK / HEADER -----------------
bugun_str = datetime.now().strftime("%d %B %Y %A")

col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.caption(f"{bugun_str}")
    kullanici_ad = st.session_state["auth_user_name"] if st.session_state["auth_user_name"] else "Misafir"
    st.markdown(f"<h2 style='margin:0; padding:0; font-weight:800; color:#0f3458;'>Günaydın, {kullanici_ad.split()[0]}</h2>", unsafe_allow_html=True)
with col_head2:
    st.write("")
    if st.session_state["auth_role"]:
        if st.button("🚪", help="Oturumu Kapat"):
            st.session_state["auth_role"] = None
            st.session_state["auth_user_name"] = ""
            st.rerun()

st.write("")

# ----------------- OTURUM AÇIK DEĞİLSE GİRİŞ EKRANI -----------------
if st.session_state["auth_role"] is None:
    st.markdown("""
        <div class="white-card">
            <div class="card-title">🔑 Kurumsal Giriş</div>
            <p style="color:#7a8b9e; font-size:14px;">Lütfen devam etmek için adınızı ve şifrenizi giriniz.</p>
        </div>
    """, unsafe_allow_html=True)
    
    secilen_kullanici = st.selectbox("Kullanıcı Adı Seçiniz:", options=["İşletme Müdürü"] + active_personel_names)
    pass_in = st.text_input("Şifre:", type="password")
    
    if st.button("Sisteme Giriş Yap"):
        if secilen_kullanici == "İşletme Müdürü" and pass_in == "1234":
            st.session_state["auth_role"] = "MUDUR"
            st.session_state["auth_unit"] = "ALL"
            st.session_state["auth_user_name"] = "İşletme Müdürü"
            st.rerun()
        elif secilen_kullanici in personel_dict and pass_in == personel_dict[secilen_kullanici]["sifre"]:
            is_s = personel_dict[secilen_kullanici]["is_sorumlu"] == 1
            st.session_state["auth_role"] = "SORUMLU" if is_s else "PERSONEL"
            st.session_state["auth_unit"] = personel_dict[secilen_kullanici]["birim"]
            st.session_state["auth_user_name"] = secilen_kullanici
            st.rerun()
        else:
            st.error("Hatalı Şifre veya Kullanıcı Seçimi!")

else:
    # ----------------- AFSÜ MOBİL SEKMELERİ -----------------
    # GÖRSELDEKİ ALT GEZİNME BARININ YERİNİ TUTAN MODÜLER TABLAR
    tab_ana, tab_izin, tab_rapor = st.tabs(["🏠 Ana Sayfa", "📅 İzinler", "📊 Raporlar"])

    # 1. TAB: ANA SAYFA (CANLI DOKU & BEYAZ KARTLAR)
    with tab_ana:
        # Görseldeki Lacivert Canlı Mesai Kartı
        st.markdown("""
            <div class="live-card">
                <span class="live-status-badge">🟢 Mesain Başladı</span>
                <div class="live-elapsed">
                    <div style="font-size:11px; color:#a0b2c6; text-transform:uppercase;">GEÇEN SÜRE</div>
                    <div class="live-elapsed-val">02s 18dk</div>
                </div>
                <div class="live-time-title">Giriş Saatin</div>
                <div class="live-time-clock">08:27</div>
                <div style="font-size:13px; color:#d0e0f0;">📍 AFSÜ İşletme Yerleşkesi</div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("↪ 🟢 Çıkış Yap / Mesaiyi Bitir"):
            st.toast("Mesai çıkış kaydınız başarıyla alındı!")

        st.markdown("<br/>", unsafe_allow_html=True)

        # Görseldeki "Bugünün Planı" Kartı
        st.markdown("""
            <div class="white-card">
                <div class="card-title">Bugünün Planı</div>
                <div class="plan-item">
                    <div>
                        <span style="color:#e85d35; font-size:18px;">☕</span> <b>Öğle Arası</b>
                        <div style="font-size:12px; color:#7a8b9e;">12:30 - 13:30</div>
                    </div>
                    <span style="background:#f4f6f8; padding:4px 10px; border-radius:10px; font-size:12px; font-weight:600;">Planlandı</span>
                </div>
                <div class="plan-item">
                    <div>
                        <span style="color:#0f3458; font-size:18px;">🏁</span> <b>Mesai Bitişi</b>
                        <div style="font-size:12px; color:#7a8b9e;">Günün planlanan çıkışı</div>
                    </div>
                    <span style="background:#f4f6f8; padding:4px 10px; border-radius:10px; font-size:12px; font-weight:600;">17:30</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 2. TAB: İZİNLER
    with tab_izin:
        st.markdown("""
            <div class="live-card" style="background: linear-gradient(135deg, #0f3458 0%, #1c5288 100%);">
                <div style="font-size:13px; color:#a0b2c6;">2026 İzin Bakiyen</div>
                <div style="font-size:36px; font-weight:800; margin:4px 0;">11 gün</div>
                <div style="font-size:12px; color:#d0e0f0;">2 gün kullanıldı · 13 gün tanımlı</div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("izin_form"):
            st.subheader("Yeni İzin Talebi")
            izin_turu = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık İzni"])
            bas_tarih = st.date_input("Başlangıç Tarihi")
            bit_tarih = st.date_input("Bitiş Tarihi")
            aciklama = st.text_area("Açıklama (İsteğe Bağlı)")
            
            if st.form_submit_button("Talebi Yöneticime İlet"):
                st.success("İzin talebiniz oluşturuldu ve onay sistemine iletildi.")

    # 3. TAB: RAPORLAR VE OPERASYON
    with tab_rapor:
        st.markdown("<h3 style='color:#0f3458;'>Operasyon Görünümü</h3>", unsafe_allow_html=True)
        
        # Görseldeki 4'lü Stat Grid Yapısı
        st.markdown("""
            <div class="stat-grid">
                <div class="stat-box">
                    <div class="stat-label">Toplam Ekip</div>
                    <div class="stat-number">75</div>
                    <div style="font-size:11px; color:#7a8b9e;">personel</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Dakiklik</div>
                    <div class="stat-number" style="color:#2e7d32;">%94.6</div>
                    <div style="font-size:11px; color:#7a8b9e;">zamanında giriş</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Bugün Giriş</div>
                    <div class="stat-number">68</div>
                    <div style="font-size:11px; color:#7a8b9e;">aktif çalışan</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Onay Bekleyen</div>
                    <div class="stat-number" style="color:#e85d35;">3</div>
                    <div style="font-size:11px; color:#7a8b9e;">açık mesai kaydı</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Mevcut SQLite veritabanı çizelgesi tablosu
        conn = sqlite3.connect("mesai_takip.db", timeout=10)
        df_mesai = pd.read_sql_query("SELECT * FROM mesai_kayitlari ORDER BY id DESC LIMIT 10", conn)
        conn.close()

        if not df_mesai.empty:
            st.markdown("<b>Son Kayıtlar</b>", unsafe_allow_html=True)
            st.dataframe(df_mesai[["personel_ad_soyad", "tarih", "mesai_baslangic", "mesai_bitis", "fazla_mesai"]], use_container_width=True)
        else:
            st.info("Henüz raporlanacak mesai verisi yok.")
