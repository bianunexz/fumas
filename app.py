import streamlit as st
from groq import Groq
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json

# Configuração da página
st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")
client = Groq()

# Função que pesquisa DIRETAMENTE no Google Notícias
def buscar_no_google_news(termo_busca, max_itens=8): # <--- MUDAMOS PARA 8 AQUI
    try:
        termo_codificado = urllib.parse.quote(f"{termo_busca} when:7d")
        url = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        noticias = []
        
        for item in root.findall('.//item')[:max_itens]:
            titulo_completo = item.find('title').text
            
            if ' - ' in titulo_completo:
                titulo = titulo_completo.rsplit(' - ', 1)[0]
                veiculo = titulo_completo.rsplit(' - ', 1)[-1]
            else:
                titulo = titulo_completo
                veiculo = "Portal de Notícias"
                
            link = item.find('link').text
            data_pub = item.find('pubDate').text
            
            noticias.append({
                "titulo": titulo, 
                "veiculo": veiculo,
                "link": link, 
                "data": data_pub
            })
            
        return noticias
    except Exception as e:
        return []

# Interface
st.title("📰 CORTINA DE FUMAÇA")
st.write("Nem tudo que domina sua timeline é o que mais impacta sua vida.")

if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.resultado = {}

if st.button("Descobrir o Top 5 da semana"): # <--- ATUALIZAMOS O BOTÃO
    with st.spinner("Pesquisando no Google e mapeando o ecossistema de notícias..."):
        try:
            # Puxamos 8 opções do Google para a IA ter uma pequena margem de escolha
            fofocas_brutas = buscar_no_google_news("famosos OR celebridades OR fofoca OR reality OR viralizou")
            serias_brutas = buscar_no_google_news("projeto de lei OR senado OR congresso OR impacto economico OR STF")
            
            prompt = f"""
            Você é um curador rigoroso de dados para um projeto de pesquisa acadêmica em comunicação.
            Sua tarefa é ler os resultados do Google abaixo e criar o TOP 5 DA SEMANA (EXATAMENTE 5 PARES ÚNICOS).
            
            REGRAS RÍGIDAS (PUNIÇÃO SE DESCUMPRIR):
            1. FOFOCAS: Escolha APENAS entretenimento, memes, polêmicas de famosos ou moda. PROIBIDO usar tragédias, mortes ou acidentes.
            2. NOTÍCIAS SÉRIAS: Escolha APENAS leis, STF, congresso, economia ou pautas sociais. PROIBIDO esportes.
            3. EMPARELHAMENTO: Forme rigorosamente 5 pares. Cada par deve ter 1 fofoca e 1 notícia séria diferente.
            
            Retorne APENAS um JSON válido nesta estrutura exata:
            {{
              "pares": [
                {{
                  "fofoca": {{"titulo": "T", "veiculo": "V", "link": "L", "resumo": "Por que viralizou?", "data_formatada": "Ex: 14 Junho"}},
                  "seria": {{"titulo": "T", "veiculo": "V", "link": "L", "resumo": "Qual o impacto real?", "data_formatada": "Ex: 14 Junho"}}
                }}
              ]
            }}
            
            RESULTADOS DO GOOGLE - FOFOCAS: {fofocas_brutas}
            RESULTADOS DO GOOGLE - SÉRIAS: {serias_brutas}
            """
            
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Você atua como um filtro editorial rígido. Retorne apenas JSON com 5 pares."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            texto_limpo = resposta.choices[0].message.content.strip()
            if texto_limpo.startswith("```"):
                texto_limpo = texto_limpo.replace("```json", "").replace("```", "").strip()
                
            st.session_state.resultado = json.loads(texto_limpo)
            st.session_state.dados_prontos = True

        except Exception as e:
            st.error("Ops! Tivemos um engasgo na hora de processar os dados. Tente de novo!")
            st.caption(f"Detalhe técnico: {e}")

st.write("---")

# Renderiza os dados no formato de pares
if st.session_state.dados_prontos and "pares" in st.session_state.resultado:
    st.subheader("🔥 Top 5 assuntos da semana") # <--- TÍTULO ATUALIZADO
    
    for idx, par in enumerate(st.session_state.resultado["pares"]):
        fofoca = par["fofoca"]
        seria = par["seria"]
        
        # Numeração visual do Top 5 no botão
        if st.button(f"{idx + 1}º 👉 {fofoca['titulo']}", key=f"btn_fofoca_{idx}"):
            
            st.markdown(f"📅 *{fofoca['data_formatada']}* | 📰 **Fonte:** {fofoca['veiculo']}")
            st.markdown(f"**Por que bombou?** {fofoca['resumo']}")
            st.markdown(f"[🔗 Ver na fonte]({fofoca['link']})")
            
            st.write("---")
            
            st.subheader("🌫️ Enquanto isso, na mesma época...")
            st.markdown(f"📅 *{seria['data_formatada']}* | 📰 **Fonte:** {seria['veiculo']}")
            st.markdown(f"**{seria['titulo']}**")
            st.markdown(f"{seria['resumo']}")
            st.markdown(f"[🔗 Ler a notícia]({seria['link']})")
            
            st.write("---")
            st.info("💭 **Para pensar:** Como as plataformas direcionam a sua atenção? A mídia não escondeu essa notícia séria, mas os algoritmos priorizaram o engajamento do entretenimento.")
