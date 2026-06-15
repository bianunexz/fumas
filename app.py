import streamlit as st
from groq import Groq
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup

st.set_page_config(
    page_title="Cortina de Fumaça",
    page_icon="🗞️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400;1,700&family=Dancing+Script:wght@600&family=Inter:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] { background-color: #F5F0E8; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, footer { visibility: hidden; }

.hero {
    background: #1a1a1a;
    background-image: linear-gradient(to bottom, rgba(10,10,10,0.6) 0%, rgba(10,10,10,0.8) 100%),
                      url('https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1600&q=80');
    background-size: cover;
    background-position: center top;
    min-height: 88vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 4rem 2rem 3rem;
}
.hero-eyebrow {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #C8B8A2;
    margin-bottom: 1.25rem;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-weight: 900;
    font-size: clamp(56px, 10vw, 110px);
    color: #F5F0E8;
    line-height: 0.92;
    margin: 0 0 0.15em;
}
.hero-title-red { color: #C0392B; }
.hero-divider { width: 48px; height: 2px; background: #C0392B; margin: 0.5rem auto 1.25rem; }
.hero-sub {
    font-family: 'Dancing Script', cursive;
    font-size: clamp(22px, 3.5vw, 36px);
    color: #C8B8A2;
    margin: 0 0 2.5rem;
    line-height: 1.5;
}

div[data-testid="stButton"] > button {
    font-family: 'Playfair Display', serif !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    color: #F5F0E8 !important;
    background: #C0392B !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0.9rem 2.5rem !important;
    letter-spacing: 0.02em !important;
    cursor: pointer !important;
}
div[data-testid="stButton"] > button:hover { background: #96281B !important; }

.datebar {
    background: #1a1a1a;
    color: #6B6050;
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    text-align: center;
    padding: 0.65rem 1rem;
}

.noticias-wrap { background: #F5F0E8; max-width: 800px; margin: 0 auto; padding: 3rem 2rem 4rem; }
.section-eyebrow { font-family: 'Inter', sans-serif; font-size: 10px; letter-spacing: 0.25em; text-transform: uppercase; color: #C0392B; margin-bottom: 0.3rem; }
.section-title { font-family: 'Playfair Display', serif; font-weight: 900; font-size: 38px; color: #1a1a1a; margin: 0; }
.rule-thick { border: none; border-top: 2.5px solid #1a1a1a; margin: 0.75rem 0 0; }
.rule-thin { border: none; border-top: 0.5px solid #D4C9BC; margin: 0; }

.item-row { display: flex; align-items: flex-start; gap: 1rem; padding: 1.1rem 0 0.6rem; }
.item-num { font-family: 'Playfair Display', serif; font-size: 11px; color: #C0392B; font-weight: 700; min-width: 24px; padding-top: 3px; letter-spacing: 0.05em; }
.item-titulo { font-family: 'Playfair Display', serif; font-size: 17px; font-weight: 700; color: #1a1a1a; line-height: 1.35; margin: 0 0 0.25rem; }
.item-meta { font-family: 'Inter', sans-serif; font-size: 11px; color: #9A8F82; }
.item-arrow { margin-left: auto; font-size: 16px; color: #C8B8A2; padding-top: 3px; flex-shrink: 0; }

.reveal-wrap { background: #1a1a1a; padding: 2rem 2rem 1.75rem; margin-bottom: 0.25rem; }
.reveal-col-label { font-family: 'Inter', sans-serif; font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 0.6rem; }
.label-red { color: #C0392B; }
.label-gray { color: #6B6050; }
.reveal-titulo { font-family: 'Playfair Display', serif; font-size: 15px; font-weight: 700; color: #F5F0E8; line-height: 1.4; margin: 0 0 0.5rem; }
.reveal-text { font-family: 'Inter', sans-serif; font-size: 13px; color: #9A8F82; line-height: 1.75; margin: 0 0 0.6rem; }
.reveal-link { font-family: 'Inter', sans-serif; font-size: 11px; color: #C0392B; text-decoration: none; letter-spacing: 0.05em; }
.reveal-inner { display: flex; gap: 0; align-items: stretch; }
.col-sep { width: 1px; background: #2e2e2e; flex-shrink: 0; margin: 0 1.5rem; }
.reflexao { font-family: 'Dancing Script', cursive; font-size: 19px; color: #C8B8A2; line-height: 1.5; border-top: 1px solid #2e2e2e; margin-top: 1.5rem; padding-top: 1.25rem; font-style: italic; }

.quem-wrap { background: #1a1a1a; padding: 4.5rem 2rem 5rem; text-align: center; }
.quem-eyebrow { font-family: 'Inter', sans-serif; font-size: 10px; letter-spacing: 0.25em; text-transform: uppercase; color: #C0392B; margin-bottom: 0.5rem; }
.quem-title { font-family: 'Playfair Display', serif; font-weight: 900; font-size: 40px; color: #F5F0E8; margin: 0 0 0.75rem; }
.quem-pergunta { font-family: 'Dancing Script', cursive; font-size: 27px; color: #C8B8A2; margin: 0 auto 2.5rem; max-width: 520px; line-height: 1.4; }
.quem-cards { display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap; margin-bottom: 2.5rem; }
.quem-card { text-align: center; }
.quem-foto-placeholder { width: 110px; height: 110px; border-radius: 50%; background: #2a2a2a; border: 3px solid #C0392B; margin: 0 auto 0.75rem; display: flex; align-items: center; justify-content: center; font-family: 'Playfair Display', serif; font-size: 32px; color: #C8B8A2; }
.quem-nome { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 17px; color: #F5F0E8; margin-bottom: 0.2rem; }
.quem-role { font-family: 'Inter', sans-serif; font-size: 11px; color: #6B6050; letter-spacing: 0.12em; text-transform: uppercase; }
.quem-missao { font-family: 'Inter', sans-serif; font-size: 14px; color: #9A8F82; line-height: 1.85; max-width: 560px; margin: 0 auto 2rem; }
.quem-fgv { font-family: 'Inter', sans-serif; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #3a3028; border-top: 1px solid #2e2e2e; padding-top: 1.5rem; max-width: 480px; margin: 0 auto; line-height: 2; }

[data-testid="stSpinner"] p { font-family: 'Inter', sans-serif !important; color: #9A8F82 !important; font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

client = Groq()

def formatar_data(data_rss):
    try:
        dt = parsedate_to_datetime(data_rss)
        meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
        return f"{dt.day} {meses[dt.month-1]}"
    except:
        return "Esta semana"

def extrair_texto_noticia(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            html = r.read()
        soup = BeautifulSoup(html, "html.parser")
        texto = " ".join([p.get_text(strip=True) for p in soup.find_all('p')[:3]])
        return texto if len(texto) > 20 else "Conteúdo não disponível."
    except:
        return "Conteúdo não extraído."

def buscar_no_google_news(termo, prefixo, max_itens=20):
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(termo+' when:7d')}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r:
            root = ET.fromstring(r.read())
        noticias = []
        for i, item in enumerate(root.findall(".//item")[:max_itens]):
            t = item.find("title").text
            titulo, veiculo = (t.rsplit(" - ",1)[0], t.rsplit(" - ",1)[-1]) if " - " in t else (t, "Portal")
            link = item.find("link").text
            noticias.append({"id": f"{prefixo}{i}", "titulo": titulo, "veiculo": veiculo, "link": link,
                             "data": formatar_data(item.find("pubDate").text),
                             "conteudo": extrair_texto_noticia(link)[:600]})
        return noticias
    except:
        return []

if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.titulos_exibidos = []
if "aberto" not in st.session_state:
    st.session_state.aberto = None

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Uma leitura diferente do seu feed</div>
    <div class="hero-title">CORTINA<br>DE <span class="hero-title-red">FUMAÇA</span></div>
    <div class="hero-divider"></div>
    <div class="hero-sub">Nem tudo que domina sua timeline<br>é o que mais importa sua vida.</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 1.4, 1])
with c2:
    if st.button("O que aconteceu essa semana?", use_container_width=True):
        with st.spinner("Lendo o noticiário da semana..."):
            try:
                fofocas_brutas = buscar_no_google_news('"pronunciamento" OR "polêmica" OR "treta" OR "cancelamento" OR "respondeu" OR "Famosos" OR "influencer"', "F", 20)
                serias_brutas  = buscar_no_google_news("projeto de lei OR investigação OR stf OR senado OR câmara OR operação policial OR política pública", "S", 20)
                if not fofocas_brutas or not serias_brutas:
                    st.error("Busca falhou. Tente novamente.")
                    st.stop()

                ja = st.session_state.titulos_exibidos
                fn = [f for f in fofocas_brutas if f["titulo"] not in ja][:5]
                sn = [s for s in serias_brutas  if s["titulo"] not in ja][:5]
                st.session_state.fofocas_originais = {f["id"]: f for f in fn}
                st.session_state.serias_originais  = {s["id"]: s for s in sn}

                fd = [{"id": f["id"], "titulo": f["titulo"], "veiculo": f["veiculo"], "conteudo": f["conteudo"]} for f in fn]
                sd = [{"id": s["id"], "titulo": s["titulo"], "veiculo": s["veiculo"], "conteudo": s["conteudo"]} for s in sn]

                prompt = f"""Você é um crítico de mídia brasileiro, com ironia leve e inteligente.
Crie 5 pares ligando fofoca a notícia séria.
FOFOCAS: {json.dumps(fd, ensure_ascii=False)}
NOTÍCIAS SÉRIAS: {json.dumps(sd, ensure_ascii=False)}
Para cada par: id_fofoca, resumo_fofoca (2 frases, tom adequado ao conteúdo), id_seria, resumo_seria (2 frases didáticas), pergunta_reflexiva (específica, mencione ambos os assuntos, não culpe o público).
JSON apenas: {{"pares": [{{"id_fofoca":"","resumo_fofoca":"","id_seria":"","resumo_seria":"","pergunta_reflexiva":""}}]}}"""

                r = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"user","content":prompt}],
                    temperature=0.5, response_format={"type":"json_object"}
                )
                st.session_state.resultado = json.loads(r.choices[0].message.content)
                for par in st.session_state.resultado.get("pares",[]):
                    fo = st.session_state.fofocas_originais.get(par.get("id_fofoca"))
                    so = st.session_state.serias_originais.get(par.get("id_seria"))
                    if fo: st.session_state.titulos_exibidos.append(fo["titulo"])
                    if so: st.session_state.titulos_exibidos.append(so["titulo"])
                st.session_state.dados_prontos = True
                st.session_state.aberto = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

# ── NOTÍCIAS ──────────────────────────────────────────────────────────────────
if st.session_state.get("dados_prontos"):
    from datetime import datetime
    hoje = datetime.now()
    meses_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    st.markdown(f'<div class="datebar">{hoje.day} de {meses_pt[hoje.month-1]} de {hoje.year}</div>', unsafe_allow_html=True)

    st.markdown('<div class="noticias-wrap">', unsafe_allow_html=True)
    st.markdown("""
        <div class="section-eyebrow">Em alta agora</div>
        <div class="section-title">Edição da semana</div>
        <hr class="rule-thick">
    """, unsafe_allow_html=True)

    for idx, par in enumerate(st.session_state.resultado.get("pares",[])):
        fofoca = st.session_state.fofocas_originais.get(par.get("id_fofoca"))
        seria  = st.session_state.serias_originais.get(par.get("id_seria"))
        if not fofoca or not seria:
            continue

        st.markdown(f"""
        <div class="item-row">
            <div class="item-num">0{idx+1}</div>
            <div style="flex:1">
                <div class="item-titulo">{fofoca['titulo']}</div>
                <div class="item-meta">{fofoca['data']} &nbsp;·&nbsp; {fofoca['veiculo']}</div>
            </div>
            <div class="item-arrow">→</div>
        </div>
        """, unsafe_allow_html=True)

        ca, cb, cc = st.columns([0.12, 1, 0.12])
        with cb:
            lbl = "▲ Fechar" if st.session_state.aberto == idx else "▼ Ver o que estava por baixo"
            if st.button(lbl, key=f"t{idx}", use_container_width=True):
                st.session_state.aberto = None if st.session_state.aberto == idx else idx
                st.rerun()

        if st.session_state.aberto == idx:
            st.markdown(f"""
            <div class="reveal-wrap">
                <div class="reveal-inner">
                    <div style="flex:1">
                        <div class="reveal-col-label label-red">🔥 Por que bombou</div>
                        <div class="reveal-titulo">{fofoca['titulo']}</div>
                        <div class="reveal-text">{par.get('resumo_fofoca')}</div>
                        <a href="{fofoca['link']}" target="_blank" class="reveal-link">→ Ver na fonte</a>
                    </div>
                    <div class="col-sep"></div>
                    <div style="flex:1">
                        <div class="reveal-col-label label-gray">🌫️ Enquanto isso</div>
                        <div class="reveal-titulo">{seria['titulo']}</div>
                        <div class="reveal-text">{par.get('resumo_seria')}</div>
                        <a href="{seria['link']}" target="_blank" class="reveal-link">→ Ler a notícia</a>
                    </div>
                </div>
                <div class="reflexao">"{par.get('pergunta_reflexiva')}"</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<hr class="rule-thin">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── QUEM SOMOS ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="quem-wrap">
    <div class="quem-eyebrow">O projeto</div>
    <div class="quem-title">Quem somos</div>
    <div class="quem-pergunta">Mas por que a Cortina de Fumaça?</div>

    <div class="quem-cards">
        <div class="quem-card">
            <div class="quem-foto-placeholder">B</div>
            <div class="quem-nome">Bianca Nunes</div>
            <div class="quem-role">Co-criadora</div>
        </div>
        <div class="quem-card">
            <div class="quem-foto-placeholder">M</div>
            <div class="quem-nome">Mariana Gontijo</div>
            <div class="quem-role">Co-criadora</div>
        </div>
    </div>

    <div class="quem-missao">
        Vivemos numa era em que o algoritmo decide o que merece atenção — e muitas vezes,
        o que mais viraliza é o que menos importa. A Cortina de Fumaça nasceu para mostrar
        esse contraste: ao lado de cada fofoca que dominou os feeds, há uma notícia séria
        que passou quase despercebida. Não para culpar ninguém, mas para abrir uma janela.
    </div>

    <div class="quem-fgv">
        Matéria de Comunicação, Filosofia &amp; Tecnologia — IA<br>
        Prof. Luis Gustavo de Oliveira Rodrigues<br>
        FGV Escola de Comunicação
    </div>
</div>
""", unsafe_allow_html=True)
