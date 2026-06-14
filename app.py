import streamlit as st
from groq import Groq
from datetime import datetime
import requests
import json

st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #080808;
        color: #e0e0d8;
    }

    /* Hero */
    .hero {
        text-align: center;
        padding: 3rem 1rem 2rem;
    }
    .hero-label {
        font-size: 0.7rem;
        letter-spacing: 0.25em;
        color: #555;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.2rem;
        font-weight: 700;
        line-height: 1.1;
        color: #f0f0e8;
        margin-bottom: 1rem;
    }
    .hero-sub {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 1.1rem;
        color: #666;
        max-width: 480px;
        margin: 0 auto 2.5rem;
        line-height: 1.6;
    }

    /* Botão principal */
    .stButton > button {
        background: #e8e8e0 !important;
        color: #080808 !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.05em !important;
        padding: 0.75rem 2.5rem !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        background: #ffffff !important;
        transform: translateY(-1px);
    }

    /* Cards de fofoca - linha do tempo estilo jornal */
    .fofoca-item {
        display: flex;
        align-items: flex-start;
        gap: 1.2rem;
        padding: 1.2rem 0;
        border-bottom: 1px solid #1a1a1a;
        cursor: pointer;
    }
    .fofoca-numero {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        font-weight: 700;
        color: #c0392b;
        min-width: 2rem;
        line-height: 1;
        margin-top: 0.2rem;
    }
    .fofoca-conteudo { flex: 1; }
    .fofoca-titulo {
        font-weight: 600;
        font-size: 1rem;
        color: #e8e8e0;
        margin-bottom: 0.3rem;
        line-height: 1.4;
    }
    .fofoca-desc {
        font-size: 0.82rem;
        color: #666;
        line-height: 1.5;
    }
    .fofoca-fonte {
        font-size: 0.72rem;
        color: #444;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-top: 0.3rem;
    }

    /* Card de notícia séria */
    .noticia-card {
        background: #0f0f0f;
        border-left: 3px solid #2d5a27;
        border-radius: 0 6px 6px 0;
        padding: 0.9rem 1.2rem;
        margin: 0.5rem 0;
    }
    .noticia-titulo {
        font-weight: 500;
        font-size: 0.95rem;
        color: #c8d8c0;
        margin-bottom: 0.3rem;
    }
    .noticia-desc { font-size: 0.82rem; color: #555; line-height: 1.5; }

    /* Análise */
    .analise-card {
        background: #0f0f0f;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 1.4rem 1.6rem;
        margin: 1rem 0;
    }
    .analise-label {
        font-size: 0.7rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #c0392b;
        margin-bottom: 0.6rem;
    }
    .analise-texto { font-size: 0.95rem; color: #aaa; line-height: 1.7; }
    .pergunta-box {
        background: #0a0a0a;
        border: 1px solid #1e1e1e;
        border-top: 3px solid #c0392b;
        border-radius: 0 0 8px 8px;
        padding: 1.4rem 1.6rem;
        margin-top: 1.5rem;
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 1.15rem;
        color: #e0e0d8;
        line-height: 1.6;
    }

    /* Seção */
    .secao-titulo {
        font-size: 0.68rem;
        letter-spacing: 0.25em;
        text-transform: uppercase;
        color: #444;
        margin: 2rem 0 1rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .secao-linha { flex: 1; height: 1px; background: #1a1a1a; }

    hr { border-color: #111 !important; }
</style>
""", unsafe_allow_html=True)

# ── Secrets ──────────────────────────────────────────────────────────────────
groq_key     = st.secrets.get("GROQ_KEY", "")
newsdata_key = st.secrets.get("NEWSDATA_KEY", "")  # newsdata.io — gratuito, 200 req/dia

if not groq_key:
    st.error("Configure GROQ_KEY nos Secrets do Streamlit.")
    st.stop()

client = Groq(api_key=groq_key)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📰 Cortina de Fumaça")
    st.caption("Nem tudo que domina sua timeline é o que mais impacta sua vida. Este projeto usa IA para revelar o que pode estar ficando em segundo plano.")
    st.divider()
    st.caption("Fontes: NewsData.io + Groq AI (llama-3.3-70b)")

# ── Funções ───────────────────────────────────────────────────────────────────
def buscar_manchetes_reais() -> tuple[list, list]:
    """Busca manchetes reais de entretenimento e notícias sérias via NewsData.io."""
    headers = {"X-ACCESS-KEY": newsdata_key}

    fofocas_raw, noticias_raw = [], []

    if newsdata_key:
        # Entretenimento/fofoca - BR + mundial
        try:
            r = requests.get(
                "https://newsdata.io/api/1/news",
                params={"language": "pt,en", "category": "entertainment,sports", "size": 10},
                headers=headers, timeout=10
            )
            if r.status_code == 200:
                fofocas_raw = r.json().get("results", [])
        except Exception:
            pass

        # Notícias sérias - política, economia, mundo
        try:
            r = requests.get(
                "https://newsdata.io/api/1/news",
                params={"language": "pt,en", "category": "politics,business,world,science,health", "size": 15},
                headers=headers, timeout=10
            )
            if r.status_code == 200:
                noticias_raw = r.json().get("results", [])
        except Exception:
            pass

    return fofocas_raw, noticias_raw


def processar_com_groq(fofocas_raw: list, noticias_raw: list) -> dict:
    """Groq seleciona os Top 5 fofocas e Top 5 notícias importantes."""
    hoje = datetime.now().strftime("%d/%m/%Y")

    if fofocas_raw and noticias_raw:
        fofocas_str = "\n".join([f"- {a.get('title','')}: {a.get('description','')[:120]}" for a in fofocas_raw[:15]])
        noticias_str = "\n".join([f"- {a.get('title','')}: {a.get('description','')[:120]}" for a in noticias_raw[:20]])

        prompt = f"""Hoje é {hoje}. Você recebeu manchetes REAIS coletadas de portais de notícias agora.

MANCHETES DE ENTRETENIMENTO/ESPORTE:
{fofocas_str}

MANCHETES DE POLÍTICA/ECONOMIA/MUNDO:
{noticias_str}

Sua tarefa:
1. Selecione as 5 manchetes de entretenimento/esporte mais impactantes e virais. Priorize as que envolvem famosos brasileiros, reality shows, futebol, celebridades internacionais. Adapte os títulos para soar naturais em português, mas mantenha os fatos reais.
2. Selecione as 5 manchetes sérias mais importantes da semana — decisões políticas, econômicas, ambientais, internacionais. Adapte para português se necessário.

Responda APENAS com este JSON:
{{
  "fofocas": [
    {{"titulo": "título adaptado e atrativo", "descricao": "1 frase explicando o que aconteceu", "fonte": "nome do portal"}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}}
  ],
  "noticias_importantes": [
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}}
  ]
}}"""

    else:
        # Fallback: Groq usa seu próprio conhecimento atualizado
        prompt = f"""Hoje é {hoje}. Use seu conhecimento mais recente sobre o Brasil e o mundo.

Liste:
1. As 5 fofocas/temas de entretenimento que estão mais em alta AGORA — famosos brasileiros, reality shows, futebol, celebridades internacionais. Seja específico com nomes e acontecimentos reais desta semana.
2. As 5 notícias sérias mais importantes desta semana no Brasil e no mundo — política, economia, direitos, meio ambiente, geopolítica. Acontecimentos que deveriam ter mais atenção.

Responda APENAS com este JSON:
{{
  "fofocas": [
    {{"titulo": "...", "descricao": "1 frase sobre o que aconteceu", "fonte": "provável fonte"}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}}
  ],
  "noticias_importantes": [
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "fonte": "..."}}
  ]
}}"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1500,
    )
    raw = r.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def analisar_cortina(fofoca: dict, noticias: list) -> dict:
    hoje = datetime.now().strftime("%d/%m/%Y")
    noticias_str = "\n".join([f"- {n['titulo']}" for n in noticias])

    prompt = f"""Você é um analista crítico de mídia e comunicação. Hoje é {hoje}.

ASSUNTO EM DESTAQUE: "{fofoca['titulo']}"
{fofoca['descricao']}

NOTÍCIAS SÉRIAS DA MESMA SEMANA:
{noticias_str}

Faça uma análise honesta e educativa:
1. Por que esse assunto específico viralizou tanto? (algoritmos, emoção, identificação, timing — seja preciso)
2. Qual o efeito real de tanta atenção nesse tema enquanto as notícias sérias ficam em segundo plano? (sem dramatizar, mas seja direto)
3. Uma pergunta aberta e provocativa para o leitor refletir — que não seja óbvia nem moralista.

Responda APENAS com este JSON:
{{
  "porque_domina": "2-3 frases analisando por que esse assunto específico captou tanta atenção",
  "analise_cortina": "3-4 frases sobre o efeito dessa distração — educativo, sem apontar culpados",
  "pergunta_reflexao": "uma pergunta instigante e original que provoque reflexão genuína"
}}"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=700,
    )
    raw = r.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-label">Educação Midiática</div>
    <div class="hero-title">Cortina de Fumaça</div>
    <div class="hero-sub">Nem tudo que domina sua timeline é o que mais impacta sua vida.</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    carregar = st.button("Descobrir o que bombou esta semana", use_container_width=True)

if carregar:
    with st.spinner("Coletando manchetes reais..."):
        fofocas_raw, noticias_raw = buscar_manchetes_reais()
    with st.spinner("Selecionando os destaques com IA..."):
        try:
            dados = processar_com_groq(fofocas_raw, noticias_raw)
            st.session_state["dados"] = dados
            st.session_state["fofoca_selecionada"] = None
            st.session_state["analise"] = None
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

# ── Resultado ─────────────────────────────────────────────────────────────────
if "dados" in st.session_state:
    dados = st.session_state["dados"]

    st.markdown("""
    <div class="secao-titulo">
        <span>🔥 O que está bombando</span>
        <div class="secao-linha"></div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Clique no assunto que mais apareceu na sua timeline:")

    for i, f in enumerate(dados["fofocas"]):
        col_txt, col_btn = st.columns([6, 1])
        with col_txt:
            st.markdown(f"""
            <div class="fofoca-item">
                <div class="fofoca-numero">{i+1}</div>
                <div class="fofoca-conteudo">
                    <div class="fofoca-titulo">{f['titulo']}</div>
                    <div class="fofoca-desc">{f['descricao']}</div>
                    <div class="fofoca-fonte">{f.get('fonte','')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<div style='padding-top:1.1rem'>", unsafe_allow_html=True)
            if st.button("→", key=f"sel_{i}", help="Analisar este tema"):
                st.session_state["fofoca_selecionada"] = f
                st.session_state["analise"] = None
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="secao-titulo" style="margin-top:2.5rem">
        <span>📰 Enquanto isso, no mundo real</span>
        <div class="secao-linha"></div>
    </div>
    """, unsafe_allow_html=True)

    for n in dados["noticias_importantes"]:
        st.markdown(f"""
        <div class="noticia-card">
            <div class="noticia-titulo">{n['titulo']}</div>
            <div class="noticia-desc">{n['descricao']}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Análise ───────────────────────────────────────────────────────────────────
if st.session_state.get("fofoca_selecionada") and "dados" in st.session_state:
    fofoca = st.session_state["fofoca_selecionada"]

    if st.session_state.get("analise") is None:
        with st.spinner(f"Analisando '{fofoca['titulo']}'..."):
            try:
                analise = analisar_cortina(fofoca, st.session_state["dados"]["noticias_importantes"])
                st.session_state["analise"] = analise
            except Exception as e:
                st.error(f"Erro: {e}")

    if st.session_state.get("analise"):
        analise = st.session_state["analise"]
        st.divider()

        st.markdown(f"""
        <div class="secao-titulo">
            <span>📡 Tema em destaque</span>
            <div class="secao-linha"></div>
        </div>
        <div class="analise-card">
            <div class="analise-label">Por que viralizou?</div>
            <div class="fofoca-titulo" style="font-size:1.1rem;margin-bottom:0.8rem">{fofoca['titulo']}</div>
            <div class="analise-texto">{analise['porque_domina']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="secao-titulo">
            <span>🌫️ O efeito cortina de fumaça</span>
            <div class="secao-linha"></div>
        </div>
        <div class="analise-card">
            <div class="analise-label">A análise</div>
            <div class="analise-texto">{analise['analise_cortina']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="pergunta-box">
            ❝ {analise['pergunta_reflexao']} ❞
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("⚠️ Análise gerada por IA com fins educativos. Não representa acusações ou verdades absolutas — é um convite ao pensamento crítico sobre como consumimos informação.")
