"""
Diagnóstico automático da carteira — 100% baseado em regras determinísticas
a partir dos dados já calculados no Dashboard. Não depende de nenhuma API
paga (diferente da aba "Análise via IA Gemini", que é opcional e mais
elaborada, mas exige uma chave de API).
"""
from __future__ import annotations

import pandas as pd

LIMITE_CONCENTRACAO_ALERTA = 30.0 # % em um único ativo → alerta vermelho
LIMITE_CONCENTRACAO_ATENCAO = 20.0 # % em um único ativo → ponto de atenção
LIMITE_TIPO_ATENCAO = 70.0 # % em um único tipo de ativo → ponto de atenção
LIMITE_PREJUIZO_ALERTA = -20.0 # rentabilidade individual → alerta
LIMITE_MARGEM_OPORTUNIDADE = 15.0 # margem de segurança → oportunidade


def gerar_diagnostico(df: pd.DataFrame) -> dict:
    """Analisa a carteira processada e retorna pontos fortes, de atenção e alertas.

    Espera um DataFrame com as colunas produzidas pelo Dashboard da
    Carteira (Ticker, Tipo, Valor Atual, Rentab. (%), e opcionalmente
    Margem Seg. (%)). Robusto a colunas ausentes — não gera exceção.
    """
    vazio = {"pontos_fortes": [], "pontos_atencao": [], "alertas": [], "peso_por_tipo": pd.Series(dtype=float)}
    if df is None or df.empty or "Valor Atual" not in df.columns:
        return vazio

    total = df["Valor Atual"].sum()
    if total <= 0:
        return vazio

    df = df.copy()
    df["Peso (%)"] = df["Valor Atual"] / total * 100

    pontos_fortes: list[str] = []
    pontos_atencao: list[str] = []
    alertas: list[str] = []

    # --- Concentração por ativo individual ---
    linha_maior = df.loc[df["Peso (%)"].idxmax()]
    peso_maior = linha_maior["Peso (%)"]
    if peso_maior >= LIMITE_CONCENTRACAO_ALERTA:
        alertas.append(
            f"🔴 Concentração elevada: **{linha_maior['Ticker']}** representa "
            f"{peso_maior:.1f}% da carteira. Uma referência comum é evitar mais de "
            f"20-25% do patrimônio em um único ativo."
        )
    elif peso_maior >= LIMITE_CONCENTRACAO_ATENCAO:
        pontos_atencao.append(
            f"🟡 **{linha_maior['Ticker']}** já representa {peso_maior:.1f}% da carteira — "
            "vale acompanhar para não concentrar demais."
        )
    else:
        pontos_fortes.append(
            f"🟢 Nenhum ativo isolado domina a carteira (maior posição: "
            f"{linha_maior['Ticker']} com {peso_maior:.1f}%)."
        )

    # --- Diversificação por tipo de ativo ---
    peso_por_tipo = df.groupby("Tipo")["Valor Atual"].sum().sort_values(ascending=False) / total * 100
    n_tipos = int((peso_por_tipo > 0).sum())
    if n_tipos <= 1:
        pontos_atencao.append(
            f"🟡 Toda a carteira está concentrada em um único tipo de ativo ({peso_por_tipo.index[0]})."
        )
    elif peso_por_tipo.iloc[0] >= LIMITE_TIPO_ATENCAO:
        pontos_atencao.append(
            f"🟡 {peso_por_tipo.index[0]} concentra {peso_por_tipo.iloc[0]:.1f}% do patrimônio — "
            "considere diversificar entre classes de ativos."
        )
    else:
        pontos_fortes.append(f"🟢 Boa diversificação entre classes de ativos ({n_tipos} tipos diferentes).")

    # --- Rentabilidade geral ---
    if "Rentab. (%)" in df.columns:
        rent_media_ponderada = (df["Rentab. (%)"] * df["Peso (%)"]).sum() / 100
        if rent_media_ponderada > 5:
            pontos_fortes.append(f"🟢 Rentabilidade média ponderada bem positiva ({rent_media_ponderada:.1f}%).")
        elif rent_media_ponderada > 0:
            pontos_fortes.append(f"🟢 Rentabilidade média ponderada positiva ({rent_media_ponderada:.1f}%).")
        elif rent_media_ponderada < -10:
            pontos_atencao.append(
                f"🟡 Rentabilidade média ponderada bem negativa ({rent_media_ponderada:.1f}%) — "
                "vale revisar as teses dos ativos com pior desempenho."
            )

        # Ativos com prejuízo relevante
        prejuizo = df[df["Rentab. (%)"] <= LIMITE_PREJUIZO_ALERTA]
        if not prejuizo.empty:
            tickers = ", ".join(prejuizo["Ticker"].tolist())
            alertas.append(
                f"🔴 Ativos com queda acumulada de {abs(LIMITE_PREJUIZO_ALERTA):.0f}% ou mais: "
                f"{tickers}. Vale reavaliar a tese de investimento."
            )

    # --- Oportunidades pelo Preço Teto ---
    if "Margem Seg. (%)" in df.columns:
        oportunidades = df[df["Margem Seg. (%)"] >= LIMITE_MARGEM_OPORTUNIDADE].sort_values(
            "Margem Seg. (%)", ascending=False
        )
        if not oportunidades.empty:
            tickers = ", ".join(oportunidades["Ticker"].tolist()[:5])
            pontos_fortes.append(
                f"🟢 Ativos com boa margem de segurança pelo Preço Teto (≥{LIMITE_MARGEM_OPORTUNIDADE:.0f}%): {tickers}."
            )

    # --- Número de ativos (diversificação básica) ---
    n_ativos = len(df)
    if n_ativos <= 2:
        pontos_atencao.append(
            f"🟡 Carteira com poucos ativos ({n_ativos}) — risco de concentração é naturalmente maior."
        )

    return {
        "pontos_fortes": pontos_fortes,
        "pontos_atencao": pontos_atencao,
        "alertas": alertas,
        "peso_por_tipo": peso_por_tipo,
    }

