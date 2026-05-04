import streamlit as st
import requests
import json
import pandas as pd
import time

st.set_page_config(page_title="Pro Amazon SEO Analizci", page_icon="🚀", layout="wide")

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

def kelime_paketi_cek(api_key, anahtar_kelime, pazar, secilen_dil, adet):
    prompt = f"""
    Sen uzman bir Amazon SEO uzmanısın. {pazar} pazaryerinde, tamamen {secilen_dil} dilinde "{anahtar_kelime}" için {adet} adet long-tail anahtar kelime üret.
    
    KURALLAR:
    1. Sadece ve sadece {secilen_dil} dilinde kelimeler üret. ASLA başka bir dilde kelime üretme.
    2. Her kelime için şu JSON formatında veri üret:
    [
      {{"kelime": "örnek", "hacim": 4, "zorluk": 2, "yorum": "Kolay hedef"}},
      {{"kelime": "örnek 2", "hacim": 5, "zorluk": 5, "yorum": "Fiyat savaşı var"}}
    ]
    3. Hacim (1-5 arası, 5 en yüksek). Zorluk (1-5 arası, 1 en kolay/rakipsiz).
    4. "yorum" kısmını KESİNLİKLE VE SADECE TÜRKÇE yaz. Max 3-4 kelime olsun (Örn: "Niş fırsat", "Rekabet yüksek", "Kolay sıralama").
    5. SADECE JSON listesi döndür, başka hiçbir metin yazma.
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
        # 1000 kelime isteneceği için timeout süresini uzattık
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=90)
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
    except Exception as e:
        return None

def detayli_analiz_yap(anahtar_kelime, pazar_secimi, secilen_dil, toplam_adet):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    
    tum_sonuclar = []
    # API'yi yormamak için 50'şerli paketler halinde çekiyoruz
    paket_boyutu = 50 
    paket_sayisi = max(1, (toplam_adet + paket_boyutu - 1) // paket_boyutu)
    
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    for i in range(paket_sayisi):
        mevcut_istek_adedi = min(paket_boyutu, toplam_adet - (i * paket_boyutu))
        
        # YÜZDESEL İLERLEME HESAPLAMASI
        ilerleme_yuzdesi = int(((i + 1) / paket_sayisi) * 100)
        progress_text.text(f"🚀 Yapay Zeka Çalışıyor... %{ilerleme_yuzdesi} Tamamlandı (Paket {i+1}/{paket_sayisi})")
        
        paket_sonuclari = kelime_paketi_cek(api_key, anahtar_kelime, pazar_secimi, secilen_dil, mevcut_istek_adedi)
        
        # Eğer API hata verirse o paketi atla, işlemi kesintiye uğratma
        if paket_sonuclari:
            tum_sonuclar.extend(paket_sonuclari)
        else:
            time.sleep(2) # Hata durumunda API'yi dinlenmeye bırak
            
        progress_bar.progress(ilerleme_yuzdesi / 100)
        time.sleep(1) # Ücretsiz API'yi banlamamak için bekleme
        
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

# --- ARAYÜZ ---
st.title("🚀 Pro Amazon SEO & Rakip Analiz Aracı")

with st.sidebar:
    st.header("⚙️ Analiz Ayarları")
    
    pazar_secimi = st.selectbox(
        "1. Hedef Pazar Yeri", 
        options=list(PAZAR_VE_DILLER.keys()),
        format_func=lambda x: x.upper()
    )
    
    mevcut_diller = PAZAR_VE_DILLER[pazar_secimi]
    secilen_dil = st.selectbox(
        "2. Arama Dili", 
        options=mevcut_diller,
        disabled=(len(mevcut_diller) == 1)
    )
    
    # 1000 KELEMEYE KADAR SEÇENEK
    kelime_secenekleri = [10, 20, 50, 100, 200, 500, 1000]
    secilen_index = st.selectbox(
        "3. Kaç Kelime Üretilsin?",
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
            st.error("Hiçbir sonuç alınamadı. (Ücretsiz API limiti dolmuş veya istek çok uzun sürmüş olabilir)")
        else:
            st.success(f"✅ Analiz Tamamlandı! {len(sonuclar)} benzersiz kelime bulundu.")
            
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
            
            # --- YENİ: İKON VE RENK ANLAMLARI ---
            with st.expander("📖 İkon ve Renklerin Anlamları", expanded=False):
                st.markdown("""
                **⭐ Hacim (Aranma Sıklığı):**
                - ⭐ 1/5 : Çok düşük arama hacmi (Nis kelimeler)
                - ⭐ 5/5 : Çok yüksek arama hacmi (Genel kelimeler)
                
                **Zorluk (Rakip Sayısı & Sıralama Gücü):**
                - 🟢 1-2 Puan : **Kolay Fırsat.** Büyük satıcılar yok, kolayca 1. sayfaya çıkılabilir.
                - 🟡 3 Puan  : **Orta Seviye.** Rekabet var ama iyi optimizasyonla başarılabilir.
                - 🔴 4-5 Puan : **Zor.** Dev markalar ve binlerce yorumlu ürünler hakim, kaçınılması tavsiye edilir.
                """)
            
            st.divider()
            
            # --- TABLO ---
            df = pd.DataFrame(sonuclar)
            
            def zorluk_emoji(z):
                if z <= 2: return "🟢 " + str(z)
                elif z <= 3: return "🟡 " + str(z)
                else: return "🔴 " + str(z)
                
            df['Zorluk'] = df['zorluk'].apply(zorluk_emoji)
            df['Hacim'] = "⭐ " + df['hacim'].astype(str)
            
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
            
            # --- YENİ: TOPLU KOPYALAMA BUTONU ---
            st.subheader("📋 Toplu Kopyalama")
            st.markdown("Aşağıdaki butona basarak tüm kelimeleri tek seferde kopyalayıp Excel'e veya başka bir yere yapıştırabilirsiniz.")
            
            # Kopyalanacak metni formatlayalım (Sekmelerle ayrılmış düz metin)
            kopyalama_metni = "Anahtar Kelime\tHacim\tZorluk\tYorum\n"
            for item in sonuclar:
                kopyalama_metni += f"{item.get('kelime', '')}\t{item.get('hacim', '')}\t{item.get('zorluk', '')}\t{item.get('yorum', '')}\n"
            
            # Streamlit'in download butonunu kopyalama butonu olarak kullanıyoruz
            st.download_button(
                label="🚀 TÜM KELİMELERİ KOPYALA / İNDİR (.TXT)",
                data=kopyalama_metni,
                file_name=f"{anahtar_kelime}_seo_raporu.txt",
                mime="text/plain",
                use_container_width=True
            )
