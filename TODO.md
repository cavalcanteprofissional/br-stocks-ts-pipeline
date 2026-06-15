# TODO

## Erro: `TypeError: Cannot interpolate with str dtype`

**Arquivo:** `src/preprocess.py:47` — `_resample_and_fill()`

### Causa

O `resample().asfreq()` introduz NaN em colunas numéricas. No pandas >=3.0, o dtype da coluna pode mudar para `object`/`string` nesse processo, e o `interpolate(method="linear")` não aceita esse dtype.

### Plano

1. **`src/preprocess.py`** — em `_resample_and_fill()`, converter a coluna para numérico antes do `ffill`/`interpolate`:
   ```python
   df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
   df[value_col] = df[value_col].ffill(limit=2)
   df[value_col] = df[value_col].interpolate(method="linear", limit_direction="both")
   ```

2. **Limpar cache corrompido** — deletar CSVs em `data/` para forçar novo download com dados limpos.

3. **Testar** — executar `poetry run streamlit run src/dashboard.py` e verificar se o erro persiste.

---

## Erro: `IndexError: list index out of range`

**Arquivo:** `src/eda.py:31` — `_best_worst_entities()`

### Causa

`_best_worst_entities()` retorna `sorted_ents[0], sorted_ents[-1]` sem verificar se `sorted_ents` está vazia. Se nenhum ativo tem dados suficientes (≤1 ponto após dropna), o dicionário `returns` fica vazio e `sorted_ents = []`.

### Plano

1. **`src/eda.py:30`** — guard contra `returns` vazio:
   ```python
   if not returns:
       return None, None, {}
   ```

2. **`src/eda.py:47-55`** (`plot_series`) — pular highlight de best/worst se for `None`:
   ```python
   if best_id is not None:
       for eid, color, label in [(best_id, "#0E9F6E", "Best Performer"), ...]:
           ...
   ```

3. **`src/dashboard.py:88-98`** — exibir KPI alternativo se `best_id` for `None`:
   ```python
   if best_id is not None:
       kpi_card(exec_col2, "Melhor Ativo", best_id, ...)
       kpi_card(exec_col3, "Pior Ativo", worst_id, ...)
   else:
       kpi_card(exec_col2, "Melhor Ativo", "—", ...)
       kpi_card(exec_col3, "Pior Ativo", "—", ...)
   ```

---

## Erro: `ValueError: Encountered all NA values`

**Arquivo:** `src/dashboard.py:102` — `main()`

### Causa

O resample semanal introduz gaps que `ffill(limit=2)` + `interpolate()` não conseguem preencher completamente (575 gaps restantes por ativo). A série não está vazia (`len > 0`) mas todos os valores são `NaN`. O guard `if not series.empty` não detecta isso — `empty` retorna `False` quando há linhas mesmo que todas sejam NaN.

### Plano

1. **`src/dashboard.py:102`** — trocar `if not series.empty` por `if not series.dropna().empty`:
   ```python
   peak_date = series.idxmax().strftime("%Y-%m") if not series.dropna().empty else "—"
   ```

---

## Erro: `ValueError: attempt to get argmin of an empty sequence` + auditoria geral

**Arquivos:** `src/eda.py`, `src/dashboard.py`, `src/preprocess.py`

### Causa Raiz

575 gaps NaN permanecem após resample semanal + `ffill(limit=2)` + `interpolate()`. Isso faz com que séries não estejam vazias (`len > 0`) mas todos os valores sejam NaN, quebrando `.idxmin()`, `.idxmax()`, `.iloc[0]`, `.iloc[-1]`, `.min()/.max()` etc.

### Auditoria — 10 vulnerabilidades encontradas

| # | Arquivo | Linha | Padrão | Risco |
|---|---------|-------|--------|-------|
| 1 | `eda.py` | 129 | `.iloc[0]` em grupo vazio | IndexError |
| 2 | `eda.py` | 149+156 | `.min()/.max()` em ndarray vazio | ValueError |
| 3 | `eda.py` | 298 | `.idxmin()` em série all-NaN | ValueError |
| 4 | `eda.py` | 323 | `.iloc[0]` em série all-NaN | IndexError |
| 5 | `dashboard.py` | 88 | `.iloc[-1]/.iloc[0]` em série all-NaN | IndexError |
| 6 | `dashboard.py` | 101 | `.iloc[-1]` em expanding all-NaN | IndexError |
| 7 | `dashboard.py` | 206 | `.iloc[-1]` em série all-NaN | IndexError |
| 8 | `dashboard.py` | 211 | `.iloc[-1]` em forecast vazio | IndexError |
| 9 | `dashboard.py` | 274 | `.iloc[-1]` em série all-NaN | IndexError |
| 10 | `preprocess.py` | 47-48 | `ffill`/`interpolate` em all-NaN | Propagação silenciosa |

### Plano de Correção

Para cada vulnerabilidade, adicionar guard `if not series.dropna().empty:` antes do acesso, ou `continue`/fallback quando a série estiver vazia.

1. **`src/eda.py:119-130`** — `if not df.empty:` antes do `df.groupby()`
2. **`src/eda.py:148-149`** — `if len(vals) == 0: continue` após `dropna().values`
3. **`src/eda.py:297-302`** — `if not drawdown.dropna().empty:` antes do annotation
4. **`src/eda.py:321-323`** — `if series.dropna().empty: continue` antes de `series.iloc[0]`
5. **`src/dashboard.py:88`** — `if not series.dropna().empty: ret = ... else: ret = 0.0`
6. **`src/dashboard.py:101`** — `if not series.dropna().empty: peak_val = ... else: peak_val = 0.0`
7. **`src/dashboard.py:206`** — `last_price = series.iloc[-1] if not series.dropna().empty else 0.0`
8. **`src/dashboard.py:211`** — `if not fc["price_forecast"].empty: fc_end_val = ... else: fc_end_val = 0.0`
9. **`src/dashboard.py:274`** — `default_price = float(series.iloc[-1]) if not series.dropna().empty else 0.0`
10. **`src/preprocess.py:47-48`** — `if df[value_col].isna().all(): logger.error(...); return df`

---

## Rodada 3: `ValueError: negative dimensions are not allowed` + fallback API

**Arquivo:** `src/eda.py:232` — `plot_acf_pacf()`

### Causa

`series.dropna()` retorna série vazia → `len(series) = 0` → `nlags = min(30, 0//2-1) = -1` → `acf(series, nlags=-1)` → `np.ones(-1)` → `ValueError`.

### Auditoria — 6 novas vulnerabilidades em `eda.py`

| # | Função | Linha | Padrão | Risco |
|---|--------|-------|--------|-------|
| 1 | `plot_calendar_heatmap` | 183 | `list(entities.keys())[0]` em dict vazio | **CRÍTICO** — `IndexError` |
| 2 | `plot_monthly_returns_heatmap` | 356 | `list(entities.keys())[0]` em dict vazio | **CRÍTICO** — `IndexError` |
| 3 | `plot_acf_pacf` | 229-232 | série vazia → `nlags=-1` → `acf()` | **CRÍTICO** — `ValueError` |
| 4 | `plot_returns_with_context` | 89 | `next()` sem default → `StopIteration` | **ALTO** |
| 5 | `plot_volatility` | 268 | `vol` do último entidade usada como threshold | **ALTO** — threshold enganoso |
| 6 | `plot_correlation` | 203-206 | DataFrame vazio → erro `px.imshow` | **MÉDIO** |

### Plano de Correção (6 guards)

| # | Função | Fix |
|---|--------|-----|
| 1 | `plot_calendar_heatmap` | `if not entities: return go.Figure()` + `if df.dropna().empty: return go.Figure()` |
| 2 | `plot_monthly_returns_heatmap` | `if not entities: return go.Figure()` + `if df["Returns"].dropna().empty: return go.Figure()` |
| 3 | `plot_acf_pacf` | `if len(series) < 3: continue` + `if nlags < 1: continue` |
| 4 | `plot_returns_with_context` | `next(..., None)` + `if r.empty: return fig` |
| 5 | `plot_volatility` | flag `has_vol` + `combined_vol = pd.concat(all_vols).dropna()` |
| 6 | `plot_correlation` | `if aligned.empty: return go.Figure()` |

### API Fallback

**Problema:** Tickers delistados (ex: `ELET3.SA`) retornam 404 da API e são pulados. Se o cache local foi limpo, não há dados de fallback.

**Solução:** Modificar `_ingest_from_api()` para:
1. Tentar download da API
2. Se API falhar (dados vazios), tentar carregar CSV local do cache
3. Se existir CSV local, usar mesmo que desatualizado
4. Se não existir, pular ticker com warning

---

## Rodada 4: `StreamlitDuplicateElementId` — plotly_chart sem key única

**Arquivo:** `src/dashboard.py`

### Causa

Quando funções EDA retornam `go.Figure()` vazio (devido aos guards all-NaN),
múltiplos `st.plotly_chart()` produzem figuras estruturalmente idênticas.
Streamlit 1.58+ gera IDs automáticos baseados no tipo + parâmetros, e IDs
duplicados disparam `StreamlitDuplicateElementId`.

### Plano

Adicionar `key` único a cada `st.plotly_chart()` no `dashboard.py`:

| Linha | Chart | key |
|-------|-------|-----|
| 114 | `plot_series` | `"chart_series"` |
| 115 | `plot_drawdown` | `"chart_drawdown"` |
| 120 | `plot_returns_with_context` | `"chart_returns"` |
| 121 | `plot_top_entities_comparison` | `"chart_top_vs_bottom"` |
| 125 | `plot_seasonal_boxplot` | `"chart_seasonal"` |
| 127 | `plot_calendar_heatmap` | `"chart_calendar"` |
| 129 | `plot_distribution` | `"chart_distribution"` |
| 133 | `plot_correlation` | `"chart_correlation"` |
| 135 | `plot_volatility` | `"chart_volatility"` |
| 137 | `plot_monthly_returns_heatmap` | `"chart_monthly"` |
| 138 | `plot_acf_pacf` | `"chart_acf_pacf"` |
| 146 | `decomp fig` | `"chart_decomp"` |
| 202 | `model comp fig` | `"chart_model_comp"` |
| 241 | `forecast fig` | `"chart_forecast"` |
| 276 | `outliers fig` | `"chart_outliers"` |

---

## Rodada 5: `ValueError: x must have 2 complete cycles requires 104 observations`

**Arquivo:** `src/decompose.py:40` — `decompose_entity()`

### Causa

`auto_detect_model()` tem guard `if len(series) < period * 2: return "additive"`,
mas `decompose_entity()` não — mesmo que `auto_detect_model` retorne cedo,
`seasonal_decompose()` é chamado com a série vazia, exigindo no mínimo
2 ciclos completos (104 obs para período = 52).

### Plano

Adicionar guard em `decompose_entity()` antes de `seasonal_decompose`:
```python
series_clean = series.dropna()
if len(series_clean) < period * 2:
    return {
        "observed": series, "trend": pd.Series(dtype=float),
        "seasonal": pd.Series(dtype=float), "resid": pd.Series(dtype=float),
        "model": "additive", "period": period,
    }
```

---

## Rodada 6: Testes E2E com Playwright

**Arquivo:** `tests/test_dashboard_e2e.py`

### Objetivo

Testar que o dashboard Streamlit carrega, renderiza dados corretamente e a
pipeline completa funciona (download + preprocess + exibição).

### Plano

1. **Adicionar dependências dev:** `playwright` + `pytest-playwright`
2. **Instalar browser Chromium:** `playwright install chromium`
3. **Escrever testes E2E:**

   | Teste | O que verifica |
   |-------|---------------|
   | `test_dashboard_loads` | Página carrega, título contém "Brazilian Stocks" |
   | `test_entity_selector` | Sidebar tem selectbox com tickers |
   | `test_kpi_cards_render` | KPI cards "Retorno Acum.", "Melhor Ativo", "All-Time High" existem |
   | `test_tab_navigation` | Todas as 6 abas estão presentes |
   | `test_overview_charts` | Aba Overview renderiza charts |
   | `test_eda_charts_render` | Aba EDA renderiza gráficos |
   | `test_decomp_tab` | Aba Decomposição carrega sem erro |
   | `test_forecast_tab` | Aba Forecast carrega e mostra projeção |
   | `test_anomalies_tab` | Aba Anomalias carrega e tem input de verificação |
   | `test_entity_switch` | Trocar entidade no selectbox atualiza os dados |
   | `test_realtime_anomaly` | Botão "Verificar Anomalia" funciona e mostra resultado |

4. **Adicionar ao `pyproject.toml`:** Config do pytest para reconhecer `asyncio_mode = "auto"`

---

## Rodada 7: Métricas de Confiabilidade do Forecast

**Arquivos:** `scripts/generate_dashboard_data.py`, `src/dashboard.py`, `src/modeling.py`

### Objetivo

Atualmente o dashboard exibe AIC, BIC e IC 95% do forecast, mas não há métricas
de confiabilidade do modelo — o usuário não sabe se o modelo tem resíduos
autocorrelacionados (má especificação), nem quão precisas são as previsões.

### Plano

| # | Item | Arquivo | Implementação |
|---|------|---------|---------------|
| 1 | **Residual diagnostics** | `scripts/generate_dashboard_data.py` | Após `auto_arima`, chamar `model_diagnostics()` (já existe em `src/modeling.py`). Exportar `ljung_box_pval`, `jarque_bera_pval`, `has_residual_autocorrelation` no dicionário do modelo |
| 2 | **In-sample RMSE/MAE/MAPE** | `scripts/generate_dashboard_data.py` | `preds = model.predict_in_sample()`; comparar com `ret.values`; calcular rmse, mae, mape. Exportar no dict do modelo |
| 3 | **Walk-forward CV** | `scripts/generate_dashboard_data.py` | Expanding window: 3 cortes (60%, 70%, 80% dos dados). Treinar `auto_arima` em cada janela, forecast horizon, calcular erro. Exportar `cv_rmse`, `cv_mae` |
| 4 | **Interval width por horizonte** | `scripts/generate_dashboard_data.py` | Média de `price_upper - price_lower` por passo k. Exportar `avg_ci_width` como lista |
| 5 | **Exibir no Dashboard** | `src/dashboard.py` (aba Forecast) | Novo bloco "📊 Métricas de Confiabilidade" com dataframe + badges |
| 6 | **Badge de especificação** | `src/dashboard.py` | Se `has_residual_autocorrelation` = False → badge verde "✅ Resíduos ok"; se True → badge vermelho "⚠️ Possível má especificação" |
| 7 | **Regenerar JSON** | CLI | `poetry run python scripts/generate_dashboard_data.py` |

---

## Rodada 8: Data Storytelling — Layout Métricas de Confiabilidade

**Arquivo:** `src/dashboard.py:204-237`

### Problemas do Layout Atual

1. **Data dump** — métricas jogadas em colunas sem hierarquia nem contexto
2. **`delta` abusado** — badge de texto "✅ Resíduos ok" dentro de `metric(delta=...)` confunde
3. **Sem agrupamento** — RMSE/MAE/MAPE (qualidade do fit) misturado com Ljung-Box (diagnóstico residual)
4. **Sem progressão narrativa** — não conta uma história (Setup → Conflito → Resolução)
5. **CV RMSE solto** — `st.metric` avulso sem contexto de comparação com in-sample
6. **MAPE em coluna quebrada** — grid `col_m1..col_m3` quebra com `if` separado para MAPE

### Plano

| Ordem | Seção | Elementos | Princípio Data Storytelling |
|-------|-------|-----------|------------------------------|
| 1 | **Veredito** | `✅ Modelo confiável` / `⚠️ Requer atenção` com caption resumo | Hook — "front-load the key insight" |
| 2 | **📈 Ajuste do Modelo** | RMSE / MAE / MAPE | Data — "the evidence" |
| 3 | **🔬 Diagnóstico Resíduos** | Ljung-Box p-valor + badge textual, Jarque-Bera p-valor | Narrative — "the context" |
| 4 | **🔄 Validação Cruzada** | CV RMSE vs In-sample + delta % + interpretação | Contrast — "compare this/that" |
| 5 | **📉 Incerteza Horizonte** | Gráfico + anotação Passo 1→52 + caption de alerta | Visuals — "show, don't tell" |

### Mudanças Técnicas

1. **Remover** `metric(delta=lb_badge)` — badge textual vira `st.markdown()` separado
2. **Adicionar** `st.markdown(f"### {verdict_emoji} {verdict_text}")` no topo com caption
3. **Agrupar** em `st.columns(2)` aninhados: lado esquerdo="Ajuste", direito="Diagnóstico"
4. **Comparar CV vs in-sample** em uma linha com delta interpretado ("✅ Modelo generaliza bem")
5. **Anotar gráfico CI** com largura do primeiro e último passo + % de crescimento

### Detalhamento Técnico

#### 1. Residual diagnostics (em `generate_dashboard_data.py`)
```python
from src.modeling import model_diagnostics
...
diag = model_diagnostics(model, ret)
models_data[eid].update({
    "ljung_box_pval": _safe_float(diag["ljung_box_pvalue"]),
    "jarque_bera_pval": _safe_float(diag["jarque_bera_pval"]),
    "has_residual_autocorrelation": diag["has_residual_autocorrelation"],
})
```

#### 2. In-sample metrics
```python
preds = model.predict_in_sample()
residuals = ret.values - preds
n = len(residuals)
rmse = float(np.sqrt(np.mean(residuals**2)))
mae = float(np.mean(np.abs(residuals)))
mape = float(np.mean(np.abs(residuals / (ret.values + 1e-10)))) * 100
```

#### 3. Walk-forward CV
```python
cv_errors = []
for split in [0.6, 0.7, 0.8]:
    cutoff = int(len(ret) * split)
    train = ret.iloc[:cutoff]
    test = ret.iloc[cutoff:cutoff + FORECAST_HORIZON]
    if len(test) < 2:
        continue
    m = auto_arima(train, ...)
    preds = m.predict(n_periods=len(test))
    cv_errors.append(float(np.sqrt(np.mean((preds - test.values)**2))))
cv_rmse = float(np.mean(cv_errors)) if cv_errors else None
```

#### 4. Dashboard display
```python
if fc_data and "rmse" in fc_data:
    with st.expander("📊 Métricas de Confiabilidade", expanded=False):
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("RMSE (in-sample)", f"{fc_data['rmse']:.4f}")
        col_m2.metric("MAE", f"{fc_data['mae']:.4f}")
        col_m3.metric("MAPE", f"{fc_data['mape']:.2f}%")
        
        col_m4, col_m5 = st.columns(2)
        lb_badge = "✅ Resíduos ok" if not fc_data.get("has_residual_autocorrelation", True) else "⚠️ Possível má especificação"
        col_m4.metric("Ljung-Box", f"p={fc_data['ljung_box_pval']:.4f}", delta=lb_badge)
        col_m5.metric("Jarque-Bera", f"p={fc_data['jarque_bera_pval']:.4f}")
        
         if fc_data.get("cv_rmse"):
            st.metric("RMSE (Walk-Forward CV)", f"{fc_data['cv_rmse']:.4f}")

---

## Rodada 9: Landing Page Scrollytelling com React + Vite

**Novo diretório:** `st/landing/` — SPA React independente

### Objetivo

Landing page scrollytelling que conta a história dos dados do dashboard de forma
mais sintética e visual, com hero section + scroll reveal + highlights animados.

### Stack

| Camada | Tecnologia | Motivo |
|--------|------------|--------|
| Framework | React 18 + Vite | SPA estática, rápida, familiar |
| Gráficos | Chart.js + react-chartjs-2 | Heatmap, bar, line com bom controle visual |
| Animações | framer-motion | Scroll reveal, count-up, fade-in |
| Scroll | Intersection Observer API (nativo) | Gatilho de seções sem lib extra |
| Dados | Subset JSON (~200KB) vs 3.24MB | Carregamento instantâneo |
| Deploy | GitHub Pages (gh-pages) | Gratuito, integrado ao repo |

### Estrutura de Diretórios

```
st/landing/
├── public/data/landing_data.json   # Subset extraído por script
├── src/
│   ├── components/
│   │   ├── HeroSection.jsx
│   │   ├── RankingSection.jsx
│   │   ├── MarketHealthSection.jsx
│   │   ├── ForecastSection.jsx
│   │   ├── CTASection.jsx
│   │   ├── ScrollReveal.jsx
│   │   └── charts/
│   │       ├── RankingBar.jsx
│   │       ├── CorrelationMatrix.jsx
│   │       ├── ForecastChart.jsx
│   │       └── DrawdownChart.jsx
│   ├── hooks/
│   │   └── useCountUp.js
│   ├── data/
│   │   └── loadData.js
│   ├── styles/
│   │   └── globals.css
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── vite.config.js
└── package.json
```

### Seções e Narrativa

| # | Seção | Conteúdo | Elemento-chave |
|---|-------|----------|----------------|
| 1 | **Hero** | Headline + subtítulo + count-up PETR4 +1.135% + scroll arrow | Count-up animado do best performer |
| 2 | **Ranking** | Bar chart horizontal sorted por retorno total + callout best/worst | "PETR4 rendeu 27x mais que ABEV3" |
| 3a | **Risco** | Drawdown chart + máximo drawdown em destaque | "O maior tombo foi de -XX%" |
| 3b | **Correlação** | Heatmap matriz de correlação + insight textual | "Bancos andam juntos; commodities seguem ciclo próprio" |
| 3c | **Sazonalidade** | Monthly returns heatmap + meses destaque | "Meses X e Y são historicamente mais fortes" |
| 4 | **Forecast** | Line chart preço + IC 95% + badge confiabilidade | "✅ Modelo confiável — Ljung-Box p=0.86" |
| 5 | **CTA** | "Explore o Dashboard Completo" + link + footer | Botão para Streamlit |

### Técnica de Scrollytelling

- Cada seção ocupa `100vh` com `scroll-snap-type: y mandatory` no container
- `ScrollReveal.jsx` wrapper → `motion.div` com `whileInView` da framer-motion
- Números fazem count-up via `useCountUp.js` hook com `requestAnimationFrame`
- Gráficos fade-in + slide-up ao entrar no viewport
- Seta animada no hero indica continuidade

### Script de Extração: `scripts/extract_landing_data.py`

Lê `data/dashboard_data.json`, extrai apenas:

```python
landing_data = {
    "metadata": { ... },
    "kpis": { "overall": ..., "entities": ... },
    "forecast": { ... },        # price_forecast, price_lower/upper, metrics, badge
    "charts": {
        "correlation": ...,
        "monthly_returns": ...,
        "drawdown": ...,
    },
    "series": {                 # apenas Close do best + worst + current entity
        "best": ..., "worst": ..., "current": ...
    }
}
```

Saída: `landing/public/data/landing_data.json`

### Ordem de Implementação

1. TODO.md — registrar plano (esta tarefa)
2. `scripts/extract_landing_data.py` — criar e executar
3. `npm create vite@latest landing -- --template react` — scaffold
4. `landing/package.json` — adicionar dependências (chart.js, react-chartjs-2, framer-motion)
5. `landing/src/styles/globals.css` — tema escuro, scroll-snap, tipografia
6. `landing/src/hooks/useCountUp.js` — hook de animação numérica
7. `landing/src/components/ScrollReveal.jsx` — wrapper framer-motion
8. `landing/src/data/loadData.js` — fetch + parse do JSON
9. `landing/src/components/charts/*.jsx` — 4 componentes de gráfico
10. `landing/src/components/HeroSection.jsx`
11. `landing/src/components/RankingSection.jsx`
12. `landing/src/components/MarketHealthSection.jsx`
13. `landing/src/components/ForecastSection.jsx`
14. `landing/src/components/CTASection.jsx`
15. `landing/src/App.jsx` — montar tudo
16. `landing/src/main.jsx` — entry point
17. `landing/vite.config.js` — base path para GitHub Pages
18. `npm run build` — testar build
19. CHANGELOG.md — v0.6.0
```

---

## Rodada 10: Fix — Card "Correlação entre Ativos" vazio

**Arquivos:** `scripts/extract_landing_data.py`, `landing/src/components/charts/CorrelationMatrix.jsx`

### Problema

O card "Correlação entre Ativos" renderiza vazio porque:

1. **Plotly serializa arrays como typed arrays binários** (base64 `{dtype, bdata}`) em vez de listas JSON. O `z` da correlação chega como `{dtype: "f8", bdata: "AAAA..."}` em vez de `[[1.0, 0.8, ...], ...]`.
2. **Chart.js scatter não funciona para matriz de correlação** — scatter com `type: "category"` não renderiza corretamente; o componente fica em branco.

### Plano

| # | O quê | Arquivo | Mudança |
|---|-------|---------|---------|
| 1 | Decodificar typed arrays | `scripts/extract_landing_data.py` | Adicionar `_decode_typed_array()` que converte `{dtype, bdata}` → lista Python via `np.frombuffer` + `base64.b64decode` |
| 2 | Reshape matriz z | `scripts/extract_landing_data.py` | Se z for flat (81 = 9×9), reshape para `[[...], [...], ...]` |
| 3 | Substituir Chart.js por HTML grid | `landing/src/components/charts/CorrelationMatrix.jsx` | Remover Chart.js scatter. Renderizar tabela CSS grid com cells coloridas por valor, tooltip com `title` |
| 4 | Re-extrair dados | CLI | `poetry run python scripts/extract_landing_data.py` |
| 5 | Rebuild | CLI | `cd landing && npm run build` |
| 6 | CHANGELOG | `CHANGELOG.md` | v0.6.1

---

## Rodada 11: Fix — JSON inválido (NaN) na landing page

**Arquivo:** `scripts/extract_landing_data.py`

### Problema

A landing page exibe "Erro ao carregar dados — Unexpected token 'N'" porque o JSON
contém `NaN` literais, que não são válidos no formato JSON.

### Causa

O heatmap `monthly_returns` do Plotly armazena `NaN` na matriz z para meses sem
dado (meses futuros, combinações ano/mês sem observação). Ao decodificar o typed
array com `np.frombuffer`, esses NaN são preservados. `json.dump` com
`allow_nan=True` (default) serializa `float('nan')` como `NaN` literal — que o
`fetch`/`JSON.parse` no navegador rejeita.

### Plano

| # | Mudança | Local | Detalhes |
|---|---------|-------|----------|
| 1 | `_decode_typed_array` | `scripts/extract_landing_data.py` | Substituir NaN por None na lista retornada |
| 2 | `_sanitize()` | `scripts/extract_landing_data.py` | Função recursiva que percorre dict/list e troca `float('nan')` por `None` — safety net |
| 3 | Aplicar sanitizer | `scripts/extract_landing_data.py::main()` | `landing = _sanitize(landing)` antes de `json.dump` |
| 4 | Re-extrair + rebuild | CLI | `poetry run python scripts/extract_landing_data.py && cd landing && npm run build` |
| 5 | CHANGELOG | `CHANGELOG.md` | v0.6.2

---

## Rodada 12: Fix — Deploy Streamlit Cloud sem dashboard_data.json

**Arquivos:** `.gitignore`, `src/dashboard.py`

### Problema

`data/` está no `.gitignore` → `dashboard_data.json` não sobe para o Streamlit Cloud →
`FileNotFoundError: data/dashboard_data.json` no deploy.

### Solução Híbrida

| # | Mudança | Arquivo | Detalhes |
|---|---------|---------|----------|
| 1 | .gitignore com exceção | `.gitignore` | `data/*` + `!data/dashboard_data.json` — só o JSON escapa |
| 2 | Fallback automático | `src/dashboard.py::load_dashboard_data()` | Se JSON não existe, roda `generate_dashboard_data.py` com `subprocess` + `st.info` + `st.stop` em caso de erro |
| 3 | Commit do JSON | git | `git add data/dashboard_data.json` e commitar |

### Fluxo

- Streamlit Cloud: JSON commitado → carrega instantâneo
- Desenvolvimento limpo: JSON está no repo → carrega instantâneo
- JSON deletado/corrompido: fallback roda pipeline ~8 min

---

## Rodada 13: Navbar + Footer similar ao landing SANOVA

**Arquivos:** `landing/src/components/Navbar.jsx` (novo), `CTASection.jsx`, `App.jsx`, `globals.css`

### Objetivo

Adicionar header (navbar) e footer semelhantes ao projeto SANOVA de referência.

### Mudanças

| # | O quê | Arquivo | Detalhes |
|---|-------|---------|----------|
| 1 | Navbar | `Navbar.jsx` (novo) | Fixed top 64px, `backdrop-filter: blur(12px)`, scroll effect (>100px escurece), hamburger menu mobile, links: Início/Ranking/Saúde/Forecast/Sobre |
| 2 | Footer | `CTASection.jsx` | Adicionar `<footer>` com copyright + créditos abaixo do botão CTA |
| 3 | IDs nas sections | `App.jsx` | Adicionar `id="hero"`, `id="ranking"`, `id="saude"`, `id="forecast"`, `id="sobre"` nas sections para anchor navigation |
| 4 | Import Navbar | `App.jsx` | `<Navbar />` no topo do return |
| 5 | Estilos | `globals.css` | Adicionar estilos da navbar (.navbar, .nav-inner, .nav-brand, .nav-links, .nav-toggle) e footer inspirados no SANOVA

---

## Rodada 14: About Me Card na section "Sobre"

**Arquivos:** `landing/src/components/AboutCard.jsx` (novo), `CTASection.jsx`, `globals.css`

### Objetivo

Adicionar card "Sobre o Desenvolvedor" na última section com dados do GitHub.

### Dados (GitHub API)

| Campo | Valor |
|-------|-------|
| Nome | Lucas Cavalcante dos Santos |
| Bio | dev dados com py, lm, streamlit, folium, pytorch, opencv |
| Localização | Fortaleza, Ceará |
| Avatar | `https://avatars.githubusercontent.com/u/133777385?v=4` |
| GitHub | `https://github.com/cavalcanteprofissional` |
| Portfolio | `https://cavalcanteprofissional.github.io/portfolio/` |
| Email | `cavalcanteprofissional@outlook.com` |
| LinkedIn | `https://linkedin.com/in/cavalcante-Lucas` |
| WhatsApp | `https://wa.me/5585996859051` |
| Repos | 38 · Seguidores: 4 · Following: 18 |

### Mudanças

| # | O quê | Arquivo | Detalhes |
|---|-------|---------|----------|
| 1 | AboutCard | `AboutCard.jsx` (novo) | Card com avatar 64px, nome, bio, localização, links sociais (GitHub/Portfolio/LinkedIn/Email), tech tags, badge de estatísticas |
| 2 | Import | `CTASection.jsx` | Inserir `<AboutCard />` dentro do ScrollReveal do footer, antes de `<site-footer>` |
| 3 | Estilos | `globals.css` | `.about-card`, `.about-avatar`, `.about-links`, `.about-tech-tags`, `.tech-tag` |
