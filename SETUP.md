# 🚀 Configurando e Publicando (Firebase + Vercel)

Este projeto é a versão em **Next.js + Firebase**, hospedada gratuitamente
no **Vercel**. Login por e-mail/senha (sem SMTP, sem espera de e-mail) e
carteira salva no Realtime Database, individual por usuário.
Não usa Firestore nem Cloud Storage — só serviços gratuitos do plano
Spark, sem exigir cartão de crédito.

## 1. Crie o projeto no Firebase (gratuito, sem cartão)

1. Acesse [console.firebase.google.com](https://console.firebase.google.com/)
   e clique em **Adicionar projeto**. Dê um nome e siga o assistente
   (pode desativar o Google Analytics, não é necessário).
2. Confirme que o projeto está no **plano Spark** (gratuito) — é o
   padrão, não exige cartão.

## 2. Ative a Autenticação por e-mail/senha

1. No menu lateral, vá em **Build → Authentication → Get started**.
2. Na aba **Sign-in method**, clique em **Email/Password** e ative a
   primeira opção (Email/Password). Salve.

## 3. Crie o Realtime Database

> ⚠️ Use o **Realtime Database**, não o Firestore e não o Cloud Storage.
> O Realtime Database é totalmente gratuito no plano Spark (1 GB de dados,
> 10 GB de tráfego/mês) e não pede cartão. O Cloud Storage passou a exigir
> o plano pago (Blaze) desde fevereiro/2026, e o Firestore pode esbarrar
> em exigência de faturamento dependendo do projeto.

1. No menu lateral, **Build → Realtime Database → Create Database**.
2. Escolha uma localização (ex: `us-central1` ou a mais próxima).
3. Inicie em **modo bloqueado** (locked mode) — as regras corretas já vêm
   prontas no arquivo `database.rules.json` deste projeto.
4. Depois de criado, abra a aba **Rules**, apague o conteúdo e cole o
   conteúdo do arquivo `database.rules.json`. Clique em **Publish**.
5. Copie a **URL do banco** que aparece no topo da aba "Data" — algo como
   `https://seu-projeto-default-rtdb.firebaseio.com`. Você vai precisar
   dela no próximo passo.

## 4. Pegue a configuração do app Web

1. No menu lateral, clique na engrenagem → **Project settings**.
2. Em **Your apps**, clique no ícone `</>` (Web) para registrar um app.
3. Dê um apelido (ex: "investdash-web") e clique em **Register app**.
4. Copie os valores de `firebaseConfig` (apiKey, authDomain, projectId,
   messagingSenderId, appId) — mais a **databaseURL** do passo 3.5.

## 5. Configure o projeto localmente

```bash
npm install
cp .env.local.example .env.local
```

Abra `.env.local` e cole os valores copiados no passo anterior, prefixados
como no exemplo (`NEXT_PUBLIC_FIREBASE_API_KEY=...`, etc.).

```bash
npm run dev
```

Acesse `http://localhost:3000` — deve redirecionar para `/login`. Crie
uma conta com e-mail/senha (login funciona na hora, sem confirmação por
e-mail) e teste o Dashboard.

> ⚠️ Fui eu (Claude) quem escrevi este projeto sem conseguir rodar
> `npm install` (ambiente sem internet). É bem possível que apareçam 1-2
> erros na primeira execução — geralmente de nomes de campos da API do
> Yahoo Finance (`yahoo-finance2`) que podem ter mudado ligeiramente.
> Me manda o erro exato do terminal que eu ajusto rápido.

## 6. Publique no Vercel (gratuito, sem cartão)

1. Suba este projeto para um repositório no GitHub (crie um novo repo,
   `git init`, `git add .`, `git commit`, `git push`).
2. Acesse [vercel.com](https://vercel.com/) e crie uma conta (pode entrar
   com o GitHub).
3. Clique em **Add New → Project**, selecione o repositório.
4. Em **Environment Variables**, adicione as mesmas 6 variáveis do seu
   `.env.local` (copie os mesmos valores).
5. Clique em **Deploy**. Em ~1 minuto o site estará no ar em
   `https://seu-projeto.vercel.app`.

### Autorizar o domínio do Vercel no Firebase

1. No Firebase, vá em **Authentication → Settings → Authorized domains**.
2. Clique em **Add domain** e adicione o domínio do seu app no Vercel
   (ex: `seu-projeto.vercel.app`) — sem isso, o login falha em produção
   com erro `auth/unauthorized-domain`.

## 7. Estrutura do projeto

```
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Layout raiz (envolve tudo com AuthProvider)
│   │   ├── page.tsx             # Redireciona para /login ou /dashboard
│   │   ├── login/page.tsx       # Login e cadastro (e-mail/senha)
│   │   ├── dashboard/page.tsx   # Carteira, cotações, preço teto
│   │   └── api/quote/route.ts   # Busca cotações via yahoo-finance2 (servidor)
│   ├── lib/
│   │   ├── firebase.ts          # Inicialização do Firebase
│   │   ├── auth-context.tsx     # Contexto de autenticação (React)
│   │   ├── portfolio.ts         # Salvar/carregar carteira no Realtime Database
│   │   └── valuation.ts         # Bazin/Graham/Gordon (portado do Python)
│   └── components/
│       ├── Navbar.tsx
│       ├── AssetTable.tsx       # Tabela editável da carteira
│       ├── SummaryCards.tsx     # Cards de patrimônio/rentabilidade
│       └── AllocationChart.tsx  # Gráfico de pizza (Recharts)
├── database.rules.json          # Regras de segurança (cole no Firebase)
└── .env.local.example
```

## 8. O que já está pronto vs. o que falta (próximas fases)

**✅ Fase 1 (esta entrega):** login/cadastro, dashboard com carteira
editável, cotações em tempo real, cálculo de Preço Teto (Bazin/Graham),
cards de resumo, gráfico de distribuição, salvar/carregar carteira na
nuvem.

**🔜 Próximas fases** (mesma ordem da versão Streamlit, portadas uma a
uma): Valuation Individual (histórico de preço, resultados financeiros,
notícias), Comparador de Ativos, Simulador de Aportes, Proventos, Metas
Financeiras, Diagnóstico Automático, tema de cores personalizável. Me
avisa quando quiser seguir para a próxima fase.
