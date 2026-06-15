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
    page_icon="🌫️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

/* Reset & base */
[data-testid="stAppViewContainer"] {
    background-color: #0D0D0D;
}
[data-testid="stHeader"] {
    background-color: #0D0D0D;
}
[data-testid="stSidebar"] {
    background-color: #111111;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 960px;
}

/* Hero */
.hero {
    text-align: center;
    padding: 3.5rem 1rem 2rem;
    border-bottom: 1px solid #2a2a2a;
    margin-bottom: 2.5rem;
}
.hero-eyebrow {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #FF4B1F;
    margin-bottom: 0.75rem;
}
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(56px, 10vw, 96px);
    color: #F5F0E8;
    line-height: 0.95;
    letter-spacing: 0.02em;
    margin: 0 0 0.5rem;
}
.hero-title span {
    color: #FF4B1F;
}
.hero-sub {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    color: #6B6B6B;
    max-width: 480px;
    margin: 0.75rem auto 0;
    line-height: 1.6;
}

/* Botão principal */
div[data-testid="stButton"] > button {
    background-color: #FF4B1F !important;
    color: #F5F0E8 !important;
    border: none !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 2rem !important;
    border-radius: 2px !important;
    cursor: pointer !important;
    transition: background 0.2s !important;
    width: auto !important;
}
div[data-testid="stButton"] > button:hover {
    background-color: #e03d10 !important;
}

/* Container do botão centralizado */
.btn-center {
    display: flex;
    justify-content: center;
    margin: 1.5rem 0 2.5rem;
}

/* Card de notícia (fofoca) */
.noticia-card {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
    position: relative;
}
.noticia-card:hover {
    border-color: #FF4B1F;
    background: #1a1a1a;
}
.noticia-tag {
    font-family: 'Inter', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #FF4B1F;
    margin-bottom: 0.4rem;
}
.noticia-titulo {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 500;
    color: #F5F0E8;
    line-height: 1.4;
    margin: 0;
}
.noticia-meta {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: #4a4a4a;
    margin-top: 0.5rem;
}

/* Secção de revelação */
.reveal-section {
    background: #111111;
    border-left: 3px solid #FF4B1F;
    border-radius: 0 4px 4px 0;
    padding: 1.5rem 1.75rem;
    margin: 0.5rem 0 1.5rem;
}
.reveal-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 13px;
    letter-spacing: 0.2em;
    color: #FF4B1F;
    margin-bottom: 0.75rem;
}
.reveal-text {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: #A0A0A0;
    line-height: 1.7;
    margin-bottom: 0.5rem;
}
.reveal-link {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: #4a4a4a;
    text-decoration: none;
}

/* Divisor entre pares */
.par-divider {
    border: none;
    border-top: 1px solid #1e1e1e;
    margin: 0.5rem 0 1.25rem;
}

/* Caixa reflexiva */
.reflexao-box {
    background: #0a0a0a;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 1rem 1.5rem;
    margin: 0.5rem 0 1.5rem;
}
.reflexao-box p {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: #6B6B6B;
    line-height: 1.6;
    margin: 0;
    font-style: italic;
}

/* Cabeçalho de seção */
.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 28px;
    color: #F5F0E8;
    letter-spacing: 0.04em;
    margin: 2rem 0 1rem;
    border-bottom: 1px solid #2a2a2a;
    padding-bottom: 0.5rem;
}

/* Notícia séria */
.seria-titulo {
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    font-weight: 600;
    color: #F5F0E8;
    margin: 0 0 0.5rem;
    line-height: 1.4;
}
.seria-resumo {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: #7a7a7a;
    line-height: 1.7;
}

/* Spinner */
[data-testid="stSpinner"] p {
    font-family: 'Inter', sans-serif !important;
    color: #6B6B6B !important;
    font-size: 13px !important;
}

/* Esconder elementos padrão do Streamlit */
#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

client = Groq()

def formatar_data(data_rss):
    try:
        dt = parsedate_to_datetime(data_rss)
        meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
        return f"{dt.day} {meses[dt.month - 1]}"
    except:
        return "Esta semana"

def extrair_texto_noticia(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        paragrafos = soup.find_all('p')
        texto = " ".join([p.get_text(strip=True) for p in paragrafos[:3]])
        return texto if len(texto) > 20 else "Conteúdo não disponível. Baseie-se apenas no título."
    except:
        return "Conteúdo não extraído. Baseie-se apenas no título."

def buscar_no_google_news(termo_busca, prefixo_id, max_itens=20):
    try:
        termo_codificado = urllib.parse.quote(f"{termo_busca} when:7d")
        url = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        itens = root.findall(".//item")
        amostra = itens[:max_itens]
        noticias = []
        for i, item in enumerate(amostra):
            titulo_completo = item.find("title").text
            if " - " in titulo_completo:
                titulo = titulo_completo.rsplit(" - ", 1)[0]
                veiculo = titulo_completo.rsplit(" - ", 1)[-1]
            else:
                titulo = titulo_completo
                veiculo = "Portal de Notícias"
            link = item.find("link").text
            noticias.append({
                "id": f"{prefixo_id}{i}",
                "titulo": titulo,
                "veiculo": veiculo,
                "link": link,
                "data": formatar_data(item.find("pubDate").text),
                "conteudo": extrair_texto_noticia(link)[:600]
            })
        return noticias
    except:
        return []

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Mídia & Realidade</div>
    <div class="hero-title">CORTINA<br>DE <span>FUMAÇA</span></div>
    <p class="hero-sub">Nem tudo que domina sua timeline é o que mais impacta sua vida.</p>
</div>
""", unsafe_allow_html=True)

if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.titulos_exibidos = []

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    descobrir = st.button("🔍 Rasgue a cortina desta semana", use_container_width=True)

if descobrir:
    with st.spinner("Mapeando o ecossistema de notícias..."):
        try:
            fofocas_brutas = buscar_no_google_news(
                '"pronunciamento" OR "polêmica" OR "treta" OR "cancelamento" OR "Comentou" OR "respondeu" OR "Famosos" OR "influencer"',
                "F", max_itens=20
            )
            serias_brutas = buscar_no_google_news(
                "projeto de lei OR investigação OR stf OR senado OR câmara OR operação policial OR política pública",
                "S", max_itens=20
            )

            if not fofocas_brutas or not serias_brutas:
                st.error("O buscador falhou. Tente novamente.")
                st.stop()

            ja_exibidos = st.session_state.titulos_exibidos
            fofocas_novas = [f for f in fofocas_brutas if f["titulo"] not in ja_exibidos][:5]
            serias_novas  = [s for s in serias_brutas  if s["titulo"] not in ja_exibidos][:5]

            st.session_state.fofocas_originais = {f["id"]: f for f in fofocas_novas}
            st.session_state.serias_originais  = {s["id"]: s for s in serias_novas}

            fofocas_dieta = [{"id": f["id"], "titulo": f["titulo"], "veiculo": f["veiculo"], "conteudo": f["conteudo"]} for f in fofocas_novas]
            serias_dieta  = [{"id": s["id"], "titulo": s["titulo"], "veiculo": s["veiculo"], "conteudo": s["conteudo"]} for s in serias_novas]

            prompt = f"""Você é um crítico de mídia brasileiro, com ironia leve e inteligente.

Crie 5 pares: cada par liga uma notícia de entretenimento/fofoca a uma notícia séria.

FOFOCAS: {json.dumps(fofocas_dieta, ensure_ascii=False)}
NOTÍCIAS SÉRIAS: {json.dumps(serias_dieta, ensure_ascii=False)}

Para cada par, preencha:

- id_fofoca / id_seria: os IDs dos itens escolhidos

- resumo_fofoca: 2 frases sobre O QUE ACONTECEU de fato.
  PASSO 1: leia o campo "conteudo" e classifique o tom: é celebração/meme, tragédia/luto, ou fofoca comum?
  PASSO 2: escreva o resumo com esse tom. NUNCA baseie só no título — títulos podem ser irônicos ou enganosos.
  Se for morte ou luto: tom sério e respeitoso, sem ironia.
  Se for meme ou celebração: explique o que aconteceu de verdade, com leveza.
  Se for fofoca comum: tom levemente irônico sobre a futilidade.

- resumo_seria: 2 frases explicando como isso afeta a vida real das pessoas. Didático, sem juridiquês.

- pergunta_reflexiva: 1 pergunta que faça o leitor refletir sobre atenção e prioridades.
  OBRIGATÓRIO: mencione o assunto específico da fofoca E o assunto específico da notícia séria na pergunta.
  PROIBIDO: perguntas genéricas como "o que é mais importante para você?" ou "passado vs futuro?".
  PROIBIDO: inventar relação de causa e efeito entre os dois assuntos.
  PROIBIDO: culpar o público por ter empatia com tragédias — critique a máquina de cliques, não as pessoas.
  Varie o formato da pergunta em cada par.

Retorne APENAS JSON válido:
{{"pares": [{{"id_fofoca": "...", "resumo_fofoca": "...", "id_seria": "...", "resumo_seria": "...", "pergunta_reflexiva": "..."}}]}}"""

            resposta = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            st.session_state.resultado = json.loads(resposta.choices[0].message.content)

            for par in st.session_state.resultado.get("pares", []):
                f_obj = st.session_state.fofocas_originais.get(par.get("id_fofoca"))
                if f_obj:
                    st.session_state.titulos_exibidos.append(f_obj["titulo"])
                s_obj = st.session_state.serias_originais.get(par.get("id_seria"))
                if s_obj:
                    st.session_state.titulos_exibidos.append(s_obj["titulo"])

            st.session_state.dados_prontos = True

        except Exception as e:
            st.error(f"Erro ao processar: {e}")

# ── Exibição ──────────────────────────────────────────────────────────────────
if st.session_state.get("dados_prontos"):
    st.markdown('<div class="section-header">Em alta esta semana</div>', unsafe_allow_html=True)

    for idx, par in enumerate(st.session_state.resultado.get("pares", [])):
        fofoca = st.session_state.fofocas_originais.get(par.get("id_fofoca"))
        seria  = st.session_state.serias_originais.get(par.get("id_seria"))

        if not fofoca or not seria:
            continue

        # Card clicável da fofoca
        st.markdown(f"""
        <div class="noticia-card">
            <div class="noticia-tag">🔥 Bombando</div>
            <p class="noticia-titulo">{fofoca['titulo']}</p>
            <div class="noticia-meta">{fofoca['data']} &nbsp;·&nbsp; {fofoca['veiculo']}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Ver o que está por baixo ↓", expanded=False):
            col_f, col_s = st.columns(2, gap="large")

            with col_f:
                st.markdown(f"""
                <div style="margin-bottom: 0.5rem;">
                    <div class="reveal-label">📢 Por que bombou</div>
                    <div class="reveal-text">{par.get('resumo_fofoca')}</div>
                    <a href="{fofoca['link']}" target="_blank" class="reveal-link">→ Ver na fonte</a>
                </div>
                """, unsafe_allow_html=True)

            with col_s:
                st.markdown(f"""
                <div style="border-left: 3px solid #2a2a2a; padding-left: 1.25rem;">
                    <div class="reveal-label">🌫️ Enquanto isso</div>
                    <div class="seria-titulo">{seria['titulo']}</div>
                    <div class="seria-resumo">{par.get('resumo_seria')}</div>
                    <a href="{seria['link']}" target="_blank" class="reveal-link" style="margin-top:0.5rem; display:block;">→ Ler a notícia</a>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="reflexao-box">
                <p>🤔 {par.get('pergunta_reflexiva')}</p>
            </div>
            """, unsafe_allow_html=True)

        if idx < len(st.session_state.resultado.get("pares", [])) - 1:
            st.markdown('<hr class="par-divider">', unsafe_allow_html=True)
