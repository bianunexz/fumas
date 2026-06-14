import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
import datetime
import json

# 1. Configuração Básica
st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")
client = Groq() # Lembrar de colocar a chave de API no ambiente

# 2. Textos Iniciais (A cara que você vai montar)
st.title("📰 CORTINA DE FUMAÇA")
st.write("Nem tudo que domina sua timeline é o que mais impacta sua vida.")

# 3. Variáveis para guardar o estado da tela (se o botão foi clicado)
if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.resultado = {}

# 4. O Botão Principal
if st.button("Descobrir o que bombou esta semana"):
    with st.spinner("Buscando o que está em alta..."):
        
        # Fazendo uma busca simples na web do mês e ano atuais
        mes_ano = datetime.datetime.now().strftime("%m/%Y")
        
        # Usando o DuckDuckGo de um jeito bem simples para pegar links reais
        busca_fofoca = DDGS().text(f"fofoca celebridades {mes_ano}", max_results=5)
        busca_seria = DDGS().text(f"noticias brasil politica economia {mes_ano}", max_results=5)
        
        # Transformando a busca em um formato que a IA entenda
        textos_encontrados = f"FOFOCAS: {list(busca_fofoca)}\n\nSÉRIAS: {list(busca_seria)}"
        
        # Pedindo para a Groq organizar isso de forma simples
        prompt = f"""
        Leia as notícias reais abaixo e escolha 5 fofocas e 3 notícias sérias.
        Retorne APENAS um JSON válido neste formato exato, sem mais nenhum texto:
        {{"fofocas": [{{"titulo": "T", "link": "L", "resumo": "R"}}], "serias": [{{"titulo": "T", "link": "L", "resumo": "R"}}]}}
        
        NOTÍCIAS REAIS ENCONTRADAS NA BUSCA:
        {textos_encontrados}
        """
        
        resposta = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Salvando os dados organizados
        st.session_state.resultado = json.loads(resposta.choices[0].message.content)
        st.session_state.dados_prontos = True

st.write("---")

# 5. Mostrando os resultados na tela de forma interativa
if st.session_state.dados_prontos:
    st.subheader("🔥 Top assuntos da semana")
    
    # Cria uma lista de opções para o usuário clicar
    for fofoca in st.session_state.resultado["fofocas"]:
        
        # Se o usuário clicar em uma fofoca, a mágica acontece
        if st.button(f"👉 {fofoca['titulo']}"):
            
            st.markdown(f"**Por que bombou?** {fofoca['resumo']}")
            st.markdown(f"[🔗 Ver fonte da fofoca]({fofoca['link']})")
            
            st.write("---")
            st.subheader("🌫️ Enquanto isso, na mesma semana...")
            
            # Mostra as notícias sérias que aconteceram ao mesmo tempo
            for seria in st.session_state.resultado["serias"]:
                st.markdown(f"**{seria['titulo']}**")
                st.markdown(f"{seria['resumo']}")
                st.markdown(f"[🔗 Ler a notícia completa]({seria['link']})")
                st.write("")
            
            st.write("---")
            st.info("💭 **Para pensar:** Como as plataformas direcionam a sua atenção? A mídia não escondeu essas notícias sérias, mas os algoritmos priorizaram o engajamento da fofoca.")
