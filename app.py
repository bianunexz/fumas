import streamlit as st
from groq import Groq
from datetime import datetime, timedelta
import json
import time

# Configuração
st.set_page_config(page_title="Cortina de Fumaça", page_icon="🌫️", layout="wide")

# Pega chave dos secrets
groq_key = st.secrets["GROQ_KEY"]
client = Groq(api_key=groq_key)

# CSS simples
st.markdown("""
<style>
    .main-title { font-size: 2.5rem; font-weight: bold; }
    .subtitle { color: #888; font-style: italic; margin-bottom: 2rem; }
    .fofoca-item { padding: 1rem; margin: 0.5rem 0; background: #fff5f5; border-left: 4px solid #ff4444; border-radius: 4px; }
    .noticia-item { padding: 1rem; margin: 0.5rem 0; background: #f0f8f0; border-left: 4px solid #2d7a27; border-radius: 4px; }
    .pergunta { font-style: italic; font-size: 1.1rem; padding: 1rem; background: #fff; border-top: 3px solid #ff4444; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🌫️ Cortina de Fumaça</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Nem tudo que domina sua timeline é o que mais impacta sua vida.</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📖 Sobre")
    st.markdown("""
    **Educação midiática**
    
    Mostramos como entretenimento domina nossa atenção enquanto notícias importantes passam batido.
    
    **Agenda-setting:** a mídia não diz o que pensar, mas sobre o que pensar.
    """)

# Função para extrair JSON
def extrair_json(texto):
    texto = texto.strip()
    if "```" in texto:
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
    return json.loads(texto.strip())

# Função de consulta ultra-simples
def buscar_tendencias(tipo):
    """Busca fofocas ou notícias com prompt mínimo"""
    
    if tipo == "fofocas":
        prompt = "Liste 5 fofocas do Brasil desta semana. JSON: {fofocas:[{titulo,descricao,link,fonte}]}"
    else:
        prompt = "Liste 4 noticias serias do Brasil desta semana sobre Congresso,STF,meio ambiente. JSON: {noticias:[{titulo,descricao,link,fonte}]}"
    
    for tentativa in range(3):
        try:
            resposta = client.chat.completions.create(
                model="compound-beta",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            texto = resposta.choices[0].message.content
            dados = extrair_json(texto)
            return dados.get("fofocas") or dados.get("noticias") or []
        except Exception as e:
            if "429" in str(e):
                time.sleep(3)
                continue
            elif "413" in str(e):
                st.error("Prompt muito grande. Tente novamente.")
                return []
            else:
                st.error(f"Erro: {str(e)[:100]}")
                return []
    return []

# Botão principal
if st.button("🔍 Descobrir o que está bombando esta semana", type="primary", use_container_width=True):
    
    hoje = datetime.now()
    semana_inicio = hoje - timedelta(days=7)
    periodo = f"{semana_inicio.strftime('%d/%m')} a {hoje.strftime('%d/%m')}"
    
    # Buscar fofocas
    with st.spinner("🔥 Buscando o que bombou..."):
        fofocas = buscar_tendencias("fofocas")
        time.sleep(2)  # Pausa para rate limit
    
    # Buscar notícias
    with st.spinner("📰 Buscando notícias importantes..."):
        noticias = buscar_tendencias("noticias")
    
    # Mostrar resultados
    if fofocas or noticias:
        st.success(f"✅ Semana: {periodo}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 O que bombou")
            for i, f in enumerate(fofocas[:5], 1):
                with st.expander(f"{i}. {f.get('titulo', 'Sem título')[:80]}", expanded=False):
                    st.write(f.get("descricao", ""))
                    if f.get("link"):
                        st.markdown(f"[📎 {f.get('fonte', 'Fonte')}]({f.get('link')})")
                    
                    if st.button(f"🧠 Analisar", key=f"analisar_{i}"):
                        with st.spinner("Analisando..."):
                            titulos_noticias = [n.get('titulo','') for n in noticias]
                            
                            prompt_analise = f"Fofoca: {f.get('titulo','')}. Noticias serias: {titulos_noticias}. Explique porque viralizou e como coexistiu com noticias serias (use 'enquanto isso'). JSON: {{porque,coexistencia,pergunta}}"
                            
                            try:
                                resp = client.chat.completions.create(
                                    model="compound-beta",
                                    messages=[{"role": "user", "content": prompt_analise}],
                                    temperature=0.3,
                                    max_tokens=200
                                )
                                analise = extrair_json(resp.choices[0].message.content)
                                
                                st.markdown("---")
                                st.markdown(f"**Por que dominou:** {analise.get('porque', '')}")
                                st.markdown(f"**Enquanto isso:** {analise.get('coexistencia', '')}")
                                st.markdown(f'<div class="pergunta">❝ {analise.get("pergunta", "")} ❞</div>', unsafe_allow_html=True)
                            except:
                                st.warning("Análise indisponível no momento")
        
        with col2:
            st.subheader("📰 O que realmente importa")
            for n in noticias[:4]:
                st.markdown(f"""
                <div class="noticia-item">
                    <strong>{n.get('titulo', 'Sem título')}</strong><br>
                    <small>{n.get('descricao', '')}</small><br>
                    📎 <a href="{n.get('link', '#')}">{n.get('fonte', 'Fonte')}</a>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        ### 🌫️ O efeito cortina de fumaça
        
        **Agenda-setting**: a mídia não diz o que pensar, mas determina sobre o que pensamos.
        
        Enquanto você consumia entretenimento esta semana, decisões importantes estavam sendo tomadas.
        """)
    
    else:
        st.warning("Não foi possível carregar. Tente novamente em alguns segundos.")

st.markdown("---")
st.caption("🌫️ Cortina de Fumaça — Educação midiática | Streamlit + Groq")
