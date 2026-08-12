import yfinance as yf
import pandas as pd
import time
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════
# E-POSTA AYARLARI (GitHub Secrets'ten okunur)
# ═══════════════════════════════════════════════════════════════
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "")
EMAIL_TO = os.environ.get("EMAIL_TO", EMAIL_USER)

def email_gonder(konu, icerik_html):
    if not EMAIL_USER or not EMAIL_APP_PASSWORD:
        print("⚠️ E-posta ayarları eksik, bildirim atlanıyor.")
        return

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = konu
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_TO

        msg.attach(MIMEText(icerik_html, 'html', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
        
        print("✅ E-posta başarıyla gönderildi!")
    except Exception as e:
        print(f"❌ E-posta gönderim hatası: {e}")

# ═══════════════════════════════════════════════════════════════
# BIST 100 HİSSELERİ
# ═══════════════════════════════════════════════════════════════
hisseler = [
    "AEFES.IS", "AGHOL.IS", "AKBNK.IS", "AKSA.IS", "AKSEN.IS",
    "ALARK.IS", "ALBRK.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS",
    "BERA.IS", "BIMAS.IS", "BINHO.IS", "BRSAN.IS", "BRYAT.IS",
    "BTCIM.IS", "CANTE.IS", "CCOLA.IS", "CIMSA.IS", "CVKMD.IS",
    "DOAS.IS", "DOHOL.IS", "DSTKF.IS", "ECILC.IS", "ECZYT.IS",
    "EGEEN.IS", "EKGYO.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS",
    "EREGL.IS", "EUREN.IS", "FENER.IS", "FROTO.IS", "GARAN.IS",
    "GENIL.IS", "GESAN.IS", "GUBRF.IS", "HALKB.IS", "HEKTS.IS",
    "ISCTR.IS", "ISMEN.IS", "KARSN.IS", "KCHOL.IS", "KLGYO.IS",
    "KONTR.IS", "KONYA.IS", "KRDMD.IS", "KTLEV.IS", "KUYAS.IS",
    "MAGEN.IS", "MAVI.IS", "MGROS.IS", "MIATK.IS", "MPARK.IS",
    "OBAMS.IS", "ODAS.IS", "ODINE.IS", "OTKAR.IS", "OYAKC.IS",
    "PAHOL.IS", "PASEU.IS", "PETKM.IS", "PGSUS.IS", "PSGYO.IS",
    "REEDR.IS", "RALYH.IS", "SAHOL.IS", "SARKY.IS", "SASA.IS",
    "SISE.IS", "SKBNK.IS", "SMRTG.IS", "SOKM.IS", "TABGD.IS",
    "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS", "TMSN.IS",
    "TOASO.IS", "TRALT.IS", "TRGYO.IS", "TSKB.IS", "TSPOR.IS",
    "TTRAK.IS", "TUKAS.IS", "TUPRS.IS", "TURSG.IS", "ULKER.IS",
    "VAKBN.IS", "VESTL.IS", "YEOTK.IS", "YKBNK.IS", "MERKO.IS",
    "XU100.IS", "ZOREN.IS"
]

# ═══════════════════════════════════════════════════════════════
# ÖNCEKİ SİNYALLERİ OKU
# ═══════════════════════════════════════════════════════════════
JSON_DOSYA = "onceki_sinyaller.json"
onceki_sinyaller = {}

if os.path.exists(JSON_DOSYA):
    try:
        with open(JSON_DOSYA, 'r', encoding='utf-8') as f:
            onceki_sinyaller = json.load(f)
        print(f"📂 Önceki sinyaller yüklendi ({len(onceki_sinyaller)} hisse)")
    except Exception as e:
        print(f"⚠️ Önceki sinyaller okunamadı: {e}")

sonuclar = []
yeni_sinyaller = {}
degisen_hisseler = []

print("=" * 80)
print(f"BIST 100 - 4H Teknik Analiz | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print(f"{'Hisse':<10} {'Canlı':>10} {'Kapanış':>10} {'EMA9':>10} {'EMA21':>10} {'SMA50':>10} {'Sinyal':<14}")
print("-" * 80)

for hisse in hisseler:
    try:
        t = yf.Ticker(hisse)
        canli_fiyat = t.fast_info.last_price

        df = yf.download(hisse, period="60d", interval="1h",
                         progress=False, auto_adjust=False)

        if df.empty or len(df) < 10:
            print(f"{hisse:<10} {'VERİ YOK':>60}")
            time.sleep(1.5)
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df_4h = df.resample('4h').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min',
            'Close': 'last', 'Volume': 'sum'
        }).dropna()

        if len(df_4h) < 50:
            print(f"{hisse:<10} {'YETERSİZ BAR':>60}")
            time.sleep(1.5)
            continue

        df_4h['EMA9']  = df_4h['Close'].ewm(span=9,  adjust=False).mean()
        df_4h['EMA21'] = df_4h['Close'].ewm(span=21, adjust=False).mean()
        df_4h['SMA50'] = df_4h['Close'].rolling(window=50).mean()

        son = df_4h.iloc[-1]
        kapanis = float(son['Close'])
        ema9  = float(son['EMA9'])
        ema21 = float(son['EMA21'])
        sma50 = float(son['SMA50'])

        if canli_fiyat > ema9 > ema21 > sma50:
            sinyal = "GÜÇLÜ AL"
        elif canli_fiyat > ema9 > ema21:
            sinyal = "AL"
        elif canli_fiyat < ema9 < ema21 < sma50:
            sinyal = "GÜÇLÜ SAT"
        elif canli_fiyat < ema9 < ema21:
            sinyal = "SAT"
        elif ema9 > ema21 and canli_fiyat > ema9:
            sinyal = "YUKARI"
        elif ema9 < ema21 and canli_fiyat < ema9:
            sinyal = "AŞAĞI"
        else:
            sinyal = "NÖTR"

        hisse_kodu = hisse.replace('.IS', '')
        yeni_sinyaller[hisse_kodu] = sinyal

        if hisse_kodu in onceki_sinyaller:
            eski_sinyal = onceki_sinyaller[hisse_kodu]
            if eski_sinyal != sinyal:
                degisen_hisseler.append({
                    'hisse': hisse_kodu,
                    'eski': eski_sinyal,
                    'yeni': sinyal,
                    'fiyat': round(canli_fiyat, 2),
                    'ema9': round(ema9, 2),
                    'ema21': round(ema21, 2),
                    'sma50': round(sma50, 2)
                })

        sonuclar.append({
            'Hisse': hisse_kodu,
            'Canli_Fiyat': round(canli_fiyat, 2),
            'Son_Kapanis': round(kapanis, 2),
            'EMA9':  round(ema9, 2),
            'EMA21': round(ema21, 2),
            'SMA50': round(sma50, 2),
            'Sinyal': sinyal,
            'Tarih': str(son.name)
        })

        print(f"{hisse_kodu:<10} {canli_fiyat:>10.2f} {kapanis:>10.2f} "
              f"{ema9:>10.2f} {ema21:>10.2f} {sma50:>10.2f} {sinyal:<14}")

    except Exception as e:
        print(f"{hisse:<10} {'HATA: ' + str(e)[:45]:>60}")

    time.sleep(1.5)

print("=" * 80)
print(f"Toplam: {len(sonuclar)} / {len(hisseler)} hisse başarıyla çekildi.")

# ═══════════════════════════════════════════════════════════════
# SİNYAL DEĞİŞİMİ VARSA E-POSTA GÖNDER
# ═══════════════════════════════════════════════════════════════
if degisen_hisseler:
    print(f"\n🔔 {len(degisen_hisseler)} hisste sinyal değişimi tespit edildi!")
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color: #1F4E78;">📊 BIST 100 Sinyal Değişimi</h2>
        <p><strong>Tarih:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        <hr>
        <table style="border-collapse: collapse; width: 100%; font-size: 14px;">
            <tr style="background: #1F4E78; color: white;">
                <th style="padding: 8px; border: 1px solid #ddd;">Hisse</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Fiyat</th>
                <th style="padding: 8px; border: 1px solid #ddd;">EMA9</th>
                <th style="padding: 8px; border: 1px solid #ddd;">EMA21</th>
                <th style="padding: 8px; border: 1px solid #ddd;">SMA50</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Önceki</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Yeni Sinyal</th>
            </tr>
    """
    
    renkler = {
        "GÜÇLÜ AL": "#C6EFCE", "AL": "#E2EFDA",
        "GÜÇLÜ SAT": "#FFC7CE", "SAT": "#FFEB9C",
        "YUKARI": "#FFF2CC", "AŞAĞI": "#FFF2CC", "NÖTR": "#F2F2F2"
    }
    
    for d in degisen_hisseler:
        eski_renk = renkler.get(d['eski'], "#F2F2F2")
        yeni_renk = renkler.get(d['yeni'], "#F2F2F2")
        html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{d['hisse']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">₺{d['fiyat']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{d['ema9']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{d['ema21']}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{d['sma50']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; background: {eski_renk};">{d['eski']}</td>
                <td style="padding: 8px; border: 1px solid #ddd; background: {yeni_renk}; font-weight: bold;">{d['yeni']}</td>
            </tr>
        """
    
    html += "</table></body></html>"
    
    email_gonder("🔔 BIST 100 Sinyal Değişimi!", html)
else:
    print("\n✅ Sinyal değişimi yok.")

# ═══════════════════════════════════════════════════════════════
# YENİ SİNYALLERİ KAYDET
# ═══════════════════════════════════════════════════════════════
with open(JSON_DOSYA, 'w', encoding='utf-8') as f:
    json.dump(yeni_sinyaller, f, ensure_ascii=False, indent=2)
print(f"💾 Yeni sinyaller kaydedildi: {JSON_DOSYA}")

# ═══════════════════════════════════════════════════════════════
# GÜNLÜK ÖZET E-POSTASI (Her çalışmada - TABLO HALİNDE)
# ═══════════════════════════════════════════════════════════════
if sonuclar:
    df_sonuc = pd.DataFrame(sonuclar)
    print("\n📊 ÖZET TABLO:")
    print(df_sonuc[['Hisse','Canli_Fiyat','EMA9','EMA21','SMA50','Sinyal']].to_string(index=False))
    
    # Sinyal renkleri
    sinyal_renk = {
        "GÜÇLÜ AL": ("#C6EFCE", "#006100"),
        "AL": ("#E2EFDA", "#375623"),
        "GÜÇLÜ SAT": ("#FFC7CE", "#9C0006"),
        "SAT": ("#FFEB9C", "#9C5700"),
        "YUKARI": ("#FFF2CC", "#000000"),
        "AŞAĞI": ("#FFF2CC", "#000000"),
        "NÖTR": ("#F2F2F2", "#000000")
    }
    
    # Önceki çalıştırmadan değişenler özeti (günlük mailin en üstüne)
    degisim_ozeti = ""
    if degisen_hisseler:
        degisim_ozeti = f"""
        <div style="background: #E7F3FF; border-left: 4px solid #1F4E78; padding: 12px; margin-bottom: 20px;">
            <h3 style="margin: 0 0 8px 0; color: #1F4E78;">🔄 Son Çalıştırmadan Değişenler ({len(degisen_hisseler)})</h3>
            <p style="margin: 0;">
        """
        for d in degisen_hisseler:
            degisim_ozeti += f"<b>{d['hisse']}</b>: {d['eski']} → {d['yeni']} | "
        degisim_ozeti += "</p></div>"
    
    # GÜÇLÜ AL tablosu
    guclu_al_df = df_sonuc[df_sonuc['Sinyal'] == 'GÜÇLÜ AL'][['Hisse','Canli_Fiyat','EMA9','EMA21','SMA50','Sinyal']]
    guclu_sat_df = df_sonuc[df_sonuc['Sinyal'] == 'GÜÇLÜ SAT'][['Hisse','Canli_Fiyat','EMA9','EMA21','SMA50','Sinyal']]
    
    def tablo_olustur(df, baslik, baslik_renk):
        if df.empty:
            return f"<h3 style='color:{baslik_renk};'>{baslik} (0)</h3><p>Hiç yok.</p>"
        
        html = f"<h3 style='color:{baslik_renk};'>{baslik} ({len(df)})</h3>"
        html += """<table style="border-collapse: collapse; width: 100%; font-size: 13px; margin-bottom: 20px;">
            <tr style="background: #1F4E78; color: white;">
                <th style="padding: 6px; border: 1px solid #ddd;">Hisse</th>
                <th style="padding: 6px; border: 1px solid #ddd;">Fiyat</th>
                <th style="padding: 6px; border: 1px solid #ddd;">EMA9</th>
                <th style="padding: 6px; border: 1px solid #ddd;">EMA21</th>
                <th style="padding: 6px; border: 1px solid #ddd;">SMA50</th>
                <th style="padding: 6px; border: 1px solid #ddd;">Sinyal</th>
            </tr>"""
        
        for _, row in df.iterrows():
            bg, fg = sinyal_renk.get(row['Sinyal'], ("#F2F2F2", "#000000"))
            html += f"""
            <tr style="background: {bg}; color: {fg};">
                <td style="padding: 6px; border: 1px solid #ddd; font-weight: bold;">{row['Hisse']}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">₺{row['Canli_Fiyat']}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">{row['EMA9']}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">{row['EMA21']}</td>
                <td style="padding: 6px; border: 1px solid #ddd;">{row['SMA50']}</td>
                <td style="padding: 6px; border: 1px solid #ddd; font-weight: bold;">{row['Sinyal']}</td>
            </tr>"""
        html += "</table>"
        return html
    
    html_ozet = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #1F4E78;">📈 BIST 100 Günlük Özet</h2>
        <p><strong>{datetime.now().strftime('%d.%m.%Y %H:%M')}</strong></p>
        {degisim_ozeti}
        <hr>
        {tablo_olustur(guclu_al_df, "🟢 GÜÇLÜ AL", "#006100")}
        {tablo_olustur(guclu_sat_df, "🔴 GÜÇLÜ SAT", "#9C0006")}
    </body></html>
    """
    
    email_gonder("📈 BIST 100 Günlük Özet", html_ozet)
