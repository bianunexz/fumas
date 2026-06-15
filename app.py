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

# NOVO: Função para o assistente "ler" a matéria com BeautifulSoup
def extrair_texto_noticia(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        # Timeout curto para não deixar seu site lento se um portal de notícias demorar
        with urllib.request.urlopen(req, timeout=4) as response:
            html = response.read()
        
        soup = BeautifulSoup(html, "html.parser")
        paragrafos = soup.find_all('p')
        
        # Pega as primeiras linhas de texto para entender o contexto real
        texto = " ".join([p.get_text(strip=True) for p in paragrafos[:3]])
        return texto if len(texto) > 20 else "Conteúdo não disponível. Baseie-se apenas no título."
    except:
        return "Conteúdo não extraído. Baseie-se apenas no título."

def buscar_no_google_news(termo_busca, prefixo_id, max_itens=5): 
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
                "conteudo": extrair_texto_noticia(link)[:600] # Envia 600 caracteres para o modelo não se perder
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
            fofocas_brutas = buscar_no_google_news('"pronunciamento" OR "polêmica" OR "treta" OR "cancelamento" OR "assumiu" OR "Virginia OR "Comentou" OR "respondeu" OR "Famosos" "', "F", max_itens=5)
            serias_brutas = buscar_no_google_news("projeto de lei OR investigação OR stf OR senado OR câmara OR operação policial OR política pública", "S", max_itens=5)

            if not fofocas_brutas or not serias_brutas:
                st.error("O buscador falhou. Tente novamente.")
                st.stop()

            st.session_state.fofocas_originais = {f["id"]: f for f in fofocas_brutas}
            st.session_state.serias_originais  = {s["id"]: s for s in serias_brutas}

            # Agora mandamos também o "conteúdo" raspado da web para a IA
            fofocas_dieta = [{"id": f["id"], "titulo": f["titulo"], "veiculo": f["veiculo"], "conteudo": f["conteudo"]} for f in fofocas_brutas]
            serias_dieta  = [{"id": s["id"], "titulo": s["titulo"], "veiculo": s["veiculo"], "conteudo": s["conteudo"]} for s in serias_brutas]

            ja_exibidos = st.session_state.titulos_exibidos


           # Prompt com persona, foco em variação e limite de 3 frases
            prompt = f"""Você é um estrategista de comunicação digital irônico e afiado. 

            Seu trabalho: criar 5 PARES ligando uma fofoca a uma notícia séria que aconteceram na mesma semana.

            FOFOCAS DISPONÍVEIS: {json.dumps(fofocas_dieta, ensure_ascii=False)}
            NOTÍCIAS SÉRIAS DISPONÍVEIS: {json.dumps(serias_dieta, ensure_ascii=False)}
            TÍTULOS JÁ EXIBIDOS (não use nenhum): {json.dumps(ja_exibidos, ensure_ascii=False)}

            REGRAS CRÍTICAS PARA NÃO FICAR REPETITIVO:
            - PROIBIDO usar as mesmas frases, palavras de transição ou estruturas de pergunta em mais de um par.
            - Se você usar uma ironia sobre dinheiro no par 1, use uma ironia sobre tempo no par 2, e sobre o algoritmo no par 3.

            resumo_fofoca:
            - Escreva em ate 5 linhas.
            - Fale com o tom de deboche de quem está revirando os olhos para a futilidade da situação.
            - NUNCA so repita o título. Traduza a fofoca para a linguagem de quem está fofocando no WhatsApp e principalmente leia a reportagem nao invente e so repita o titulo.
            
            resumo_seria:
            - Escreva em ate 5 linhas.
            - OBRIGATÓRIO: Explique como essa notícia afeta o dia a dia do brasileiro comum.
            - Fuja do juridiquês. Em vez de "Projeto de lei foi apresentado", use "Se isso virar lei, a prática muda para..."
            - Se o 'conteudo' estiver vazio ou for inútil interprete e tente detectar ironia, nunca deduza o impacto prático apenas pelo título. NUNCA so repita o título.
            
            pergunta_reflexiva:
            - Provoque o leitor misturando as duas notícias, mas CRIE UMA ABORDAGEM INÉDITA PARA CADA PAR.
            - Varie o estilo: por exemplo em uma pergunta, foque no absurdo de valores financeiros; em outra, foque na cegueira do público; em outra, questione a cortina de fumaça da mídia.
            - NUNCA repita o formato "Quem precisa de X quando se tem Y?". Reinvente a ironia toda vez.

            Retorne APENAS JSON válido:
            {{"pares": [{{"id_fofoca": "...", "resumo_fofoca": "...", "id_seria": "...", "resumo_seria": "...", "pergunta_reflexiva": "..."}}]}}"""
                        
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7, 
                response_format={"type": "json_object"}
            )

            st.session_state.resultado = json.loads(resposta.choices[0].message.content)

            for par in st.session_state.resultado.get("pares", []):
                f_obj = st.session_state.fofocas_originais.get(par.get("id_fofoca"))
                if f_obj:
                    st.session_state.titulos_exibidos.append(f_obj["titulo"])

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
