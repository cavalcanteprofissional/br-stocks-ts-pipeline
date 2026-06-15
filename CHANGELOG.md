# Changelog

All notable changes to this project will be documented in this file.

## [0.9.0] — 2026-06-15

### Added

- **About Me Card na section "Sobre"** — `landing/src/components/AboutCard.jsx`:
  - Card escuro (`var(--bg-card)`, `border-radius: var(--radius)`) com foto do
    desenvolvedor (avatar GitHub 64px, borda accent), nome, bio e localização
  - Links sociais inline: GitHub, Portfólio, LinkedIn, Email — com ícones SVG
    e hover accent
  - Tech tags: py, lm, streamlit, folium, pytorch, opencv — no estilo badge verde
  - Estatísticas do GitHub: 38 repositórios, 4 seguidores, 18 following

### Changed

- `CTASection.jsx` — importa `<AboutCard />` e o insere dentro do `ScrollReveal`
  do footer, antes de `<site-footer>`

### Added (CSS)

- `globals.css`: `.about-card`, `.about-card-inner`, `.about-top`, `.about-avatar`,
  `.about-name`, `.about-bio`, `.about-location`, `.about-links`, `.about-link`,
  `.about-tech-tags`, `.tech-tag`, `.about-stats`
- Responsivo: `.about-card` padding reduz para 24px em mobile

## [0.8.0] — 2026-06-15

### Added

- **Navbar fixa inspirada no landing SANOVA** — `landing/src/components/Navbar.jsx`:
  - Fixed-top 64px com `backdrop-filter: blur(12px)`, borda inferior sutil
  - Scroll effect: escurece o fundo ap&oacute;s 100px de scroll (classe `.scrolled`)
  - Hamburger menu mobile com tr&ecirc;s barras animadas (transform rotate 45&deg;)
  - Links de navega&ccedil;&atilde;o: In&iacute;cio, Ranking, Sa&uacute;de, Forecast, Sobre
  - Smooth scroll via anchor `#id` para cada section

- **Footer no padr&atilde;o SANOVA** — `CTASection.jsx`:
  - Tag `<footer>` com `border-top`, `display: flex; justify-content: space-between`
  - Copyright din&acirc;mico + cr&eacute;ditos lado a lado
  - Responsivo: empilha verticalmente em mobile

### Changed

- **IDs nas sections** — `App.jsx` + HeroSection, RankingSection, MarketHealthSection,
  ForecastSection, CTASection receberam `id` individual (`hero`, `ranking`, `saude`,
  `forecast`, `sobre`) para navega&ccedil;&atilde;o por anchor
- **Navbar importada** no topo do return em `App.jsx`
- **HeroSection** — `paddingTop: "var(--nav-height)"` para compensar navbar fixa
- **CTASection layout** — agora usa `flexDirection: "column"` para empilhar CTA + footer

### Added (CSS)

- `globals.css`: `--nav-height: 64px`
- Estilos `.navbar`, `.nav-inner`, `.nav-brand`, `.nav-links`, `.nav-toggle`
- Estilos `.site-footer`, `.footer-inner`
- Responsivo: nav-links vira slide-down em &le;768px

## [0.7.0] — 2026-06-14

### Fixed

- **Deploy Streamlit Cloud quebrava sem `dashboard_data.json`** — `data/` estava
  no `.gitignore`, então o JSON não subia para o Cloud, causando `FileNotFoundError`.
  - `.gitignore`: `data/*` com exceção `!data/dashboard_data.json`
  - `dashboard_data.json` commitado no repositório
  - `load_dashboard_data()` ganhou fallback: se o JSON não existir, executa
    `generate_dashboard_data.py` via `subprocess` com `st.info` e `st.error`
    em caso de falha

## [0.6.2] — 2026-06-14

### Fixed

- **JSON inválido (NaN) na landing page** — o heatmap `monthly_returns` do Plotly
  armazena `NaN` na matriz z para meses sem observação. `np.frombuffer()` preservava
  esses NaN, e `json.dump(allow_nan=True)` os serializava como `NaN` literal — que o
  navegador rejeita como JSON inválido.
  - `_decode_typed_array()` agora converte NaN → None na lista retornada
  - Adicionado `_sanitize()` recursivo que percorre todo o dict e troca
    `float('nan')` por `None` como safety net antes do `json.dump`

## [0.6.1] — 2026-06-14

### Fixed

- **Card "Correlação entre Ativos" vazio na landing page** — duas causas corrigidas:
  - `scripts/extract_landing_data.py`: Plotly serializa arrays como typed arrays binários
    (`{dtype: "f8", bdata: "base64..."}`) em vez de listas JSON. Adicionado
    `_decode_typed_array()` que converte via `np.frombuffer` + `base64.b64decode`,
    com reshape automático de matrizes z flat (9×9=81) para lista aninhada.
  - `landing/src/components/charts/CorrelationMatrix.jsx`: Substituído Chart.js scatter
    (que não renderizava com `type: "category"`) por tabela CSS Grid com cells coloridas
    proporcionalmente ao valor, tooltip via atributo `title`, e sem dependências de chart.

## [0.6.0] — 2026-06-14

### Added

- **Landing Page Scrollytelling** (`st/landing/`) — SPA React + Vite independente:
  - **Hero Section** com headline, subtítulo, count-up animado (+1.135% PETR4) e scroll indicator
  - **Ranking Section** com bar chart horizontal dos retornos totais e callout best/worst
  - **Market Health Section** com drawdown chart (best vs worst), matriz de correlação interativa, e análise textual
  - **Forecast Section** com chart de projeção (IC 95%), badge de confiabilidade do modelo, e métricas RMSE/CV
  - **CTA Section** com link para o dashboard interativo
  - Scroll snap sections com scroll reveals animados via framer-motion
  - Tema escuro, responsivo, font Inter

- **Script de extração** (`scripts/extract_landing_data.py`) — subset de ~95KB do `dashboard_data.json` (3.24MB) contendo apenas KPIs, forecast, correlação e séries do melhor/pior ativo

### Changed

- `TODO.md` — Rodada 9 adicionada com plano detalhado da landing page

## [0.5.0] — 2026-06-14

### Changed

- **Data Storytelling — Layout do expander "📊 Métricas de Confiabilidade"** (`src/dashboard.py`):
  - Adicionado **veredito** no topo (`✅ Modelo confiável` / `⚠️ Requer atenção`) com caption resumo — hook narrativo
  - Métricas agrupadas em **2 colunas temáticas**: "📈 Ajuste do Modelo" (RMSE/MAE/MAPE) × "🔬 Diagnóstico dos Resíduos" (Ljung-Box/Jarque-Bera + badge textual)
  - **Badge textual** movido de `metric(delta=...)` para `st.markdown()` separado — eliminado uso indevido do delta numérico
  - **Validação Cruzada** com CV RMSE vs In-sample lado a lado, delta percentual interpretado (`✅ Modelo generaliza bem` / `⚠️ Overfitting possível`)
  - **Gráfico de Incerteza** com anotações de largura no Passo 1 e último passo, crescimento percentual, e caption de alerta
  - Princípios aplicados: *front-load key insight*, *contrast and compare*, *progressive reveal*, *show don't tell*

## [0.4.0] — 2026-06-14

### Added

- **Métricas de confiabilidade do forecast** — pipeline e dashboard agora
  computam e exibem:
  - RMSE/MAE/MAPE in-sample
  - RMSE walk-forward CV (expanding window 70/30)
  - Ljung-Box p-value (autocorrelação residual) com badge ✅/⚠️
  - Jarque-Bera p-value (normalidade residual)
  - Largura média do IC 95% por horizonte com gráfico de incerteza
  - Todos exportados via `generate_dashboard_data.py` e exibidos no expander
    "📊 Métricas de Confiabilidade" na aba Forecast

### Changed

- **Pipeline otimizado** — forecast reusa ordem ARIMA do fitting (evita `auto_arima`
  duplicado); walk-forward CV usa `ARIMA.fit()` com ordem fixa, não `auto_arima`
- **`src/dashboard.py`** — novo expander com métricas + gráfico de incerteza

## [0.3.0] — 2026-06-14

### Added

- **Testes E2E com Playwright** — `tests/test_dashboard_e2e.py` com 12 testes
  que cobrem: carregamento da página, seletor de ativos, KPI cards, navegação
  por abas (Overview, EDA, Decomposição, Forecast, Anomalias), troca de
  entidade, verificação de anomalia em tempo real, e screenshot da página.
  Dependências dev: `playwright` + `pytest-playwright`.

## [0.2.7] — 2026-06-14

### Fixed

- **`ValueError: x must have 2 complete cycles`** — `decompose_entity()` em
  `src/decompose.py` chamava `seasonal_decompose()` sem verificar se a série
  tinha dados suficientes. Adicionado guard `if len(series.dropna()) < period * 2`
  que retorna um dict com componentes vazios, que o `plot_decomposition` já
  trata graciosamente com `if series.dropna().empty: continue`.

## [0.2.6] — 2026-06-14

### Fixed

- **`StreamlitDuplicateElementId`** — todos os 16 `st.plotly_chart()` em
  `dashboard.py` agora recebem `key` único (ex: `"chart_series"`,
  `"chart_drawdown"`, etc.). Isso evita colisão de IDs automáticos quando
  múltiplas funções EDA retornam `go.Figure()` vazio (após guards all-NaN).

## [0.2.5] — 2026-06-14

### Fixed

- **`ValueError: negative dimensions are not allowed`** — `plot_acf_pacf` em
  `eda.py` quebrava com `nlags=-1` quando `series.dropna()` retornava vazio.
  Adicionados guards `if len(series) < 3: continue` e `if nlags < 1: continue`.
- **Auditoria complementar — 6 novas vulnerabilidades empty/NaN em `eda.py`:**
  - `plot_calendar_heatmap`: guard `if not entities` + `if df.dropna().empty`
  - `plot_monthly_returns_heatmap`: guard `if not entities` + `if df["Returns"].dropna().empty`
  - `plot_returns_with_context`: `next(..., None)` + `if r.empty: return fig`
  - `plot_volatility`: substituído `"vol" in dir()` por `all_vols` tracking
  - `plot_correlation`: guard `if not entities` + `if aligned.empty`

### Changed

- **API fallback** (`src/ingest.py`): `_ingest_from_api()` agora sempre tenta o
  download first, e se falha (ticker delistado, 404, erro de rede), faz fallback
  para CSV local do cache. Isso garante que tickers como `ELET3.SA` continuem
  funcionando se já foram baixados anteriormente.
- **Tick padrão removido**: `ELET3.SA` removido da lista default em `config.py`
  por estar consistentemente delistado (404).

## [0.2.4] — 2026-06-14

### Fixed

- **Auditoria geral de vulnerabilidades empty/NaN** — 10 locais corrigidos:

  **`src/eda.py` (4):**
  - `plot_seasonal_boxplot`: guard `if not df.empty` antes de `.groupby()`
  - `plot_distribution`: guard `if len(vals) == 0: continue` antes de
    `np.histogram` e `np.linspace(vals.min(), vals.max())`
  - `plot_drawdown`: guard `if not drawdown.dropna().empty` antes de
    `.idxmin()` e annotation
  - `plot_top_entities_comparison`: guard `if series.dropna().empty: continue`
    antes de `series.iloc[0]`

  **`src/dashboard.py` (5):**
  - KPI "Retorno Acum.": guard `if not series.dropna().empty` antes de
    `series.iloc[-1] / series.iloc[0]`
  - KPI "All-Time High": guard `if not series.dropna().empty` antes de
    `series.expanding().max().iloc[-1]` e `series.idxmax()`
  - Forecast tab: guard `if not series.dropna().empty` antes de
    `series.iloc[-1]` para `last_price`
  - Forecast tab: guard `if not fc["price_forecast"].empty` antes de
    `fc["price_forecast"].iloc[-1]`
  - Anomalias tab: guard `if not series.dropna().empty` no `default_price`

  **`src/preprocess.py` (1):**
  - `_resample_and_fill`: early return com log se `df[value_col].isna().all()`

## [0.2.3] — 2026-06-14

### Fixed

- **`ValueError: Encountered all NA values`** — `series.idxmax()` no dashboard
  falhava quando a série tinha linhas mas todos os valores eram NaN (575 gaps
  não preenchidos após resample + interpolação). Guard `if not series.empty`
  substituído por `if not series.dropna().empty` em `src/dashboard.py:102`.

## [0.2.2] — 2026-06-14

### Fixed

- **`IndexError: list index out of range`** — `_best_worst_entities()` em
  `src/eda.py` assumia que sempre haveria ao menos um ativo com dados
  suficientes para calcular retorno. Corrigido com guard `if not returns` e
  propagação de `None` para os callers (`plot_series` em `eda.py`, KPI cards
  em `dashboard.py`), que agora exibem "—" quando não há dados disponíveis.

## [0.2.1] — 2026-06-14

### Fixed

- **`TypeError: Cannot interpolate with str dtype`** — yfinance retorna colunas
  MultiIndex mesmo para ticker único; o CSV salvo continha o ticker como primeira
  linha de dados, convertendo `Close` para object dtype. Corrigido:
  - `src/ingest.py`: achatamento de MultiIndex com `droplevel(1)` e conversão
    explícita com `pd.to_numeric` ao selecionar `VALUE_COLUMN`.
  - `src/preprocess.py`: `pd.to_numeric(errors="coerce")` como safety net antes
    de `ffill`/`interpolate`.
- Cache CSV corrompido foi limpo para forçar novo download limpo.

## [0.2.0] — 2026-06-14

### Added (Data Storytelling — EDA)

- **Professional color palette** `STORY_COLORS` — palette temática de 10 cores
  para séries financeiras, substituindo as cores padrão do Plotly.
- **`plot_price_with_events()`** — gráfico de preço com anotações de eventos
  de mercado (COVID-19 crash, eleições, guerra Ucrânia), highlight do melhor
  e pior performer.
- **`plot_returns_with_context()`** — retornos com banda de volatilidade e
  linha de threshold (2 desvios padrão), anotações nos maiores desvios.
- **`plot_drawdown()`** — drawdown máximo desde o pico, com linha de -20% e
  anotações dos maiores drawdowns — narrativa visual de risco.
- **`plot_top_entities_comparison()`** — comparação de retorno acumulado entre
  top/bottom 3 entidades, com score final no hover.
- **`plot_monthly_returns_heatmap()`** — heatmap de retorno médio por mês/ano
  com escala verde-vermelho, revelando sazonalidade de retornos.

### Fixed (Precisão Estatística)

- **Q-Q plot** — substituída implementação manual com `np.random.normal` por
  `scipy.stats.probplot`, garantindo resultados determinísticos e precisos.
- **KDE overlay** — adicionada curva de densidade estimada sobre histogramas
  de distribuição.
- **ACF/PACF** — substituído OLS manual por `statsmodels.tsa.stattools.acf` e
  `pacf`, com banda de confiança de 95% (√n).

### Changed (Visual Design — Dashboard)

- **Título com hook** — "Brazilian Stocks — Time Series Analysis" → "Brazilian
  Stocks — Onde o Mercado está se movendo?"
- **KPI cards contextuais** — Valor Atual vs Período Anterior (delta %),
  substituindo métricas estáticas soltas.
- **Executive Summary** — cards de destaque com o melhor e pior ticker do
  período, retorno acumulado, e data do pico máximo — narrativa de "Setup →
  Descoberta → Ação".
- **Model Tab interpretado** — AIC/BIC agora acompanhados de interpretação em
  linguagem natural ("Quanto menor o AIC, melhor o ajuste — comparado aos
  outros ativos...").
- **Model comparison** — ranking visual dos modelos por AIC com barra
  horizontal colorida.
- **Anomalias com severidade** — gráfico de pizza da proporção de anomalias
  por severidade (low/medium/high), além da série temporal.
- **Drawdown no Overview** — gráfico de drawdown adicionado como segundo
  chart na visão geral, contando a história de risco do ativo.

### Removed

- `requirements.txt` — migrado para Poetry (`pyproject.toml` + `poetry.lock`).
- Funções duplicadas de plot inline no dashboard — agora reusa `eda.py`
  diretamente em vez de recriar figuras.
- `plot_acf_pacf` manual — substituído por implementação `statsmodels`.

## [0.1.0] — 2026-06-14

### Added

- Pipeline completo de séries temporais para ações brasileiras
- Ingestão via Yahoo Finance (yfinance) com cache CSV
- Pré-processamento com resample semanal e features (lags, rolling, calendário)
- 8 plots EDA (série, retornos, boxplot sazonal, distribuição, heatmap,
  correlação, ACF/PACF, volatilidade)
- Decomposição sazonal auto-detect (additive vs multiplicative)
- Detecção de outliers IQR batch + tempo real
- ARIMA/SARIMA com auto_arima (pmdarima) + diagnósticos
- Validação train/test split + TimeSeries CV (MAE, RMSE, MAPE, MASE)
- CLI orquestrador (argparse)
- Dashboard Streamlit com 6 abas
- AnomalyMonitor para integração contínua
- Testes unitários (10 testes, 100% passing)
- Gerenciamento de dependências via Poetry
- Licença MIT
