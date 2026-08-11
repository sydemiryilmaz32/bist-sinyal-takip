import yfinance as yf
import pandas as pd
import time
import os
import json
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════
# TELEGRAM AYARLARI
# ═══════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def telegram_bildir(mesaj):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram ayarlanmamış, bildirim atlanıyor.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print("✅ Telegram bildirimi gönderildi")
        else:
            print(f"❌ Telegram hatası: {response.text}")
    except Exception as e:
        print(f"❌ Telegram bağlantı hatası: {e}")

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
            sinyal = "🟢 GÜÇLÜ AL"
        elif canli_fiyat > ema9 > ema21:
            sinyal = "🟢 AL"
        elif canli_fiyat < ema9 < ema21 < sma50:
            sinyal = "🔴 GÜÇLÜ SAT"
        elif canli_fiyat < ema9 < ema21:
            sinyal = "🔴 SAT"
        elif ema9 > ema21 and canli_fiyat > ema9:
            sinyal = "🟡 YUKARI"
        elif ema9 < ema21 and canli_fiyat < ema9:
            sinyal = "🟡 AŞAĞI"
        else:
            sinyal = "⚪ NÖTR"

        hisse_kodu = hisse.replace('.IS', '')
        yeni_sinyaller[hisse_kodu] = sinyal

        if hisse_kodu in onceki_sinyaller:
            eski_sinyal = onceki_sinyaller[hisse_kodu]
            if eski_sinyal != sinyal:
                degisen_hisseler.append({
                    'hisse': hisse_kodu,
                    'eski': eski_sinyal,
                    'yeni': sinyal,
                    'fiyat': round(canli_fiyat, 2)
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
# SİNYAL DEĞİŞİM BİLDİRİMLERİ
# ═══════════════════════════════════════════════════════════════
if degisen_hisseler:
    print(f"\n🔔 {len(degisen_hisseler)} hisste sinyal değişimi tespit edildi!")
    
    mesaj = f"📊 <b>BIST 100 Sinyal Değişimi</b>\n"
    mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    mesaj += "─" * 30 + "\n"
    
    for d in degisen_hisseler:
        mesaj += f"\n<b>{d['hisse']}</b> | ₺{d['fiyat']}\n"
        mesaj += f"   {d['eski']} → {d['yeni']}\n"
    
    telegram_bildir(mesaj)
else:
    print("\n✅ Sinyal değişimi yok.")

# ═══════════════════════════════════════════════════════════════
# YENİ SİNYALLERİ KAYDET
# ═══════════════════════════════════════════════════════════════
with open(JSON_DOSYA, 'w', encoding='utf-8') as f:
    json.dump(yeni_sinyaller, f, ensure_ascii=False, indent=2)
print(f"💾 Yeni sinyaller kaydedildi: {JSON_DOSYA}")

# ═══════════════════════════════════════════════════════════════
# GÜNCEL ÖZET (Her çalışmada gönder)
# ═══════════════════════════════════════════════════════════════
if sonuclar:
    df_sonuc = pd.DataFrame(sonuclar)
    print("\n📊 ÖZET TABLO:")
    print(df_sonuc[['Hisse','Canli_Fiyat','EMA9','EMA21','SMA50','Sinyal']].to_string(index=False))
    
    guclu_al = df_sonuc[df_sonuc['Sinyal'] == '🟢 GÜÇLÜ AL']['Hisse'].tolist()
    guclu_sat = df_sonuc[df_sonuc['Sinyal'] == '🔴 GÜÇLÜ SAT']['Hisse'].tolist()
    
    if guclu_al or guclu_sat:
        ozet_mesaj = f"📈 <b>BIST 100 Güncel Durum</b>\n"
        ozet_mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        if guclu_al:
            ozet_mesaj += f"🟢 <b>GÜÇLÜ AL ({len(guclu_al)}):</b>\n" + ", ".join(guclu_al) + "\n\n"
        if guclu_sat:
            ozet_mesaj += f"🔴 <b>GÜÇLÜ SAT ({len(guclu_sat)}):</b>\n" + ", ".join(guclu_sat) + "\n"
        telegram_bildir(ozet_mesaj)
