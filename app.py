import streamlit as st
from groq import Groq
from datetime import datetime, timedelta
import json

# Configuração básica
st.set_page_config(page_title="Cortina de Fumaça", page_icon="🌫️", layout="wide")

# Pega a chave dos secrets
groq_key = st.secrets["GROQ_KEY"]
client = Groq(api_key=groq_key)

# Título
st.title("🌫️ Cortina de Fumaça")
st.markdown("### O que bombou vs o que importa esta semana")

# Botão principal
if st.button("🔍 Descobrir agora", type="primary", use_container_width=True):
    
    hoje = datetime.now()
    semana_passada = hoje - timedelta(days=7)
    periodo = f"{semana_passada.strftime('%d/%m')} a {hoje.strftime('%d/%m')}"
    
    # Busca fofocas
    with st.spinner("Buscando o que bombou..."):
        prompt_fofocas = f"""Busque na web as 5 maiores fofocas/entretenimento da semana {periodo} no Brasil.
        Retorne APENAS JSON assim: {{"fofocas":[{{"titulo":"","descricao":"","link":""}}]}}"""
        
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_fofocas}],
            temperature=0.3
        )
        
        try:
            texto = resposta.choices[0].message.content
            texto = texto.replace("```json","").replace("```","").strip()
            fofocas = json.loads(texto)["fofocas"]
        except:
            fofocas = []
    
    # Busca notícias sérias
    with st.spinner("Buscando notícias importantes..."):
        prompt_noticias = f"""Busque na web 4 notícias sérias da semana {periodo} que tiveram 
        menos atenção: Congresso, STF, meio ambiente, saúde. 
        Retorne APENAS JSON assim: {{"noticias":[{{"titulo":"","descricao":"","link":""}}]}}"""
        
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_noticias}],
            temperature=0.3
        )
        
        try:
            texto = resposta.choices[0].message.content
            texto = texto.replace("```json","").replace("```","").strip()
            noticias = json.loads(texto)["noticias"]
        except:
            noticias = []
    
    # Mostra resultados
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 O que bombou")
        if fofocas:
            for item in fofocas:
                with st.expander(item.get("titulo", "Sem título")):
                    st.write(item.get("descricao", ""))
                    if item.get("link"):
                        st.markdown(f"[Ver fonte]({item['link']})")
        else:
            st.warning("Nada encontrado")
    
    with col2:
        st.subheader("📰 O que importa")
        if noticias:
            for item in noticias:
                with st.expander(item.get("titulo", "Sem título"), expanded=True):
                    st.write(item.get("descricao", ""))
                    if item.get("link"):
                        st.markdown(f"[Ver fonte]({item['link']})")
        else:
            st.warning("Nada encontrado")

st.markdown("---")
st.caption("🌫️ Educação midiática | Desenvolvido com Streamlit + Groq")
