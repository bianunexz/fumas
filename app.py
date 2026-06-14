import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
import json

# Configuração da página
st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")
client = Groq() 

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
            # A GRANDE MUDANÇA: Forçando o buscador a pegar só Brasil (br-pt) e da última semana (w)
            fofocas_brutas = DDGS().text("fofocas celebridades entretenimento brasil", region="br-pt", timelimit="w", max_results=8)
            serias_brutas = DDGS().text("noticias brasil politica stf economia", region="br-pt", timelimit="w", max_results=8)
            
            # Cortamos o excesso de texto para a IA ler rápido
            lista_fofocas = [{"titulo": r.get('title', ''), "link": r.get('href', ''), "resumo": r.get('body', '')[:120]} for r in fofocas_brutas]
            lista_serias = [{"titulo": r.get('title', ''), "link": r.get('href', ''), "resumo": r.get('body', '')[:120]} for r in serias_brutas]
            
            prompt = f"""
            Você é um organizador de dados. 
            Com base nas listas abaixo, selecione as 5 melhores fofocas e 3 notícias sérias.
            
            Retorne EXCLUSIVAMENTE um JSON válido com esta estrutura:
            {{
              "fofocas": [ {{"titulo": "T", "link": "L", "resumo": "R"}} ],
              "serias": [ {{"titulo": "T", "link": "L", "resumo": "R"}} ]
            }}
            Não escreva mais nada além do código JSON.
            
            FOFOCAS REAIS: {lista_fofocas}
            SÉRIAS REAIS: {lista_serias}
            """
            
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Você só responde em formato JSON estruturado. Sem introduções."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Limpeza bruta do texto da IA
            texto_limpo = resposta.choices[0].message.content.strip()
            if texto_limpo.startswith("```"):
                texto_limpo = texto_limpo.replace("```json", "").replace("```", "").strip()
                
            st.session_state.resultado = json.loads(texto_limpo)
            st.session_state.dados_prontos = True

        except Exception as e:
            st.error("Poxa, os servidores de busca demoraram para responder. Tente clicar no botão novamente!")
            st.caption(f"Detalhe técnico: {e}")

st.write("---")

# Mostrando os resultados na tela
if st.session_state.dados_prontos and "fofocas" in st.session_state.resultado:
    st.subheader("🔥 Top assuntos da semana")
    
    for fofoca in st.session_state.resultado["fofocas"]:
        
        # O botão revela as notícias sérias
        if st.button(f"👉 {fofoca['titulo']}"):
            
            st.markdown(f"**Por que bombou?** {fofoca['resumo']}...")
            st.markdown(f"[🔗 Ver fonte da fofoca]({fofoca['link']})")
            
            st.write("---")
            st.subheader("🌫️ Enquanto isso, na mesma semana...")
            
            # O .get("serias", []) impede que a tela quebre caso a IA engula a lista
            for seria in st.session_state.resultado.get("serias", []):
                st.markdown(f"**{seria['titulo']}**")
                st.markdown(f"{seria['resumo']}...")
                st.markdown(f"[🔗 Ler a notícia completa]({seria['link']})")
                st.write("")
            
            st.write("---")
            st.info("💭 **Para pensar:** Como as plataformas direcionam a sua atenção? A mídia não escondeu essas notícias sérias, mas os algoritmos priorizaram o engajamento da fofoca.")
