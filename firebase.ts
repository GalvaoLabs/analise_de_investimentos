// Inicialização do Firebase — roda no navegador (client-side).
// Usamos o Realtime Database (não o Firestore nem o Cloud Storage), porque
// ele é totalmente gratuito no plano Spark: 1 GB de dados armazenados e
// 10 GB de tráfego por mês, sem exigir cartão de crédito.
//
// A configuração abaixo vem de variáveis NEXT_PUBLIC_*, que são públicas
// por design do Firebase. A segurança real é garantida pelas Regras do
// Realtime Database (veja database.rules.json), não por esconder as chaves.
import { getApps, initializeApp, type FirebaseOptions } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getDatabase } from "firebase/database";

const firebaseConfig: FirebaseOptions = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  databaseURL: process.env.NEXT_PUBLIC_FIREBASE_DATABASE_URL,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Evita reinicializar o app em hot-reloads durante o desenvolvimento.
const app = getApps().length > 0 ? getApps()[0]! : initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getDatabase(app);
export default app;
