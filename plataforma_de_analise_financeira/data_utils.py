"""
Módulo de utilidades: busca de dados de mercado (yfinance / brapi como fallback)
e modelos de valuation (Bazin, Graham, Gordon).
"""
from __future__ import annotations

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

# Tipos de ativo que são sempre negociados na B3 (recebem sufixo .SA no Yahoo Finance)
TIPOS_B3 = {"Ação", "FII", "BDR"}

TIPOS_ATIVO = ["Ação", "FII", "BDR", "ETF", "Criptomoeda"]


def normalizar_ticker(ticker: str, tipo: str | None = None) -> str:
    """Normaliza o ticker para o formato aceito pelo Yahoo Finance.

    - Ações, FIIs e BDRs: sempre negociados na B3 → recebem sufixo ``.SA``.
    - ETFs: se o ticker parecer um ETF da B3 (termina em "11", até 6
      caracteres, ex: BOVA11, IVVB11), recebe ``.SA``; senão é tratado
      como ETF internacional (ex: SPY, QQQ, VOO) e usado como está.
    - Criptomoedas: usa o padrão do Yahoo Finance (ex: BTC-USD, ETH-USD).
      Se o usuário digitar só o código (ex: "BTC"), completa com "-USD".
    """
    ticker = ticker.upper().strip()

    if tipo == "Criptomoeda":
        return ticker if "-" in ticker else f"{ticker}-USD"

    if ticker.endswith(".SA"):
        return ticker

    if tipo in TIPOS_B3:
        return f"{ticker}.SA"

    if tipo == "ETF":
        if ticker.endswith("11") and len(ticker) <= 6:
            return f"{ticker}.SA"
        return ticker # ETF internacional (ex: SPY, QQQ, VOO)

    if tipo is None and len(ticker) <= 6 and ticker[-1].isdigit():
        return f"{ticker}.SA"
    return ticker


@st.cache_data(ttl=300, show_spinner=False)
def buscar_dados_ativo(ticker: str, tipo: str | None = None) -> dict:
    """Busca cotação e indicadores fundamentalistas de um ativo.

    Tenta primeiro o yfinance (Yahoo Finance); em caso de falha, cai para a
    API pública gratuita da brapi (apenas cotação básica).
    """
    symbol = normalizar_ticker(ticker, tipo)

    dados = {
        "ok": False,
        "fonte": None,
        "nome": ticker,
        "preco": 0.0,
        "div_12m": 0.0,
        "dy_pct": 0.0,
        "pl": 0.0,
        "pvp": 0.0,
        "lpa": 0.0,
        "vpa": 0.0,
        "roe": 0.0,
        "erro": None,
    }

    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}
        preco = info.get("currentPrice") or info.get("regularMarketPrice")

        if not preco:
            raise ValueError("Preço não encontrado via yfinance")

        dados["preco"] = float(preco)
        dados["lpa"] = float(info.get("trailingEps") or 0.0)
        dados["vpa"] = float(info.get("bookValue") or 0.0)
        dados["pl"] = float(info.get("trailingPE") or 0.0)
        dados["pvp"] = float(info.get("priceToBook") or 0.0)
        dados["roe"] = float((info.get("returnOnEquity") or 0.0) * 100)
        dados["nome"] = info.get("longName") or info.get("shortName") or ticker

        try:
            if not stock.dividends.empty:
                dados["div_12m"] = float(stock.dividends.tail(12).sum())
                if dados["preco"] > 0:
                    dados["dy_pct"] = (dados["div_12m"] / dados["preco"]) * 100
        except Exception:
            pass

        dados["ok"] = True
        dados["fonte"] = "yfinance"
        return dados

    except Exception as e_yf:
        # Fallback: brapi (apenas para ativos B3)
        try:
            ticker_puro = ticker.replace(".SA", "")
            url = f"https://brapi.dev/api/quote/{ticker_puro}"
            res = requests.get(url, timeout=6).json()
            results = res.get("results") or []
            if results:
                item = results[0]
                dados["preco"] = float(item.get("regularMarketPrice") or 0.0)
                dados["nome"] = item.get("shortName", ticker)
                dados["ok"] = dados["preco"] > 0
                dados["fonte"] = "brapi"
                if not dados["ok"]:
                    dados["erro"] = "Preço indisponível nas fontes de dados."
                return dados
            dados["erro"] = f"Ativo não encontrado ({e_yf})"
            return dados
        except Exception as e_brapi:
            dados["erro"] = f"yfinance: {e_yf} | brapi: {e_brapi}"
            return dados


@st.cache_data(ttl=900, show_spinner=False)
def buscar_historico(ticker: str, tipo: str | None = None, periodo: str = "1y"):
    """Busca o histórico de preços de fechamento de um ativo."""
    symbol = normalizar_ticker(ticker, tipo)
    try:
        hist = yf.Ticker(symbol).history(period=periodo)
        return hist
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_dividendos_historico(ticker: str, tipo: str | None = None):
    """Busca o histórico completo de dividendos/proventos pagos por um ativo.

    Retorna uma pandas Series indexada por data (ou None se indisponível).
    """
    symbol = normalizar_ticker(ticker, tipo)
    try:
        div = yf.Ticker(symbol).dividends
        return div if div is not None and not div.empty else None
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_resultados_financeiros(ticker: str, tipo: str | None = None):
    """Busca receita e lucro líquido anuais via yfinance.

    Retorna um DataFrame (índice = data, colunas = "Receita"/"Lucro Líquido")
    ou None se os dados não estiverem disponíveis — comum para muitos
    tickers da B3, cuja cobertura fundamentalista no Yahoo Finance é
    mais limitada que a de ativos americanos.
    """
    symbol = normalizar_ticker(ticker, tipo)
    try:
        fin = yf.Ticker(symbol).financials
        if fin is None or fin.empty:
            return None

        linhas_receita = [i for i in fin.index if "Total Revenue" in i]
        linhas_lucro = [i for i in fin.index if i == "Net Income" or "Net Income Common Stockholders" in i]

        dados = {}
        if linhas_receita:
            dados["Receita"] = fin.loc[linhas_receita[0]]
        if linhas_lucro:
            dados["Lucro Líquido"] = fin.loc[linhas_lucro[0]]

        if not dados:
            return None

        df = pd.DataFrame(dados)
        df.index.name = "Data"
        df = df.sort_index()
        df = df.dropna(how="all")
        return df if not df.empty else None
    except Exception:
        return None


# ==========================================
# MODELOS DE VALUATION (PREÇO TETO)
# ==========================================
def calcular_teto_bazin(div_12m: float, dy_desejado: float = 0.06) -> float:
    """Método de Décio Bazin: Preço Teto = Dividendo Anual / DY Desejado."""
    if dy_desejado <= 0:
        return 0.0
    return div_12m / dy_desejado


def calcular_teto_graham(lpa: float, vpa: float) -> float:
    """Método de Benjamin Graham: Preço Justo = sqrt(22.5 * LPA * VPA)."""
    if lpa > 0 and vpa > 0:
        return (22.5 * lpa * vpa) ** 0.5
    return 0.0


def calcular_teto_gordon(div_12m: float, g: float = 0.03, k: float = 0.10) -> float:
    """Modelo de Crescimento de Gordon (Dividend Discount Model)."""
    if k <= g or div_12m <= 0:
        return 0.0
    return (div_12m * (1 + g)) / (k - g)


def calcular_teto_medio(*valores: float) -> float:
    """Média dos modelos de valuation aplicáveis (ignora valores <= 0)."""
    validos = [v for v in valores if v and v > 0]
    return sum(validos) / len(validos) if validos else 0.0


def margem_seguranca(preco_atual: float, preco_teto: float) -> float:
    """Margem de segurança percentual: quanto o preço está abaixo do teto."""
    if preco_atual <= 0 or preco_teto <= 0:
        return 0.0
    return (preco_teto - preco_atual) / preco_atual * 100


def classificar_status(preco_atual: float, preco_teto: float) -> tuple[str, str]:
    """Retorna (rótulo, classe_css) com base na margem de segurança."""
    if preco_atual <= 0 or preco_teto <= 0:
        return "Sem dados", "badge-neutral"
    margem = margem_seguranca(preco_atual, preco_teto)
    if margem >= 15:
        return "Forte Compra", "badge-buy"
    if margem >= 0:
        return "Compra", "badge-buy"
    if margem >= -10:
        return "Neutro", "badge-neutral"
    return "Aguardar", "badge-wait"

