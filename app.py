import streamlit as st
from groq import Groq
from datetime import datetime, timedelta
import json

# Configuração
st.set_page_config(page_title="Cortina de Fumaça", page_icon="🌫️", layout="wide")

# Pega chave dos secrets
groq_key = st.secrets["GROQ_KEY"]
client = Groq(api_key=groq_key)

# CSS simples
st.markdown("""
<style>
    .main-title { font-size: 2.5rem; font-weight: bold; margin-bottom: 0; }
    .subtitle { color: #666; font-style: italic; margin-bottom: 2rem; }
    .section-title { font-size: 1.3rem; font-weight: bold; margin-top: 2rem; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; }
    .fofoca-item { padding: 1rem; margin: 0.5rem 0; background: #fff5f5; border-left: 4px solid #ff4444; border-radius: 4px; }
    .noticia-item { padding: 1rem; margin: 0.5rem 0; background: #f0f8f0; border-left: 4px solid #2d7a27; border-radius: 4px; }
    .analise-box { padding: 1.5rem; margin: 1rem 0; background: #fafafa; border: 1px solid #ddd; border-radius: 8px; }
    .pergunta-box { padding: 1.5rem; background: #fff; border-top: 3px solid #ff4444; font-style: italic; font-size: 1.1rem; }
    .aviso { color: #888; font-size: 0.8rem; text-align: center; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown('<p class="main-title">🌫️ Cortina de Fumaça</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Nem tudo que domina sua timeline é o que mais impacta sua vida.</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### Sobre")
    st.markdown("""
    Ferramenta de **educação midiática**.
    
    Mostra como entretenimento domina nossa atenção enquanto notícias importantes passam despercebidas.
    
    **Conceito:** Agenda-setting
    
    ---
    ⚠️ Este projeto não acusa a mídia de mentir nem afirma conspirações.
    """)

# Função para extrair JSON da resposta
def extrair_json(texto):
    texto = texto.strip()
    if "```" in texto:
        partes = texto.split("```")
        for p in partes:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:]
            if p.startswith("{"):
                return json.loads(p)
    return json.loads(texto)

# Botão principal
if st.button("🔍 Descobrir o que está bombando esta semana", type="primary", use_container_width=True):
    
    hoje = datetime.now()
    semana_inicio = hoje - timedelta(days=7)
    periodo = f"{semana_inicio.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}"
    
    # ── BUSCAR FOFOCAS ──
    with st.spinner("🔥 Buscando fofocas e entretenimento da semana..."):
        prompt_fofocas = f"""Hoje é {hoje.strftime('%d/%m/%Y')}. 
        
Use sua busca na web para encontrar as 5 MAIORES fofocas e assuntos de entretenimento que estão bombando no Brasil e no mundo NESTA SEMANA ({periodo}).

Preciso de notícias REAIS e ATUAIS. Nomes reais de famosos, reality shows, polêmicas, futebol, celebridades.

Retorne APENAS um JSON neste formato exato:
{{
    "fofocas": [
        {{
            "titulo": "Título real da notícia",
            "descricao": "O que aconteceu, com data",
            "por_que_viralizou": "Explicação do apelo",
            "fonte": "Nome do site",
            "link": "https://link.real.da.noticia"
        }}
    ]
}}

IMPORTANTE: Use APENAS informações reais encontradas na web AGORA. Não invente."""
        
        try:
            resposta = client.chat.completions.create(
                model="compound-beta",  # ← MODELO COM BUSCA WEB
                messages=[{"role": "user", "content": prompt_fofocas}],
                temperature=0.2,
                max_tokens=1000
            )
            dados_fofocas = extrair_json(resposta.choices[0].message.content)
            fofocas = dados_fofocas.get("fofocas", [])
        except Exception as e:
            st.error(f"Erro ao buscar fofocas: {e}")
            fofocas = []
    
    # ── BUSCAR NOTÍCIAS SÉRIAS ──
    with st.spinner("📰 Buscando notícias importantes da semana..."):
        prompt_noticias = f"""Hoje é {hoje.strftime('%d/%m/%Y')}.

Use sua busca na web para encontrar 4-5 notícias SÉRIAS e IMPORTANTES que aconteceram NESTA SEMANA ({periodo}) no Brasil e no mundo, mas que receberam MENOS ATENÇÃO do que mereciam.

Foque em:
- Votações no Congresso Nacional
- Decisões do STF
- Operações da Polícia Federal
- Dados de desmatamento na Amazônia
- Crises de saúde pública
- Violações de direitos humanos
- Crises internacionais relevantes

Preciso de notícias REAIS com datas DESTA SEMANA.

Retorne APENAS um JSON neste formato exato:
{{
    "noticias": [
        {{
            "titulo": "Título real da notícia",
            "descricao": "O que aconteceu e impacto, com data",
            "por_que_importante": "Por que afeta a vida das pessoas",
            "fonte": "Nome do site",
            "link": "https://link.real.da.noticia"
        }}
    ]
}}

IMPORTANTE: Use APENAS informações reais encontradas na web AGORA. Não invente."""
        
        try:
            resposta = client.chat.completions.create(
                model="compound-beta",  # ← MODELO COM BUSCA WEB
                messages=[{"role": "user", "content": prompt_noticias}],
                temperature=0.2,
                max_tokens=1000
            )
            dados_noticias = extrair_json(resposta.choices[0].message.content)
            noticias = dados_noticias.get("noticias", [])
        except Exception as e:
            st.error(f"Erro ao buscar notícias: {e}")
            noticias = []
    
    # ── MOSTRAR RESULTADOS ──
    if fofocas or noticias:
        st.success(f"✅ Análise da semana: {periodo}")
        
        col1, col2 = st.columns(2)
        
        # Coluna das fofocas
        with col1:
            st.markdown('<p class="section-title">🔥 O que está bombando</p>', unsafe_allow_html=True)
            st.caption("Entretenimento & Fofocas")
            
            for i, f in enumerate(fofocas, 1):
                with st.expander(f"🔥 {f['titulo']}", expanded=False):
                    st.markdown(f"**{f['descricao']}**")
                    st.markdown(f"*Por que viralizou:* {f['por_que_viralizou']}")
                    if f.get("link"):
                        st.markdown(f"📎 [{f['fonte']}]({f['link']})")
                    
                    # Análise da fofoca
                    if st.button(f"🧠 Analisar este tema", key=f"analisar_{i}"):
                        with st.spinner("Analisando..."):
                            prompt_analise = f"""Analise esta fofoca da semana como educador midiático:

FOFOCA: {f['titulo']} - {f['descricao']}

NOTÍCIAS SÉRIAS DA MESMA SEMANA:
{chr(10).join([f"- {n['titulo']}: {n['descricao']}" for n in noticias])}

Responda APENAS JSON:
{{
    "porque_domina": "Por que viralizou (algoritmos, psicologia)",
    "coexistencia": "Como os dois tipos disputaram atenção na mesma semana (use 'enquanto isso' e 'ao mesmo tempo')",
    "pergunta": "Pergunta reflexiva sobre consumo de informação"
}}"""
                            
                            try:
                                resp = client.chat.completions.create(
                                    model="compound-beta",
                                    messages=[{"role": "user", "content": prompt_analise}],
                                    temperature=0.4,
                                    max_tokens=500
                                )
                                analise = extrair_json(resp.choices[0].message.content)
                                
                                st.markdown("---")
                                st.markdown("### 🧠 Por que dominou?")
                                st.markdown(analise["porque_domina"])
                                st.markdown("### 🌫️ Atenção dividida")
                                st.markdown(analise["coexistencia"])
                                st.markdown(f'<div class="pergunta-box">❝ {analise["pergunta"]} ❞</div>', unsafe_allow_html=True)
                            except:
                                st.error("Não foi possível gerar a análise")
        
        # Coluna das notícias sérias
        with col2:
            st.markdown('<p class="section-title">📰 O que realmente importa</p>', unsafe_allow_html=True)
            st.caption("Notícias com impacto real")
            
            for n in noticias:
                st.markdown(f"""
                <div class="noticia-item">
                    <strong>{n['titulo']}</strong><br>
                    <small>{n['descricao']}</small><br>
                    <em>Por que importa:</em> {n['por_que_importante']}<br>
                    📎 <a href="{n.get('link', '#')}">{n.get('fonte', 'Fonte')}</a>
                </div>
                """, unsafe_allow_html=True)
        
        # Mensagem final
        st.markdown("---")
        st.markdown("""
        ## 🌫️ O efeito cortina de fumaça
        
        Não é conspiração. É **agenda-setting**: a mídia e plataformas não dizem *o que pensar*, 
        mas determinam *sobre o que pensamos*.
        
        **Na mesma semana**, enquanto você via fofocas, decisões importantes estavam sendo tomadas.
        
        A pergunta é: **o que você vai escolher consumir na próxima semana?**
        """)
    
    else:
        st.error("Não foi possível carregar os dados. Tente novamente.")

# Footer
st.markdown('<p class="aviso">🌫️ Cortina de Fumaça — Projeto de educação midiática | Desenvolvido com Streamlit + Groq</p>', unsafe_allow_html=True)
