import streamlit as st
from groq import Groq
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json

st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")
client = Groq()

def buscar_no_google_news(termo_busca, max_itens=10): # Aumentamos para 10 para ter mais opções
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
            
            # Mandamos a data crua, a IA vai formatar
            noticias.append({
                "titulo": titulo, 
                "veiculo": veiculo,
                "link": link, 
                "data": data_pub
            })
            
        return noticias
    except Exception as e:
        return []

st.title("📰 CORTINA DE FUMAÇA")
st.write("Nem tudo que domina sua timeline é o que mais impacta sua vida.")

if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.resultado = {}

if st.button("Descobrir os assuntos da semana"):
    with st.spinner("Mapeando a atenção da internet..."):
        try:
            # Termos muito mais focados no puro suco da fofoca brasileira
            fofocas_brutas = buscar_no_google_news("fofoca OR polêmica OR traição OR cancelado OR babado OR flagra", max_itens=8)
            # Focando nas burocracias de alto impacto
            serias_brutas = buscar_no_google_news("Politica OR investigação OR senado OR stf OR pec", max_itens=8)
            
            if not fofocas_brutas or not serias_brutas:
                st.error("O buscador falhou na coleta de dados. Tente novamente.")
                st.stop()
            
            prompt = f"""
            Você é um curador rigoroso de dados.
            Sua tarefa é ler os resultados abaixo e criar entre 3 e 5 PARES ÚNICOS de notícias.
            
            REGRAS:
            1. FOFOCAS: Escolha APENAS polêmicas, trivialidades de famosos, barracos ou memes. Evite notícias de "Dia dos Namorados" ou coisas comportadas.
            2. SÉRIAS: Escolha APENAS votações, leis e impacto político pesado.
            3. EMPARELHAMENTO: Forme no mínimo 3 pares, máximo 5. Cada par tem 1 fofoca e 1 séria diferente.
            
            Retorne APENAS um JSON válido nesta estrutura exata:
            {{
              "pares": [
                {{
                  "fofoca": {{"titulo": "T", "veiculo": "V", "link": "L", "resumo": "Por que viralizou?", "data_formatada": "Reescreva a data crua em português (Ex: 12 de Junho). SEM HORÁRIO GMT."}},
                  "seria": {{"titulo": "T", "veiculo": "V", "link": "L", "resumo": "Qual o impacto na sociedade?", "data_formatada": "Reescreva a data crua em português (Ex: 12 de Junho). SEM HORÁRIO GMT."}}
                }}
              ]
            }}
            
            FOFOCAS: {fofocas_brutas}
            SÉRIAS: {serias_brutas}
            """
            
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Você atua como um filtro editorial. Retorne apenas JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, 
                response_format={"type": "json_object"}
            )
            
            texto_limpo = resposta.choices[0].message.content.strip()
            if not texto_limpo:
                raise ValueError("A IA retornou vazio.")
                
            st.session_state.resultado = json.loads(texto_limpo)
            st.session_state.dados_prontos = True

        except Exception as e:
            st.error("Ops! Tivemos um engasgo na conexão com os dados. Clique no botão mais uma vez!")
            # VOLTEI COM ESSA LINHA PARA A GENTE VER O ERRO SE ELE ACONTECER:
            st.caption(f"Detalhe técnico: {e}")
