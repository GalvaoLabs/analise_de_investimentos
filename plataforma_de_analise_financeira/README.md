# 💹 Plataforma de Análise Financeira

Aplicação em **Python + Streamlit** para gestão de carteira, valuation
(Preço Teto por Bazin, Graham e Gordon), comparação de ativos, simulação de
aportes e consultoria por IA (Google Gemini).

## Estrutura do projeto

```
├── app.py # Interface (navegação, páginas, componentes visuais)
├── auth.py # Login por e-mail (código de verificação) via Supabase
├── storage.py # Persistência por usuário (carteira + metas) no Supabase
├── supabase_client.py # Cliente Supabase compartilhado
├── data_utils.py # Busca de dados de mercado e modelos de valuation
├── diagnostico.py # Diagnóstico automático da carteira (regras, sem IA)
├── news_utils.py # Notícias por ativo + classificação heurística de sentimento
├── metas_utils.py # Cálculos de projeção para metas financeiras
├── theme.py # Paletas de cor e geração de CSS dinâmico
├── style.css # Estrutura visual base (variáveis, cards, badges)
├── .streamlit/config.toml # Tema nativo do Streamlit (fundamental p/ tabelas)
├── .streamlit/secrets.toml.example # Modelo de credenciais (copie p/ secrets.toml)
├── SETUP_LOGIN.md # Guia passo a passo de login + persistência
├── requirements.txt
└── README.md
```

## 🔐 Login individual + carteira salva na nuvem

Cada pessoa que acessa o app faz login com o **próprio e-mail** (código de
verificação de 6 dígitos, sem senha) e vê **apenas a sua carteira**, salva
de forma persistente no Supabase. A sessão fica salva em cookie por 30
dias, então um F5 não desloga o usuário. Serviço único, gratuito, e que
**nunca** pede cartão de crédito.

**Configuração obrigatória antes de publicar** — siga o passo a passo em
[`SETUP_LOGIN.md`](./SETUP_LOGIN.md). Resumo:
1. Crie um projeto gratuito no Supabase e as tabelas `carteiras` e `metas`.
2. Preencha `.streamlit/secrets.toml` (copie de `secrets.toml.example`).
3. Ajuste os templates **"Confirm signup"** e **"Magic Link"** no
   Supabase para incluir `{{ .Token }}`.
4. No Streamlit Community Cloud, cole os mesmos secrets em **App settings → Secrets**.

## 💱 Tipos de ativo suportados

Ações, FIIs, BDRs, ETFs (nacionais como BOVA11/IVVB11 e internacionais
como SPY/QQQ/VOO) e Criptomoedas (BTC, ETH, etc. — cotadas contra USD via
Yahoo Finance). Os modelos de valuation (Bazin, Graham, Gordon) se aplicam
principalmente a Ações e FIIs; para ETFs e Criptomoedas, o app mostra
cotação e histórico, sem "preço teto" (esses modelos não fazem sentido
para ativos sem dividendos/lucro contábil).

> ⚠️ Mantenha a pasta `.streamlit/` (com `config.toml`) na raiz do projeto,
> junto com `app.py`. Sem ela, as tabelas (`st.dataframe`/`st.data_editor`)
> voltam a aparecer com fundo branco — ver seção "Sobre o tema" abaixo.

## Como executar

```bash
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

O app abre em `http://localhost:8501`.

## Módulos

1. **📊 Dashboard da Carteira** — cadastro editável de ativos, cotações em
   tempo real, patrimônio consolidado, renda passiva estimada, gráficos de
   pizza/barras/treemap, **diagnóstico automático por regras** (concentração,
   diversificação, alertas) e exportação da carteira processada em CSV.
2. **🎯 Valuation Individual** — indicadores fundamentalistas, três modelos
   de preço teto (+ teto médio), gráfico de histórico de preço com as
   linhas de teto sobrepostas, **resultados financeiros anuais** (receita/
   lucro, quando disponível) e **notícias recentes** com classificação
   heurística de sentimento (🟢/🟡/🔴).
3. **⚖️ Comparador de Ativos** — compara múltiplos ativos lado a lado
   (P/L, P/VP, ROE, DY, margem de segurança).
4. **💰 Simulador de Aportes** — distribui um valor de aporte entre
   os ativos da carteira já processados, priorizando os com maior margem de
   segurança.
5. **💸 Proventos** *(novo)* — evolução mensal de dividendos/JCP/rendimentos
   recebidos nos últimos 12 meses, dividend yield da carteira e detalhamento
   por ativo.
6. **🏆 Metas Financeiras** *(novo)* — defina uma meta de patrimônio e veja
   a projeção de prazo em 3 cenários (pessimista/base/otimista), com a meta
   salva na nuvem.
7. **🤖 Análise via IA Gemini** — gera um relatório estratégico da carteira
   em linguagem natural e permite baixá-lo em Markdown (opcional — exige
   chave de API gratuita do Gemini).
8. **📘 Guia do Usuário** — tutorial de uso de cada módulo.

## O que ficou de fora (e por quê)

Entre as sugestões avaliadas, **não implementamos um "screening" (filtro
avançado de ativos por múltiplos critérios)**. Isso exigiria uma base de
dados com milhares de tickers e seus indicadores sempre atualizados —
inviável de manter de forma gratuita e confiável só com yfinance/brapi
(que são otimizados para consultar um ativo de cada vez, não para varrer
o mercado inteiro). Se esse recurso for essencial, o caminho realista é
contratar uma API de dados de mercado paga (ex: Brapi PRO, Alpha Vantage
Premium) — o que sairia do escopo "100% gratuito" do projeto.

## O que mudou em relação à versão anterior

- **Fallback de dados:** se o yfinance falhar, a aplicação tenta a API
  gratuita da brapi.dev automaticamente.
- **Normalização de ticker mais robusta:** usa o tipo do ativo (Ação/FII/
  BDR/ETF) para decidir o sufixo `.SA`, em vez de depender só do tamanho do
  texto.
- **Novo modelo de status:** classificação em Forte Compra / Compra /
  Neutro / Aguardar com badges coloridos, em vez de um binário simples.
- **Teto Médio:** combina os modelos aplicáveis (Bazin, Graham, Gordon)
  para uma referência mais robusta de valuation.
- **Gráfico de histórico de preço** com as linhas de preço teto sobrepostas
  no módulo de Valuation Individual.
- **Treemap de composição da carteira** por tipo e ativo.
- **Exportação em CSV** da carteira processada e do relatório de IA em
  Markdown.
- **Simulador de Aportes**, módulo novo.
- **Barra de progresso** durante buscas em lote e tratamento de erros por
  ativo (a aplicação não trava se um ticker falhar).
- **CSS modernizado:** variáveis de tema centralizadas, badges de status,
  cards com hover mais suave, `st.metric` estilizado, scrollbar customizada
  e regras de responsividade para telas menores.
- **Código modularizado:** funções de dados/valuation isoladas em
  `data_utils.py`, facilitando testes e manutenção.
- **Diagnóstico automático da carteira** (`diagnostico.py`) — análise por
  regras (concentração, diversificação, rentabilidade, oportunidades),
  gratuita e instantânea, sem depender de nenhuma API de IA.
- **Notícias com classificação heurística de sentimento** (`news_utils.py`)
  — busca notícias recentes do ativo via yfinance e classifica por
  palavras-chave (🟢 positivo / 🟡 neutro / 🔴 negativo). É uma heurística
  simples, não um modelo de IA — serve como triagem rápida.
- **Resultados financeiros anuais** (receita/lucro) na aba Valuation
  Individual, quando disponíveis no Yahoo Finance.
- **Aba de Proventos**, com evolução mensal e dividend yield da carteira.
- **Aba de Metas Financeiras**, com projeção em 3 cenários e persistência
  na nuvem.
- **ETFs e Criptomoedas** como novos tipos de ativo suportados.

## Sobre o tema e a personalização de cores

Na barra lateral, o expander **🎨 Aparência** permite:
- Alternar entre **modo Escuro** e **modo Claro**.
- Escolher uma das 6 paletas de cor de destaque (Oceano, Esmeralda, Ametista,
  Solar, Rubi, Grafite), ou ativar **cor personalizada** com dois seletores
  de cor (destaque e destaque forte).

A troca é aplicada instantaneamente aos cards, botões, badges, textos e
gráficos (Plotly usa a mesma cor de destaque escolhida).

**Limitação técnica importante:** o `st.dataframe` / `st.data_editor` do
Streamlit é renderizado em canvas e **não lê o CSS da página** — ele segue
apenas o tema definido em `.streamlit/config.toml`, que é fixo por processo
(não muda dinamicamente por usuário). Por isso incluímos esse arquivo com um
tema escuro coerente: isso resolve o problema do fundo branco nas tabelas e
nos menus suspensos, mesmo que o restante da interface mude de cor. Se você
quiser que a tabela também siga o modo claro, edite `base = "dark"` para
`base = "light"` em `.streamlit/config.toml` (isso afeta todos os usuários
do app, não é por sessão).

## Notas

- Os cálculos de valuation são simplificados e **não constituem
  recomendação de investimento**. Consulte um profissional certificado
  antes de tomar decisões financeiras.
- A chave de API do Gemini é usada apenas na sessão local e não é
  armazenada pela aplicação.

