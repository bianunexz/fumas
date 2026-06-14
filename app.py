import streamlit as st
from groq import Groq
import urllib.request
import xml.etree.ElementTree as ET
import re
import json

# Configuração da página
st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")
client = Groq() # Ele vai puxar a GROQ_API_KEY que já está lá nos seus Secrets!

# Função que lê as notícias direto da fonte oficial, sem depender de buscadores
def buscar_noticias_g1(url_rss, max_itens=10):
    try:
        # Finge ser um navegador normal para o site não bloquear
        req = urllib.request.Request(url_rss, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        noticias = []
        
        for item in root.findall('.//item')[:max_itens]:
            titulo = item.find('title').text
            link = item.find('link').text
            descricao_bruta = item.find('description').text if item.find('description') is not None else ""
            
            # Limpa qualquer sujeira de código HTML que venha no texto
            descricao_limpa = re.sub('<[^<]+>', '', descricao_bruta).strip()
            
            noticias.append({"titulo": titulo, "link": link, "resumo": descricao_limpa[:150]})
            
        return noticias
    except Exception as e:
        return []

# Interface
st.title("📰 CORTINA DE FUMAÇA")
st.write("Nem tudo que domina sua timeline é o que mais impacta sua vida.")

if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.resultado = {}

if st.button("Descobrir o que bombou esta semana"):
    with st.spinner("Lendo feeds de notícias e analisando o peso dos algoritmos..."):
        try:
            # Puxa dados REAIS e instantâneos do RSS do G1
            fofocas_brutas = buscar_noticias_g1('https://g1.globo.com/rss/g1/pop-arte/')
            serias_brutas = buscar_noticias_g1('https://g1.globo.com/rss/g1/politica/')
            
            prompt = f"""
            Você é um curador de dados. 
            Com base EXCLUSIVAMENTE nestas notícias reais do Brasil capturadas agora, selecione 5 fofocas/entretenimento e 3 notícias sérias de política.
            
            Retorne APENAS um JSON válido nesta estrutura:
            {{
              "fofocas": [ {{"titulo": "T", "link": "L", "resumo": "R"}} ],
              "serias": [ {{"titulo": "T", "link": "L", "resumo": "R"}} ]
            }}
            
            FOFOCAS: {fofocas_brutas}
            SÉRIAS: {serias_brutas}
            """
            
            # Voltamos para o modelo da Groq que tinha funcionado perfeitamente
            resposta = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Você só responde em formato JSON estruturado."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            texto_limpo = resposta.choices[0].message.content.strip()
            if texto_limpo.startswith("```"):
                texto_limpo = texto_limpo.replace("```json", "").replace("```", "").strip()
                
            st.session_state.resultado = json.loads(texto_limpo)
            st.session_state.dados_prontos = True

        except Exception as e:
            st.error("Ops! Tivemos um engasgo na hora de processar os dados. Tente de novo!")
            st.caption(f"Detalhe técnico: {e}")

st.write("---")

# Renderiza os dados
if st.session_state.dados_prontos and "fofocas" in st.session_state.resultado:
    st.subheader("🔥 Top assuntos da semana")
    
    for fofoca in st.session_state.resultado["fofocas"]:
        if st.button(f"👉 {fofoca['titulo']}"):
            
            st.markdown(f"**Por que bombou?** {fofoca['resumo']}...")
            st.markdown(f"[🔗 Ver fonte da fofoca]({fofoca['link']})")
            
            st.write("---")
            st.subheader("🌫️ Enquanto isso, na mesma semana...")
            
            for seria in st.session_state.resultado.get("serias", []):
                st.markdown(f"**{seria['titulo']}**")
                st.markdown(f"{seria['resumo']}...")
                st.markdown(f"[🔗 Ler a notícia completa]({seria['link']})")
                st.write("")
            
            st.write("---")
            st.info("💭 **Para pensar:** Como as plataformas direcionam a sua atenção? A mídia não escondeu essas notícias sérias, mas os algoritmos priorizaram o engajamento da fofoca.")
