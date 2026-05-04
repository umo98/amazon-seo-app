import streamlit as st
import requests
import json
import pandas as pd
import time

st.set_page_config(page_title="Pro Amazon SEO Analizci", page_icon="🚀", layout="wide")

# MiniMax modeli uzun metinlerde çok daha kararlıdır
MODEL_ID = "openrouter/owl-alpha"

PAZAR_VE_DILLER = {
    "amazon.com": ["Amerikan İngilizcesi"],
    "amazon.co.uk": ["İngilizce (UK)"],
    "amazon.de": ["Almanca"],
    "amazon.fr": ["Fransızca"],
    "amazon.es": ["İspanyolca"],
    "amazon.it": ["İtalyanca"],
    "amazon.nl": ["Hollandaca"],
    "amazon.pl": ["Lehçe"],
    "amazon.se": ["İsveççe"],
    "amazon.be": ["Felemenkçe (Flaman)", "Fransızca (Valon)"],
    "amazon.ie": ["İngilizce (IE)"],
    "amazon.jp": ["Japonca"],
    "amazon.ca": ["İngilizce", "Fransızca"],
    "amazon.com.au": ["Avustralya İngilizcesi"]
}

# Güçlü hata yakalama ile API'ye istek atan fonksiyon
def kelime_paketi_cek(api_key, anahtar_kelime, pazar, secilen_dil, adet):
    prompt = f"""
    Sen uzman bir Amazon SEO uzmanısın. {pazar} pazaryerinde, tamamen {secilen_dil} dilinde "{anahtar_kelime}" için {adet} adet long-tail anahtar kelime üret.
    
    KURALLAR:
    1. Sadece {secilen_dil} dilinde kelimeler üret.
    2. JSON formatı: [{{"kelime": "örnek", "hacim": 4, "zorluk": 2, "yorum": "Kolay hedef"}}]
    3. Hacim (1-5), Zorluk (1-5).
    4. "yorum" KESİNLİKLE TÜRKÇE olacak, max 3 kelime (Örn: "Niş fırsat").
    5. SADECE JSON listesi döndür.
    """
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    max_deneme = 2
    for deneme in range(max_deneme):
        try:
            # Timeout'u 120 saniyeye çıkardık
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            raw_cevap = response.json()['choices'][0]['message']['content']
            
            if "```json" in raw_cevap:
                raw_cevap = raw_cevap.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_cevap:
                raw_cevap = raw_cevap.split("```")[1].split("```")[0].strip()
                
            start_idx = raw_cevap.find('[')
            end_idx = raw_cevap.rfind(']')
            if start_idx != -1 and end_idx != -1:
                raw_cevap = raw_cevap[start_idx:end_idx+1]
                
            return json.loads(raw_cevap)
            
        except requests.exceptions.Timeout:
            time.sleep(3)
            continue
        except Exception as e:
            time.sleep(2)
            continue
            
    return None

def detayli_analiz_yap(anahtar_kelime, pazar_secimi, secilen_dil, toplam_adet):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    
    tum_sonuclar = []
    hata_sayisi = 0
    
    # PAZAR BOYUTUNU 10'A İNDİRDİK (En güvenli sınır)
    paket_boyutu = 10 
    paket_sayisi = max(1, (toplam_adet + paket_boyutu - 1) // paket_boyutu)
    
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    for i in range(paket_sayisi):
        mevcut_istek_adedi = min(paket_boyutu, toplam_adet - (i * paket_boyutu))
        ilerleme_yuzdesi = int(((i + 1) / paket_sayisi) * 100)
        
        progress_text.text(f"🚀 Yapay Zeka Çalışıyor... %{ilerleme_yuzdesi} (Paket {i+1}/{paket_sayisi}) - Başarılı: {len(tum_sonuclar)} kelime")
        
        paket_sonuclari = kelime_paketi_cek(api_key, anahtar_kelime, pazar_secimi, secilen_dil, mevcut_istek_adedi)
        
        if paket_sonuclari:
            tum_sonuclar.extend(paket_sonuclari)
        else:
            hata_sayisi += 1
            
        progress_bar.progress(ilerleme_yuzdesi / 100)
        time.sleep(2)
        
    progress_text.empty()
    progress_bar.empty()
    
    # TEKRAR EDENLERİ TEMİZLE
    gorulen_kelimeler = set()
    benzersiz_sonuclar = []
    for item in tum_sonuclar:
        k = item.get("kelime", "").strip().lower()
        if k and k not in gorulen_kelimeler:
            gorulen_kelimeler.add(k)
            benzersiz_sonuclar.append(item)
            
    return benzersiz_sonuclar[:toplam_adet], hata_sayisi

# --- ARAYÜZ ---
st.title("🚀 Pro Amazon SEO & Rakip Analiz Aracı")

with st.sidebar:
    st.header("⚙️ Analiz Ayarları")
    pazar_secimi = st.selectbox("1. Hedef Pazar Yeri", options=list(PAZAR_VE_DILLER.keys()), format_func=lambda x: x.upper())
    mevcut_diller = PAZAR_VE_DILLER[pazar_secimi]
    secilen_dil = st.selectbox("2. Arama Dili", options=mevcut_diller, disabled=(len(mevcut_diller) == 1))
    
    kelime_secenekleri = [10, 20, 50, 100, 200, 500, 1000]
    secilen_index = st.selectbox("3. Kaç Kelime Üretilsin?", options=range(len(kelime_secenekleri)), format_func=lambda i: f"{kelime_secenekleri[i]} Kelime")
    toplam_kelime_adedi = kelime_secenekleri[secilen_index]

anahtar_kelime = st.text_input("🔍 Anahtar Kelimenizi Girin", placeholder="Örn: wireless mouse", key="kelime_input")

if st.button("📊 DETAYLI RAPORU OLUŞTUR", type="primary", use_container_width=True):
    if not anahtar_kelime:
        st.warning("Lütfen bir anahtar kelime girin!")
    else:
        sonuclar, hata_sayisi = detayli_analiz_yap(anahtar_kelime, pazar_secimi, secilen_dil, toplam_kelime_adedi)
        
        if not sonuclar:
            st.error("❌ Hiçbir sonuç alınamadı. OpenRouter API key'inizin aktif olduğundan emin olun.")
        else:
            if hata_sayisi > 0:
                st.warning(f"⚠️ Not: Ücretsiz API limitleri nedeniyle {hata_sayisi} paket atlandı. Ancak {len(sonuclar)} kelime başarıyla getirildi!")
            else:
                st.success(f"✅ Analiz Sorunsuz Tamamlandı! {len(sonuclar)} benzersiz kelime bulundu.")
            
            # --- RAPOR ÖZETİ ---
            st.subheader("📋 Hızlı Pazar Özeti")
            col1, col2, col3, col4 = st.columns(4)
            
            toplam_hacim = sum(k.get("hacim", 0) for k in sonuclar)
            kolay_kelime_sayisi = sum(1 for k in sonuclar if k.get("zorluk", 5) <= 2)
            zor_kelime_sayisi = sum(1 for k in sonuclar if k.get("zorluk", 0) >= 4)
            
            col1.metric("Toplam Kelime", len(sonuclar))
            col2.metric("Toplam Hacim Skoru", toplam_hacim)
            col3.metric("🟢 Kolay Hedefler", kolay_kelime_sayisi)
            col4.metric("🔴 Zor Hedefler", zor_kelime_sayisi)
            
            # --- İKON VE RENK AÇIKLAMALARI (EXPANDER KULLANILMADAN DOĞRUDAN YAZILDI) ---
            st.markdown("""
            ---
            ### 📖 İkon ve Renklerin Anlamları
            
            **🟢🟡🔴 Hacim Sütunu (Aranma Sıklığı):**
            - 🟢 4-5 Puan : **Yüksek Hacim (Olumlu).** Çok aranan, talebi yüksek kelimeler.
            - 🟡 3 Puan  : Orta seviye arama hacmi.
            - 🔴 1-2 Puan : **Düşük Hacim (Olumsuz).** Nadir aranan, niş kelimeler.
            
            **🟢🟡🔴 Zorluk Sütunu (Rakip Sayısı):**
            - 🟢 1-2 Puan : **Kolay Fırsat (Olumlu).** Büyük satıcılar yok, kolayca 1. sayfaya çıkılabilir.
            - 🟡 3 Puan  : **Orta Seviye.** Rekabet var ama iyi optimizasyonla başarılabilir.
            - 🔴 4-5 Puan : **Zor (Olumsuz).** Dev markalar hakim, zor sıralama.
            ---
            """)
            
            # --- TABLO ---
            df = pd.DataFrame(sonuclar)
            
            def zorluk_emoji(z):
                if z <= 2: return "🟢 " + str(z)
                elif z <= 3: return "🟡 " + str(z)
                else: return "🔴 " + str(z)
                
            def hacim_emoji(h):
                if h >= 4: return "🟢 " + str(h)
                elif h == 3: return "🟡 " + str(h)
                else: return "🔴 " + str(h)

            df['Zorluk'] = df['zorluk'].apply(zorluk_emoji)
            df['Hacim'] = df['hacim'].apply(hacim_emoji)
            
            df_gosterim = df[['kelime', 'Hacim', 'Zorluk', 'yorum']].rename(columns={
                'kelime': 'Anahtar Kelime',
                'yorum': 'Stratejik Yorum (TR)'
            })
            
            st.subheader(f"📈 {pazar_secimi.upper()} Detaylı Tablo")
            st.dataframe(df_gosterim, use_container_width=True, hide_index=True, height=min(700, len(sonuclar) * 30))
            
            st.divider()
            
            # --- ALTIN FIRSATLAR ---
            st.subheader("🏆 Altın Fırsatlar (En İyi 10 Kelime)")
            altin_firsatlar = [k for k in sonuclar if k.get("hacim", 0) >= 4 and k.get("zorluk", 5) <= 2]
            if altin_firsatlar:
                for idx, af in enumerate(altin_firsatlar[:10], 1):
                    st.markdown(f"**{idx}. {af['kelime']}** | Hacim: {af['hacim']}/5 | Zorluk: {af['zorluk']}/5 | *{af['yorum']}*")
            else:
                st.info("Bu aramada 'Hacmi Yüksek + Zorluğu Düşük' mükemmel eşleşme bulunamadı.")
            
            st.divider()
            
            # --- SADECE KELİMELERİ KOPYALAMA ---
            st.subheader("📋 Hızlı Anahtar Kelime Kopyalama")
            st.markdown("Aşağıdaki kutucuğun sağ üst köşesindeki **«Kopyala»** ikonuna tıklayın. Sadece kelimeler anında panoya kopyalanacaktır.")
            
            sadece_kelimeler = "\n".join([item.get('kelime', '') for item in sonuclar])
            st.code(sadece_kelimeler, language=None)
