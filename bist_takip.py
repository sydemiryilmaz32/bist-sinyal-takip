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
# TEKNİK GÖSTERGELER (ta kütüphanesi)
# ═══════════════════════════════════════════════════════════════
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator
from ta.volatility import AverageTrueRange, BollingerBands

# ═══════════════════════════════════════════════════════════════
# E-POSTA AYARLARI
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
        print("✅ E-posta gönderildi!")
    except Exception as e:
        print(f"❌ E-posta hatası: {e}")

# ═══════════════════════════════════════════════════════════════
# BIST 100
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

print("=" * 100)
print(f"BIST 100 - 4H Teknik Analiz + Hedef/Stop | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)
print(f"{'Hisse':<8} {'Fiyat':>8} {'EMA9':>8} {'EMA21':>8} {'SMA50':>8} {'RSI':>6} {'MACD':>7} {'ADX':>5} {'Hedef':>8} {'Stop':>8} {'R/R':>5} {'Sinyal':<12}")
print("-" * 100)

for hisse in hisseler:
    try:
        t = yf.Ticker(hisse)
        canli_fiyat = t.fast_info.last_price

        df = yf.download(hisse, period="60d", interval="1h",
                         progress=False, auto_adjust=False)

        if df.empty or len(df) < 10:
            print(f"{hisse:<8} {'VERİ YOK':>90}")
            time.sleep(1.5)
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df_4h = df.resample('4h').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min',
            'Close': 'last', 'Volume': 'sum'
        }).dropna()

        if len(df_4h) < 50:
            print(f"{hisse:<8} {'YETERSİZ BAR':>90}")
            time.sleep(1.5)
            continue

        # ─── TEMEL ORTALAMALAR ───
        df_4h['EMA9']  = df_4h['Close'].ewm(span=9,  adjust=False).mean()
        df_4h['EMA21'] = df_4h['Close'].ewm(span=21, adjust=False).mean()
        df_4h['SMA50'] = df_4h['Close'].rolling(window=50).mean()

        son = df_4h.iloc[-1]
        kapanis = float(son['Close'])
        ema9  = float(son['EMA9'])
        ema21 = float(son['EMA21'])
        sma50 = float(son['SMA50'])

        # ─── GÖSTERGELER ───
        # RSI(14)
        rsi_val = RSIIndicator(df_4h['Close'], window=14).rsi().iloc[-1]
        rsi = round(rsi_val, 1) if pd.notna(rsi_val) else 50

        # MACD
        macd_ind = MACD(df_4h['Close'])
        macd_hist = macd_ind.macd_diff().iloc[-1]
        macd_str = f"{macd_hist:+.2f}" if pd.notna(macd_hist) else "0.00"

        # ADX(14) - Trend gücü
        adx_val = ADXIndicator(df_4h['High'], df_4h['Low'], df_4h['Close'], window=14).adx().iloc[-1]
        adx = round(adx_val, 1) if pd.notna(adx_val) else 0

        # ATR(14) - Hedef/Stop için
        atr_val = AverageTrueRange(df_4h['High'], df_4h['Low'], df_4h['Close'], window=14).average_true_range().iloc[-1]
        atr = atr_val if pd.notna(atr_val) else 0

        # Bollinger Bands (20,2)
        bb = BollingerBands(df_4h['Close'], window=20, window_dev=2)
        bb_upper = bb.bollinger_hband().iloc[-1]
        bb_lower = bb.bollinger_lband().iloc[-1]
        bb_pos = "ÜST" if canli_fiyat > bb_upper else "ALT" if canli_fiyat < bb_lower else "İÇİ"

        # ─── SİNYAL ───
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

        # ─── HEDEF / STOP (ATR Bazlı) ───
        atr_mult_hedef = 2.0
        atr_mult_stop = 1.5

        if "AL" in sinyal:
            hedef = round(canli_fiyat + (atr * atr_mult_hedef), 2)
            stop = round(canli_fiyat - (atr * atr_mult_stop), 2)
        elif "SAT" in sinyal:
            hedef = round(canli_fiyat - (atr * atr_mult_hedef), 2)
            stop = round(canli_fiyat + (atr * atr_mult_stop), 2)
        else:
            hedef = round(canli_fiyat + (atr * atr_mult_hedef), 2)
            stop = round(canli_fiyat - (atr * atr_mult_stop), 2)

        # Risk/Ödül
        risk = abs(canli_fiyat - stop)
        odul = abs(hedef - canli_fiyat)
        rr = round(odul / risk, 2) if risk > 0 else 0

        hisse_kodu = hisse.replace('.IS', '')
        yeni_sinyaller[hisse_kodu] = sinyal

        # Sinyal değişimi kontrolü
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
                    'sma50': round(sma50, 2),
                    'rsi': rsi,
                    'adx': adx,
                    'hedef': hedef,
                    'stop': stop,
                    'rr': rr
                })

        sonuclar.append({
            'Hisse': hisse_kodu,
            'Canli_Fiyat': round(canli_fiyat, 2),
            'EMA9': round(ema9, 2),
            'EMA21': round(ema21, 2),
            'SMA50': round(sma50, 2),
            'RSI': rsi,
            'MACD': macd_str,
            'ADX': adx,
            'Hedef': hedef,
            'Stop': stop,
            'RR': rr,
            'BB_Pos': bb_pos,
            'Sinyal': sinyal,
            'Tarih': str(son.name)
        })

        print(f"{hisse_kodu:<8} {canli_fiyat:>8.2f} {ema9:>8.2f} {ema21:>8.2f} {sma50:>8.2f} "
              f"{rsi:>6.1f} {macd_str:>7} {adx:>5.1f} {hedef:>8.2f} {stop:>8.2f} {rr:>5.2f} {sinyal:<12}")

    except Exception as e:
        print(f"{hisse:<8} {'HATA: ' + str(e)[:50]:>90}")

    time.sleep(1.5)

print("=" * 100)
print(f"Toplam: {len(sonuclar)} / {len(hisseler)} hisse başarıyla çekildi.")

# ═══════════════════════════════════════════════════════════════
# SİNYAL DEĞİŞİMİ MAILİ
# ═══════════════════════════════════════════════════════════════
if degisen_hisseler:
    print(f"\n🔔 {len(degisen_hisseler)} hisste sinyal değişimi!")

    html = f"""
    <html><body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #1F4E78;">📊 BIST 100 — Sinyal Değişimi</h2>
    <p><strong>{datetime.now().strftime('%d.%m.%Y %H:%M')}</strong></p>
    <hr>
    <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
      <tr style="background: #1F4E78; color: white;">
        <th style="padding: 7px; border: 1px solid #ccc;">Hisse</th>
        <th style="padding: 7px; border: 1px solid #ccc;">Fiyat</th>
        <th style="padding: 7px; border: 1px solid #ccc;">EMA9</th>
        <th style="padding: 7px; border: 1px solid #ccc;">EMA21</th>
        <th style="padding: 7px; border: 1px solid #ccc;">SMA50</th>
        <th style="padding: 7px; border: 1px solid #ccc;">RSI</th>
        <th style="padding: 7px; border: 1px solid #ccc;">ADX</th>
        <th style="padding: 7px; border: 1px solid #ccc;">Hedef</th>
        <th style="padding: 7px; border: 1px solid #ccc;">Stop</th>
        <th style="padding: 7px; border: 1px solid #ccc;">R/R</th>
        <th style="padding: 7px; border: 1px solid #ccc;">Önceki</th>
        <th style="padding: 7px; border: 1px solid #ccc;">Yeni</th>
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
        # RSI renk
        rsi_renk = "#FF9999" if d['rsi'] > 70 else "#99FF99" if d['rsi'] < 30 else "#FFFFFF"
        # ADX yorum
        adx_yorum = "💪" if d['adx'] > 25 else ""

        html += f"""
        <tr>
          <td style="padding: 7px; border: 1px solid #ccc; font-weight: bold;">{d['hisse']}</td>
          <td style="padding: 7px; border: 1px solid #ccc;">₺{d['fiyat']}</td>
          <td style="padding: 7px; border: 1px solid #ccc;">{d['ema9']}</td>
          <td style="padding: 7px; border: 1px solid #ccc;">{d['ema21']}</td>
          <td style="padding: 7px; border: 1px solid #ccc;">{d['sma50']}</td>
          <td style="padding: 7px; border: 1px solid #ccc; background: {rsi_renk};">{d['rsi']}</td>
          <td style="padding: 7px; border: 1px solid #ccc;">{d['adx']} {adx_yorum}</td>
          <td style="padding: 7px; border: 1px solid #ccc; color: #006100; font-weight: bold;">₺{d['hedef']}</td>
          <td style="padding: 7px; border: 1px solid #ccc; color: #9C0006; font-weight: bold;">₺{d['stop']}</td>
          <td style="padding: 7px; border: 1px solid #ccc; font-weight: bold;">{d['rr']}</td>
          <td style="padding: 7px; border: 1px solid #ccc; background: {eski_renk};">{d['eski']}</td>
          <td style="padding: 7px; border: 1px solid #ccc; background: {yeni_renk}; font-weight: bold;">{d['yeni']}</td>
        </tr>
        """

    html += "</table>"
    html += """<p style="margin-top: 15px; font-size: 12px; color: #666;">
    <b>Notlar:</b> Hedef/Stop ATR(14) bazlı hesaplanmıştır. ADX > 25 güçlü trend, RSI > 70 aşırı alım / < 30 aşırı satım.
    </p></body></html>"""

    email_gonder("🔔 BIST 100 Sinyal Değişimi!", html)
else:
    print("\n✅ Sinyal değişimi yok.")

# ═══════════════════════════════════════════════════════════════
# YENİ SİNYALLERİ KAYDET
# ═══════════════════════════════════════════════════════════════
with open(JSON_DOSYA, 'w', encoding='utf-8') as f:
    json.dump(yeni_sinyaller, f, ensure_ascii=False, indent=2)
print(f"💾 Sinyaller kaydedildi.")

# ═══════════════════════════════════════════════════════════════
# GÜNLÜK ÖZET MAILİ (TABLO HALİNDE)
# ═══════════════════════════════════════════════════════════════
if sonuclar:
    df_sonuc = pd.DataFrame(sonuclar)
    print("\n📊 ÖZET:")
    print(df_sonuc[['Hisse','Canli_Fiyat','RSI','ADX','Hedef','Stop','RR','Sinyal']].to_string(index=False))

    sinyal_renk = {
        "GÜÇLÜ AL": ("#C6EFCE", "#006100"),
        "AL": ("#E2EFDA", "#375623"),
        "GÜÇLÜ SAT": ("#FFC7CE", "#9C0006"),
        "SAT": ("#FFEB9C", "#9C5700"),
        "YUKARI": ("#FFF2CC", "#000000"),
        "AŞAĞI": ("#FFF2CC", "#000000"),
        "NÖTR": ("#F2F2F2", "#000000")
    }

    # Değişim özeti
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

    def tablo_olustur(df, baslik, baslik_renk):
        if df.empty:
            return f"<h3 style='color:{baslik_renk};'>{baslik} (0)</h3><p>Yok.</p>"

        html = f"<h3 style='color:{baslik_renk};'>{baslik} ({len(df)})</h3>"
        html += """<table style="border-collapse: collapse; width: 100%; font-size: 12px; margin-bottom: 20px;">
          <tr style="background: #1F4E78; color: white;">
            <th style="padding: 5px; border: 1px solid #ddd;">Hisse</th>
            <th style="padding: 5px; border: 1px solid #ddd;">Fiyat</th>
            <th style="padding: 5px; border: 1px solid #ddd;">EMA9</th>
            <th style="padding: 5px; border: 1px solid #ddd;">EMA21</th>
            <th style="padding: 5px; border: 1px solid #ddd;">SMA50</th>
            <th style="padding: 5px; border: 1px solid #ddd;">RSI</th>
            <th style="padding: 5px; border: 1px solid #ddd;">MACD</th>
            <th style="padding: 5px; border: 1px solid #ddd;">ADX</th>
            <th style="padding: 5px; border: 1px solid #ddd;">Hedef</th>
            <th style="padding: 5px; border: 1px solid #ddd;">Stop</th>
            <th style="padding: 5px; border: 1px solid #ddd;">R/R</th>
            <th style="padding: 5px; border: 1px solid #ddd;">BB</th>
          </tr>
        """

        for _, row in df.iterrows():
            bg, fg = sinyal_renk.get(row['Sinyal'], ("#F2F2F2", "#000000"))
            # RSI renklendirme
            rsi_bg = "#FFCCCC" if row['RSI'] > 70 else "#CCFFCC" if row['RSI'] < 30 else bg
            # ADX ikon
            adx_ikon = "🔥" if row['ADX'] > 25 else ""

            html += f"""
            <tr style="background: {bg}; color: {fg};">
              <td style="padding: 5px; border: 1px solid #ddd; font-weight: bold;">{row['Hisse']}</td>
              <td style="padding: 5px; border: 1px solid #ddd;">₺{row['Canli_Fiyat']}</td>
              <td style="padding: 5px; border: 1px solid #ddd;">{row['EMA9']}</td>
              <td style="padding: 5px; border: 1px solid #ddd;">{row['EMA21']}</td>
              <td style="padding: 5px; border: 1px solid #ddd;">{row['SMA50']}</td>
              <td style="padding: 5px; border: 1px solid #ddd; background: {rsi_bg};">{row['RSI']}</td>
              <td style="padding: 5px; border: 1px solid #ddd;">{row['MACD']}</td>
              <td style="padding: 5px; border: 1px solid #ddd;">{row['ADX']} {adx_ikon}</td>
              <td style="padding: 5px; border: 1px solid #ddd; color: #006100; font-weight: bold;">₺{row['Hedef']}</td>
              <td style="padding: 5px; border: 1px solid #ddd; color: #9C0006; font-weight: bold;">₺{row['Stop']}</td>
              <td style="padding: 5px; border: 1px solid #ddd; font-weight: bold;">{row['RR']}</td>
              <td style="padding: 5px; border: 1px solid #ddd;">{row['BB_Pos']}</td>
            </tr>
            """
        html += "</table>"
        return html

    guclu_al_df = df_sonuc[df_sonuc['Sinyal'] == 'GÜÇLÜ AL']
    guclu_sat_df = df_sonuc[df_sonuc['Sinyal'] == 'GÜÇLÜ SAT']
    al_df = df_sonuc[df_sonuc['Sinyal'] == 'AL']
    sat_df = df_sonuc[df_sonuc['Sinyal'] == 'SAT']

    html_ozet = f"""
    <html><body style="font-family: Arial, sans-serif;">
      <h2 style="color: #1F4E78;">📈 BIST 100 Günlük Özet</h2>
      <p><strong>{datetime.now().strftime('%d.%m.%Y %H:%M')}</strong></p>
      {degisim_ozeti}
      <hr>
      {tablo_olustur(guclu_al_df, "🟢 GÜÇLÜ AL", "#006100")}
      {tablo_olustur(guclu_sat_df, "🔴 GÜÇLÜ SAT", "#9C0006")}
      {tablo_olustur(al_df, "🟢 AL", "#375623")}
      {tablo_olustur(sat_df, "🔴 SAT", "#9C5700")}
      <p style="font-size: 11px; color: #666; margin-top: 20px;">
        <b>Uzman Notu:</b> Hedef/Stop = ATR(14) × 2.0 / 1.5 çarpanları ile hesaplanmıştır. 
        ADX > 25 = Güçlü trend, RSI > 70 = Aşırı alım (dikkat), RSI < 30 = Aşırı satım (fırsat). 
        BB = Bollinger Bands pozisyonu. MACD histogram pozitif = momentum yukarı.
      </p>
    </body></html>
    """

    email_gonder("📈 BIST 100 Günlük Özet + Hedef/Stop", html_ozet)
