import streamlit as st
from groq import Groq
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")
client = Groq()

def formatar_data(data_rss):
    try:
        dt = parsedate_to_datetime(data_rss)
        meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
        return f"{dt.day} de {meses[dt.month - 1]}"
    except:
        return "Nesta semana"

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

# ── Interface ─────────────────────────────────────────────────────────────────
st.title("📰 CORTINA DE FUMAÇA")
st.write("Nem tudo que domina sua timeline é o que mais impacta sua vida.")

if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.titulos_exibidos = []

if st.button("Descobrir os assuntos da semana"):
    with st.spinner("Lendo matérias e mapeando o ecossistema de notícias (Isso pode levar alguns segundos)..."):
        try:
            # Pede 20 notícias ao Google para ter margem de exclusão
            fofocas_brutas = buscar_no_google_news('"pronunciamento" OR "polêmica" OR "treta" OR "cancelamento" OR "Comentou" OR "respondeu" OR "Famosos" OR "influencer"', "F", max_itens=20)
            serias_brutas = buscar_no_google_news("projeto de lei OR investigação OR stf OR senado OR câmara OR operação policial OR política pública", "S", max_itens=20)

            if not fofocas_brutas or not serias_brutas:
                st.error("O buscador falhou. Tente novamente.")
                st.stop()

            ja_exibidos = st.session_state.titulos_exibidos

            # FILTRO REAL NO CÓDIGO PYTHON: Tira o que já foi lido e seleciona as 5 inéditas
            fofocas_novas = [f for f in fofocas_brutas if f["titulo"] not in ja_exibidos][:5]
            serias_novas = [s for s in serias_brutas if s["titulo"] not in ja_exibidos][:5]

            st.session_state.fofocas_originais = {f["id"]: f for f in fofocas_novas}
            st.session_state.serias_originais  = {s["id"]: s for s in serias_novas}

            fofocas_dieta = [{"id": f["id"], "titulo": f["titulo"], "veiculo": f["veiculo"], "conteudo": f["conteudo"]} for f in fofocas_novas]
            serias_dieta  = [{"id": s["id"], "titulo": s["titulo"], "veiculo": s["veiculo"], "conteudo": s["conteudo"]} for s in serias_novas]

            # Prompt ajustado para leitura profunda, detecção de ironia e resumos maiores
            prompt = f"""Você é um estrategista de comunicação digital e crítico de mídia. 

            Seu trabalho: criar 5 PARES ligando uma notícia de entretenimento/fofoca a uma notícia séria da mesma semana.

            FOFOCAS DISPONÍVEIS: {json.dumps(fofocas_dieta, ensure_ascii=False)}
            NOTÍCIAS SÉRIAS DISPONÍVEIS: {json.dumps(serias_dieta, ensure_ascii=False)}

            REGRAS DE SEGURANÇA E EMPATIA (MÁXIMA PRIORIDADE):
            1. O VALOR DA VIDA É ABSOLUTO: Se a 'fofoca' envolver morte, luto, doença ou acidente grave, MUDE SEU COMPORTAMENTO. Jamais trate uma perda humana como 'futilidade' ou pergunte por que as pessoas se importam. É natural se importar com vidas.
            2. ECONOMIA DA ATENÇÃO: A fofoca e a notícia séria NÃO TÊM RELAÇÃO na vida real. Nunca misture os personagens nas suas explicações.

            resumo_fofoca:
            - Escreva um mini parágrafo.
            - OBRIGATÓRIO: Leia o 'conteudo' raspado! Explique o que aconteceu e leia a noticia nao so interprete o titulo sem entender as ironias.
            - SE FOR TRAGÉDIA/LUTO: Use um tom 100% respeitoso, sério e jornalístico. Sem ironias.
            - SE FOR FOFOCA COMUM: Use tom de deboche suave sobre a futilidade do assunto.
            
            resumo_seria:
            - Escreva um mini parágrafo.
            - OBRIGATÓRIO: Leia o 'conteudo' raspado.
            - Explique de forma muito didática como isso afeta a vida, a saúde ou o bolso da sociedade. Sem juridiquês.
            
            pergunta_reflexiva:
            - SE A NOTÍCIA ENVOLVER LUTO/TRAGÉDIA: Sua crítica DEVE ser sobre a MÁQUINA DE CLIQUES. (Exemplo: "Por que a internet transforma até a dor e o luto em um espetáculo para gerar engajamento, enquanto projetos como [Notícia Séria] ficam esquecidos no feed?"). Nunca julgue a empatia do público.
            - SE FOR FOFOCA COMUM: Faça o usuário pensar sobre atenção (Exemplo: "Por que damos milhões de cliques para [Fofoca Inútil], enquanto ignoramos o impacto real de [Notícia Séria]?").
            - Mude as palavras da pergunta em cada par. Não invente relações de causa e efeito entre os dois assuntos que nao tem nada aver.

            Retorne APENAS JSON válido:
            {{"pares": [{{"id_fofoca": "...", "resumo_fofoca": "...", "id_seria": "...", "resumo_seria": "...", "pergunta_reflexiva": "..."}}]}}"""
                        
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7, 
                response_format={"type": "json_object"}
            )

            st.session_state.resultado = json.loads(resposta.choices[0].message.content)

            # Salva no histórico para não repetir nos próximos cliques
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
    st.subheader("🔥 Assuntos em alta da semana")
    for idx, par in enumerate(st.session_state.resultado.get("pares", [])):
        fofoca = st.session_state.fofocas_originais.get(par.get("id_fofoca"))
        seria  = st.session_state.serias_originais.get(par.get("id_seria"))

        if fofoca and seria:
            if st.button(f"👉 {fofoca['titulo']}", key=f"btn_{idx}"):
                st.markdown(f"📅 *{fofoca['data']}* | 📰 **Fonte:** {fofoca['veiculo']}")
                st.markdown(f"**Por que bombou?** {par.get('resumo_fofoca')}")
                st.markdown(f"[🔗 Ver na fonte]({fofoca['link']})")
                st.write("---")
                st.subheader("🌫️ Enquanto isso...")
                st.markdown(f"📅 *{seria['data']}* | 📰 **Fonte:** {seria['veiculo']}")
                st.markdown(f"**{seria['titulo']}**")
                st.markdown(f"{par.get('resumo_seria')}")
                st.markdown(f"[🔗 Ler a notícia]({seria['link']})")
                st.write("---")
                st.info(f"🤔 **Para pensar:** {par.get('pergunta_reflexiva')}")
                st.write("---")
