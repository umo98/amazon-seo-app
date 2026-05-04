import streamlit as st
import requests
import json

st.set_page_config(page_title="Amazon SEO Analizci", page_icon="🛒", layout="wide")

MODEL_ID = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

def analizi_yap(anahtar_kelime, hedef_dil, hedef_pazar):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    
    prompt = f"""
    Sen dünyanın en iyi Amazon Pazaryeri SEO uzmanısın. 
    Kullanıcının girdiği "{anahtar_kelime}" kelimesi için "{hedef_pazar}" pazaryerinde, "{hedef_dil}" dilinde aranma potansiyeli olan 10 adet alt anahtar kelime (long-tail keywords) üret.
    
    Kurallar:
    1. Sadece belirtilen dilde kelimeler üret.
    2. Her kelimeyi 2 metrikle puanla:
       - Aranma Hacmi (1-5 arası, 5 en yüksek)
       - Zorluk (1-5 arası, 1 en kolay/rakipsiz, 5 çok zor/dev markalar hakim)
    3. Çıktını KESİNLİKLE sadece bir JSON dizisi olarak ver, başka hiçbir açıklama yazma.
    4. JSON formatı şu şekilde olsun:
    [
      {{"kelime": "örnek kelime", "hacim": 4, "zorluk": 2}},
      {{"kelime": "örnek kelime 2", "hacim": 5, "zorluk": 5}}
    ]
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
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
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
        
    except json.JSONDecodeError:
        st.error("Yapay zeka farklı bir format üretmiş, lütfen tekrar deneyin.")
        return None
    except Exception as e:
        st.error(f"Bir API hatası oluştu: {e}")
        return None

st.title("🛒 Amazon Anahtar Kelime & SEO Analizci")
st.markdown("Nvidia Nemotron Modeli ile Güçlü Analiz")

with st.sidebar:
    st.subheader("Pazar Ayarları")
    diller = {"İngilizce": "İngilizce", "Almanca": "Almanca", "Fransızca": "Fransızca", "İspanyolca": "İspanyolca", "İtalyanca": "İtalyanca", "Türkçe": "Türkçe"}
    pazarlar = {"Amazon.com (ABD)": "Amazon.com", "Amazon.de (Almanya)": "Amazon.de", "Amazon.co.uk (İngiltere)": "Amazon.co.uk", "Amazon.fr (Fransa)": "Amazon.fr"}
    
    hedef_dil = st.selectbox("Hedef Dil", list(diller.keys()))
    hedef_pazar = st.selectbox("Hedef Pazar", list(pazarlar.keys()))

anahtar_kelime = st.text_input("🔍 Anahtar Kelimenizi Girin", placeholder="Örn: wireless mouse")

if st.button("Analizi Başlat", type="primary", use_container_width=True):
    if not anahtar_kelime:
        st.warning("Lütfen bir anahtar kelime girin!")
    else:
        with st.spinner(f"Nvidia AI '{anahtar_kelime}' için çalışıyor..."):
            sonuclar = analizi_yap(anahtar_kelime, diller[hedef_dil], pazarlar[hedef_pazar])
            
            if sonuclar:
                st.success("Analiz Tamamlandı!")
                def zorluk_rengi(zorluk):
                    if zorluk <= 2: return "🟢"
                    elif zorluk <= 3: return "🟡"
                    else: return "🔴"
                
                for i, veri in enumerate(sonuclar, 1):
                    col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                    col1.write(f"**{i}**")
                    col2.write(veri.get("kelime", ""))
                    col3.write(f"⭐ {veri.get('hacim', 'N/A')}/5")
                    col4.write(f"{zorluk_rengi(veri.get('zorluk', 3))} {veri.get('zorluk', 'N/A')}/5")
                    st.divider()
