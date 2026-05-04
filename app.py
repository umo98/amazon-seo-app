import streamlit as st
import requests
import json
import pandas as pd
import time

st.set_page_config(page_title="Gelişmiş Amazon SEO Analizci", page_icon="🚀", layout="wide")

MODEL_ID = "openrouter/owl-alpha"

# PAZAR YERLERİ VE ONLARIN DESTEKLEDİĞİ DİLLER (LISTE ŞEKLİNDE)
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

# HER BİR PAKET İÇİN API'YE GİDEN FONKSİYON
def kelime_paketi_cek(api_key, anahtar_kelime, pazar, secilen_dil, adet):
    prompt = f"""
    Sen uzman bir Amazon SEO uzmanısın. {pazar} pazaryerinde, tamamen {secilen_dil} dilinde "{anahtar_kelime}" için {adet} adet long-tail (uzun kuyruk) anahtar kelime üret.
    
    KURALLAR:
    1. Sadece ve sadece {secilen_dil} dilinde kelimeler üret. ASLA başka bir dilde kelime üretme.
    2. Her kelime için şu JSON formatında veri üret:
    [
      {{"kelime": "örnek", "hacim": 4, "zorluk": 2, "yorum": "Ofis çalışanları için ideal"}},
      {{"kelime": "örnek 2", "hacim": 5, "zorluk": 5, "yorum": "Yüksek rekabet, marka hakim"}}
    ]
    3. Hacim (1-5 arası, 5 en yüksek). Zorluk (1-5 arası, 1 en kolay/rakipsiz).
    4. "yorum" kısmını max 4-5 kelime olacak şekilde stratejik yaz (Örn: "Kolay hedef", "Fiyat savaşı var", "Niş fırsat").
    5. SADECE JSON listesi döndür, başka hiçbir metin, selamlama veya açıklama yazma.
    """
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        raw_cevap = response.json()['choices'][0]['message']['content']
        
        # JSON temizleme
        if "```json" in raw_cevap:
            raw_cevap = raw_cevap.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_cevap:
            raw_cevap = raw_cevap.split("```")[1].split("```")[0].strip()
            
        start_idx = raw_cevap.find('[')
        end_idx = raw_cevap.rfind(']')
        if start_idx != -1 and end_idx != -1:
            raw_cevap = raw_cevap[start_idx:end_idx+1]
            
        return json.loads(raw_cevap)
    except Exception as e:
        return None

# ANA ANALİZ FONKSİYONU (PAKETLERİ BİRLEŞTİRİR)
def detayli_analiz_yap(anahtar_kelime, pazar_secimi, secilen_dil, toplam_adet):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    
    tum_sonuclar = []
    paket_boyutu = 25 
    paket_sayisi = max(1, (toplam_adet + paket_boyutu - 1) // paket_boyutu)
    
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    for i in range(paket_sayisi):
        mevcut_istek_adedi = min(paket_boyutu, toplam_adet - (i * paket_boyutu))
        progress_text.text(f"🚀 Yapay Zeka Çalışıyor... Paket {i+1}/{paket_sayisi} ({(i+1)*paket_boyutu}/{toplam_adet} kelime)")
        
        paket_sonuclari = kelime_paketi_cek(api_key, anahtar_kelime, pazar_secimi, secilen_dil, mevcut_istek_adedi)
        
        if paket_sonuclari:
            tum_sonuclar.extend(paket_sonuclari)
        
        progress_bar.progress((i + 1) / paket_sayisi)
        time.sleep(0.5) 
        
    progress_text.empty()
    progress_bar.empty()
    
    # Tekrar eden kelimeleri temizle
    gorulen_kelimeler = set()
    benzersiz_sonuclar = []
    for item in tum_sonuclar:
        k = item.get("kelime", "").strip().lower()
        if k and k not in gorulen_kelimeler:
            gorulen_kelimeler.add(k)
            benzersiz_sonuclar.append(item)
            
    return benzersiz_sonuclar[:toplam_adet]


# --- GELİŞMİŞ ARAYÜZ ---
st.title("🚀 Gelişmiş Amazon SEO & Rakip Analiz Aracı")
st.markdown("14 Farklı Amazon Pazarında, Diline Özel Detaylı Raporlama")

with st.sidebar:
    st.header("⚙️ Analiz Ayarları")
    
    # 1. PAZAR YERİ SEÇİMİ
    pazar_secimi = st.selectbox(
        "1. Hedef Pazar Yeri", 
        options=list(PAZAR_VE_DILLER.keys()),
        format_func=lambda x: x.upper()
    )
    
    # 2. DİNAMİK DİL SEÇİMİ (Seçilen pazara göre dilleri listeler)
    mevcut_diller = PAZAR_VE_DILLER[pazar_secimi]
    
    # Eğer pazarın tek dili varsa default olarak onu seç, birden fazlaysa dropdown aç
    secilen_dil = st.selectbox(
        "2. Arama Dili", 
        options=mevcut_diller,
        disabled=(len(mevcut_diller) == 1) # Tek dil varsa gri yapılır ama görünür
    )
    
    # 3. KELİME SAYISI SEÇİMİ
    kelime_secenekleri = [10, 20, 50, 100, 150, 200]
    secilen_index = st.selectbox(
        "3. Kaç Anahtar Kelime Üretilsin?",
        options=range(len(kelime_secenekleri)),
        format_func=lambda i: f"{kelime_secenekleri[i]} Kelime"
    )
    toplam_kelime_adedi = kelime_secenekleri[secilen_index]

anahtar_kelime = st.text_input("🔍 Anahtar Kelimenizi Girin", placeholder="Örn: wireless mouse", key="kelime_input")

if st.button("📊 DETAYLI RAPORU OLUŞTUR", type="primary", use_container_width=True):
    if not anahtar_kelime:
        st.warning("Lütfen bir anahtar kelime girin!")
    else:
        sonuclar = detayli_analiz_yap(anahtar_kelime, pazar_secimi, secilen_dil, toplam_kelime_adedi)
        
        if not sonuclar:
            st.error("Hiçbir sonuç alınamadı. API kotanız dolmuş veya model hata vermiş olabilir.")
        else:
            st.success(f"✅ Analiz Tamamlandı! {len(sonuclar)} benzersiz kelime bulundu.")
            
            # --- RAPOR ÖZETİ ---
            st.subheader("📋 Hızlı Pazar Özeti")
            col1, col2, col3, col4 = st.columns(4)
            
            toplam_hacim = sum(k.get("hacim", 0) for k in sonuclar)
            kolay_kelime_sayisi = sum(1 for k in sonuclar if k.get("zorluk", 5) <= 2)
            zor_kelime_sayisi = sum(1 for k in sonuclar if k.get("zorluk", 0) >= 4)
            
            col1.metric("Toplam Kelime", len(sonuclar))
            col2.metric("Toplam Hacim Skoru", toplam_hacim, help="Tüm kelimelerin hacim puanlarının toplamı")
            col3.metric("🟢 Kolay Hedefler (1-2)", kolay_kelime_sayisi, help="Rakip sayısı düşük kelimeler")
            col4.metric("🔴 Zor Hedefler (4-5)", zor_kelime_sayisi, help="Büyük markaların hakim olduğu kelimeler")
            
            st.divider()
            
            # --- PANDAS TABLOSU OLUŞTURMA ---
            df = pd.DataFrame(sonuclar)
            
            def zorluk_emoji(z):
                if z <= 2: return "🟢 " + str(z)
                elif z <= 3: return "🟡 " + str(z)
                else: return "🔴 " + str(z)
                
            df['Zorluk'] = df['zorluk'].apply(zorluk_emoji)
            df['Hacim'] = "⭐ " + df['hacim'].astype(str)
            
            df_gosterim = df[['kelime', 'Hacim', 'Zorluk', 'yorum']].rename(columns={
                'kelime': 'Anahtar Kelime',
                'yorum': 'Stratejik Yorum'
            })
            
            st.subheader(f"📈 {pazar_secimi.upper()} - {secilen_dil} Detaylı Kelime Tablosu")
            st.dataframe(
                df_gosterim, 
                use_container_width=True, 
                hide_index=True,
                height=min(600, len(sonuclar) * 35) 
            )
            
            st.divider()
            
            # --- ALTIN FIRSATLAR ---
            st.subheader("🏆 Altın Fırsatlar (En İyi 5 Kelime)")
            st.markdown("*Hacmi yüksek (4-5) ve Zorluğu düşük (1-2) olan kelimeler*")
            
            altin_firsatlar = [k for k in sonuclar if k.get("hacim", 0) >= 4 and k.get("zorluk", 5) <= 2]
            if altin_firsatlar:
                for idx, af in enumerate(altin_firsatlar[:5], 1):
                    st.markdown(f"**{idx}. {af['kelime']}** | Hacim: {af['hacim']}/5 | Zorluk: {af['zorluk']}/5 | *{af['yorum']}*")
            else:
                st.info("Bu aramada 'Hacmi Yüksek + Zorluğu Düşük' mükemmel eşleşme bulunamadı. Daha fazla uzun kuyruk kelime üretmeyi deneyebilirsiniz.")
