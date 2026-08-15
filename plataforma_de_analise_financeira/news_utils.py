"""
Notícias recentes de um ativo (via yfinance), com classificação heurística
de sentimento (positivo/neutro/negativo) baseada em palavras-chave —
gratuito, sem nenhuma API paga de NLP/IA.

⚠️ Limitação importante: é uma heurística simples de palavras-chave no
título da notícia, não um modelo de linguagem real. Serve como triagem
rápida para decidir o que vale a pena ler com atenção — não substitui a
leitura da notícia completa nem constitui análise definitiva.
"""
from __future__ import annotations

import streamlit as st
import yfinance as yf

from data_utils import normalizar_ticker

PALAVRAS_POSITIVAS = [
    "lucro recorde", "supera expectativas", "supera projeções", "crescimento",
    "dividendo extraordinário", "aprovação", "recompra", "elevação", "upgrade",
    "valorização", "recorde", "expansão", "resultado positivo", "melhora",
    "avança", "dispara", "sobe forte", "alta de", " sobe ",
]
PALAVRAS_NEGATIVAS = [
    "prejuízo", "queda de", "corte", "downgrade", "recall", "investigação",
    "multa", "processo", "demissão", "atraso", "desvalorização", "despenca",
    " cai ", "recuo", "resultado negativo", "piora", "rebaixamento",
    "default", "calote", "fraude", "escândalo",
]


def _classificar_sentimento(titulo: str) -> tuple[str, str]:
    """Retorna (rótulo, emoji) a partir de contagem de palavras-chave no título."""
    texto = f" {titulo.lower()} "
    pos = sum(1 for p in PALAVRAS_POSITIVAS if p in texto)
    neg = sum(1 for p in PALAVRAS_NEGATIVAS if p in texto)
    if pos > neg:
        return "Positivo", "🟢"
    if neg > pos:
        return "Negativo", "🔴"
    return "Neutro", "🟡"


@st.cache_data(ttl=1800, show_spinner=False)
def buscar_noticias(ticker: str, tipo: str | None = None, limite: int = 8) -> list[dict]:
    """Busca notícias recentes do ativo via yfinance.

    Retorna uma lista de dicts com título, link, publicador, data e
    sentimento heurístico. Lista vazia se não houver notícias disponíveis
    (comum para tickers menos líquidos ou fora dos EUA).
    """
    symbol = normalizar_ticker(ticker, tipo)
    try:
        bruto = yf.Ticker(symbol).news or []
    except Exception:
        return []

    noticias = []
    for item in bruto[:limite]:
        # yfinance mudou o formato do payload de notícias entre versões;
        # tratamos os dois formatos (plano e aninhado em "content").
        conteudo = item.get("content", item) if isinstance(item, dict) else {}
        titulo = conteudo.get("title") or item.get("title")
        if not titulo:
            continue

        link = (
            (conteudo.get("canonicalUrl") or {}).get("url")
            or conteudo.get("link")
            or item.get("link")
        )
        publicador = (
            (conteudo.get("provider") or {}).get("displayName")
            or item.get("publisher")
            or "Fonte desconhecida"
        )
        data_pub = conteudo.get("pubDate") or item.get("providerPublishTime")

        rotulo, emoji = _classificar_sentimento(titulo)
        noticias.append(
            {
                "titulo": titulo,
                "link": link,
                "publicador": publicador,
                "data": data_pub,
                "sentimento": rotulo,
                "emoji": emoji,
            }
        )
    return noticias
