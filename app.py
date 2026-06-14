import streamlit as st
from groq import Groq
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json

st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")
client = Groq()

def buscar_no_google_news(termo_busca, max_itens=8):
    try:
        termo_codificado = urllib.parse.quote(f"{termo_busca} when:7d")
        url = f"https://news.google.com/rss/search?q={termo_codificado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        noticias = []
        
        for item in root.findall('.//item')[:max_itens]:
            titulo_completo = item.find('title').text
            
            if ' - ' in titulo_completo:
                titulo = titulo_completo.rsplit(' - ', 1)[0]
                veiculo = titulo_completo.rsplit(' - ', 1)[-1]
            else:
                titulo = titulo_completo
                veiculo = "Portal de Notícias"
                
            link = item.find('link').text
            data_pub = item.find('pubDate').text
            
            noticias.append({
                "titulo": titulo, 
                "veiculo": veiculo,
                "link": link, 
                "data": data_pub
            })
            
        return noticias
    except Exception as e:
        return []

st.title("📰 CORTINA DE FUMAÇA")
st.write("Nem tudo que domina sua timeline é o que mais impacta sua vida.")

if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.resultado = {}

if st.button("Descobrir os assuntos da semana"):
    with st.spinner("Mapeando a atenção da internet..."):
        try:
            fofocas_brutas = buscar_no_google_news("fofoca OR polêmica OR traição OR cancelado OR babado", max_itens=8)
            serias_brutas = buscar_no_google_news("projeto de lei OR senado OR stf OR pec", max_itens=8)
            
            if not fofocas_brutas or not serias_brutas:
                st.error("O buscador falhou na coleta de dados. Tente novamente.")
                st.stop()
            
            prompt = f"""
            Você é um curador rigoroso de dados.
            Sua tarefa é ler os resultados abaixo e criar entre 3 e 5 PARES ÚNICOS de notícias.
            
            REGRAS:
            1. FOFOCAS: Escolha APENAS polêmicas, trivialidades de famosos, barracos ou memes. Evite coisas comportadas.
            2. SÉRIAS: Escolha APENAS votações, leis e impacto político pesado.
            3. EMPARELHAMENTO: Forme no mínimo 3 pares, máximo 5. Cada par tem 1 fofoca e 1 séria diferente.
            
            Retorne APENAS um JSON válido nesta estrutura exata com a chave "pares":
            {{
              "pares": [
                {{
                  "fofoca": {{"titulo": "T", "veiculo": "V", "link": "L", "resumo": "Por que viralizou?", "data_formatada": "Ex: 12 de Junho"}},
                  "seria": {{"titulo": "T", "veiculo": "V", "link": "L", "resumo": "Qual o impacto na sociedade?", "data_formatada": "Ex: 12 de Junho"}}
                }}
              ]
            }}
            
            FOFOCAS: {fofocas_brutas}
            SÉRIAS: {serias_brutas}
            """
            
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Você atua como um filtro editorial. Retorne apenas JSON com a chave 'pares'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, 
                response_format={"type": "json_object"}
            )
            
            texto_limpo = resposta.choices[0].message.content.strip()
            if not texto_limpo:
                raise ValueError("A IA retornou vazio.")
                
            st.session_state.resultado = json.loads(texto_limpo)
            st.session_state.dados_prontos = True

        except Exception as e:
            st.error("Ops! Tivemos um engasgo na conexão com os dados. Clique no botão mais uma vez!")
            st.caption(f"Detalhe técnico: {e}")

st.write("---")

# Renderização flexível e à prova de falhas
if st.session_state.dados_prontos:
    st.subheader("🔥 Assuntos em alta da semana")
    
    # Modo caça-dados: Tenta pegar a chave "pares", mas se falhar, pega qualquer lista que a IA tenha gerado
    lista_pares = st.session_state.resultado.get("pares")
    
    if not lista_pares and len(st.session_state.resultado) > 0:
        primeira_chave = list(st.session_state.resultado.keys())[0]
        lista_pares = st.session_state.resultado[primeira_chave]

    # Se mesmo assim não for uma lista, o código grita e mostra o problema
    if not lista_pares or not isinstance(lista_pares, list):
        st.warning("⚠️ Os algoritmos se confundiram na hora de tabular os dados. Veja o resultado bruto abaixo:")
        st.json(st.session_state.resultado)
    else:
        for idx, par in enumerate(lista_pares):
            fofoca = par.get("fofoca")
            seria = par.get("seria")
            
            if not fofoca or not seria:
                continue
                
            titulo_f = fofoca.get('titulo', 'Assunto em alta')
            data_f = fofoca.get('data_formatada', 'Nesta semana')
            veiculo_f = fofoca.get('veiculo', 'Internet')
            resumo_f = fofoca.get('resumo', 'Viralizou nas redes.')
            link_f = fofoca.get('link', '#')

            titulo_s = seria.get('titulo', 'Notícia importante')
            data_s = seria.get('data_formatada', 'Nesta semana')
            veiculo_s = seria.get('veiculo', 'Portal de Notícias')
            resumo_s = seria.get('resumo', 'Impacto na sociedade.')
            link_s = seria.get('link', '#')
            
            if st.button(f"👉 {titulo_f}", key=f"btn_fofoca_{idx}"):
                
                st.markdown(f"📅 *{data_f}* | 📰 **Fonte:** {veiculo_f}")
                st.markdown(f"**Por que bombou?** {resumo_f}")
                st.markdown(f"[🔗 Ver na fonte]({link_f})")
                
                st.write("---")
                
                st.subheader("🌫️ Enquanto isso, na mesma época...")
                st.markdown(f"📅 *{data_s}* | 📰 **Fonte:** {veiculo_s}")
                st.markdown(f"**{titulo_s}**")
                st.markdown(f"{resumo_s}")
                st.markdown(f"[🔗 Ler a notícia]({link_s})")
                
                st.write("---")
                st.info("💭 **Para pensar:** Como as plataformas direcionam a sua atenção? A mídia não escondeu essa notícia séria, mas os algoritmos priorizaram o engajamento do entretenimento.")
