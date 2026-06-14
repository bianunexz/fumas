import streamlit as st
from groq import Groq
import requests
from datetime import datetime, timedelta

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Cortina de Fumaça",
    page_icon="🔍",
    layout="centered",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d0d0d;
        color: #e8e8e0;
    }
    h1 { font-family: 'Playfair Display', serif; font-size: 2.6rem; color: #e8e8e0; }
    h2, h3 { font-family: 'Playfair Display', serif; color: #e8e8e0; }
    .stTextInput > div > div > input {
        background: #1a1a1a;
        border: 1px solid #333;
        color: #e8e8e0;
        border-radius: 8px;
    }
    .stButton > button {
        background: #c0392b;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 2rem;
        transition: background 0.2s;
    }
    .stButton > button:hover { background: #e74c3c; }
    .card {
        background: #1a1a1a;
        border-left: 4px solid #c0392b;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
    }
    .tag {
        display: inline-block;
        background: #2d2d2d;
        color: #aaa;
        font-size: 0.75rem;
        padding: 2px 10px;
        border-radius: 20px;
        margin-bottom: 0.5rem;
    }
    .question-box {
        background: #161616;
        border: 1px solid #c0392b44;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-top: 1.5rem;
        font-style: italic;
        color: #ccc;
    }
    hr { border-color: #222; }
</style>
""", unsafe_allow_html=True)

# ── Cabeçalho ───────────────────────────────────────────────────────────────
st.markdown("# 🔍 Cortina de Fumaça")
st.markdown("*Qual notícia está monopolizando sua atenção — e o que pode estar ficando de fora?*")
st.divider()

# ── Carrega chaves do secrets.toml (nunca expostas na interface) ─────────────
groq_key = st.secrets.get("GROQ_KEY", "")
news_key = st.secrets.get("NEWS_KEY", "")

if not groq_key:
    st.error("⚠️ Chave Groq não encontrada. Configure GROQ_KEY no arquivo .streamlit/secrets.toml ou nos Secrets do Streamlit Cloud.")
    st.stop()

# ── Sidebar: apenas info do projeto ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### ℹ️ Sobre o projeto")
    st.caption("Ferramenta de educação midiática. Não acusa ninguém — apenas estimula reflexão crítica sobre como nossa atenção é direcionada.")
    st.divider()
    if news_key:
        st.success("✅ NewsAPI conectada")
    else:
        st.info("NewsAPI não configurada — use o modo manual.")

# ── Funções ──────────────────────────────────────────────────────────────────
def buscar_noticias_em_alta(api_key: str) -> list[dict]:
    """Busca as notícias mais populares da semana via NewsAPI."""
    ontem = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?language=pt&pageSize=10&sortBy=popularity&apiKey={api_key}"
    )
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("status") == "ok":
            return data.get("articles", [])
    except Exception:
        pass
    return []

def analisar_cortina(client: Groq, tema_quente: str, tema_manual: bool) -> dict:
    """Pede ao Groq para identificar a cortina de fumaça."""
    if tema_manual:
        contexto = f"O usuário informou que o tema mais comentado na mídia esta semana é: '{tema_quente}'."
    else:
        contexto = f"O tema que está dominando as manchetes brasileiras esta semana é: '{tema_quente}'."

    prompt = f"""Você é um analista de mídia crítico e educador. {contexto}

Sua tarefa:
1. Confirme se esse tema realmente está recebendo atenção desproporcional na mídia.
2. Identifique 2 a 3 ASSUNTOS REAIS E CONCRETOS que estão acontecendo AGORA (semana de {datetime.now().strftime('%d/%m/%Y')}) e que podem estar sendo ofuscados por esse tema dominante. Seja específico: nomes de projetos de lei, países, crises, votações, escândalos reais. Não invente — se não souber, diga que são possibilidades plausíveis.
3. Explique, com base em como a mídia e os algoritmos funcionam, por que essa dinâmica pode ser considerada uma possível "cortina de fumaça" — sem acusar intenção, apenas analisando o efeito.
4. Termine com UMA pergunta aberta provocativa para o leitor refletir.

Responda em JSON com exatamente estas chaves:
{{
  "tema_dominante": "...",
  "porque_domina": "...",
  "temas_ofuscados": [
    {{"titulo": "...", "descricao": "..."}},
    {{"titulo": "...", "descricao": "..."}}
  ],
  "analise_cortina": "...",
  "pergunta_reflexao": "..."
}}
Responda APENAS com o JSON, sem texto antes ou depois."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1200,
    )
    import json
    raw = response.choices[0].message.content.strip()
    # remove possíveis ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ── Interface principal ───────────────────────────────────────────────────────
modo = st.radio(
    "Como você quer começar?",
    ["🔎 Buscar notícias automaticamente (NewsAPI)", "✏️ Informar o tema manualmente"],
    horizontal=True,
)

tema_escolhido = None

if modo == "🔎 Buscar notícias automaticamente (NewsAPI)":
    if not news_key:
        st.info("Insira sua chave da NewsAPI na barra lateral para busca automática.")
    else:
        if st.button("Buscar notícias da semana"):
            with st.spinner("Buscando manchetes..."):
                artigos = buscar_noticias_em_alta(news_key)
            if artigos:
                titulos = [a["title"] for a in artigos if a.get("title")]
                st.markdown("**Selecione a notícia que parece dominar sua timeline:**")
                tema_escolhido = st.selectbox("", titulos)
            else:
                st.error("Não foi possível buscar notícias. Verifique sua chave NewsAPI.")

else:
    tema_escolhido = st.text_input(
        "Qual assunto está dominando as notícias agora?",
        placeholder="Ex: escândalo político, morte de celebridade, copa do mundo...",
    )

# ── Análise ───────────────────────────────────────────────────────────────────
if tema_escolhido:
    if st.button("🔍 Analisar cortina de fumaça"):
        with st.spinner("Analisando padrões de atenção midiática..."):
            try:
                client = Groq(api_key=groq_key)
                resultado = analisar_cortina(
                    client,
                    tema_escolhido,
                    tema_manual=(modo != "🔎 Buscar notícias automaticamente (NewsAPI)"),
                )

                st.divider()
                st.markdown("## 📡 Tema em destaque")
                st.markdown(f'<div class="card"><span class="tag">DOMINANDO AS MANCHETES</span><br><b>{resultado["tema_dominante"]}</b><br><br>{resultado["porque_domina"]}</div>', unsafe_allow_html=True)

                st.markdown("## 🌫️ O que pode estar ficando de fora")
                for t in resultado["temas_ofuscados"]:
                    st.markdown(f'<div class="card"><span class="tag">POUCO COBERTO</span><br><b>{t["titulo"]}</b><br><br>{t["descricao"]}</div>', unsafe_allow_html=True)

                st.markdown("## 🧐 Por que isso pode ser uma cortina de fumaça?")
                st.markdown(f'<div class="card">{resultado["analise_cortina"]}</div>', unsafe_allow_html=True)

                st.markdown("## 💭 Para você refletir")
                st.markdown(f'<div class="question-box">❝ {resultado["pergunta_reflexao"]} ❞</div>', unsafe_allow_html=True)

                st.caption("⚠️ Esta análise é gerada por IA e tem fins educativos. Não representa acusações ou verdades absolutas — é um convite ao pensamento crítico.")

            except Exception as e:
                st.error(f"Erro na análise: {e}")
