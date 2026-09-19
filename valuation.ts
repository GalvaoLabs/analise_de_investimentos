// Modelos de valuation — mesma lógica do data_utils.py da versão Streamlit,
// portada para TypeScript.

export function calcularTetoBazin(div12m: number, dyDesejado: number = 0.06): number {
  if (dyDesejado <= 0) return 0;
  return div12m / dyDesejado;
}

export function calcularTetoGraham(lpa: number, vpa: number): number {
  if (lpa > 0 && vpa > 0) {
    return Math.sqrt(22.5 * lpa * vpa);
  }
  return 0;
}

export function calcularTetoGordon(div12m: number, g: number = 0.03, k: number = 0.1): number {
  if (k <= g || div12m <= 0) return 0;
  return (div12m * (1 + g)) / (k - g);
}

export function calcularTetoMedio(...valores: number[]): number {
  const validos = valores.filter((v) => v && v > 0);
  if (validos.length === 0) return 0;
  return validos.reduce((soma, v) => soma + v, 0) / validos.length;
}

export function margemSeguranca(precoAtual: number, precoTeto: number): number {
  if (precoAtual <= 0 || precoTeto <= 0) return 0;
  return ((precoTeto - precoAtual) / precoAtual) * 100;
}

export type StatusAtivo = "Forte Compra" | "Compra" | "Neutro" | "Sem dados" | "Aguardar";

export function classificarStatus(precoAtual: number, precoTeto: number): StatusAtivo {
  if (precoAtual <= 0 || precoTeto <= 0) return "Sem dados";
  const margem = margemSeguranca(precoAtual, precoTeto);
  if (margem >= 15) return "Forte Compra";
  if (margem >= 0) return "Compra";
  if (margem >= -10) return "Neutro";
  return "Aguardar";
}

/** Tipos de ativo negociados sempre na B3 (recebem sufixo .SA no Yahoo Finance). */
const TIPOS_B3 = new Set(["Ação", "FII", "BDR"]);

export const TIPOS_ATIVO = ["Ação", "FII", "BDR", "ETF", "Criptomoeda"] as const;
export type TipoAtivo = (typeof TIPOS_ATIVO)[number];

/** Normaliza o ticker para o formato aceito pelo Yahoo Finance — mesma
 * lógica de data_utils.py (normalizar_ticker). */
export function normalizarTicker(tickerBruto: string, tipo?: TipoAtivo): string {
  const ticker = tickerBruto.toUpperCase().trim();

  if (tipo === "Criptomoeda") {
    return ticker.includes("-") ? ticker : `${ticker}-USD`;
  }

  if (ticker.endsWith(".SA")) return ticker;

  if (tipo && TIPOS_B3.has(tipo)) {
    return `${ticker}.SA`;
  }

  if (tipo === "ETF") {
    if (ticker.endsWith("11") && ticker.length <= 6) {
      return `${ticker}.SA`;
    }
    return ticker; // ETF internacional (ex: SPY, QQQ, VOO)
  }

  if (!tipo && ticker.length <= 6 && /\d$/.test(ticker)) {
    return `${ticker}.SA`;
  }
  return ticker;
}
