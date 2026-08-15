"""Cálculos para o simulador de metas financeiras (juros compostos com aportes mensais)."""
from __future__ import annotations

import math


def taxa_mensal_equivalente(taxa_anual_pct: float) -> float:
    """Converte uma taxa anual (%) para a taxa mensal equivalente (juros compostos)."""
    taxa_anual = taxa_anual_pct / 100
    return (1 + taxa_anual) ** (1 / 12) - 1


def meses_para_meta(
    valor_atual: float,
    aporte_mensal: float,
    taxa_anual_pct: float,
    meta: float,
    limite_meses: int = 600,
) -> int | None:
    """Calcula quantos meses faltam para atingir a meta.

    Usa busca numérica mês a mês (robusta mesmo com aporte_mensal = 0).
    Retorna None se a meta for inatingível dentro do limite (~50 anos).
    """
    if meta <= 0:
        return 0
    if valor_atual >= meta:
        return 0
    if aporte_mensal <= 0 and taxa_anual_pct <= 0:
        return None

    taxa_m = taxa_mensal_equivalente(taxa_anual_pct)
    saldo = valor_atual

    if taxa_m <= 0 and aporte_mensal <= 0:
        return None
    if taxa_m <= 0:
        faltante = meta - valor_atual
        return math.ceil(faltante / aporte_mensal)

    for n in range(1, limite_meses + 1):
        saldo = saldo * (1 + taxa_m) + aporte_mensal
        if saldo >= meta:
            return n
    return None


def projetar_evolucao(valor_atual: float, aporte_mensal: float, taxa_anual_pct: float, meses: int) -> list[float]:
    """Retorna o patrimônio projetado mês a mês (índice 0 = hoje)."""
    taxa_m = taxa_mensal_equivalente(taxa_anual_pct)
    valores = [valor_atual]
    saldo = valor_atual
    for _ in range(max(meses, 0)):
        saldo = saldo * (1 + taxa_m) + aporte_mensal
        valores.append(saldo)
    return valores


def formatar_prazo(meses: int | None) -> str:
    """Formata um número de meses como 'X anos e Y meses' (texto amigável)."""
    if meses is None:
        return "mais de 50 anos (ajuste o aporte ou a rentabilidade)"
    if meses == 0:
        return "meta já atingida! 🎉"
    anos, resto_meses = divmod(meses, 12)
    partes = []
    if anos > 0:
        partes.append(f"{anos} ano{'s' if anos != 1 else ''}")
    if resto_meses > 0:
        partes.append(f"{resto_meses} {'mês' if resto_meses == 1 else 'meses'}")
    return " e ".join(partes) if partes else "menos de 1 mês"

