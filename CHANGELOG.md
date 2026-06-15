# Changelog

All notable changes to this project will be documented in this file.

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
