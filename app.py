import streamlit as st
from groq import Groq
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from email.utils import parsedate_to_datetime

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

# ALTERAÇÃO 1: Reduzido para max_itens=5 e retirado o fator "aleatório"
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
        
        # Pega as top matérias ranqueadas pelo Google, sem sortear aleatoriamente
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
            noticias.append({
                "id": f"{prefixo_id}{i}",
                "titulo": titulo,
                "veiculo": veiculo,
                "link": item.find("link").text,
                "data": formatar_data(item.find("pubDate").text)
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
    with st.spinner("Mapeando o ecossistema de notícias..."):
        try:
            # ALTERAÇÃO 2: Termos de busca refinados para achar a "fofoca quente"
            fofocas_brutas = buscar_no_google_news('"pronunciamento" OR "polêmica" OR "treta" OR "cancelamento" OR "assumiu" OR "Virginia OR Comentou OR respondeu OR Famosos "', "F", max_itens=5)
            serias_brutas = buscar_no_google_news("projeto de lei OR investigação OR stf OR senado OR câmara OR operação policial OR política pública", "S", max_itens=5)

            if not fofocas_brutas or not serias_brutas:
                st.error("O buscador falhou. Tente novamente.")
                st.stop()

            st.session_state.fofocas_originais = {f["id"]: f for f in fofocas_brutas}
            st.session_state.serias_originais  = {s["id"]: s for s in serias_brutas}

            fofocas_dieta = [{"id": f["id"], "titulo": f["titulo"], "veiculo": f["veiculo"]} for f in fofocas_brutas]
            serias_dieta  = [{"id": s["id"], "titulo": s["titulo"], "veiculo": s["veiculo"]} for s in serias_brutas]

            ja_exibidos = st.session_state.titulos_exibidos

            # ALTERAÇÃO 3: Prompt mais focado em exigir variação sem dar "gabarito" fixo
            prompt = f"""Você é um jovem que adora fofoca mas também se preocupa com o que acontece no mundo.

            Seu trabalho: criar 5 PARES ligando uma fofoca a uma notícia séria que aconteceram na mesma semana.

            FOFOCAS DISPONÍVEIS: {json.dumps(fofocas_dieta, ensure_ascii=False)}
            NOTÍCIAS SÉRIAS DISPONÍVEIS: {json.dumps(serias_dieta, ensure_ascii=False)}
            TÍTULOS JÁ EXIBIDOS (não use nenhum): {json.dumps(ja_exibidos, ensure_ascii=False)}

            REGRAS CRÍTICAS DE ESCRITA:
            Antes de escrever, leia os títulos e veículos para entender o tom.
            CRÍTICO: Você DEVE variar a estrutura de texto em cada par. NUNCA repita as mesmas frases ou o mesmo formato de explicação. Seja original em cada um!

            resumo_fofoca:
            - NÃO repita o título.
            - Conte o que aconteceu com ironia leve.
            - Explique de forma CRIATIVA por que isso chamou tanta atenção do público (sem julgar quem acompanhou).
            
            resumo_seria:
            - NÃO comece repetindo o título.
            - Explique a notícia de forma simples, como se fosse contar pra um amigo.
            - Fale como isso afeta a vida real das pessoas, sem ser muito dramático.
            
            pergunta_reflexiva:
            - Tom de "espera, isso é estranho né?" — não de sermão.
            - Conecta o tema da fofoca com a notícia séria fazendo uma crítica irônica.
            - NUNCA use a mesma estrutura de pergunta duas vezes. Invente jeitos novos de perguntar em cada par!

            Retorne APENAS JSON válido:
            {{"pares": [{{"id_fofoca": "...", "resumo_fofoca": "...", "id_seria": "...", "resumo_seria": "...", "pergunta_reflexiva": "..."}}]}}"""
                        
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8, # ALTERAÇÃO 4: Temperatura maior para ele parar de repetir as mesmas frases
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
                titulo = titulo_completo.rsplit(" - ", 1)[0]
                veiculo = titulo_completo.rsplit(" - ", 1)[-1]
            else:
                titulo = titulo_completo
                veiculo = "Portal de Notícias"
            noticias.append({
                "id": f"{prefixo_id}{i}",
                "titulo": titulo,
                "veiculo": veiculo,
                "link": item.find("link").text,
                "data": formatar_data(item.find("pubDate").text)
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
    with st.spinner("Mapeando o ecossistema de notícias..."):
        try:
            fofocas_brutas = buscar_no_google_news("fofoca OR treta OR influencer OR flagra OR celebridade OR briga famosos OR Virginia", "F")
            serias_brutas = buscar_no_google_news("projeto de lei OR investigação OR stf OR senado OR câmara OR operação policial OR política pública", "S")

            if not fofocas_brutas or not serias_brutas:
                st.error("O buscador falhou. Tente novamente.")
                st.stop()

            st.session_state.fofocas_originais = {f["id"]: f for f in fofocas_brutas}
            st.session_state.serias_originais  = {s["id"]: s for s in serias_brutas}

            fofocas_dieta = [{"id": f["id"], "titulo": f["titulo"], "veiculo": f["veiculo"]} for f in fofocas_brutas]
            serias_dieta  = [{"id": s["id"], "titulo": s["titulo"], "veiculo": s["veiculo"]} for s in serias_brutas]

            ja_exibidos = st.session_state.titulos_exibidos

            # ... (código anterior) ...

            # O prompt corrigido (com as chaves duplicadas onde aparece o JSON)
            prompt = f"""Você é um jovem que adora fofoca mas também se preocupa com o que acontece no mundo.

            Seu trabalho: criar 5 PARES ligando uma fofoca a uma notícia séria que aconteceram na mesma semana.

            FOFOCAS DISPONÍVEIS: {json.dumps(fofocas_dieta, ensure_ascii=False)}
            NOTÍCIAS SÉRIAS DISPONÍVEIS: {json.dumps(serias_dieta, ensure_ascii=False)}
            TÍTULOS JÁ EXIBIDOS (não use nenhum): {json.dumps(ja_exibidos, ensure_ascii=False)}

            REGRAS:
            Antes de escrever qualquer resumo, leia com atenção o título completo e o veículo de cada notícia para entender o tom, o contexto e se é irônico, sensacionalista ou sério. Só então escreva os resumos.
            resumo_fofoca:
            - NÃO só repita o título
            - Conta o que aconteceu com ironia leve
            - Explica por que isso prendeu a atenção de todo mundo sem julgar quem acompanhou
            - Exemplo: "A Virginia postou um look de Dubai que custava mais do que o salário anual de muita gente. E isso foi comentado pois muita gente acompanha esse tipo de conteúdo porque xxxxxxxx E, quando os influenciadores mostram tudo isso xxxxxxx, o assunto acaba gerando ainda mais xxxxxxx."
            
            resumo_seria:
            - NÃO comece repetindo o título
            - Explica a notícia de forma simples, como se fosse contar pra alguém que não acompanhou
            - Fala como isso afeta a vida real das pessoas, sem ser dramático
            - Exemplo: "O Senado votou uma proposta que pode reduzir o valor recebido por trabalhadores de carteira assinada em casos de afastamento por doença. Essa é uma mudança importante porque afeta diretamente xxxxxxxxx. Por isso, acompanhar esse assunto é essencial para xxxxxxxx"
            
            pergunta_reflexiva:
            - Tom de "espera, isso é estranho né?" — não de sermão
            - Conecta a fofoca específica com a notícia específica
            -E Faz um critica em tom ironico
            - Exemplo: "Enquanto você via o [fofoca], sabia que [notícia] estava acontecendo?
                        Você realmente escolheu xxxxxx e ignorar xxxxxxx, ou o algoritmo decidiu isso por você?    
                        Se uma xxxxxx pode xxxxxx, por que ela recebe menos atenção do que xxxxxxx"
            Retorne APENAS JSON válido:
            {{"pares": [{{"id_fofoca": "...", "resumo_fofoca": "...", "id_seria": "...", "resumo_seria": "...", "pergunta_reflexiva": "..."}}]}}"""
                        
                        # ... (código restante) ...
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
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
