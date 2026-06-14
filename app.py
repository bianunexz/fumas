import streamlit as st
from google import genai
from google.genai import types
import json

# Configuração da página do Streamlit
st.set_page_config(page_title="Cortina de Fumaça", page_icon="📰")

# Inicializa o novo cliente oficial do Google (Lê o GEMINI_API_KEY dos Secrets automaticamente)
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Textos Iniciais da Interface
st.title("📰 CORTINA DE FUMAÇA")
st.write("Nem tudo que domina sua timeline é o que mais impacta sua vida.")

# Variáveis de estado para controlar o clique do botão
if "dados_prontos" not in st.session_state:
    st.session_state.dados_prontos = False
    st.session_state.resultado = {}

# O Botão Principal
if st.button("Descobrir o que bombou esta semana"):
    with st.spinner("O Gemini está navegando na Web e analisando os algoritmos desta semana..."):
        try:
            # Criamos o prompt dizendo exatamente o que queremos coletar na internet
            prompt = """
            Faça uma pesquisa na web sobre o cenário atual do Brasil nesta semana corrente de junho de 2026.
            
            Selecione e organize:
            1. As 5 maiores fofocas, polêmicas de celebridades ou assuntos de entretenimento que mais geraram engajamento e cliques.
            2. De 3 a 5 notícias sérias (como projetos de lei no Congresso, votações, decisões do STF, economia ou pautas sociais) que aconteceram no mesmo período.
            
            Você deve retornar estritamente um código JSON estruturado usando esta formatação exata:
            {
              "fofocas": [ {"titulo": "Manchete da fofoca", "link": "URL real da fonte encontrada", "resumo": "Explicação curta do motivo de ter viralizado"} ],
              "serias": [ {"titulo": "Manchete séria", "link": "URL real da fonte encontrada", "resumo": "Explicação curta do impacto real"} ]
            }
            Não insira nenhuma introdução, saudação ou bloco de texto markdown fora do JSON.
            """

            # Chamada do modelo usando a nova biblioteca padrão de 2026
            # Habilitamos a ferramenta 'google_search' para ele buscar na web em tempo real
            resposta = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],  # Ativa a busca nativa do Google!
                    response_mime_type="application/json",  # Garante o retorno estruturado
                ),
            )
            
            # Limpeza rápida para garantir que pegamos apenas o objeto JSON
            texto_resposta = resposta.text.strip()
            if texto_resposta.startswith("```"):
                texto_resposta = texto_resposta.replace("```json", "").replace("```", "").strip()

            st.session_state.resultado = json.loads(texto_resposta)
            st.session_state.dados_prontos = True

        except Exception as e:
            st.error("Houve uma falha ao estruturar os dados da pesquisa de mídia. Tente clicar no botão novamente.")
            st.caption(f"Detalhe técnico: {e}")

st.write("---")

# Exibição dinâmica dos resultados coletados
if st.session_state.dados_prontos and "fofocas" in st.session_state.resultado:
    st.subheader("🔥 Top assuntos da semana")
    st.caption("Clique em uma fofoca para ver como os algoritmos disputaram sua atenção:")
    
    for idx, fofoca in enumerate(st.session_state.resultado["fofocas"]):
        # Chave única para cada botão gerado no loop
        if st.button(f"👉 {fofoca['titulo']}", key=f"btn_fofoca_{idx}"):
            
            st.markdown(f"**Por que bombou?** {fofoca['resumo']}")
            st.markdown(f"[🔗 Ver fonte da fofoca]({fofoca['link']})")
            
            st.write("---")
            st.subheader("🌫️ Enquanto isso, na mesma semana...")
            
            for seria in st.session_state.resultado.get("serias", []):
                st.markdown(f"**{seria['titulo']}**")
                st.markdown(f"{seria['resumo']}")
                st.markdown(f"[🔗 Ler a notícia completa]({seria['link']})")
                st.write("")
            
            st.write("---")
            st.info("💭 **Para pensar:** Como as plataformas direcionam a sua atenção? A mídia não escondeu essas notícias sérias, mas os algoritmos priorizaram o engajamento da fofoca.")
