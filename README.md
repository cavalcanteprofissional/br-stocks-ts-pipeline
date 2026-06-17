<p align="center">
  <a href="https://www.youtube.com/watch?v=KxS8jGZ89RA">
    <img src="landing/src/assets/thumbnail.png" alt="BR Stocks" width="700" />
  </a>
</p>
<p align="center">
  <a href="https://www.youtube.com/watch?v=KxS8jGZ89RA">link do vídeo</a>
</p>

<h1 align="center">BR Stocks — Análise de Séries Temporais</h1>

<p align="center">
  <b>Pipeline automatizado</b> de forecasting multi-modelo, anomalias e visualização<br />
  para o mercado de ações brasileiro.
</p>

<p align="center">
  <a href="https://br-stocks-ts-pipeline-sca7v3vvdzvpfc42zdkxkg.streamlit.app/">
    <img src="https://img.shields.io/badge/Dashboard-Streamlit%20Cloud-1A56DB?style=flat-square&logo=streamlit" alt="Dashboard" />
  </a>
  <a href="https://cavalcanteprofissional.github.io/br-stocks-ts-pipeline/">
    <img src="https://img.shields.io/badge/Landing-GitHub%20Pages-0E9F6E?style=flat-square&logo=github" alt="Landing" />
  </a>
  <a href="https://github.com/cavalcanteprofissional/br-stocks-ts-pipeline/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License" />
  </a>
  <a href="https://github.com/cavalcanteprofissional/br-stocks-ts-pipeline/releases">
    <img src="https://img.shields.io/badge/Version-0.11.0-blue?style=flat-square" alt="Version" />
  </a>
</p>

---

## Fluxo

```mermaid
flowchart TD
    A["📡 Yahoo Finance<br/>(yfinance)"] --> B["⚙️ Pipeline offline<br/>ARIMA + Prophet + LSTM<br/>~35 min"]
    B --> C["📦 dashboard_data.json<br/>~4.31 MB"]
    C --> D["📊 Dashboard Streamlit<br/>(<2s load)"]
    C --> E["🎬 Landing Page<br/>(React + Vite)"]
    C --> F["📈 Gráficos de Resíduos<br/>Série + Histograma + Q-Q"]
    D --> G["Streamlit Cloud"]
    E --> H["GitHub Pages"]
```

---

## Sobre

Pipeline automatizado de séries temporais que baixa dados do Yahoo Finance, treina **3 modelos de forecasting** (ARIMA/SARIMA, Prophet e LSTM) e gera um JSON pré-computado para carregamento instantâneo no dashboard — sem chamadas de API, sem spinners, sem modelos rodando em runtime.

| Etapa | Descrição |
|-------|-----------|
| **Pipeline offline** | Baixa dados, pré-processa, treina ARIMA + Prophet + LSTM, gera forecasts com IC 95%, detecta anomalias e computa métricas de confiabilidade |
| **Comparação Multi-Modelo** | RMSE, SMAPE, R², MAE, MAPE side-by-side; walk-forward CV 5 folds; ranking visual do melhor modelo por ticker |
| **Gráficos de Resíduos** | Série temporal, histograma + KDE e Q-Q plot no expander de Métricas de Confiabilidade |
| **Serialização** | Tudo vira um JSON de ~4.31 MB — o dashboard só lê esse arquivo |
| **Dashboard instantâneo** | Abre em <2s — sem chamadas de API, sem spinner, sem modelos em runtime |
| **Landing page** | Scrollytelling com React + Vite para apresentar os insights de forma visual |

### Stack

| Camada | Tecnologia |
|--------|-----------|
| Pipeline | Python 3.11+, pandas 3.0+, statsmodels, pmdarima, Prophet 1.3+, PyTorch 2.12 |
| Dashboard | Streamlit 1.58+, Plotly |
| Landing Page | React 18, Vite, Chart.js, framer-motion |
| Dados | Yahoo Finance (`yfinance`) |
| Infra | Poetry, Streamlit Cloud, GitHub Pages |
| Testes | Playwright (E2E), pytest |

---

## Dados

### Origem

Os dados vêm da **Yahoo Finance** via biblioteca [`yfinance`](https://github.com/ranaroussi/yfinance). São baixados uma única vez pelo pipeline e armazenados em cache como CSV em `data/`.

### Tickers

9 ações representativas de diferentes setores do mercado brasileiro:

| Ticker | Empresa | Setor |
|--------|---------|-------|
| `PETR4.SA` | Petrobras | Óleo & Gás |
| `VALE3.SA` | Vale | Mineração |
| `ITUB4.SA` | Itaú Unibanco | Bancário |
| `BBDC4.SA` | Bradesco | Bancário |
| `ABEV3.SA` | Ambev | Bebidas |
| `WEGE3.SA` | WEG | Indústria |
| `BBAS3.SA` | Banco do Brasil | Bancário |
| `B3SA3.SA` | B3 | Financeiro (Bolsa) |
| `RENT3.SA` | Localiza | Locação de Veículos |

### Período e Frequência

| Propriedade | Valor |
|-------------|-------|
| Início | 2015-01-01 |
| Frequência original | Diária |
| Frequência de modelagem | Semanal (`resample` com `.last()`) |
| Dados disponíveis | ~10 anos → ~520 semanas |

### Pipeline de Transformação

| Etapa | Descrição |
|-------|-----------|
| **Ingestão** | CSV bruto por ticker em `data/`; fallback para cache se ticker delistado |
| **Preprocessamento** | Série semanal com `Close`, log-retornos, `returns`, `drawdown` |
| **EDA** | 11 gráficos Plotly (série, retornos, sazonalidade, correlação, volatilidade, ACF/PACF, heatmap mensal, drawdown) |
| **Decomposição** | Tendência + Sazonalidade + Resíduo (additive/multiplicativo auto-detectado) |
| **Modelos** | ARIMA/SARIMA (`auto_arima`), Prophet (Meta), LSTM (PyTorch, lookback=12, 50 epochs) |
| **Comparação** | RMSE, SMAPE, R², MAE, MAPE entre os 3 modelos; walk-forward CV 5 folds; ranking visual |
| **Forecast** | Previsão com IC 95% (12 semanas) para cada modelo |
| **Outliers** | Anomalias batch (IQR sobre resíduos) + detecção em tempo real |
| **Diagnóstico** | Ljung-Box, Jarque-Bera, RMSE, MAE, MAPE, SMAPE, R², walk-forward CV |
| **Resíduos** | Série temporal, histograma + KDE, Q-Q plot para cada modelo |

---

## Modelos

| Modelo | Pacote | Destaque |
|--------|--------|----------|
| **ARIMA/SARIMA** | `pmdarima` + `statsmodels` | Ordem `(p,d,q)(P,D,Q,s)` otimizada por `auto_arima` |
| **Prophet** | `prophet` (Meta) | Changepoint prior = 0.05, sazonalidade semanal + anual |
| **LSTM** | PyTorch 2.12 | Lookback=12, 2 camadas, dropout=0.2, 50 epochs |

> Prophet venceu em 6/9 tickers (RMSE), ARIMA em 2/9, LSTM consistentemente em 3º. Pipeline ~35 min para 9 tickers × 3 modelos.

---

## Começando

### Pré-requisitos

- Python >=3.11
- [Poetry](https://python-poetry.org/) — instale com `pipx install poetry`
- Node.js 18+

### Instalação

```bash
git clone https://github.com/cavalcanteprofissional/br-stocks-ts-pipeline.git
cd br-stocks-ts-pipeline

# Dependências Python
poetry install

# Dependências da Landing Page
cd landing && npm install && cd ..
```

> PyTorch 2.12 é instalado via pip separadamente (conflito com `triton` no Poetry):
> `pip install torch==2.12.0`

### Pipeline (gerar JSON)

```bash
poetry run python scripts/generate_dashboard_data.py
```

> ~35 minutos para 9 tickers × 3 modelos. Resultado em `data/dashboard_data.json` (~4.31 MB).

### Dashboard Local

```bash
poetry run streamlit run src/dashboard.py
```

> Carrega em **<2s** — o JSON está pré-computado.

### Landing Page Local

```bash
cd landing
npm run dev
```

Acesse `http://localhost:5173/br-stocks-ts-pipeline/`

### Extrair dados para Landing Page

```bash
poetry run python scripts/extract_landing_data.py
cd landing && npm run build
```

Gera `landing/public/landing_data.json` (~97 KB).

---

## Estrutura

```
st/
├── data/                          # Cache CSV + dashboard_data.json
├── landing/                       # React + Vite landing page
│   ├── public/
│   │   └── landing_data.json      # Subset ~97 KB
│   └── src/
│       ├── assets/                # hero-bg.mp4, logo.png, thumbnail.png
│       ├── components/
│       │   ├── charts/            # RankingBar, DrawdownChart, CorrelationMatrix, ForecastChart
│       │   ├── AboutCard.jsx
│       │   ├── CTASection.jsx
│       │   ├── ForecastSection.jsx
│       │   ├── HeroSection.jsx
│       │   ├── MarketHealthSection.jsx
│       │   ├── Navbar.jsx
│       │   ├── RankingSection.jsx
│       │   └── ScrollReveal.jsx
│       ├── hooks/
│       │   └── useCountUp.js
│       ├── data/
│       │   └── loadData.js
│       └── styles/
│           └── globals.css
├── scripts/
│   ├── generate_dashboard_data.py # Pipeline completo (ARIMA + Prophet + LSTM)
│   ├── extract_landing_data.py    # Subset para landing
│   ├── debug_yf.py                # Debug Yahoo Finance
│   └── debug_csv.py               # Debug CSV
├── src/
│   ├── config.py                  # Configuração central (incl. LSTM params)
│   ├── ingest.py                  # Download yfinance + cache + fallback
│   ├── preprocess.py              # Resample, log-retornos, features
│   ├── eda.py                     # 11 gráficos Plotly
│   ├── decompose.py               # Decomposição sazonal
│   ├── outliers.py                # Detecção batch + real-time
│   ├── modeling.py                # Orquestração ARIMA (legado)
│   ├── validation.py              # Métricas, CV, train/test split
│   ├── anomaly_monitor.py         # Monitor contínuo de anomalias
│   ├── pipeline.py                # CLI orquestrador completo
│   ├── dashboard.py               # App Streamlit
│   └── models/
│       ├── __init__.py            # MODEL_REGISTRY (ARIMA, Prophet, LSTM)
│       ├── base.py                # BaseModel ABC + compute_metrics
│       ├── arima_model.py         # Wrapper auto_arima
│       ├── prophet_model.py       # Wrapper Meta Prophet
│       └── lstm_model.py          # LSTM PyTorch
├── tests/
│   ├── test_preprocess.py
│   ├── test_outliers.py
│   ├── test_modeling.py
│   └── test_dashboard_e2e.py      # Playwright E2E (12 testes)
├── CHANGELOG.md
├── TODO.md
└── README.md
```

---

## Testes

```bash
# Unitários
poetry run pytest tests/ -v

# E2E (Playwright)
poetry run pytest tests/test_dashboard_e2e.py -v
```

> 12 testes E2E com Playwright, 11 passando, 1 xfail (limitação do Streamlit em troca de tab).

---

## Deploy

### Dashboard (Streamlit Cloud)

O deploy é automático via GitHub. O segredo: `data/dashboard_data.json` está commitado (exceção no `.gitignore`), então o Cloud carrega o JSON instantaneamente. Caso o JSON não exista, o pipeline roda como fallback via `subprocess`.

### Landing Page (GitHub Pages)

```bash
cd landing
npm run build
npm run deploy
```

> ⚠️ O `.gitignore` raiz tem `data/` — por isso o JSON da landing fica em `public/landing_data.json`, não em `public/data/`.

---

## Roadmap

### Concluído

- [x] Pipeline offline → JSON
- [x] Dashboard instantâneo (<2s)
- [x] Landing page scrollytelling (React + Vite)
- [x] Navbar + Footer estilo SANOVA
- [x] About Me Card com tech tags e stats GitHub
- [x] Vídeo background na Hero Section
- [x] Comparação Multi-Modelo (ARIMA vs Prophet vs LSTM)
- [x] Gráficos de Resíduos (série, histograma, Q-Q plot)
- [x] Métricas de Confiabilidade (RMSE, MAE, MAPE, SMAPE, R², Ljung-Box, Jarque-Bera)
- [x] Walk-forward Cross-Validation (5 folds)
- [x] Testes E2E com Playwright (12 testes)
- [x] Deploy Streamlit Cloud com fallback automático
- [x] Deploy GitHub Pages

### Melhorias Futuras

| Prioridade | Item |
|-----------|------|
| Alta | Cache incremental do JSON (~35 min → ~30s) |
| Média | CI/CD com GitHub Actions |
| Média | Monitor de integração contínua (AnomalyMonitor em produção) |
| Média | Dark/light theme toggle no dashboard |
| Média | Gráficos de resíduos expandidos (subseção dedicada) |
| Baixa | XGBoost/Random Forest como 4º modelo |
| Baixa | Streamlit multi-página (visão geral vs detalhe) |
| Baixa | i18n (português/inglês) |

---

## Autor

<p align="center">
  <b>Lucas Cavalcante dos Santos</b><br />
  dev dados com py, lm, streamlit, folium, pytorch, opencv<br />
  <a href="https://github.com/cavalcanteprofissional">GitHub</a> ·
  <a href="https://cavalcanteprofissional.github.io/portfolio/">Portfólio</a> ·
  <a href="https://linkedin.com/in/cavalcante-Lucas">LinkedIn</a>
</p>

---

## Licença

MIT
