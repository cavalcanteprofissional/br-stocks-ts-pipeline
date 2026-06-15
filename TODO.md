# TODO — Status do Projeto

> Todas as fases planejadas foram concluídas. ✅

## ✅ Concluído

### Fase 1 — Correções de Estabilidade (Rodadas 3–5)
- `TypeError: Cannot interpolate with str dtype` — corrigido com `pd.to_numeric` + `ffill(limit=2)` + `interpolate`
- `IndexError: list index out of range` — guard `if not returns` em `_best_worst_entities()`
- `ValueError: Encountered all NA values` — `dropna().empty` substitui `.empty` em todo o código
- Auditoria 10 vulnerabilidades empty/NaN (eda.py, dashboard.py, preprocess.py)
- `ValueError: negative dimensions are not allowed` — guard `nlags < 1` + 6 novas vulnerabilidades corrigidas
- API fallback para tickers delistados
- `StreamlitDuplicateElementId` — keys únicas em todos os `st.plotly_chart()`
- `ValueError: x must have 2 complete cycles` — guard `len(series) < period * 2`

### Fase 2 — Testes E2E (Rodada 6)
- Playwright + pytest-playwright: 12 testes, 11 passando, 1 xfail

### Fase 3 — Métricas de Confiabilidade (Rodadas 7–8)
- RMSE/MAE/MAPE in-sample, Walk-forward CV, Ljung-Box/Jarque-Bera
- Layout data storytelling no expander "📊 Métricas de Confiabilidade"
- Anotação de incerteza no horizonte

### Fase 4 — Landing Page (Rodadas 9–11)
- SPA React + Vite com scrollytelling e animações
- 5 seções hero/ranking/saúde/forecast/cta
- Navbar + Footer estilo SANOVA (Rodada 13)
- About Card (Rodada 14)
- Fix: correlação vazia, NaN no JSON
- Deploy via gh-pages

### Fase 5 — Deploy Streamlit Cloud (Rodada 12)
- `.gitignore` com exceção para `dashboard_data.json`
- Fallback automático via `subprocess`

### Fase 6 — Comparação Multi-Modelo (Rodada 15)
- ARIMA/SARIMA, Prophet, LSTM (PyTorch)
- Walk-forward CV 5 folds via `TimeSeriesSplit`
- `src/models/` — pacote com `BaseModel`, `ARIMAModel`, `ProphetModel`, `LSTMModel`
- JSON com estrutura aninhada: `forecast[eid][modelo]` + `model_comparison[eid]`
- Dashboard: nova aba "Comparação" com tabela, gráfico e forecast sobreposto
- Métricas: SMAPE + R² adicionados, MAPE sinalizado com warning explicativo

## 🔮 Melhorias Futuras (Ideias)

| Prioridade | Item | Contexto |
|-----------|------|----------|
| Baixa | XGBoost/Random Forest como 4º modelo | Testar se árvores capturam padrões não-lineares melhores que LSTM |
| Baixa | Streamlit multi-página | Separar Visão Geral (todos ativos) vs Detalhe (um ativo) |
| Baixa | Dark/light theme toggle | Streamlit nativo + CSS custom |
| Baixa | i18n (português/inglês) | Dashboard bilíngue |
| Média | CI/CD com GitHub Actions | Rodar pipeline + testes + deploy automático |
| Média | Monitor de integração contínua | AnomalyMonitor em produção com alertas |
| Alta | Cache incremental do JSON | Só refazer modelos se dados mudaram (~8 min → ~30s)
| Média | Gráficos de resíduos dos modelos | Resíduos ao longo do tempo, histograma + KDE, Q-Q plot. Exportar array de resíduos no JSON (`forecast[eid][modelo].residuals`). Adicionar subseção no expander "📊 Métricas de Confiabilidade" na aba Forecast do dashboard.
