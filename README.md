# 💹 Plataforma de Análise Financeira (Next.js + Firebase)

Versão moderna, em React/Next.js, da plataforma de análise de
investimentos — hospedada gratuitamente no **Vercel**, com login e
carteira individual por usuário via **Firebase**.

## Stack

- **Next.js 14** (App Router) + **TypeScript**
- **Tailwind CSS** — estilo
- **Firebase Authentication** — login por e-mail/senha (sem SMTP)
- **Firebase Realtime Database** — carteira salva na nuvem, isolada por usuário
- **yahoo-finance2** — cotações e indicadores fundamentalistas
- **Recharts** — gráficos

Tudo com camadas gratuitas que **não exigem cartão de crédito**.

> Escolhemos o **Realtime Database** de propósito, em vez do Firestore ou
> do Cloud Storage: ele é gratuito no plano Spark do Firebase (1 GB de
> dados, 10 GB de tráfego/mês) e não pede faturamento. O Cloud Storage
> exige o plano pago (Blaze) desde fevereiro/2026, e opções de banco SQL
> (Cloud SQL, Firebase SQL Connect) têm custo mensal fixo.

## Começando

Siga o [`SETUP.md`](./SETUP.md) — tem o passo a passo completo (criar o
projeto Firebase, configurar variáveis de ambiente, testar localmente e
publicar no Vercel).

Resumo rápido, se você já tem a configuração do Firebase em mãos:

```bash
npm install
cp .env.local.example .env.local   # preencha com sua config do Firebase
npm run dev
```

## Por que Next.js + Firebase em vez da versão Streamlit?

A versão em Python/Streamlit deste projeto continua existindo e é
totalmente funcional — essa versão em Next.js foi construída para quem
quer uma interface mais polida e responsiva (interações instantâneas,
sem recarregar a página inteira a cada clique) e está disposto a lidar
com um pouco mais de complexidade de deploy (Node.js, variáveis de
ambiente, Git) em troca disso.

## Estado atual

Veja a seção "O que já está pronto vs. o que falta" em
[`SETUP.md`](./SETUP.md) para o roteiro de funcionalidades.
