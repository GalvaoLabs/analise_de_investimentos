// Persistência da carteira do usuário no Realtime Database.
// Cada usuário tem um nó próprio em `portfolios/{uid}`, protegido pelas
// regras em database.rules.json (só o dono lê/escreve).
//
// Usamos Realtime Database em vez de Firestore/Cloud Storage porque ele é
// gratuito no plano Spark do Firebase, sem exigir cartão de crédito.
import { get, ref, serverTimestamp, set } from "firebase/database";
import { db } from "./firebase";
import type { TipoAtivo } from "./valuation";

export interface AtivoCarteira {
  ticker: string;
  tipo: TipoAtivo;
  quantidade: number;
  precoMedio: number;
}

const CARTEIRA_PADRAO: AtivoCarteira[] = [
  { ticker: "BBAS3", tipo: "Ação", quantidade: 100, precoMedio: 24.5 },
  { ticker: "MXRF11", tipo: "FII", quantidade: 300, precoMedio: 10.15 },
  { ticker: "IVVB11", tipo: "ETF", quantidade: 15, precoMedio: 280.0 },
];

/** Converte o que veio do Realtime Database em um array de ativos.
 *
 * O RTDB não tem tipo "array" nativo: ele guarda arrays como objetos de
 * chaves numéricas e, se algum índice ficar vazio, devolve um objeto em
 * vez de array. Por isso normalizamos aqui os dois formatos. */
function normalizarAtivos(valor: unknown): AtivoCarteira[] | null {
  if (Array.isArray(valor)) {
    return valor.filter(Boolean) as AtivoCarteira[];
  }
  if (valor && typeof valor === "object") {
    const lista = Object.values(valor as Record<string, unknown>).filter(Boolean);
    if (lista.length > 0) {
      return lista as AtivoCarteira[];
    }
  }
  return null;
}

export async function carregarCarteira(uid: string): Promise<AtivoCarteira[]> {
  try {
    const snap = await get(ref(db, `portfolios/${uid}/ativos`));
    if (snap.exists()) {
      const ativos = normalizarAtivos(snap.val());
      if (ativos) return ativos;
    }
  } catch (erro) {
    console.error("Erro ao carregar carteira:", erro);
  }
  return CARTEIRA_PADRAO;
}

export async function salvarCarteira(uid: string, ativos: AtivoCarteira[]): Promise<void> {
  await set(ref(db, `portfolios/${uid}`), {
    ativos,
    atualizadoEm: serverTimestamp(),
  });
}
