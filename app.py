import streamlit as st
from groq import Groq
from datetime import datetime
import json

st.set_page_config(page_title="Cortina de Fumaça", page_icon="🔍", layout="centered")

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
    .stButton > button {
        background: #c0392b; color: white; border: none;
        border-radius: 8px; font-weight: 600; padding: 0.6rem 2rem;
    }
    .stButton > button:hover { background: #e74c3c; }
    .card {
        background: #1a1a1a; border-left: 4px solid #c0392b;
        border-radius: 8px; padding: 1.2rem 1.5rem; margin: 1rem 0;
    }
    .tag {
        display: inline-block; background: #2d2d2d; color: #aaa;
        font-size: 0.75rem; padding: 2px 10px; border-radius: 20px; margin-bottom: 0.5rem;
    }
    .question-box {
        background: #161616; border: 1px solid #c0392b44;
        border-radius: 10px; padding: 1.2rem 1.5rem;
        margin-top: 1.5rem; font-style: italic; color: #ccc;
    }
    hr { border-color: #222; }
    .stTextInput > div > div > input {
        background: #1a1a1a; border: 1px solid #333; color: #e8e8e0; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

groq_key = st.secrets.get("GROQ_KEY", "")
if not groq_key:
    st.error("Chave GROQ_KEY não encontrada nos Secrets do Streamlit.")
    st.stop()

client = Groq(api_key=groq_key)

st.markdown("# 🔍 Cortina de Fumaça")
st.markdown("*Qual notícia está monopolizando sua atenção — e o que pode estar ficando de fora?*")
st.divider()

with st.sidebar:
    st.markdown("### ℹ️ Sobre")
    st.caption("Ferramenta de educação midiática. Não acusa ninguém — apenas estimula reflexão crítica sobre como nossa atenção é direcionada.")

def buscar_noticias_quentes() -> list[str]:
    hoje = datetime.now().strftime("%d/%m/%Y")
    prompt = f"""Hoje é {hoje}. Liste as 8 notícias ou temas que estão mais em alta no Brasil AGORA — 
coisas que as pessoas estão comentando nas redes sociais, nos grupos de WhatsApp e nas manchetes.
Pode ser política, celebridade, esporte, economia, tragédia, meme viral, qualquer coisa real.
Seja específico: nomes, acontecimentos concretos.

Responda APENAS com um JSON assim, sem texto antes ou depois:
{{"noticias": ["notícia 1", "notícia 2", "notícia 3", "notícia 4", "notícia 5", "notícia 6", "notícia 7", "notícia 8"]}}"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=500,
    )
    raw = r.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    return data["noticias"]

def analisar_cortina(tema: str) -> dict:
    hoje = datetime.now().strftime("%d/%m/%Y")
    prompt = f"""Você é um analista de mídia crítico e educador. Hoje é {hoje}.
O tema que está dominando as manchetes e redes sociais é: '{tema}'.

Sua tarefa:
1. Explique brevemente por que esse tema está recebendo tanta atenção agora.
2. Identifique 2 ou 3 assuntos REAIS e CONCRETOS que estão acontecendo nesta semana e que podem estar sendo ofuscados por esse tema dominante. Seja específico: projetos de lei, crises, votações, escândalos, acontecimentos internacionais. Se não tiver certeza, indique como "possível".
3. Explique, com base em como mídia e algoritmos funcionam, por que essa dinâmica pode ser considerada uma possível "cortina de fumaça" — sem acusar intenção, apenas analisando o efeito.
4. Faça UMA pergunta aberta e provocativa para o leitor refletir.

Responda APENAS com este JSON, sem texto antes ou depois:
{{
  "tema_dominante": "...",
  "porque_domina": "...",
  "temas_ofuscados": [
    {{"titulo": "...", "descricao": "..."}},
    {{"titulo": "...", "descricao": "..."}}
  ],
  "analise_cortina": "...",
  "pergunta_reflexao": "..."
}}"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1200,
    )
    raw = r.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ── Interface ────────────────────────────────────────────────────────────────
modo = st.radio(
    "Como quer começar?",
    ["🔥 Ver o que está bombando agora", "✏️ Digitar o tema manualmente"],
    horizontal=True,
)

tema_escolhido = None

if modo == "🔥 Ver o que está bombando agora":
    if st.button("Buscar o que está em alta"):
        with st.spinner("Vendo o que o Brasil está comentando..."):
            try:
                noticias = buscar_noticias_quentes()
                st.session_state["noticias"] = noticias
            except Exception as e:
                st.error(f"Erro ao buscar notícias: {e}")

    if "noticias" in st.session_state:
        st.markdown("**Selecione o tema que parece dominar sua timeline:**")
        tema_escolhido = st.selectbox("", st.session_state["noticias"])

else:
    tema_escolhido = st.text_input(
        "Qual assunto está dominando as notícias agora?",
        placeholder="Ex: impeachment, morte de famoso, Copa do Mundo...",
    )

if tema_escolhido:
    if st.button("🔍 Analisar cortina de fumaça"):
        with st.spinner("Analisando padrões de atenção midiática..."):
            try:
                resultado = analisar_cortina(tema_escolhido)

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

                st.caption("⚠️ Análise gerada por IA com fins educativos. Não representa acusações ou verdades absolutas — é um convite ao pensamento crítico.")

            except Exception as e:
                st.error(f"Erro na análise: {e}")
