import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
import datetime
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
            mes_ano = datetime.datetime.now().strftime("%m/%Y")
            
            # Busca filtrada e enxuta para não sobrecarregar a IA
            fofocas_brutas = DDGS().text(f"fofoca celebridades brasil {mes_ano}", max_results=5)
            serias_brutas = DDGS().text(f"noticias brasil politica stf economia {mes_ano}", max_results=5)
            
            # Cortamos o excesso de texto para garantir que a IA não dê BadRequest (Erro 400)
            lista_fofocas = [{"titulo": r.get('title', ''), "link": r.get('href', ''), "resumo": r.get('body', '')[:100]} for r in fofocas_brutas]
            lista_serias = [{"titulo": r.get('title', ''), "link": r.get('href', ''), "resumo": r.get('body', '')[:100]} for r in serias_brutas]
            
            prompt = f"""
            Você é um organizador de dados. 
            Com base nas listas abaixo, selecione 5 fofocas e 3 notícias sérias.
            
            Retorne EXCLUSIVAMENTE um JSON válido com esta estrutura:
            {{
              "fofocas": [ {{"titulo": "T", "link": "L", "resumo": "R"}} ],
              "serias": [ {{"titulo": "T", "link": "L", "resumo": "R"}} ]
            }}
            Não escreva mais nada além do código JSON.
            
            FOFOCAS REAIS: {lista_fofocas}
            SÉRIAS REAIS: {lista_serias}
            """
            
            # Chamada super segura para a Groq
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant", # <--- A ÚNICA LINHA QUE MUDA
                messages=[
                    {"role": "system", "content": "Você só responde em formato JSON estruturado. Sem introduções."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Limpeza bruta do retorno da IA para evitar qualquer erro de conversão
            texto_limpo = resposta.choices[0].message.content.strip()
            if texto_limpo.startswith("```"):
                texto_limpo = texto_limpo.replace("```json", "").replace("```", "").strip()
                
            # Salvando os dados organizados
            st.session_state.resultado = json.loads(texto_limpo)
            st.session_state.dados_prontos = True

        except Exception as e:
            # Se a internet ou a API engasgar, o usuário vê isso em vez de um erro fatal
            st.error("Poxa, os servidores de busca demoraram para responder. Tente clicar no botão novamente!")
            st.caption(f"Detalhe técnico: {e}")

st.write("---")

# Mostrando os resultados na tela de forma interativa
if st.session_state.dados_prontos and "fofocas" in st.session_state.resultado:
    st.subheader("🔥 Top assuntos da semana")
    
    # Cria uma lista de opções para o usuário clicar
    for fofoca in st.session_state.resultado["fofocas"]:
        
        # Se o usuário clicar em uma fofoca, a mágica acontece
        if st.button(f"👉 {fofoca['titulo']}"):
            
            st.markdown(f"**Por que bombou?** {fofoca['resumo']}...")
            st.markdown(f"[🔗 Ver fonte da fofoca]({fofoca['link']})")
            
            st.write("---")
            st.subheader("🌫️ Enquanto isso, na mesma semana...")
            
            # Mostra as notícias sérias que aconteceram ao mesmo tempo
            for seria in st.session_state.resultado.get("serias", []):
                st.markdown(f"**{seria['titulo']}**")
                st.markdown(f"{seria['resumo']}...")
                st.markdown(f"[🔗 Ler a notícia completa]({seria['link']})")
                st.write("")
            
            st.write("---")
            st.info("💭 **Para pensar:** Como as plataformas direcionam a sua atenção? A mídia não escondeu essas notícias sérias, mas os algoritmos priorizaram o engajamento da fofoca.")
