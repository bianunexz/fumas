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
    
    # Instruções de configuração
    st.markdown("### 📖 Como configurar")
    st.markdown("**Localmente:** Crie `.streamlit/secrets.toml`")
    st.code('GROQ_API_KEY = "gsk_sua_chave"', language="toml")
    st.markdown("**No Streamlit Cloud:**")
    st.markdown("Vá em Settings > Secrets e adicione:")
    st.code('GROQ_API_KEY = "gsk_sua_chave"', language="toml")
    
    st.markdown("---")
    st.markdown("""
    ### Sobre o projeto
    
    O **Cortina de Fumaça** não acusa a mídia de mentir. 
    Apenas mostra como assuntos de entretenimento dominam 
    nossa atenção enquanto notícias importantes passam 
    despercebidas.
    
    **Conceito central:** Agenda-setting
    """)

# Função para consultar a API do Groq
def consultar_groq(prompt, api_key):
    """Consulta a API do Groq com busca web"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Usando o modelo com busca web nativa
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "Você é um assistente de pesquisa que analisa tendências de mídia. Você tem acesso à busca web para encontrar informações atualizadas. Retorne APENAS JSON válido, sem formatação markdown."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Erro na API: {str(e)}")
        return None

def extrair_json(texto):
    """Extrai JSON de uma string que pode conter markdown"""
    try:
        # Remove possíveis blocos de código markdown
        texto = texto.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)
    except:
        return None

# Função principal
def main():
    # Obter chave API
    groq_api_key = get_api_key()
    
    # Verificar se a chave API foi fornecida
    if not groq_api_key:
        st.info("👈 Configure sua chave API Groq na barra lateral ou nos secrets para começar")
        st.markdown("""
        ### Como obter sua chave:
        1. Acesse [console.groq.com](https://console.groq.com)
        2. Crie uma conta gratuita
        3. Vá em "API Keys"
        4. Copie sua chave (começa com `gsk_`)
        """)
        return
    
    # Botão principal
    if st.button("🔍 Descobrir o que está bombando esta semana", type="primary", use_container_width=True):
        with st.spinner("🔎 Buscando informações atualizadas..."):
            
            # Datas da semana atual
            hoje = datetime.now()
            inicio_semana = hoje - timedelta(days=7)
            periodo = f"{inicio_semana.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}"
            
            # Prompt para buscar fofocas e notícias importantes
            prompt = f"""Busque informações REAIS e ATUAIS para a semana de {periodo}.

1. PRIMEIRO: Liste as 5 maiores fofocas e assuntos de entretenimento que estão dominando as redes sociais e portais de notícias no Brasil e no mundo esta semana. Para cada item, inclua: título chamativo, breve descrição, por que viralizou, e UM link real de uma fonte confiável.

2. DEPOIS: Liste 4-5 notícias SÉRIAS e importantes que aconteceram NA MESMA SEMANA mas receberam muito menos atenção do que mereciam. Foque em: Votações no Congresso, Decisões do STF, Dados de desmatamento/meio ambiente, Saúde pública, Direitos humanos, Crises internacionais relevantes.

Para cada notícia, inclua: título, resumo do impacto real, por que é importante, e UM link real de fonte jornalística confiável.

IMPORTANTE: Use APENAS informações reais encontradas na web. Inclua links verdadeiros e verificáveis. Não invente nada. Retorne APENAS um JSON válido neste formato:

{{
    "periodo": "{periodo}",
    "fofocas": [
        {{
            "titulo": "...",
            "descricao": "...",
            "por_que_viralizou": "...",
            "fonte": "Nome do site",
            "link": "https://..."
        }}
    ],
    "noticias_importantes": [
        {{
            "titulo": "...",
            "impacto": "...",
            "por_que_importante": "...",
            "fonte": "Nome do site",
            "link": "https://..."
        }}
    ]
}}"""
            
            resultado = consultar_groq(prompt, groq_api_key)
            
            if resultado:
                dados = extrair_json(resultado)
                
                if dados:
                    st.success(f"✅ Análise da semana: {dados.get('periodo', periodo)}")
                    
                    # Criar duas colunas
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("## 🎭 O que bombou")
                        st.markdown("*Entretenimento & Fofocas*")
                        st.markdown("---")
                        
                        for i, fofoca in enumerate(dados.get('fofocas', []), 1):
                            with st.expander(f"🔥 {fofoca['titulo']}", expanded=False):
                                st.markdown(f"**Descrição:** {fofoca['descricao']}")
                                st.markdown(f"**Por que viralizou:** {fofoca['por_que_viralizou']}")
                                st.markdown(f"**Fonte:** [{fofoca['fonte']}]({fofoca['link']})")
                                
                                # Análise automática
                                st.markdown("---")
                                st.markdown("### 🧠 Análise")
                                st.markdown("Este assunto viralizou por envolver elementos que ativam nossa atenção imediata: novidade, figuras públicas ou controvérsia. Algoritmos de plataformas como Instagram, TikTok e X priorizam conteúdos que geram engajamento rápido, criando um ciclo onde o entretenimento se espalha mais rápido que informação relevante.")
                                
                                st.markdown("### 💭 Para refletir")
                                st.markdown("*Enquanto você via este conteúdo, outras notícias importantes estavam acontecendo na mesma semana. Você percebeu?*")
                    
                    with col2:
                        st.markdown("## 📰 O que importa (mas não viraliza)")
                        st.markdown("*Notícias com impacto real na sua vida*")
                        st.markdown("---")
                        
                        for i, noticia in enumerate(dados.get('noticias_importantes', []), 1):
                            with st.expander(f"📌 {noticia['titulo']}", expanded=True if i == 1 else False):
                                st.markdown(f"**Impacto real:** {noticia['impacto']}")
                                st.markdown(f"**Por que é importante:** {noticia['por_que_importante']}")
                                st.markdown(f"**Fonte:** [{noticia['fonte']}]({noticia['link']})")
                                
                                # Contexto da coexistência
                                st.markdown("---")
                                st.markdown("### 🔄 Enquanto isso...")
                                st.markdown(f"""**Na mesma semana em que** você provavelmente ouviu falar de fofocas e entretenimento, esta notícia passou quase despercebida — mesmo podendo afetar diretamente sua vida, seus direitos ou seu futuro.

Isso não significa que alguém "escondeu" esta notícia de propósito. Significa apenas que o sistema de atenção em que vivemos — redes sociais, portais, algoritmos — favorece naturalmente o que é mais chamativo, não o que é mais importante.""")
                    
                    # Reflexão final
                    st.markdown("---")
                    st.markdown("""
                    ## 🌫️ O efeito cortina de fumaça
                    
                    Não se trata de conspiração. Trata-se de **agenda-setting**: a mídia e as plataformas não dizem *o que pensar*, mas determinam *sobre o que pensamos*.
                    
                    A pergunta que fica é: **na próxima semana, o que você vai escolher consumir?**
                    """)
                    
                else:
                    st.error("Não foi possível processar os dados. Tente novamente.")
                    st.code(resultado[:500])
            else:
                st.error("Erro ao consultar a API. Verifique sua chave e tente novamente.")

if __name__ == "__main__":
    main()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>"
    "🌫️ Cortina de Fumaça — Projeto de educação midiática | "
    "Desenvolvido com Python, Streamlit e Groq"
    "</p>",
    unsafe_allow_html=True
)
