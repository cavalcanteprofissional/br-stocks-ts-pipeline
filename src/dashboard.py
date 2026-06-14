import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit import session_state as state

from src.config import config
from src.ingest import ingest
from src.preprocess import preprocess
from src.decompose import decompose_entity, plot_decomposition
from src.outliers import detect_outliers_batch, detect_anomaly_realtime, compute_residual_stats
from src.modeling import fit_arima, forecast
from src.eda import (
    STORY_COLORS, plot_series, plot_returns_with_context,
    plot_seasonal_boxplot, plot_distribution, plot_correlation,
    plot_volatility, plot_acf_pacf, plot_drawdown,
    plot_top_entities_comparison, plot_monthly_returns_heatmap,
    plot_calendar_heatmap, _best_worst_entities,
)

st.set_page_config(layout="wide", page_title="Brazilian Stocks — Onde o Mercado está se movendo?")

RESULTS_DIR = Path(config.OUTPUT_DIR)


@st.cache_data
def load_data():
    raw = ingest()
    entities = preprocess(raw)
    return entities


@st.cache_data
def load_model(entity_id: str, series):
    return fit_arima(series)


@st.cache_data
def load_forecast_model(model, steps: int):
    return forecast(model, steps)


@st.cache_data
def load_decomposition(df):
    return decompose_entity(df)


@st.cache_data
def load_outliers(series):
    return detect_outliers_batch(series)


def kpi_card(col, label, value, delta=None, help_text=None):
    col.metric(label, value, delta=delta, help=help_text)


def main():
    st.title("Brazilian Stocks — Onde o Mercado está se movendo?")
    st.markdown("_" + config.DATA_SOURCE.upper() + "  ·  " + config.RESAMPLE_FREQ + " resample  ·  " + str(len(config.TICKERS)) + " tickers_")

    with st.spinner("Carregando dados..."):
        entities = load_data()

    entity_ids = list(entities.keys())
    value_col = config.VALUE_COLUMN
    freq = config.RESAMPLE_FREQ

    entity = st.sidebar.selectbox("Selecione o Ativo", entity_ids, index=0)
    st.sidebar.subheader("Opções")
    forecast_horizon = st.sidebar.slider("Horizonte de Forecast", 4, 52, config.FORECAST_HORIZON)

    df = entities[entity]
    series = df[value_col]

    worst_id, best_id, all_returns = _best_worst_entities(entities, value_col)

    tab_overview, tab_eda, tab_decomp, tab_model, tab_forecast, tab_anomalies = st.tabs([
        "Overview", "EDA", "Decomposição", "Modelo", "Forecast", "Anomalias",
    ])

    with tab_overview:
        st.subheader("Summary Executivo")

        exec_col1, exec_col2, exec_col3, exec_col4 = st.columns(4)
        ret = (series.iloc[-1] / series.iloc[0] - 1) * 100
        kpi_card(exec_col1, "Retorno Acum.", f"{ret:+.1f}%",
                 delta=None, help_text="Desde o primeiro dado até hoje")
        kpi_card(exec_col2, "Melhor Ativo", best_id,
                 delta=f"{all_returns[best_id]*100:+.1f}%", help_text="Maior retorno no período")
        kpi_card(exec_col3, "Pior Ativo", worst_id,
                 delta=f"{all_returns[worst_id]*100:+.1f}%", help_text="Menor retorno no período")
        peak_val = series.expanding().max().iloc[-1]
        peak_date = series.idxmax().strftime("%Y-%m") if not series.empty else "—"
        kpi_card(exec_col4, "All-Time High", f"${peak_val:.2f}",
                 delta=peak_date, help_text="Preço máximo histórico")

        st.markdown("---")
        st.plotly_chart(plot_series(entities), use_container_width=True)
        st.plotly_chart(plot_drawdown(entities), use_container_width=True)

    with tab_eda:
        st.subheader("Análise Exploratória")

        st.plotly_chart(plot_returns_with_context(entities), use_container_width=True)
        st.plotly_chart(plot_top_entities_comparison(entities), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_seasonal_boxplot(entities), use_container_width=True)
        with col2:
            st.plotly_chart(plot_calendar_heatmap(entities), use_container_width=True)

        st.plotly_chart(plot_distribution(entities), use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(plot_correlation(entities), use_container_width=True)
        with col4:
            st.plotly_chart(plot_volatility(entities), use_container_width=True)

        st.plotly_chart(plot_monthly_returns_heatmap(entities), use_container_width=True)
        st.plotly_chart(plot_acf_pacf(entities), use_container_width=True)

    with tab_decomp:
        with st.spinner("Decompondo..."):
            decomp = load_decomposition(df)
        st.info(f"Modelo detectado: **{decomp['model']}**  ·  Período sazonal: **{decomp['period']}**")
        st.caption("Additive = flutuação constante  |  Multiplicative = flutuação proporcional ao nível")
        fig = plot_decomposition(decomp, title=entity)
        st.plotly_chart(fig, use_container_width=True)

    with tab_model:
        st.subheader("Testes de Estacionaridade")
        from src.modeling import check_stationarity

        stat = check_stationarity(series)
        stat_df = pd.DataFrame([{
            "Test": "ADF", "Stat": f"{stat['adf_stat']:.4f}",
            "P-Value": f"{stat['adf_pval']:.4f}",
            "Estacionário": "Sim" if stat["adf_stationary"] else "Não",
            "Interpretação": "Série é estacionária" if stat["adf_stationary"] else "Série tem raiz unitária (não estacionária)",
        }, {
            "Test": "KPSS", "Stat": f"{stat['kpss_stat']:.4f}",
            "P-Value": f"{stat['kpss_pval']:.4f}",
            "Estacionário": "Sim" if stat["kpss_stationary"] else "Não",
            "Interpretação": "Série é estacionária em torno da tendência" if stat["kpss_stationary"] else "Série não é estacionária",
        }])
        st.dataframe(stat_df, hide_index=True, use_container_width=True)
        st.caption("ADF: H0 = série tem raiz unitária  |  KPSS: H0 = série é estacionária")

        with st.spinner("Ajustando ARIMA/SARIMA..."):
            returns_series = df["Returns"].dropna() if "Returns" in df.columns else series
            model = load_model(entity, returns_series)

        st.subheader("Modelo Ajustado")
        order = model.order
        seas = model.seasonal_order
        order_desc = f"ARIMA{order} (p={order[0]}, d={order[1]}, q={order[2]})"
        seas_desc = f"SARIMA{seas} (P={seas[0]}, D={seas[1]}, Q={seas[2]}, m={seas[3]})" if seas[3] > 1 else "Sem componente sazonal"

        st.info(f"**{order_desc}**  ·  {seas_desc}")
        c1, c2 = st.columns(2)
        c1.metric("AIC", f"{model.aic():.2f}", help="Akaike Information Criterion — quanto menor, melhor o ajuste")
        c2.metric("BIC", f"{model.bic():.2f}", help="Bayesian Information Criterion — penaliza mais complexidade")

        if len(entities) > 1:
            st.subheader("Comparação entre Modelos")
            from src.modeling import fit_arima as fit_fn
            comp_rows = []
            for eid in entity_ids[:6]:
                s = entities[eid]["Returns"].dropna() if "Returns" in entities[eid].columns else entities[eid][value_col]
                try:
                    m = fit_fn(s)
                    comp_rows.append({"Ativo": eid, "Ordem": str(m.order), "AIC": round(m.aic(), 2)})
                except Exception:
                    comp_rows.append({"Ativo": eid, "Ordem": "—", "AIC": None})
            comp_df = pd.DataFrame(comp_rows).dropna()
            comp_df = comp_df.sort_values("AIC")
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=comp_df["AIC"], y=comp_df["Ativo"],
                orientation="h", marker_color=STORY_COLORS[:len(comp_df)],
                text=comp_df["AIC"], textposition="outside",
            ))
            fig_comp.update_layout(title="AIC por Ativo (menor = melhor)", height=300, xaxis_title="AIC")
            st.plotly_chart(fig_comp, use_container_width=True)

    with tab_forecast:
        with st.spinner("Gerando forecast..."):
            returns_series = df["Returns"].dropna() if "Returns" in df.columns else series
            model = load_model(entity, returns_series)
            fc = load_forecast_model(model, forecast_horizon)
            last_date = df.index[-1]
            fc.index = pd.date_range(start=last_date, periods=len(fc) + 1, freq=freq)[1:]

        if "Returns" in df.columns:
            last_price = series.iloc[-1]
            fc["price_forecast"] = last_price * np.exp(fc["forecast"].cumsum())
            fc["price_lower"] = last_price * np.exp(fc["lower_bound"].cumsum())
            fc["price_upper"] = last_price * np.exp(fc["upper_bound"].cumsum())

            fc_end_val = fc["price_forecast"].iloc[-1]
            fc_change = (fc_end_val / last_price - 1) * 100

            st.subheader(f"Projeção: Último preço R${last_price:.2f} → R${fc_end_val:.2f} ({fc_change:+.1f}%)")
            st.caption("Intervalo de 95% de confiança. Quanto maior o horizonte, maior a incerteza.")

            fig_fc = go.Figure()
            fig_fc.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines",
                                        name="Histórico", line=dict(color=STORY_COLORS[0], width=2)))
            fig_fc.add_trace(go.Scatter(x=fc.index, y=fc["price_forecast"], mode="lines+markers",
                                        name="Forecast", line=dict(color=STORY_COLORS[1], width=2)))
            fig_fc.add_trace(go.Scatter(x=fc.index, y=fc["price_upper"], fill=None,
                                        mode="lines", line=dict(width=0), showlegend=False))
            fig_fc.add_trace(go.Scatter(x=fc.index, y=fc["price_lower"],
                                        fill="tonexty", mode="lines", line=dict(width=0),
                                        name="IC 95%", fillcolor="rgba(30,86,219,0.12)"))
            fig_fc.add_annotation(x=fc.index[-1], y=fc_end_val,
                                  text=f"R${fc_end_val:.2f}", showarrow=True, arrowhead=1)
            fig_fc.update_layout(title="Projeção de Preço", height=400)
            st.plotly_chart(fig_fc, use_container_width=True)

        st.subheader("Tabela do Forecast")
        display_fc = fc[["forecast", "lower_bound", "upper_bound"]].round(4)
        st.dataframe(display_fc, use_container_width=True)

    with tab_anomalies:
        st.subheader("Outliers em Lote")
        with st.spinner("Detectando outliers..."):
            outliers = load_outliers(series)

        if not outliers.empty:
            sev_counts = outliers["severity"].value_counts()
            sev_fig = go.Figure(data=[go.Pie(
                labels=sev_counts.index, values=sev_counts.values,
                marker=dict(colors=["#F59E0B", "#FF5630", "#E02424", "#0E9F6E", "#1A56DB"]),
                hole=0.4,
            )])
            sev_fig.update_layout(title="Proporção por Severidade", height=300)

            col_a1, col_a2 = st.columns([1, 2])
            col_a1.plotly_chart(sev_fig, use_container_width=True)
            col_a2.metric("Total de Outliers", len(outliers))
            delta_str = f"{len(outliers)/len(series.dropna())*100:.1f}% dos dados"
            col_a2.metric("% do Total", delta_str)

            fig_out = go.Figure()
            fig_out.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines",
                                         name=value_col, line=dict(color=STORY_COLORS[0], width=2)))
            fig_out.add_trace(go.Scatter(x=outliers["date"], y=outliers["value"],
                                         mode="markers", name="Anomalias",
                                         marker=dict(color="#E02424", size=8, symbol="x"),
                                         hovertemplate="%{x}<br>Valor: %{y:.2f}<br>Severidade: %{text}<extra></extra>",
                                         text=outliers["severity"]))
            fig_out.update_layout(title=f"Anomalias Detectadas — {entity}", height=400)
            st.plotly_chart(fig_out, use_container_width=True)
        else:
            st.success("Nenhum outlier detectado para este ativo.")

        st.subheader("Verificação em Tempo Real")
        stats = compute_residual_stats(series)

        col_in1, col_in2 = st.columns(2)
        with col_in1:
            new_price = st.number_input("Novo valor:", value=float(series.iloc[-1]), format="%.2f")
        with col_in2:
            if st.button("Verificar Anomalia"):
                result = detect_anomaly_realtime(new_price, stats)
                verdict = "🚨 ANOMALIA" if result["is_anomaly"] else "✅ Normal"
                sev_map = {"high": "🔴 Alta", "medium": "🟡 Média", "none": "🟢 Nenhuma"}
                st.metric("Veredito", verdict)
                st.metric("Severidade", sev_map.get(result["severity"], result["severity"]))
                st.metric("Desvio", f"{result['deviation']:.4f}")
                st.metric("Threshold", f"{result['threshold']:.4f}")

                if "anomaly_log" not in state:
                    state.anomaly_log = []
                state.anomaly_log.append({
                    "timestamp": pd.Timestamp.now(), "entity": entity,
                    "value": new_price, "is_anomaly": result["is_anomaly"],
                    "severity": result["severity"],
                })

        if "anomaly_log" in state and state.anomaly_log:
            st.subheader("Log de Anomalias")
            log_df = pd.DataFrame(state.anomaly_log)
            st.dataframe(log_df, hide_index=True, use_container_width=True)
            if st.button("Limpar Log"):
                state.anomaly_log = []


if __name__ == "__main__":
    main()
