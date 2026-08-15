# 🔐 Configurando Login + Carteira por Usuário (100% Supabase, sem cartão)

Este guia habilita login individual (cada pessoa vê só a própria
carteira) usando **apenas o Supabase** — o único serviço, entre os que
avaliamos, que nunca pede cartão de crédito (nem para criar o projeto,
nem no free tier). Leva uns 5 minutos.

> Por que não Google? Criar credenciais OAuth no Google Cloud Console
> tecnicamente não tem custo, mas hoje o Console geralmente exige uma
> conta de faturamento (cartão) vinculada ao projeto antes de liberar a
> criação de credenciais — mesmo que você nunca seja cobrado. Por isso,
> para manter o projeto 100% livre de cartão, usamos só o Supabase.

O login é por **código de verificação por e-mail** (sem senha): o usuário
digita o e-mail, recebe um código de 6 dígitos, digita o código de volta
no app. A sessão fica salva em cookie por 30 dias, então recarregar a
página não desloga o usuário.

> ⚠️ Projetos gratuitos do Supabase pausam automaticamente após **7 dias
> sem uso**. Se acontecer, abra o painel do Supabase e clique em
> "Restore" — menos de um minuto.

## 1. Crie o projeto no Supabase

1. Acesse [supabase.com](https://supabase.com/) e crie uma conta / projeto
   (defina uma senha de banco forte quando pedido).
2. Em **Project Settings → API**, copie a **Project URL** e a **anon
   public key**.

## 2. Crie as tabelas (carteira + metas financeiras)

No **SQL Editor** do Supabase:

```sql
create table carteiras (
    user_id text primary key,
    dados jsonb not null,
    atualizado_em timestamptz default now()
);

create table metas (
    user_id text primary key,
    dados jsonb not null,
    atualizado_em timestamptz default now()
);
```

## 3. Configure o `secrets.toml`

Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`:

```toml
[supabase]
url = "https://SEU-PROJETO.supabase.co"
key = "SUA_ANON_KEY"
```

**Nunca** faça commit de `secrets.toml` — adicione-o ao `.gitignore`.

## 4. Ative o código de verificação no e-mail (passo crítico!)

Por padrão, o e-mail do Supabase só tem um **link**. Como o app pede um
**código**, você precisa expor esse código no e-mail.

> ⚠️ **É preciso editar DOIS templates, não só um:**
> - No **primeiro** login de um e-mail novo, o Supabase usa o template
> **"Confirm signup"**.
> - A partir do **segundo** login, ele usa o template **"Magic Link"**.
>
> Editar só um dos dois faz o outro continuar mandando apenas um link —
> e clicar nesse link (em vez de copiar o código) costuma resultar em
> erro de página inacessível, porque ele tenta abrir a "Site URL" padrão
> do projeto (geralmente `localhost`).

1. No painel do Supabase, vá em **Authentication → Email Templates**.
2. Abra **Confirm signup** e, no corpo HTML, adicione:
   ```html
   <p>Seu código de verificação: <strong>{{ .Token }}</strong></p>
   ```
   Salve.
3. Repita exatamente o mesmo no template **Magic Link**.
4. (Recomendado) Em **Authentication → URL Configuration**, troque o
   **Site URL** de `localhost` para a URL do seu app publicado (ex.:
   `https://seu-app.streamlit.app`) — evita o erro de "localhost
   inacessível" caso alguém clique no link por engano.

## 5. Ao publicar no Streamlit Community Cloud

Em **App settings → Secrets**, cole o conteúdo do seu `secrets.toml`
(não precisa subir o arquivo para o repositório). Nenhuma configuração
de redirect é necessária — diferente do login com Google.

## 6. Testando localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Acesse `http://localhost:8501`, digite seu e-mail, confira a caixa de
entrada (e o spam) e digite o código recebido.

## 7. Como funciona por dentro

- `supabase_client.py` — cria e cacheia o cliente do Supabase.
- `auth.py` — controla o fluxo de login por código, gerencia o cookie de
  sessão (`extra-streamlit-components`), e expõe `usuario_id()` (e-mail)
  para o resto do app.
- `storage.py` — salva/carrega a carteira do usuário logado no Supabase
  (com fallback para arquivo JSON local se não configurado — só testes).
- No **Dashboard da Carteira**, o botão **"💾 Salvar minha carteira"**
  grava a tabela editável atual; no próximo login, ela carrega sozinha.

