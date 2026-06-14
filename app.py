import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import json
import os

# Configuração da página
st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")

# Configuração do Gemini puxando a chave dos Secrets do Streamlit
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Textos Iniciais
st.title("📰 CORTINA DE FUMAÇA")
st.write("Nem tudo que domina sua timeline é o que mais impacta sua vida.")

# Variáveis para guardar o estado da tela
if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.resultado = {}

# O Botão Principal
if st.button("Descobrir o que bombou esta semana"):
    with st.spinner("Analisando algoritmos e coletando dados da semana..."):
        try:
            ddgs = DDGS()
            
            # Buscando as notícias e fofocas dos últimos dias no Brasil
            fofocas_brutas = ddgs.news("famosos OR fofoca OR celebridades OR viralizou", region="br-pt", timelimit="w", max_results=10)
            serias_brutas = ddgs.news("projeto de lei OR senado OR stf OR câmara OR impacto", region="br-pt", timelimit="w", max_results=10)
            
            lista_fofocas = [{"titulo": r.get('title', ''), "link": r.get('url', ''), "resumo": r.get('body', '')} for r in fofocas_brutas]
            lista_serias = [{"titulo": r.get('title', ''), "link": r.get('url', ''), "resumo": r.get('body', '')} for r in serias_brutas]
            
            prompt = f"""
            Você é um curador de dados para um projeto de educação midiática. 
            Com base EXCLUSIVAMENTE nas listas de notícias reais abaixo, selecione as 5 fofocas de entretenimento e as 3 notícias políticas/sociais mais impactantes.
            
            FOFOCAS REAIS DA SEMANA: {lista_fofocas}
            NOTÍCIAS SÉRIAS DA SEMANA: {lista_serias}
            """
            
            # Instanciando o modelo Gemini Flash (rápido e gratuito)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            # Pedindo para o Gemini responder estritamente em JSON usando o Schema esperado
            resposta = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "fofocas": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "titulo": {"type": "string"},
                                        "link": {"type": "string"},
                                        "resumo": {"type": "string"}
                                    }
                                }
                            },
                            "serias": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "titulo": {"type": "string"},
                                        "link": {"type": "string"},
                                        "resumo": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                )
            )
            
            # Transformando o texto da resposta em um dicionário Python
            st.session_state.resultado = json.loads(resposta.text)
            st.session_state.dados_prontos = True

        except Exception as e:
            st.error("Poxa, os servidores de busca demoraram para responder ou houve uma falha de conexão. Tente clicar no botão novamente!")
            st.caption(f"Detalhe técnico: {e}")

st.write("---")

# Mostrando os resultados na tela
if st.session_state.dados_prontos and "fofocas" in st.session_state.resultado:
    st.subheader("🔥 Top assuntos da semana")
    
    for fofoca in st.session_state.resultado["fofocas"]:
        
        # O botão revela as notícias sérias
        if st.button(f"👉 {fofoca['titulo']}"):
            
            st.markdown(f"**Por que bombou?** {fofoca['resumo']}")
            st.markdown(f"[🔗 Ver fonte da fofoca]({fofoca['link']})")
            
            st.write("---")
            st.subheader("🌫️ Enquanto isso, na mesma semana...")
            
            # Percorre as notícias sérias capturadas
            for seria in st.session_state.resultado.get("serias", []):
                st.markdown(f"**{seria['titulo']}**")
                st.markdown(f"{seria['resumo']}")
                st.markdown(f"[🔗 Ler a notícia completa]({seria['link']})")
                st.write("")
            
            st.write("---")
            st.info("💭 **Para pensar:** Como as plataformas direcionam a sua atenção? A mídia não escondeu essas notícias sérias, mas os algoritmos priorizaram o engajamento da fofoca.")
