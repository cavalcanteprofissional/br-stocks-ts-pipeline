# Changelog

All notable changes to this project will be documented in this file.

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
