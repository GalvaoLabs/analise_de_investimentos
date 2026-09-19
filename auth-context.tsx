"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";
import { auth } from "./firebase";

interface AuthContextValue {
  user: User | null;
  carregando: boolean;
  entrar: (email: string, senha: string) => Promise<void>;
  cadastrar: (email: string, senha: string) => Promise<void>;
  sair: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (usuarioAtual) => {
      setUser(usuarioAtual);
      setCarregando(false);
    });
    return unsubscribe;
  }, []);

  async function entrar(email: string, senha: string) {
    await signInWithEmailAndPassword(auth, email, senha);
  }

  async function cadastrar(email: string, senha: string) {
    await createUserWithEmailAndPassword(auth, email, senha);
  }

  async function sair() {
    await firebaseSignOut(auth);
  }

  return (
    <AuthContext.Provider value={{ user, carregando, entrar, cadastrar, sair }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth precisa ser usado dentro de um <AuthProvider>");
  }
  return context;
}

/** Traduz os códigos de erro do Firebase Auth para mensagens em português. */
export function traduzirErroAuth(codigo: string): string {
  const mensagens: Record<string, string> = {
    "auth/invalid-email": "E-mail inválido.",
    "auth/user-disabled": "Esta conta foi desativada.",
    "auth/user-not-found": "Usuário não encontrado. Verifique o e-mail ou cadastre-se.",
    "auth/wrong-password": "Senha incorreta.",
    "auth/invalid-credential": "E-mail ou senha incorretos.",
    "auth/email-already-in-use": "Este e-mail já está cadastrado. Tente entrar.",
    "auth/weak-password": "A senha precisa ter pelo menos 6 caracteres.",
    "auth/too-many-requests": "Muitas tentativas. Aguarde um momento e tente novamente.",
    "auth/network-request-failed": "Falha de conexão. Verifique sua internet.",
    "auth/invalid-api-key":
      "Chave da API inválida. Confira o .env.local e reinicie o servidor (npm run dev).",
    "auth/api-key-not-valid":
      "Chave da API inválida. Confira o .env.local e reinicie o servidor (npm run dev).",
    "auth/operation-not-allowed":
      "Login por e-mail/senha não está ativado no Firebase. Ative em Authentication → Sign-in method → Email/Password.",
    "auth/unauthorized-domain":
      "Este domínio não está autorizado no Firebase (Authentication → Settings → Authorized domains).",
    "auth/configuration-not-found":
      "Configuração do Firebase não encontrada. Verifique se o Authentication foi ativado no console.",
  };
  // Se o código não for conhecido, mostramos ele próprio — esconder o
  // código atrás de uma mensagem genérica dificulta muito o diagnóstico.
  return mensagens[codigo] ?? `Erro inesperado: ${codigo || "desconhecido"}`;
}

/** Retorna a lista de variáveis de ambiente do Firebase que estão faltando. */
export function variaveisFirebaseFaltando(): string[] {
  const obrigatorias: Record<string, string | undefined> = {
    NEXT_PUBLIC_FIREBASE_API_KEY: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    NEXT_PUBLIC_FIREBASE_DATABASE_URL: process.env.NEXT_PUBLIC_FIREBASE_DATABASE_URL,
    NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    NEXT_PUBLIC_FIREBASE_APP_ID: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  };
  return Object.entries(obrigatorias)
    .filter(([, valor]) => !valor)
    .map(([nome]) => nome);
}
