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
```
