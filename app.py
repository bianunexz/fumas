import streamlit as st
import requests
from datetime import datetime, timedelta
import json

# Configuração da página
st.set_page_config(
    page_title="Cortina de Fumaça",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Título e descrição
st.title("🌫️ Cortina de Fumaça")
st.markdown("""
### O que está ocupando sua atenção esta semana?

*Descubra o que está bombando nas redes e, ao mesmo tempo, o que está acontecendo de realmente importante no Brasil e no mundo.*
""")

# Função para obter a chave API (dos secrets ou manual)
def get_api_key():
    """Obtém a chave API dos secrets do Streamlit ou do input manual"""
    # Primeiro tenta pegar dos secrets
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        pass
    
    # Se não tiver nos secrets, mostra input manual
    with st.sidebar:
        st.warning("⚠️ Chave API não configurada nos secrets")
        api_key = st.text_input(
            "Ou cole sua chave aqui:",
            type="password",
            placeholder="gsk_...",
            help="Obtenha sua chave em https://console.groq.com"
        )
        return api_key

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuração")
    
    # Mostrar status da chave API
    if "GROQ_API_KEY" in st.secrets:
        st.success("✅ Chave API configurada")
    else:
        st.info("Configure sua chave API nos secrets")
    
    st.markdown("---")
    st.markdown("""
    ### 📖 Como configurar
    
    **Localmente:** Crie `.streamlit/secrets.toml`
    ```toml
    GROQ_API_KEY = "gsk_sua_chave"
