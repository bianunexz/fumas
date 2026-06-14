import streamlit as st
from groq import Groq
from datetime import datetime, timedelta
import json
import re

# ── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #080808;
    color: #e0e0d8;
}
.hero {
    text-align: center;
    padding: 3.5rem 1rem 2rem;
}
.hero-label {
    font-size: 0.68rem;
    letter-spacing: 0.3em;
    color: #444;
    text-transform: uppercase;
    margin-bottom: 1rem;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 3.4rem;
    font-weight: 700;
    color: #f0f0e8;
    margin-bottom: 0.8rem;
    line-height: 1.1;
}
.hero-sub {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1.05rem;
    color: #555;
    max-width: 420px;
    margin: 0 auto 2.5rem;
    line-height: 1.7;
}
.stButton > button {
    background: #e8e8e0 !important;
    color: #080808 !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.06em !important;
    padding: 0.75rem 2.5rem !important;
}
.stButton > button:hover { background: #fff !important; }

.secao {
    font-size: 0.66rem;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: #444;
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 2.5rem 0 1.2rem;
}
.secao-linha { flex: 1; height: 1px; background: #1c1c1c; }

.fofoca-row {
    display: flex;
    align-items: flex-start;
    gap: 1.1rem;
    padding: 1.1rem 0;
    border-bottom: 1px solid #141414;
}
.fofoca-num {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #c0392b;
    min-width: 2rem;
    line-height: 1;
    padding-top: 0.15rem;
}
.fofoca-titulo { font-weight: 600; font-size: 0.97rem; color: #e8e8e0; margin-bottom: 0.25rem; }
.fofoca-desc { font-size: 0.8rem; color: #555; line-height: 1.5; }
.fofoca-link a { font-size: 0.72rem; color: #c0392b; text-decoration: none; letter-spacing: 0.04em; }
.fofoca-link a:hover { text-decoration: underline; }

.noticia-card {
    background: #0d0d0d;
    border-left: 3px solid #1e4d1a;
    border-radius: 0 6px 6px 0;
    padding: 0.9rem 1.2rem;
    margin: 0.5rem 0;
}
.noticia-titulo { font-weight: 500; font-size: 0.93rem; color: #b8d0b0; margin-bottom: 0.25rem; }
.noticia-desc { font-size: 0.8rem; color: #4a4a4a; line-height: 1.5; margin-bottom: 0.35rem; }
.noticia-link a { font-size: 0.72rem; color: #2d7a27; text-decoration: none; }
.noticia-link a:hover { text-decoration: underline; }

.analise-card {
    background: #0d0d0d;
    border: 1px solid #1a1a1a;
    border-radius: 8px;
    padding: 1.3rem 1.5rem;
    margin: 0.8rem 0;
}
.analise-label {
    font-size: 0.66rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #c0392b;
    margin-bottom: 0.6rem;
}
.analise-texto { font-size: 0.93rem; color: #888; line-height: 1.75; }

.pergunta-box {
    background: #0a0a0a;
    border-top: 3px solid #c0392b;
    border-radius: 0 0 8px 8px;
    padding: 1.4rem 1.6rem;
    margin-top: 1.5rem;
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1.12rem;
    color: #e0e0d8;
    line-height: 1.65;
}
.aviso {
    font-size: 0.75rem;
    color: #333;
    text-align: center;
    margin-top: 2rem;
    line-height: 1.6;
    border-top: 1px solid #141414;
    padding-top: 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# ── Secrets ───────────────────────────────────────────────────────────────────
groq_key = st.secrets.get("GROQ_KEY", "")
if not groq_key:
    st.error("Configure GROQ_KEY nos Secrets do Streamlit.")
    st.stop()

client = Groq(api_key=groq_key)

with st.sidebar:
    st.markdown("### 📰 Cortina de Fumaça")
    st.caption("Ferramenta de educação midiática. Usa IA com busca web real para identificar o que estava em alta e o que ficou em segundo plano.")
    st.divider()
    st.caption("Modelo: Groq compound-beta (busca web nativa)")

# ── Funções ───────────────────────────────────────────────────────────────────
def limpar_json(raw: str) -> str:
    if "```" in raw:
        partes = raw.split("```")
        for p in partes:
            if p.startswith("json"):
                return p[4:].strip()
            if p.strip().startswith("{"):
                return p.strip()
    return raw.strip()

def buscar_fofocas_reais() -> list[dict]:
    """Usa compound-beta (busca web nativa) para pegar fofocas reais da semana."""
    hoje = datetime.now().strftime("%d/%m/%Y")

    semana_inicio = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
    prompt = f"""Hoje é {hoje}. Faça uma busca na web agora e encontre as 5 fofocas ou assuntos de entretenimento que estão mais em alta no Brasil e no mundo NESTA SEMANA.

⚠️ REGRA FUNDAMENTAL: Todos os assuntos devem ter acontecido entre {semana_inicio} e {hoje}. Nada de notícias antigas, genéricas ou sem data confirmada.

Foco em: famosos brasileiros, reality shows, celebridades internacionais, futebol (jogadores, VAR, confusões), música pop, TikTok viral, casamentos/separações, polêmicas de famosos.

Para cada assunto, inclua a data exata em que aconteceu na descrição (ex: "na segunda-feira, dia 09/06").

Responda APENAS com este JSON (sem texto antes ou depois):
{{
  "fofocas": [
    {{"titulo": "...", "descricao": "o que aconteceu + quando aconteceu esta semana", "url": "https://...", "fonte": "nome do portal"}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}}
  ]
}}"""

    r = client.chat.completions.create(
        model="compound-beta",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1200,
    )
    raw = limpar_json(r.choices[0].message.content)
    return json.loads(raw)["fofocas"]


def buscar_noticias_importantes() -> list[dict]:
    """Usa compound-beta para buscar notícias sérias recentes."""
    hoje = datetime.now().strftime("%d/%m/%Y")

    semana_inicio = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
    prompt = f"""Hoje é {hoje}. Faça uma busca na web agora e encontre de 4 a 5 notícias REAIS desta semana (entre {semana_inicio} e {hoje}) no Brasil e no mundo com impacto social, político ou econômico relevante que receberam MENOS atenção do grande público.

⚠️ REGRA FUNDAMENTAL: As notícias devem ser da MESMA SEMANA que as fofocas em alta — entre {semana_inicio} e {hoje}. Isso é essencial para o projeto: queremos mostrar o que aconteceu AO MESMO TEMPO que as fofocas dominavam as redes.

Foco em: votações no Congresso, decisões do STF, operações da Polícia Federal, dados de desmatamento, crises internacionais específicas, projetos de lei polêmicos, saúde pública, direitos humanos.

IMPORTANTE: seja específico. Não quero "reforma tributária" genérica. Quero "Câmara aprova X por Y votos no dia Z" ou "STF decide sobre W em sessão de terça-feira". Inclua a data exata na descrição.

Responda APENAS com este JSON:
{{
  "noticias": [
    {{"titulo": "título específico e factual", "descricao": "o que aconteceu + data exata desta semana + quem está envolvido", "url": "https://...", "fonte": "nome do veículo"}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}}
  ]
}}"""

    r = client.chat.completions.create(
        model="compound-beta",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1200,
    )
    raw = limpar_json(r.choices[0].message.content)
    return json.loads(raw)["noticias"]


def analisar_cortina(fofoca: dict, noticias: list[dict]) -> dict:
    hoje = datetime.now().strftime("%d/%m/%Y")
    noticias_str = "\n".join([f"- {n['titulo']}: {n['descricao']}" for n in noticias])

    prompt = f"""Você é um analista de comunicação e mídia com abordagem educativa. Hoje é {hoje}.

ASSUNTO EM DESTAQUE ESTA SEMANA:
Título: {fofoca['titulo']}
O que aconteceu: {fofoca['descricao']}

NOTÍCIAS IMPORTANTES DA MESMA SEMANA (aconteceram nos mesmos dias) COM MENOS ATENÇÃO:
{noticias_str}

⚠️ CONTEXTO IMPORTANTE: Esses dois grupos de assuntos aconteceram na MESMA SEMANA. A fofoca dominou as redes enquanto as notícias sérias também estavam acontecendo — ao mesmo tempo, nos mesmos dias. Não afirme que um escondeu o outro: mostre que disputaram atenção simultaneamente.

Escreva uma análise honesta e educativa com 3 partes:

1. POR QUE VIRALIZOU: Explique, com base em algoritmos e psicologia da atenção, por que esse assunto específico captou tanto engajamento nessa semana. Seja preciso — emoção, identidade, entretenimento, simplicidade narrativa.

2. ATENÇÃO DIVIDIDA NA MESMA SEMANA: Mostre que os dois tipos de assunto aconteceram simultaneamente e competiram pela atenção. Use linguagem como "ao mesmo tempo que", "enquanto isso", "na mesma semana em que". Explique agenda-setting de forma acessível, sem sugerir conspiração.

3. PERGUNTA DE REFLEXÃO: Uma pergunta original e instigante sobre hábitos pessoais de consumo de informação ou sobre como plataformas moldam o que consideramos importante. Evite clichês como "será que a mídia mente?".

Responda APENAS com este JSON:
{{
  "porque_domina": "análise de 2-3 frases sobre por que esse assunto específico capturou atenção",
  "analise_cortina": "3-4 frases sobre atenção dividida e agenda-setting, sem afirmar conspiração",
  "pergunta_reflexao": "uma pergunta original e provocativa"
}}"""

    r = client.chat.completions.create(
        model="compound-beta",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=800,
    )
    raw = limpar_json(r.choices[0].message.content)
    return json.loads(raw)

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

# ── Carregamento ──────────────────────────────────────────────────────────────
if carregar:
    st.session_state.pop("dados", None)
    st.session_state.pop("fofoca_selecionada", None)
    st.session_state.pop("analise", None)

    col_a, col_b = st.columns(2)
    with col_a:
        with st.spinner("🔍 Buscando fofocas da semana..."):
            try:
                fofocas = buscar_fofocas_reais()
            except Exception as e:
                st.error(f"Erro fofocas: {e}")
                fofocas = []
    with col_b:
        with st.spinner("📰 Buscando notícias importantes..."):
            try:
                noticias = buscar_noticias_importantes()
            except Exception as e:
                st.error(f"Erro notícias: {e}")
                noticias = []

    if fofocas or noticias:
        st.session_state["dados"] = {"fofocas": fofocas, "noticias": noticias}

# ── Exibir resultados ─────────────────────────────────────────────────────────
if "dados" in st.session_state:
    dados = st.session_state["dados"]

    # Fofocas
    st.markdown("""
    <div class="secao"><span>🔥 O que está bombando esta semana</span><div class="secao-linha"></div></div>
    <p style="font-size:0.82rem;color:#444;margin-bottom:0.5rem">Clique em → para ver a análise completa</p>
    """, unsafe_allow_html=True)

    for i, f in enumerate(dados["fofocas"]):
        col_txt, col_btn = st.columns([6, 1])
        with col_txt:
            link_html = f'<div class="fofoca-link"><a href="{f.get("url","#")}" target="_blank">🔗 Saiba mais ({f.get("fonte","")})</a></div>' if f.get("url") else ""
            st.markdown(f"""
            <div class="fofoca-row">
                <div class="fofoca-num">{i+1}</div>
                <div style="flex:1">
                    <div class="fofoca-titulo">{f['titulo']}</div>
                    <div class="fofoca-desc">{f['descricao']}</div>
                    {link_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<div style='padding-top:1rem'>", unsafe_allow_html=True)
            if st.button("→", key=f"sel_{i}"):
                st.session_state["fofoca_selecionada"] = f
                st.session_state["analise"] = None
            st.markdown("</div>", unsafe_allow_html=True)

    # Notícias sérias
    st.markdown("""
    <div class="secao" style="margin-top:3rem">
        <span>📰 Enquanto isso, no mundo real</span>
        <div class="secao-linha"></div>
    </div>
    """, unsafe_allow_html=True)

    for n in dados["noticias"]:
        link_html = f'<div class="noticia-link"><a href="{n.get("url","#")}" target="_blank">🔗 Ler em {n.get("fonte","")}</a></div>' if n.get("url") else ""
        st.markdown(f"""
        <div class="noticia-card">
            <div class="noticia-titulo">{n['titulo']}</div>
            <div class="noticia-desc">{n['descricao']}</div>
            {link_html}
        </div>
        """, unsafe_allow_html=True)

# ── Análise ───────────────────────────────────────────────────────────────────
if st.session_state.get("fofoca_selecionada") and "dados" in st.session_state:
    fofoca = st.session_state["fofoca_selecionada"]

    if st.session_state.get("analise") is None:
        with st.spinner(f"Analisando '{fofoca['titulo']}'..."):
            try:
                analise = analisar_cortina(fofoca, st.session_state["dados"]["noticias"])
                st.session_state["analise"] = analise
            except Exception as e:
                st.error(f"Erro na análise: {e}")

    if st.session_state.get("analise"):
        analise = st.session_state["analise"]

        st.markdown("""
        <div class="secao" style="margin-top:3rem">
            <span>📡 Análise do tema</span>
            <div class="secao-linha"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="analise-card">
            <div class="analise-label">Tema em destaque</div>
            <div class="fofoca-titulo" style="font-size:1.05rem;margin-bottom:0.7rem">{fofoca['titulo']}</div>
            <div class="analise-label" style="margin-top:0.8rem">Por que viralizou?</div>
            <div class="analise-texto">{analise['porque_domina']}</div>
        </div>

        <div class="analise-card">
            <div class="analise-label">🌫️ Atenção dividida — agenda-setting</div>
            <div class="analise-texto">{analise['analise_cortina']}</div>
        </div>

        <div class="pergunta-box">
            ❝ {analise['pergunta_reflexao']} ❞
        </div>

        <div class="aviso">
            ⚠️ Esta análise é gerada por IA com fins exclusivamente educativos.<br>
            Não afirma que existe uma relação causal entre os assuntos.<br>
            Os dois temas simplesmente disputaram atenção no mesmo período — cabe a você decidir como distribuir a sua.
        </div>
        """, unsafe_allow_html=True)
}
.hero-sub {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1.05rem;
    color: #555;
    max-width: 420px;
    margin: 0 auto 2.5rem;
    line-height: 1.7;
}
.stButton > button {
    background: #e8e8e0 !important;
    color: #080808 !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.06em !important;
    padding: 0.75rem 2.5rem !important;
}
.stButton > button:hover { background: #fff !important; }

.secao {
    font-size: 0.66rem;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: #444;
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 2.5rem 0 1.2rem;
}
.secao-linha { flex: 1; height: 1px; background: #1c1c1c; }

.fofoca-row {
    display: flex;
    align-items: flex-start;
    gap: 1.1rem;
    padding: 1.1rem 0;
    border-bottom: 1px solid #141414;
}
.fofoca-num {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #c0392b;
    min-width: 2rem;
    line-height: 1;
    padding-top: 0.15rem;
}
.fofoca-titulo { font-weight: 600; font-size: 0.97rem; color: #e8e8e0; margin-bottom: 0.25rem; }
.fofoca-desc { font-size: 0.8rem; color: #555; line-height: 1.5; }
.fofoca-link a { font-size: 0.72rem; color: #c0392b; text-decoration: none; letter-spacing: 0.04em; }
.fofoca-link a:hover { text-decoration: underline; }

.noticia-card {
    background: #0d0d0d;
    border-left: 3px solid #1e4d1a;
    border-radius: 0 6px 6px 0;
    padding: 0.9rem 1.2rem;
    margin: 0.5rem 0;
}
.noticia-titulo { font-weight: 500; font-size: 0.93rem; color: #b8d0b0; margin-bottom: 0.25rem; }
.noticia-desc { font-size: 0.8rem; color: #4a4a4a; line-height: 1.5; margin-bottom: 0.35rem; }
.noticia-link a { font-size: 0.72rem; color: #2d7a27; text-decoration: none; }
.noticia-link a:hover { text-decoration: underline; }

.analise-card {
    background: #0d0d0d;
    border: 1px solid #1a1a1a;
    border-radius: 8px;
    padding: 1.3rem 1.5rem;
    margin: 0.8rem 0;
}
.analise-label {
    font-size: 0.66rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #c0392b;
    margin-bottom: 0.6rem;
}
.analise-texto { font-size: 0.93rem; color: #888; line-height: 1.75; }

.pergunta-box {
    background: #0a0a0a;
    border-top: 3px solid #c0392b;
    border-radius: 0 0 8px 8px;
    padding: 1.4rem 1.6rem;
    margin-top: 1.5rem;
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 1.12rem;
    color: #e0e0d8;
    line-height: 1.65;
}
.aviso {
    font-size: 0.75rem;
    color: #333;
    text-align: center;
    margin-top: 2rem;
    line-height: 1.6;
    border-top: 1px solid #141414;
    padding-top: 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# ── Secrets ───────────────────────────────────────────────────────────────────
groq_key = st.secrets.get("GROQ_KEY", "")
if not groq_key:
    st.error("Configure GROQ_KEY nos Secrets do Streamlit.")
    st.stop()

client = Groq(api_key=groq_key)

with st.sidebar:
    st.markdown("### 📰 Cortina de Fumaça")
    st.caption("Ferramenta de educação midiática. Usa IA com busca web real para identificar o que estava em alta e o que ficou em segundo plano.")
    st.divider()
    st.caption("Modelo: Groq compound-beta (busca web nativa)")

# ── Funções ───────────────────────────────────────────────────────────────────
def limpar_json(raw: str) -> str:
    if "```" in raw:
        partes = raw.split("```")
        for p in partes:
            if p.startswith("json"):
                return p[4:].strip()
            if p.strip().startswith("{"):
                return p.strip()
    return raw.strip()

def buscar_fofocas_reais() -> list[dict]:
    """Usa compound-beta (busca web nativa) para pegar fofocas reais da semana."""
    hoje = datetime.now().strftime("%d/%m/%Y")

    semana_inicio = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
    prompt = f"""Hoje é {hoje}. Faça uma busca na web agora e encontre as 5 fofocas ou assuntos de entretenimento que estão mais em alta no Brasil e no mundo NESTA SEMANA.

⚠️ REGRA FUNDAMENTAL: Todos os assuntos devem ter acontecido entre {semana_inicio} e {hoje}. Nada de notícias antigas, genéricas ou sem data confirmada.

Foco em: famosos brasileiros, reality shows, celebridades internacionais, futebol (jogadores, VAR, confusões), música pop, TikTok viral, casamentos/separações, polêmicas de famosos.

Para cada assunto, inclua a data exata em que aconteceu na descrição (ex: "na segunda-feira, dia 09/06").

Responda APENAS com este JSON (sem texto antes ou depois):
{{
  "fofocas": [
    {{"titulo": "...", "descricao": "o que aconteceu + quando aconteceu esta semana", "url": "https://...", "fonte": "nome do portal"}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}}
  ]
}}"""

    r = client.chat.completions.create(
        model="compound-beta",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1200,
    )
    raw = limpar_json(r.choices[0].message.content)
    return json.loads(raw)["fofocas"]


def buscar_noticias_importantes() -> list[dict]:
    """Usa compound-beta para buscar notícias sérias recentes."""
    hoje = datetime.now().strftime("%d/%m/%Y")

    semana_inicio = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
    prompt = f"""Hoje é {hoje}. Faça uma busca na web agora e encontre de 4 a 5 notícias REAIS desta semana (entre {semana_inicio} e {hoje}) no Brasil e no mundo com impacto social, político ou econômico relevante que receberam MENOS atenção do grande público.

⚠️ REGRA FUNDAMENTAL: As notícias devem ser da MESMA SEMANA que as fofocas em alta — entre {semana_inicio} e {hoje}. Isso é essencial para o projeto: queremos mostrar o que aconteceu AO MESMO TEMPO que as fofocas dominavam as redes.

Foco em: votações no Congresso, decisões do STF, operações da Polícia Federal, dados de desmatamento, crises internacionais específicas, projetos de lei polêmicos, saúde pública, direitos humanos.

IMPORTANTE: seja específico. Não quero "reforma tributária" genérica. Quero "Câmara aprova X por Y votos no dia Z" ou "STF decide sobre W em sessão de terça-feira". Inclua a data exata na descrição.

Responda APENAS com este JSON:
{{
  "noticias": [
    {{"titulo": "título específico e factual", "descricao": "o que aconteceu + data exata desta semana + quem está envolvido", "url": "https://...", "fonte": "nome do veículo"}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}},
    {{"titulo": "...", "descricao": "...", "url": "https://...", "fonte": "..."}}
  ]
}}"""

    r = client.chat.completions.create(
        model="compound-beta",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1200,
    )
    raw = limpar_json(r.choices[0].message.content)
    return json.loads(raw)["noticias"]


def analisar_cortina(fofoca: dict, noticias: list[dict]) -> dict:
    hoje = datetime.now().strftime("%d/%m/%Y")
    noticias_str = "\n".join([f"- {n['titulo']}: {n['descricao']}" for n in noticias])

    prompt = f"""Você é um analista de comunicação e mídia com abordagem educativa. Hoje é {hoje}.

ASSUNTO EM DESTAQUE ESTA SEMANA:
Título: {fofoca['titulo']}
O que aconteceu: {fofoca['descricao']}

NOTÍCIAS IMPORTANTES DA MESMA SEMANA (aconteceram nos mesmos dias) COM MENOS ATENÇÃO:
{noticias_str}

⚠️ CONTEXTO IMPORTANTE: Esses dois grupos de assuntos aconteceram na MESMA SEMANA. A fofoca dominou as redes enquanto as notícias sérias também estavam acontecendo — ao mesmo tempo, nos mesmos dias. Não afirme que um escondeu o outro: mostre que disputaram atenção simultaneamente.

Escreva uma análise honesta e educativa com 3 partes:

1. POR QUE VIRALIZOU: Explique, com base em algoritmos e psicologia da atenção, por que esse assunto específico captou tanto engajamento nessa semana. Seja preciso — emoção, identidade, entretenimento, simplicidade narrativa.

2. ATENÇÃO DIVIDIDA NA MESMA SEMANA: Mostre que os dois tipos de assunto aconteceram simultaneamente e competiram pela atenção. Use linguagem como "ao mesmo tempo que", "enquanto isso", "na mesma semana em que". Explique agenda-setting de forma acessível, sem sugerir conspiração.

3. PERGUNTA DE REFLEXÃO: Uma pergunta original e instigante sobre hábitos pessoais de consumo de informação ou sobre como plataformas moldam o que consideramos importante. Evite clichês como "será que a mídia mente?".

Responda APENAS com este JSON:
{{
  "porque_domina": "análise de 2-3 frases sobre por que esse assunto específico capturou atenção",
  "analise_cortina": "3-4 frases sobre atenção dividida e agenda-setting, sem afirmar conspiração",
  "pergunta_reflexao": "uma pergunta original e provocativa"
}}"""

    r = client.chat.completions.create(
        model="compound-beta",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=800,
    )
    raw = limpar_json(r.choices[0].message.content)
    return json.loads(raw)

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

# ── Carregamento ──────────────────────────────────────────────────────────────
if carregar:
    st.session_state.pop("dados", None)
    st.session_state.pop("fofoca_selecionada", None)
    st.session_state.pop("analise", None)

    col_a, col_b = st.columns(2)
    with col_a:
        with st.spinner("🔍 Buscando fofocas da semana..."):
            try:
                fofocas = buscar_fofocas_reais()
            except Exception as e:
                st.error(f"Erro fofocas: {e}")
                fofocas = []
    with col_b:
        with st.spinner("📰 Buscando notícias importantes..."):
            try:
                noticias = buscar_noticias_importantes()
            except Exception as e:
                st.error(f"Erro notícias: {e}")
                noticias = []

    if fofocas or noticias:
        st.session_state["dados"] = {"fofocas": fofocas, "noticias": noticias}

# ── Exibir resultados ─────────────────────────────────────────────────────────
if "dados" in st.session_state:
    dados = st.session_state["dados"]

    # Fofocas
    st.markdown("""
    <div class="secao"><span>🔥 O que está bombando esta semana</span><div class="secao-linha"></div></div>
    <p style="font-size:0.82rem;color:#444;margin-bottom:0.5rem">Clique em → para ver a análise completa</p>
    """, unsafe_allow_html=True)

    for i, f in enumerate(dados["fofocas"]):
        col_txt, col_btn = st.columns([6, 1])
        with col_txt:
            link_html = f'<div class="fofoca-link"><a href="{f.get("url","#")}" target="_blank">🔗 Saiba mais ({f.get("fonte","")})</a></div>' if f.get("url") else ""
            st.markdown(f"""
            <div class="fofoca-row">
                <div class="fofoca-num">{i+1}</div>
                <div style="flex:1">
                    <div class="fofoca-titulo">{f['titulo']}</div>
                    <div class="fofoca-desc">{f['descricao']}</div>
                    {link_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<div style='padding-top:1rem'>", unsafe_allow_html=True)
            if st.button("→", key=f"sel_{i}"):
                st.session_state["fofoca_selecionada"] = f
                st.session_state["analise"] = None
            st.markdown("</div>", unsafe_allow_html=True)

    # Notícias sérias
    st.markdown("""
    <div class="secao" style="margin-top:3rem">
        <span>📰 Enquanto isso, no mundo real</span>
        <div class="secao-linha"></div>
    </div>
    """, unsafe_allow_html=True)

    for n in dados["noticias"]:
        link_html = f'<div class="noticia-link"><a href="{n.get("url","#")}" target="_blank">🔗 Ler em {n.get("fonte","")}</a></div>' if n.get("url") else ""
        st.markdown(f"""
        <div class="noticia-card">
            <div class="noticia-titulo">{n['titulo']}</div>
            <div class="noticia-desc">{n['descricao']}</div>
            {link_html}
        </div>
        """, unsafe_allow_html=True)

# ── Análise ───────────────────────────────────────────────────────────────────
if st.session_state.get("fofoca_selecionada") and "dados" in st.session_state:
    fofoca = st.session_state["fofoca_selecionada"]

    if st.session_state.get("analise") is None:
        with st.spinner(f"Analisando '{fofoca['titulo']}'..."):
            try:
                analise = analisar_cortina(fofoca, st.session_state["dados"]["noticias"])
                st.session_state["analise"] = analise
            except Exception as e:
                st.error(f"Erro na análise: {e}")

    if st.session_state.get("analise"):
        analise = st.session_state["analise"]

        st.markdown("""
        <div class="secao" style="margin-top:3rem">
            <span>📡 Análise do tema</span>
            <div class="secao-linha"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="analise-card">
            <div class="analise-label">Tema em destaque</div>
            <div class="fofoca-titulo" style="font-size:1.05rem;margin-bottom:0.7rem">{fofoca['titulo']}</div>
            <div class="analise-label" style="margin-top:0.8rem">Por que viralizou?</div>
            <div class="analise-texto">{analise['porque_domina']}</div>
        </div>

        <div class="analise-card">
            <div class="analise-label">🌫️ Atenção dividida — agenda-setting</div>
            <div class="analise-texto">{analise['analise_cortina']}</div>
        </div>

        <div class="pergunta-box">
            ❝ {analise['pergunta_reflexao']} ❞
        </div>

        <div class="aviso">
            ⚠️ Esta análise é gerada por IA com fins exclusivamente educativos.<br>
            Não afirma que existe uma relação causal entre os assuntos.<br>
            Os dois temas simplesmente disputaram atenção no mesmo período — cabe a você decidir como distribuir a sua.
        </div>
        """, unsafe_allow_html=True)
