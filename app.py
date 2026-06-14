import streamlit as st
from groq import Groq
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from email.utils import parsedate_to_datetime
import random # Importante para diversificar

# 1. Configurações
st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")
client = Groq()

def formatar_data(data_rss):
    try:
        dt = parsedate_to_datetime(data_rss)
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        return f"{dt.day} de {meses[dt.month - 1]}"
    except:
        return "Nesta semana"

def buscar_no_google_news(termo_busca, prefixo_id, max_itens=20): # Aumentamos para 20
    try:
        termo_codificado = urllib.parse.quote(f"{termo_busca} when:7d")
        # O &num=20 garante que buscaremos mais resultados
        url = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419&num=20"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        itens = root.findall('.//item')
        
        # Sorteia uma amostra aleatória dos resultados para nunca vir a mesma lista
        amostra = random.sample(itens, min(len(itens), max_itens))
        
        noticias = []
        for i, item in enumerate(amostra):
            titulo_completo = item.find('title').text
            if ' - ' in titulo_completo:
                titulo = titulo_completo.rsplit(' - ', 1)[0]
                veiculo = titulo_completo.rsplit(' - ', 1)[-1]
            else:
                titulo = titulo_completo
                veiculo = "Portal de Notícias"
                
            noticias.append({
                "id": f"{prefixo_id}{i}",
                "titulo": titulo,
                "veiculo": veiculo,
                "link": item.find('link').text,
                "data": formatar_data(item.find('pubDate').text)
            })
        return noticias
    except:
        return []

# 2. Interface
st.title("📰 CORTINA DE FUMAÇA")
st.write("Nem tudo que domina sua timeline é o que mais impacta sua vida.")

if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False

if st.button("Descobrir os assuntos da semana"):
    with st.spinner("Mapeando o ecossistema de notícias..."):
        try:# 
            fofocas_brutas = buscar_no_google_news("briga famosos OR influencer OR treta OR reality OR viral OR famoso OR flagra OR fofoca OR celebridade OR Virginia", "F")
            serias_brutas = buscar_no_google_news("projeto de lei OR investigação OR stf OR senado OR câmara OR operação policial", "S")
            
            if not fofocas_brutas or not serias_brutas:
                st.error("O buscador falhou. Tente novamente.")
                st.stop()
                
            st.session_state.fofocas_originais = {f["id"]: f for f in fofocas_brutas}
            st.session_state.serias_originais = {s["id"]: s for s in serias_brutas}
            
            fofocas_dieta = [{"id": f["id"], "titulo": f["titulo"], "veiculo": f["veiculo"]} for f in fofocas_brutas]
            serias_dieta = [{"id": s["id"], "titulo": s["titulo"], "veiculo": s["veiculo"]} for s in serias_brutas]
            
            prompt = f"""
            Analise os dados e crie entre 3 e 5 PARES DE NOTÍCIAS.
            Regras: 
            1. Seja surpreendente: escolha assuntos variados.
            2. Evite o óbvio e busque o contraste entre o fútil e o urgente.
            Retorne APENAS JSON com chave "pares" contendo id_fofoca, resumo_fofoca, id_seria, resumo_seria.
            Dados: {fofocas_dieta} | {serias_dieta}
            """
            
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7, # Aumentamos a temperatura para a IA ser mais criativa/variada
                response_format={"type": "json_object"}
            )
            
            st.session_state.resultado = json.loads(resposta.choices[0].message.content)
            st.session_state.dados_prontos = True
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

# 3. Exibição
if st.session_state.get("dados_prontos"):
    st.subheader("🔥 Assuntos em alta da semana")
    for idx, par in enumerate(st.session_state.resultado.get("pares", [])):
        fofoca = st.session_state.fofocas_originais.get(par.get("id_fofoca"))
        seria = st.session_state.serias_originais.get(par.get("id_seria"))
        
        if fofoca and seria:
            if st.button(f"👉 {fofoca['titulo']}", key=f"btn_{idx}"):
                st.markdown(f"📅 *{fofoca['data']}* | 📰 **Fonte:** {fofoca['veiculo']}")
                st.markdown(f"**Por que bombou?** {par.get('resumo_fofoca')}")
                st.markdown(f"[🔗 Ver na fonte]({fofoca['link']})")
                st.write("---")
                st.subheader("🌫️ Enquanto isso...")
                st.markdown(f"📅 *{seria['data']}* | 📰 **Fonte:** {seria['veiculo']}")
                st.markdown(f"**{seria['titulo']}**")
                st.markdown(f"{par.get('resumo_seria')}")
                st.markdown(f"[🔗 Ler a notícia]({seria['link']})")
                st.write("---")
