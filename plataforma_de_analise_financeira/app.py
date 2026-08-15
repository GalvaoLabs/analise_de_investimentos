from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from auth import exigir_login, render_user_badge, usuario_id
from data_utils import (
    TIPOS_ATIVO,
    buscar_dados_ativo,
    buscar_dividendos_historico,
    buscar_historico,
    buscar_resultados_financeiros,
    calcular_teto_bazin,
    calcular_teto_gordon,
    calcular_teto_graham,
    calcular_teto_medio,
    classificar_status,
    margem_seguranca,
)
from diagnostico import gerar_diagnostico
from metas_utils import formatar_prazo, meses_para_meta, projetar_evolucao
from news_utils import buscar_noticias
from storage import carregar_carteira, carregar_meta, salvar_carteira, salvar_meta
from theme import (
    DEFAULT_MODO,
    DEFAULT_PALETA,
    MODOS,
    PALETAS,
    build_theme_css,
    get_active_accents,
)

try:
    import google.generativeai as genai
except ImportError: # biblioteca opcional
    genai = None

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(
    page_title="Plataforma de Análise Financeira",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)


def carregar_css():
    try:
        with open("style.css", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo style.css não encontrado — usando estilo padrão do Streamlit.")


carregar_css()
exigir_login()
st.sidebar.image("logo.png")
st.sidebar.title("Painel de Controle")
render_user_badge()
USER_ID = usuario_id()

# ==========================================
# SELETOR DE TEMA (cor de destaque + modo claro/escuro)
# ==========================================
if "tema_modo" not in st.session_state:
    st.session_state["tema_modo"] = DEFAULT_MODO
if "tema_paleta" not in st.session_state:
    st.session_state["tema_paleta"] = DEFAULT_PALETA
if "tema_personalizado" not in st.session_state:
    st.session_state["tema_personalizado"] = False

with st.sidebar.expander("Aparência", expanded=False):
    st.session_state["tema_modo"] = st.radio(
        "Modo", list(MODOS.keys()), horizontal=True, index=list(MODOS.keys()).index(st.session_state["tema_modo"])
    )
    st.session_state["tema_personalizado"] = st.checkbox(
        "Usar cor personalizada", value=st.session_state["tema_personalizado"]
    )

    accent_custom = None
    accent_strong_custom = None
    if st.session_state["tema_personalizado"]:
        c1, c2 = st.columns(2)
        accent_custom = c1.color_picker("Destaque", value="#38BDF8")
        accent_strong_custom = c2.color_picker("Destaque forte", value="#0284C7")
    else:
        st.session_state["tema_paleta"] = st.selectbox(
            "Paleta de cores",
            list(PALETAS.keys()),
            index=list(PALETAS.keys()).index(st.session_state["tema_paleta"]),
        )

# Injeta o CSS de tema DEPOIS do style.css base, para sobrescrever as variáveis via cascata
st.markdown(
    f"<style>{build_theme_css(st.session_state['tema_paleta'], st.session_state['tema_modo'], accent_custom, accent_strong_custom)}</style>",
    unsafe_allow_html=True,
)

CORES_ATIVAS = get_active_accents(st.session_state["tema_paleta"], accent_custom, accent_strong_custom)
ACCENT = CORES_ATIVAS["accent"]
ACCENT_STRONG = CORES_ATIVAS["accent_strong"]
PLOTLY_TEMPLATE_ATIVO = "plotly_dark" if st.session_state["tema_modo"] == "Escuro" else "plotly_white"

IMG_STOCK_MARKET = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=500&q=80"
IMG_ANALYTICS = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500&q=80"
IMG_REAL_ESTATE = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=500&q=80"
IMG_GLOBAL = "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=500&q=80"

PLOTLY_CONFIG = {"displayModeBar": False}


def card_html(titulo: str, valor: str, subtexto: str = "", img: str | None = None) -> str:
    img_tag = f'<img src="{img}" class="card-image">' if img else ""
    return f"""
        <div class="card-container">
            {img_tag}
            <div class="card-content">
                <div class="card-title">{titulo}</div>
                <div class="card-value">{valor}</div>
                <div class="card-subtext">{subtexto}</div>
            </div>
        </div>
    """


# ==========================================
# SIDEBAR / NAVEGAÇÃO
# ==========================================
aba = st.sidebar.radio(
    "Selecione o Módulo:",
    [
        "Dashboard da Carteira",
        "Valuation Individual",
        "Comparador de Ativos",
        "Simulador de Aportes",
        "Proventos",
        "Metas Financeiras",
        "Análise via IA Gemini",
        "Guia do Usuário / Tutorial",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("Integração IA")
gemini_api_key = st.sidebar.text_input(
    "Chave API Google Gemini:", type="password", help="Obtenha gratuitamente em aistudio.google.com/app/apikey"
)
st.sidebar.caption("Sua chave é usada apenas nesta sessão local e nunca é armazenada.")

st.sidebar.markdown("---")
st.sidebar.caption("Dados via Yahoo Finance (yfinance), com fallback para brapi.dev.")

# ==========================================
# ABA 1: DASHBOARD DA CARTEIRA
# ==========================================
if aba == "Dashboard da Carteira":
    st.title("Gestão e Consolidação de Carteira")
    st.write("Gerencie seus ativos, calcule margens de segurança e acompanhe a evolução patrimonial.")

    if "carteira_inicial" not in st.session_state:
        carteira_salva = carregar_carteira(USER_ID)
        if carteira_salva is not None and not carteira_salva.empty:
            st.session_state["carteira_inicial"] = carteira_salva
        else:
            st.session_state["carteira_inicial"] = pd.DataFrame(
                [
                    {"Ticker": "BBAS3", "Tipo": "Ação", "Quantidade": 100, "Preço Médio": 24.50},
                    {"Ticker": "VALE3", "Tipo": "Ação", "Quantidade": 50, "Preço Médio": 62.00},
                    {"Ticker": "MXRF11", "Tipo": "FII", "Quantidade": 300, "Preço Médio": 10.15},
                    {"Ticker": "HGLG11", "Tipo": "FII", "Quantidade": 20, "Preço Médio": 160.00},
                    {"Ticker": "AAPL34", "Tipo": "BDR", "Quantidade": 30, "Preço Médio": 42.00},
                {"Ticker": "IVVB11", "Tipo": "ETF", "Quantidade": 15, "Preço Médio": 280.00},
                {"Ticker": "BTC", "Tipo": "Criptomoeda", "Quantidade": 0.01, "Preço Médio": 350000.00},
                ]
            )

    df_edit = st.data_editor(
        st.session_state["carteira_inicial"],
        num_rows="dynamic",
        use_container_width=True,
        key="editor_carteira",
        column_config={
            "Tipo": st.column_config.SelectboxColumn(options=TIPOS_ATIVO),
            "Quantidade": st.column_config.NumberColumn(min_value=0.0, step=0.0001, format="%.4f"),
            "Preço Médio": st.column_config.NumberColumn(min_value=0.0, format="R$ %.2f"),
        },
    )

    dy_alvo_dash = st.slider("DY Alvo (Método Bazin)", 2.0, 15.0, 6.0, 0.5, format="%.1f%%") / 100

    col_proc, col_salvar = st.columns([2, 1])
    processar = col_proc.button("Processar Carteira Completa", type="primary", use_container_width=True)
    salvar = col_salvar.button("💾 Salvar minha carteira", use_container_width=True)

    if salvar:
        if salvar_carteira(USER_ID, df_edit):
            st.session_state["carteira_inicial"] = df_edit
            st.toast("Carteira salva com sucesso!", icon="✅")

    if processar:
        resultados = []
        erros = []
        linhas = df_edit.dropna(subset=["Ticker"]).reset_index(drop=True)
        total = max(len(linhas), 1)
        barra = st.progress(0.0, text="Iniciando...")

        for i, row in linhas.iterrows():
            ticker = str(row["Ticker"]).upper().strip()
            if not ticker:
                continue

            barra.progress((i + 1) / total, text=f"Buscando {ticker}...")
            info = buscar_dados_ativo(ticker, row["Tipo"])

            if not info["ok"]:
                erros.append(f"{ticker}: {info.get('erro', 'erro desconhecido')}")
                continue

            preco = info["preco"]
            qtd = float(row["Quantidade"] or 0)
            pm = float(row["Preço Médio"] or 0)

            tot_investido = qtd * pm
            tot_atual = qtd * preco
            lucro_reais = tot_atual - tot_investido
            lucro_pct = (lucro_reais / tot_investido * 100) if tot_investido > 0 else 0.0

            teto_bazin = calcular_teto_bazin(info["div_12m"], dy_alvo_dash)
            teto_graham = calcular_teto_graham(info["lpa"], info["vpa"]) if row["Tipo"] == "Ação" else 0.0
            teto_medio = calcular_teto_medio(teto_bazin, teto_graham)
            status, css_class = classificar_status(preco, teto_medio if teto_medio > 0 else teto_bazin)

            resultados.append(
                {
                    "Ticker": ticker,
                    "Tipo": row["Tipo"],
                    "Qtd": qtd,
                    "P. Médio": pm,
                    "P. Atual": round(preco, 2),
                    "Total Investido": round(tot_investido, 2),
                    "Valor Atual": round(tot_atual, 2),
                    "Resultado ($)": round(lucro_reais, 2),
                    "Rentab. (%)": round(lucro_pct, 2),
                    "Div. 12M": round(info["div_12m"], 2),
                    "DY (%)": round(info["dy_pct"], 2),
                    "Teto Bazin": round(teto_bazin, 2),
                    "Teto Graham": round(teto_graham, 2) if row["Tipo"] == "Ação" else None,
                    "Margem Seg. (%)": round(margem_seguranca(preco, teto_medio if teto_medio > 0 else teto_bazin), 2),
                    "Status": status,
                }
            )

        barra.empty()
        if erros:
            st.warning("Não foi possível obter dados para: " + "; ".join(erros))

        if resultados:
            st.session_state["df_carteira"] = pd.DataFrame(resultados)
        elif not erros:
            st.info("Nenhum ativo válido informado.")

    if "df_carteira" in st.session_state:
        df_c = st.session_state["df_carteira"]

        tot_inv = df_c["Total Investido"].sum()
        tot_at = df_c["Valor Atual"].sum()
        lucro_tot = tot_at - tot_inv
        rent_tot = (lucro_tot / tot_inv * 100) if tot_inv > 0 else 0.0
        renda_anual_est = (df_c["Qtd"] * df_c["Div. 12M"]).sum()

        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                card_html("Patrimônio Atual", f"R$ {tot_at:,.2f}", f"Rentabilidade: {rent_tot:.2f}%", IMG_STOCK_MARKET),
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                card_html("Total Investido", f"R$ {tot_inv:,.2f}", "Custo Histórico", IMG_ANALYTICS),
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                card_html("Lucro / Prejuízo", f"R$ {lucro_tot:,.2f}", "Ganho de Capital", IMG_REAL_ESTATE),
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                card_html(
                    "Renda Passiva Anual",
                    f"R$ {renda_anual_est:,.2f}",
                    f"Média R$ {renda_anual_est / 12:,.2f}/mês",
                    IMG_GLOBAL,
                ),
                unsafe_allow_html=True,
            )

        st.subheader("Tabela de Ativos da Carteira")
        st.dataframe(
            df_c,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Margem Seg. (%)": st.column_config.ProgressColumn(
                    "Margem Seg. (%)", min_value=-30, max_value=30, format="%.1f%%"
                ),
                "Rentab. (%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )

        csv_buffer = io.StringIO()
        df_c.to_csv(csv_buffer, index=False, sep=";", decimal=",")
        st.download_button(
            "⬇️ Exportar carteira processada (CSV)",
            data=csv_buffer.getvalue(),
            file_name="carteira_processada.csv",
            mime="text/csv",
        )

        st.subheader("Visualização Gráfica")
        g1, g2 = st.columns(2)
        with g1:
            fig_pizza = px.pie(
                df_c,
                values="Valor Atual",
                names="Tipo",
                title="Distribuição de Patrimônio por Categoria",
                hole=0.45,
                template=PLOTLY_TEMPLATE_ATIVO,
                color_discrete_sequence=[ACCENT, ACCENT_STRONG, "#94A3B8", "#64748B", "#CBD5E1"],
            )
            fig_pizza.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pizza, use_container_width=True, config=PLOTLY_CONFIG)

        with g2:
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(x=df_c["Ticker"], y=df_c["P. Atual"], name="Preço Atual", marker_color=ACCENT_STRONG))
            fig_bar.add_trace(go.Bar(x=df_c["Ticker"], y=df_c["Teto Bazin"], name="Teto Bazin", marker_color="#4ADE80"))
            fig_bar.update_layout(
                title="Preço Atual vs. Preço Teto Bazin",
                barmode="group",
                template=PLOTLY_TEMPLATE_ATIVO,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)

        st.subheader("Composição do Patrimônio por Ativo")
        fig_tree = px.treemap(
            df_c,
            path=["Tipo", "Ticker"],
            values="Valor Atual",
            color="Rentab. (%)",
            color_continuous_scale="RdYlGn",
            template=PLOTLY_TEMPLATE_ATIVO,
        )
        fig_tree.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=30, l=0, r=0, b=0))
        st.plotly_chart(fig_tree, use_container_width=True, config=PLOTLY_CONFIG)

        # --- Diagnóstico automático (baseado em regras, sem custo de IA) ---
        st.markdown("---")
        st.subheader("Diagnóstico Automático da Carteira")
        st.caption(
            "Análise por regras determinísticas (concentração, diversificação, rentabilidade) — "
            "gratuita e instantânea. Para uma análise mais elaborada em linguagem natural, "
            "use a aba **Análise via IA Gemini**."
        )
        diag = gerar_diagnostico(df_c)

        dcol1, dcol2, dcol3 = st.columns(3)
        with dcol1:
            st.markdown("**🟢 Pontos Fortes**")
            if diag["pontos_fortes"]:
                for item in diag["pontos_fortes"]:
                    st.markdown(f"- {item}")
            else:
                st.caption("Nenhum ponto forte identificado ainda.")
        with dcol2:
            st.markdown("**🟡 Pontos de Atenção**")
            if diag["pontos_atencao"]:
                for item in diag["pontos_atencao"]:
                    st.markdown(f"- {item}")
            else:
                st.caption("Nenhum ponto de atenção identificado.")
        with dcol3:
            st.markdown("**🔴 Alertas**")
            if diag["alertas"]:
                for item in diag["alertas"]:
                    st.markdown(f"- {item}")
            else:
                st.caption("Nenhum alerta no momento.")
    else:
        st.info("Clique em **Processar Carteira Completa** para visualizar os indicadores.")

# ==========================================
# ABA 2: VALUATION INDIVIDUAL
# ==========================================
elif aba == "Valuation Individual":
    st.title("Valuation Individual de Ativos")
    st.write("Calcule modelos de precificação teto para decisões individuais de compra.")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ticker_in = st.text_input(
            "Ticker do Ativo (ex: PETR4, MXRF11, SPY, BTC):", "BBAS3"
        ).upper().strip()
    with col2:
        tipo_in = st.selectbox("Categoria do Ativo:", TIPOS_ATIVO)
    with col3:
        dy_alvo = st.number_input("DY Alvo Bazin (%):", min_value=1.0, value=6.0, step=0.5) / 100

    if tipo_in == "Criptomoeda":
        st.caption(
            "ℹ️ Criptomoedas não têm dividendos, lucro ou patrimônio contábil, então os "
            "modelos de valuation (Bazin/Graham/Gordon) não se aplicam — o app mostra "
            "apenas cotação e histórico de preço."
        )
    elif tipo_in == "ETF":
        st.caption(
            "ℹ️ Para ETFs, os modelos de valuation costumam não fazer sentido (o preço "
            "reflete a cesta de ativos) — use como referência apenas o histórico de preço."
        )

    if st.button("Executar Valuation", type="primary"):
        with st.spinner("Buscando dados e aplicando modelos..."):
            d = buscar_dados_ativo(ticker_in, tipo_in)

        if not d["ok"]:
            st.error(f"Não foi possível obter dados para {ticker_in}: {d.get('erro')}")
        else:
            t_bazin = calcular_teto_bazin(d["div_12m"], dy_alvo)
            t_graham = calcular_teto_graham(d["lpa"], d["vpa"]) if tipo_in == "Ação" else 0.0
            t_gordon = calcular_teto_gordon(d["div_12m"])
            t_medio = calcular_teto_medio(t_bazin, t_graham, t_gordon)
            p_atual = d["preco"]
            status, _ = classificar_status(p_atual, t_medio if t_medio > 0 else t_bazin)

            st.markdown(f"### Análise Detalhada: **{d['nome']} ({ticker_in})** &nbsp; `{status}`")
            st.caption(f"Fonte dos dados: {d['fonte']}")

            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.markdown(card_html("Preço Atual", f"R$ {p_atual:.2f}"), unsafe_allow_html=True)
            with m2:
                st.markdown(card_html(f"Teto Bazin ({dy_alvo * 100:.1f}%)", f"R$ {t_bazin:.2f}"), unsafe_allow_html=True)
            with m3:
                t_g_str = f"R$ {t_graham:.2f}" if tipo_in == "Ação" and t_graham > 0 else "N/A"
                st.markdown(card_html("Teto Graham", t_g_str), unsafe_allow_html=True)
            with m4:
                t_gd_str = f"R$ {t_gordon:.2f}" if t_gordon > 0 else "N/A"
                st.markdown(card_html("Teto Gordon", t_gd_str), unsafe_allow_html=True)
            with m5:
                st.markdown(card_html("Teto Médio", f"R$ {t_medio:.2f}" if t_medio > 0 else "N/A"), unsafe_allow_html=True)

            st.subheader("Indicadores Fundamentalistas")
            f1, f2, f3, f4, f5 = st.columns(5)
            f1.metric("P/L", f"{d['pl']:.2f}" if d["pl"] else "N/A")
            f2.metric("P/VP", f"{d['pvp']:.2f}" if d["pvp"] else "N/A")
            f3.metric("Dividend Yield", f"{d['dy_pct']:.2f}%")
            f4.metric("LPA", f"R$ {d['lpa']:.2f}")
            f5.metric("ROE", f"{d['roe']:.2f}%")

            st.subheader("Histórico de Preço (12 meses)")
            hist = buscar_historico(ticker_in, tipo_in, "1y")
            if hist is not None and not hist.empty:
                fig_hist = go.Figure()
                fig_hist.add_trace(
                    go.Scatter(x=hist.index, y=hist["Close"], name="Preço de Fechamento", line=dict(color=ACCENT))
                )
                if t_bazin > 0:
                    fig_hist.add_hline(y=t_bazin, line_dash="dash", line_color="#4ADE80", annotation_text="Teto Bazin")
                if t_graham > 0:
                    fig_hist.add_hline(y=t_graham, line_dash="dot", line_color="#FACC15", annotation_text="Teto Graham")
                fig_hist.update_layout(
                    template=PLOTLY_TEMPLATE_ATIVO,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=20, l=0, r=0, b=0),
                )
                st.plotly_chart(fig_hist, use_container_width=True, config=PLOTLY_CONFIG)
            else:
                st.info("Histórico de preços indisponível para este ativo.")

            # --- Resultados financeiros (receita/lucro) — quando disponível ---
            if tipo_in in ("Ação", "FII", "BDR"):
                st.subheader("Resultados Financeiros Anuais")
                resultados_fin = buscar_resultados_financeiros(ticker_in, tipo_in)
                if resultados_fin is not None and not resultados_fin.empty:
                    fig_res = go.Figure()
                    if "Receita" in resultados_fin.columns:
                        fig_res.add_trace(
                            go.Bar(x=resultados_fin.index, y=resultados_fin["Receita"], name="Receita", marker_color=ACCENT)
                        )
                    if "Lucro Líquido" in resultados_fin.columns:
                        fig_res.add_trace(
                            go.Bar(
                                x=resultados_fin.index,
                                y=resultados_fin["Lucro Líquido"],
                                name="Lucro Líquido",
                                marker_color=ACCENT_STRONG,
                            )
                        )
                    fig_res.update_layout(
                        barmode="group",
                        template=PLOTLY_TEMPLATE_ATIVO,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=20, l=0, r=0, b=0),
                    )
                    st.plotly_chart(fig_res, use_container_width=True, config=PLOTLY_CONFIG)
                else:
                    st.caption(
                        "ℹ️ Dados de receita/lucro indisponíveis para este ativo no Yahoo Finance "
                        "(cobertura fundamentalista de tickers da B3 costuma ser mais limitada)."
                    )

            # --- Notícias recentes (com classificação heurística de sentimento) ---
            st.subheader("Notícias Recentes")
            noticias = buscar_noticias(ticker_in, tipo_in, limite=6)
            if noticias:
                for n in noticias:
                    st.markdown(f"{n['emoji']} **[{n['titulo']}]({n['link']})** — {n['publicador']}")
                st.caption(
                    "⚠️ Classificação de sentimento é uma heurística simples por palavras-chave, "
                    "não um modelo de IA — use como triagem rápida, não como análise definitiva."
                )
            else:
                st.caption("Nenhuma notícia recente encontrada para este ativo.")

# ==========================================
# ABA 3: COMPARADOR DE ATIVOS
# ==========================================
elif aba == "Comparador de Ativos":
    st.title("Comparador Multi-Ativos")
    st.write("Compare os múltiplos fundamentais e preços teto de múltiplos ativos lado a lado.")

    tickers_list = st.text_input("Lista de Tickers (separados por vírgula):", "BBAS3, ITSA4, SANB11, CXSE3")
    tipo_comp = st.selectbox("Categoria dos ativos informados:", TIPOS_ATIVO, key="tipo_comparador")

    if st.button("Executar Comparação", type="primary"):
        lista = [t.strip().upper() for t in tickers_list.split(",") if t.strip()]
        dados_comparativos = []
        dados_radar = []

        barra = st.progress(0.0, text="Processando ativos...")
        for i, t in enumerate(lista):
            info = buscar_dados_ativo(t, tipo_comp)
            barra.progress((i + 1) / max(len(lista), 1), text=f"Processando {t}...")
            if not info["ok"]:
                continue

            t_bazin = calcular_teto_bazin(info["div_12m"], 0.06)
            t_graham = calcular_teto_graham(info["lpa"], info["vpa"]) if tipo_comp == "Ação" else 0.0
            margem = margem_seguranca(info["preco"], t_bazin)

            dados_comparativos.append(
                {
                    "Ticker": t,
                    "Preço Atual": f"R$ {info['preco']:.2f}",
                    "DY (%)": f"{info['dy_pct']:.2f}%",
                    "P/L": f"{info['pl']:.2f}" if info["pl"] else "N/A",
                    "P/VP": f"{info['pvp']:.2f}" if info["pvp"] else "N/A",
                    "ROE (%)": f"{info['roe']:.2f}%",
                    "Teto Bazin (6%)": f"R$ {t_bazin:.2f}",
                    "Teto Graham": f"R$ {t_graham:.2f}" if t_graham > 0 else "N/A",
                    "Margem Seg. (%)": round(margem, 2),
                }
            )
            dados_radar.append(
                {"Ticker": t, "DY": info["dy_pct"], "ROE": info["roe"], "P/L": info["pl"], "P/VP": info["pvp"]}
            )
        barra.empty()

        if dados_comparativos:
            df_comp = pd.DataFrame(dados_comparativos)
            st.dataframe(
                df_comp,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Margem Seg. (%)": st.column_config.ProgressColumn(min_value=-30, max_value=30, format="%.1f%%")
                },
            )

            st.subheader("Comparação de Dividend Yield")
            fig_dy = px.bar(
                pd.DataFrame(dados_radar),
                x="Ticker",
                y="DY",
                template=PLOTLY_TEMPLATE_ATIVO,
                color="DY",
                color_continuous_scale=[ACCENT_STRONG, ACCENT],
                labels={"DY": "Dividend Yield (%)"},
            )
            fig_dy.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_dy, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.error("Nenhum ativo pôde ser processado. Verifique os tickers informados.")

# ==========================================
# ABA 4: SIMULADOR DE APORTES
# ==========================================
elif aba == "Simulador de Aportes":
    st.title("Simulador de Aportes")
    st.write(
        "Distribui um novo aporte priorizando os ativos com maior margem de segurança "
        "(mais descontados em relação ao preço teto) já processados no Dashboard."
    )

    if "df_carteira" not in st.session_state:
        st.info("Processe sua carteira na aba **Dashboard da Carteira** primeiro.")
    else:
        df_c = st.session_state["df_carteira"].copy()
        valor_aporte = st.number_input("Valor do novo aporte (R$):", min_value=0.0, value=1000.0, step=100.0)

        elegiveis = df_c[df_c["Margem Seg. (%)"] > 0].sort_values("Margem Seg. (%)", ascending=False)

        if elegiveis.empty:
            st.warning("Nenhum ativo da carteira está abaixo do preço teto no momento. Considere aguardar.")
        else:
            peso_total = elegiveis["Margem Seg. (%)"].sum()
            elegiveis["Peso (%)"] = elegiveis["Margem Seg. (%)"] / peso_total * 100
            elegiveis["Valor Sugerido (R$)"] = (elegiveis["Peso (%)"] / 100 * valor_aporte).round(2)
            elegiveis["Qtd. Sugerida (aprox.)"] = (
                elegiveis["Valor Sugerido (R$)"] / elegiveis["P. Atual"]
            ).apply(lambda x: int(x) if x >= 1 else 0)

            st.subheader("Sugestão de Alocação")
            st.dataframe(
                elegiveis[
                    [
                        "Ticker",
                        "Tipo",
                        "P. Atual",
                        "Margem Seg. (%)",
                        "Peso (%)",
                        "Valor Sugerido (R$)",
                        "Qtd. Sugerida (aprox.)",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Peso (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                },
            )
            st.caption(
                "⚠️ Simulação simplificada baseada apenas na margem de segurança atual. "
                "Não considera diversificação-alvo, correlação entre ativos ou perfil de risco."
            )

            fig_aporte = px.pie(
                elegiveis,
                values="Valor Sugerido (R$)",
                names="Ticker",
                template=PLOTLY_TEMPLATE_ATIVO,
                hole=0.45,
                title="Distribuição Sugerida do Aporte",
            )
            fig_aporte.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_aporte, use_container_width=True, config=PLOTLY_CONFIG)

# ==========================================
# ABA: PROVENTOS
# ==========================================
elif aba == "Proventos":
    st.title("Proventos Recebidos")
    st.write(
        "Acompanhe dividendos, JCP e rendimentos de FIIs recebidos pela sua carteira "
        "nos últimos 12 meses."
    )

    if "df_carteira" not in st.session_state:
        st.info("Processe sua carteira na aba **Dashboard da Carteira** primeiro.")
    else:
        df_c = st.session_state["df_carteira"]
        hoje = pd.Timestamp.now().normalize()
        inicio_periodo = hoje - pd.DateOffset(months=11)
        meses_periodo = pd.period_range(start=inicio_periodo, end=hoje, freq="M")

        totais_por_mes = pd.Series(0.0, index=meses_periodo)
        totais_por_ativo = []

        with st.spinner("Buscando histórico de proventos..."):
            for _, row in df_c.iterrows():
                ticker, tipo, qtd = row["Ticker"], row["Tipo"], row["Qtd"]
                serie = buscar_dividendos_historico(ticker, tipo)
                if serie is None or serie.empty:
                    continue

                serie = serie.copy()
                if getattr(serie.index, "tz", None) is not None:
                    serie.index = serie.index.tz_localize(None)

                serie = serie[serie.index >= inicio_periodo]
                if serie.empty:
                    continue

                valor_recebido = serie * qtd
                total_ativo = float(valor_recebido.sum())
                totais_por_ativo.append(
                    {"Ticker": ticker, "Tipo": tipo, "Proventos 12M (R$)": round(total_ativo, 2)}
                )

                por_mes = valor_recebido.groupby(valor_recebido.index.to_period("M")).sum()
                for periodo, valor in por_mes.items():
                    if periodo in totais_por_mes.index:
                        totais_por_mes[periodo] += float(valor)

        total_geral = float(totais_por_mes.sum())
        patrimonio_atual = float(df_c["Valor Atual"].sum())
        dy_carteira = (total_geral / patrimonio_atual * 100) if patrimonio_atual > 0 else 0.0

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(card_html("Total Recebido (12M)", f"R$ {total_geral:,.2f}"), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Média Mensal", f"R$ {total_geral / 12:,.2f}"), unsafe_allow_html=True)
        with c3:
            st.markdown(
                card_html("Dividend Yield da Carteira", f"{dy_carteira:.2f}%", "Sobre o patrimônio atual"),
                unsafe_allow_html=True,
            )

        st.subheader("Evolução Mensal")
        if total_geral > 0:
            df_mensal = pd.DataFrame(
                {"Mês": [str(p) for p in totais_por_mes.index], "Proventos (R$)": totais_por_mes.values}
            )
            fig_prov = go.Figure()
            fig_prov.add_trace(go.Bar(x=df_mensal["Mês"], y=df_mensal["Proventos (R$)"], marker_color=ACCENT))
            fig_prov.update_layout(
                template=PLOTLY_TEMPLATE_ATIVO,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=20, l=0, r=0, b=0),
            )
            st.plotly_chart(fig_prov, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("Nenhum provento encontrado nos últimos 12 meses para os ativos desta carteira.")

        if totais_por_ativo:
            st.subheader("Proventos por Ativo (12 meses)")
            df_ativo = pd.DataFrame(totais_por_ativo).sort_values("Proventos 12M (R$)", ascending=False)
            st.dataframe(df_ativo, use_container_width=True, hide_index=True)

        st.caption(
            "⚠️ O cálculo usa a quantidade **atual** de cada ativo aplicada a todos os pagamentos "
            "dos últimos 12 meses — não reflete mudanças de posição ao longo do período "
            "(compras/vendas feitas durante o período)."
        )

# ==========================================
# ABA: METAS FINANCEIRAS
# ==========================================
elif aba == "Metas Financeiras":
    st.title("Metas Financeiras")
    st.write("Defina uma meta de patrimônio e veja a projeção de quando você deve alcançá-la.")

    if "meta_carregada" not in st.session_state:
        meta_salva = carregar_meta(USER_ID)
        st.session_state["meta_valor"] = (meta_salva or {}).get("valor_meta", 100000.0)
        st.session_state["meta_aporte"] = (meta_salva or {}).get("aporte_mensal", 500.0)
        st.session_state["meta_taxa"] = (meta_salva or {}).get("taxa_anual", 10.0)
        st.session_state["meta_carregada"] = True

    patrimonio_atual = 0.0
    if "df_carteira" in st.session_state:
        patrimonio_atual = float(st.session_state["df_carteira"]["Valor Atual"].sum())

    col1, col2, col3 = st.columns(3)
    with col1:
        valor_meta = st.number_input(
            "Meta de patrimônio (R$)", min_value=0.0, value=float(st.session_state["meta_valor"]), step=1000.0
        )
    with col2:
        aporte_mensal = st.number_input(
            "Aporte mensal planejado (R$)", min_value=0.0, value=float(st.session_state["meta_aporte"]), step=50.0
        )
    with col3:
        taxa_anual = st.number_input(
            "Rentabilidade anual esperada (%)",
            min_value=0.0,
            max_value=50.0,
            value=float(st.session_state["meta_taxa"]),
            step=0.5,
        )

    if st.button("Salvar meta"):
        if salvar_meta(USER_ID, {"valor_meta": valor_meta, "aporte_mensal": aporte_mensal, "taxa_anual": taxa_anual}):
            st.session_state["meta_valor"] = valor_meta
            st.session_state["meta_aporte"] = aporte_mensal
            st.session_state["meta_taxa"] = taxa_anual
            st.toast("Meta salva com sucesso!", icon="✅")

    st.markdown("---")

    if patrimonio_atual <= 0:
        st.info(
            "Processe sua carteira na aba **Dashboard da Carteira** para que o patrimônio atual "
            "seja usado como ponto de partida da projeção (por enquanto, considerando R$ 0,00)."
        )

    progresso = min(patrimonio_atual / valor_meta * 100, 100) if valor_meta > 0 else 0.0

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        st.markdown(
            card_html("Patrimônio Atual", f"R$ {patrimonio_atual:,.2f}", f"{progresso:.1f}% da meta"),
            unsafe_allow_html=True,
        )
    with pcol2:
        st.markdown(card_html("Meta", f"R$ {valor_meta:,.2f}"), unsafe_allow_html=True)

    st.progress(min(progresso / 100, 1.0))

    st.subheader("Projeção de Prazo")
    cenarios = {
        "Pessimista": max(taxa_anual - 3, 0.0),
        "Base": taxa_anual,
        "Otimista": taxa_anual + 3,
    }

    linhas_cenario = []
    max_meses_grafico = 12
    for nome_cenario, taxa in cenarios.items():
        meses = meses_para_meta(patrimonio_atual, aporte_mensal, taxa, valor_meta)
        linhas_cenario.append(
            {"Cenário": nome_cenario, "Rentabilidade a.a.": f"{taxa:.1f}%", "Prazo estimado": formatar_prazo(meses)}
        )
        meses_grafico = min(meses, 360) if meses is not None else 60
        max_meses_grafico = max(max_meses_grafico, meses_grafico)

    fig_proj = go.Figure()
    for nome_cenario, taxa in cenarios.items():
        evolucao = projetar_evolucao(patrimonio_atual, aporte_mensal, taxa, max_meses_grafico)
        fig_proj.add_trace(go.Scatter(x=list(range(len(evolucao))), y=evolucao, name=nome_cenario, mode="lines"))

    if valor_meta > 0:
        fig_proj.add_hline(y=valor_meta, line_dash="dash", line_color="#F87171", annotation_text="Meta")
    fig_proj.update_layout(
        template=PLOTLY_TEMPLATE_ATIVO,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Meses a partir de hoje",
        yaxis_title="Patrimônio projetado (R$)",
        margin=dict(t=20, l=0, r=0, b=0),
    )
    st.plotly_chart(fig_proj, use_container_width=True, config=PLOTLY_CONFIG)

    st.dataframe(pd.DataFrame(linhas_cenario), use_container_width=True, hide_index=True)

    st.caption(
        "⚠️ Projeção simplificada com juros compostos e aporte mensal constante — não considera "
        "inflação, impostos ou variação real do mercado. Use como referência, não como garantia."
    )

# ==========================================
# ABA 5: CONSULTORIA COM IA
# ==========================================
elif aba == "Análise via IA Gemini":
    st.title("Consultoria Financeira Automatizada via IA")


    if genai is None:
        st.error("A biblioteca `google-generativeai` não está instalada. Rode: pip install google-generativeai")
    elif "df_carteira" not in st.session_state:
        st.info("Processe sua carteira na aba **Dashboard da Carteira** para habilitar este módulo.")
    else:
        df_c = st.session_state["df_carteira"]
        st.write("Carteira selecionada para avaliação:")
        st.dataframe(
            df_c[["Ticker", "Tipo", "Valor Atual", "Rentab. (%)", "DY (%)", "Status"]],
            use_container_width=True,
            hide_index=True,
        )

        if st.button("Gerar Relatório Estratégico", type="primary"):
            if not gemini_api_key:
                st.error("Informe sua chave API do Google Gemini no painel lateral.")
            else:
                try:
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")

                    contexto = df_c.to_string(index=False)
                    prompt = f"""
                    Você é um analista financeiro sênior especializado no mercado brasileiro.
                    Avalie a seguinte carteira de investimentos:

                    {contexto}

                    Forneça um relatório estruturado em Markdown com:
                    1. Avaliação de Risco e Diversificação.
                    2. Melhores Oportunidades de Alocação (com base no Preço Teto).
                    3. Ativos que exigem Atenção/Acompanhamento.
                    4. Recomendações Práticas para os Próximos Aportes.

                    Deixe explícito ao final que esta análise é gerada por IA, tem caráter
                    exclusivamente educacional e NÃO constitui recomendação de investimento.
                    """

                    with st.spinner("Gerando diagnóstico analítico..."):
                        res = model.generate_content(prompt)
                        st.markdown(res.text)
                        st.session_state["ultima_analise_ia"] = res.text

                except Exception as e:
                    st.error(f"Erro na comunicação com a API Gemini: {e}")

        if "ultima_analise_ia" in st.session_state:
            st.download_button(
                "⬇️ Baixar relatório (Markdown)",
                data=st.session_state["ultima_analise_ia"],
                file_name="relatorio_ia.md",
                mime="text/markdown",
            )

# ==========================================
# ABA 6: GUIA DO USUÁRIO / TUTORIAL
# ==========================================
elif aba == "Guia do Usuário / Tutorial":
    st.title("Guia de Utilização da Plataforma")
    st.write("Aprenda a utilizar os recursos de valuation, gestão de carteira e análise inteligente.")

    st.markdown("---")

    st.markdown(
        """
        <div class="tutorial-box">
            <div class="tutorial-step">Passo 1 · Gestão e Consolidação de Carteira</div>
            Acesse o módulo <b>Dashboard da Carteira</b> para inserir e editar seus ativos na tabela interativa.
            Informe o Ticker (ex: BBAS3, MXRF11), Categoria, Quantidade e Preço Médio. Ao clicar em
            <b>Processar Carteira Completa</b>, o sistema busca automaticamente as cotações em tempo real e
            calcula o patrimônio consolidado, o ganho de capital e a projeção de renda passiva anual.
        </div>

        <div class="tutorial-box">
            <div class="tutorial-step">Passo 2 · Entendendo os Modelos de Valuation (Preço Teto)</div>
            A aplicação utiliza três metodologias reconhecidas no mercado financeiro:
            <ul>
                <li><b>Método Décio Bazin:</b> Preço Teto = Dividendo Anual ÷ DY desejado. Se o preço atual
                estiver abaixo do teto, o ativo é sinalizado como oportunidade de compra.</li>
                <li><b>Método Benjamin Graham:</b> Indicado para Ações — Preço Justo = √(22,5 × LPA × VPA).</li>
                <li><b>Modelo de Gordon:</b> Considera o crescimento constante dos dividendos no longo prazo.</li>
            </ul>
            O <b>Teto Médio</b> combina os modelos aplicáveis para uma referência mais robusta.
        </div>

        <div class="tutorial-box">
            <div class="tutorial-step">Passo 3 · Comparação Multi-Ativos</div>
            No módulo <b>Comparador de Ativos</b>, insira múltiplos tickers separados por vírgula para
            visualizar lado a lado P/L, P/VP, ROE, Dividend Yield e Preços Teto — útil para escolher o
            melhor ativo do mesmo setor para o próximo aporte.
        </div>

        <div class="tutorial-box">
            <div class="tutorial-step">Passo 4 · Simulador de Aportes</div>
            Informe o valor de um novo aporte e a plataforma sugere uma distribuição proporcional à
            margem de segurança de cada ativo já processado — priorizando os mais descontados.
        </div>

        <div class="tutorial-box">
            <div class="tutorial-step">Passo 5 · Consultoria de Investimentos com IA</div>
            Insira sua chave API do Google Gemini na barra lateral. Após processar sua carteira, use a
            aba <b>Análise via IA Gemini</b> para solicitar um relatório diagnóstico sobre diversificação,
            oportunidades e pontos de atenção.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption(
        "⚠️ Esta plataforma tem fins exclusivamente educacionais. As informações e cálculos apresentados "
        "não constituem recomendação de investimento. Consulte um profissional certificado antes de tomar "
        "decisões financeiras."
    )

