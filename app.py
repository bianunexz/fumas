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

# CSS simples e elegante
st.markdown("""
<style>
    .main-title { font-size: 2.5rem; font-weight: bold; }
    .subtitle { color: #888; font-style: italic; margin-bottom: 2rem; }
    .fofoca-item { padding: 1rem; margin: 0.5rem 0; background: #fff5f5; border-left: 4px solid #ff4444; border-radius: 4px; }
    .noticia-item { padding: 1rem; margin: 0.5rem 0; background: #f0f8f0; border-left: 4px solid #2d7a27; border-radius: 4px; }
    .analise-box { padding: 1rem; margin: 0.5rem 0; background: #fafafa; border-radius: 8px; }
    .pergunta { font-style: italic; font-size: 1.1rem; padding: 1rem; background: #fff; border-top: 3px solid #ff4444; }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown('<p class="main-title">🌫️ Cortina de Fumaça</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Nem tudo que domina sua timeline é o que mais impacta sua vida.</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📖 Sobre")
    st.markdown("""
    **Educação midiática**
    
    Mostramos como entretenimento domina nossa atenção enquanto notícias importantes passam batido.
    
    **Agenda-setting:** a mídia não diz o que pensar, mas sobre o que pensar.
    
    ---
    ⚠️ Não acusamos ninguém. Não é conspiração.
    """)

# Função simples para extrair JSON
def extrair_json(texto):
    texto = texto.strip()
    if "```" in texto:
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
    return json.loads(texto.strip())

# Função para consultar a API com retry
def consultar_groq(prompt, max_tokens=500):
    """Consulta a API com retry em caso de rate limit"""
    for tentativa in range(3):
        try:
            resposta = client.chat.completions.create(
                model="compound-beta",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=max_tokens
            )
            return resposta.choices[0].message.content
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e):
                time.sleep(2)  # Espera 2 segundos
                continue
            else:
                raise e
    return None

# Botão principal
if st.button("🔍 Descobrir o que está bombando esta semana", type="primary", use_container_width=True):
    
    hoje = datetime.now()
    semana_inicio = hoje - timedelta(days=7)
    periodo = f"{semana_inicio.strftime('%d/%m')} a {hoje.strftime('%d/%m')}"
    
    fofocas = []
    noticias = []
    
    # ── BUSCAR FOFOCAS ──
    with st.spinner("🔥 Buscando o que bombou esta semana..."):
        prompt_fofocas = f"""Busque na web agora: 5 maiores fofocas/entretenimento da semana {periodo} no Brasil. Nomes reais. Retorne JSON: {{"fofocas":[{{"titulo":"","descricao":"","link":"","fonte":""}}]}}"""
        
        try:
            resposta = consultar_groq(prompt_fofocas, max_tokens=400)
            if resposta:
                dados = extrair_json(resposta)
                fofocas = dados.get("fofocas", [])
        except Exception as e:
            st.error(f"Erro fofocas: {str(e)[:200]}")
    
    # Pequena pausa para não estourar rate limit
    time.sleep(1)
    
    # ── BUSCAR NOTÍCIAS ──
    with st.spinner("📰 Buscando notícias importantes..."):
        prompt_noticias = f"""Busque na web agora: 4 notícias sérias da semana {periodo} Brasil/mundo sobre Congresso, STF, meio ambiente, saúde ou direitos humanos. Retorne JSON: {{"noticias":[{{"titulo":"","descricao":"","link":"","fonte":""}}]}}"""
        
        try:
            resposta = consultar_groq(prompt_noticias, max_tokens=400)
            if resposta:
                dados = extrair_json(resposta)
                noticias = dados.get("noticias", [])
        except Exception as e:
            st.error(f"Erro notícias: {str(e)[:200]}")
    
    # ── MOSTRAR RESULTADOS ──
    if fofocas or noticias:
        st.success(f"✅ Semana analisada: {periodo}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 O que bombou")
            for i, f in enumerate(fofocas[:5], 1):
                with st.expander(f"{i}. {f.get('titulo', 'Sem título')[:80]}", expanded=False):
                    st.write(f.get("descricao", ""))
                    if f.get("link"):
                        st.markdown(f"[📎 {f.get('fonte', 'Fonte')}]({f.get('link')})")
                    
                    # Botão de análise individual
                    if st.button(f"🧠 Analisar", key=f"analisar_{i}"):
                        with st.spinner("Gerando análise..."):
                            prompt_analise = f"""Analise como educador midiático. Fofoca: {f.get('titulo','')}. Notícias sérias da mesma semana: {'; '.join([n.get('titulo','') for n in noticias])}. Explique por que viralizou, como ambos coexistiram (use 'enquanto isso'), e faça pergunta reflexiva. JSON: {{"porque":"","coexistencia":"","pergunta":""}}"""
                            
                            try:
                                resp = consultar_groq(prompt_analise, max_tokens=300)
                                if resp:
                                    analise = extrair_json(resp)
                                    st.markdown("---")
                                    st.markdown(f"**Por que dominou:** {analise.get('porque', '')}")
                                    st.markdown(f"**Enquanto isso:** {analise.get('coexistencia', '')}")
                                    st.markdown(f'<div class="pergunta">❝ {analise.get("pergunta", "")} ❞</div>', unsafe_allow_html=True)
                            except:
                                st.warning("Análise indisponível")
        
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
        
        # Mensagem final
        st.markdown("---")
        st.markdown("""
        ### 🌫️ O efeito cortina de fumaça
        
        **Agenda-setting**: a mídia não diz o que pensar, mas determina sobre o que pensamos.
        
        Enquanto você consumia entretenimento esta semana, decisões importantes estavam sendo tomadas.
        
        **Na próxima semana, o que você vai escolher consumir?**
        """)
    
    else:
        st.warning("Tente novamente em alguns segundos (limite da API).")

st.markdown("---")
st.caption("🌫️ Cortina de Fumaça — Educação midiática com Python + Streamlit + Groq")
