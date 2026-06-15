import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit import session_state as state

from src.config import config
from src.outliers import detect_anomaly_realtime

DATA_PATH = Path(config.CACHE_DIR) / "dashboard_data.json"
STORY_COLORS = [
    "#1A56DB", "#E02424", "#0E9F6E", "#F59E0B",
    "#7E3AF2", "#00B8D9", "#FF5630", "#36B37E",
    "#6554C0", "#172B4D",
]


DASHBOARD_SCRIPT = Path("scripts/generate_dashboard_data.py")


def load_dashboard_data():
    if not DATA_PATH.exists():
        st.info("Gerando dados da pipeline pela primeira vez... Isso leva ~8 minutos. ☕")
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, str(DASHBOARD_SCRIPT)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            st.error(f"Falha ao gerar dados:\n```\n{result.stderr[-2000:]}\n```")
            st.stop()
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _figure_from_dict(d):
    if d is None:
        return go.Figure()
    return go.Figure(data=d.get("data"), layout=d.get("layout"))


def kpi_card(col, label, value, delta=None, help_text=None):
    col.metric(label, value, delta=delta, help=help_text)


def main():
    st.set_page_config(layout="wide", page_title="Brazilian Stocks — Onde o Mercado está se movendo?")

    data = load_dashboard_data()
    meta = data["metadata"]
    entity_ids = meta["tickers"]

    st.title("Brazilian Stocks — Onde o Mercado está se movendo?")
    st.markdown("_" + config.DATA_SOURCE.upper() + "  ·  " + meta["resample_freq"] + " resample  ·  " + str(len(entity_ids)) + " tickers_")

    entity = st.sidebar.selectbox("Selecione o Ativo", entity_ids, index=0)
    st.sidebar.subheader("Opções")

    kpis = data["kpis"]
    entities_series = data["series"]
    charts = data["charts"]
    decomp_data = data["decomposition"].get(entity, {})
    model_data = data["models"].get(entity, {})
    fc_models = data["forecast"].get(entity, {})
    _old_flat = "forecast" in fc_models or "dates" in fc_models
    if _old_flat:
        fc_models = {"ARIMA": fc_models}
    fc_data = fc_models.get("ARIMA", {})
    out_data = data["outliers"].get(entity, {})
    res_stats = data["residual_stats"].get(entity, {})
    comp_data = data.get("model_comparison", {}).get(entity, {})

    tab_overview, tab_eda, tab_decomp, tab_model, tab_forecast, tab_comparison, tab_anomalies = st.tabs([
        "Overview", "EDA", "Decomposição", "Modelo", "Forecast", "Comparação", "Anomalias",
    ])

    with tab_overview:
        st.subheader("Summary Executivo")

        exec_col1, exec_col2, exec_col3, exec_col4 = st.columns(4)
        ent_kpi = kpis["entities"].get(entity, {})
        ret = ent_kpi.get("total_return_pct", 0.0)
        kpi_card(exec_col1, "Retorno Acum.", f"{ret:+.1f}%", help_text="Desde o primeiro dado até hoje")

        overall = kpis.get("overall", {})
        best = overall.get("best_entity")
        worst = overall.get("worst_entity")
        best_ret = overall.get("best_return")
        worst_ret = overall.get("worst_return")
        if best:
            kpi_card(exec_col2, "Melhor Ativo", best, delta=f"{best_ret*100:+.1f}%" if best_ret else None,
                     help_text="Maior retorno no período")
            kpi_card(exec_col3, "Pior Ativo", worst, delta=f"{worst_ret*100:+.1f}%" if worst_ret else None,
                     help_text="Menor retorno no período")
        else:
            kpi_card(exec_col2, "Melhor Ativo", "—", delta="N/A")
            kpi_card(exec_col3, "Pior Ativo", "—", delta="N/A")

        peak_val = ent_kpi.get("peak_value", 0.0)
        peak_date = ent_kpi.get("peak_date", "—")
        kpi_card(exec_col4, "All-Time High", f"${peak_val:.2f}" if peak_val else "—",
                 delta=peak_date, help_text="Preço máximo histórico")

        st.markdown("---")
        st.plotly_chart(_figure_from_dict(charts.get("series")), use_container_width=True, key="chart_series")
        st.plotly_chart(_figure_from_dict(charts.get("drawdown")), use_container_width=True, key="chart_drawdown")

    with tab_eda:
        st.subheader("Análise Exploratória")
        st.plotly_chart(_figure_from_dict(charts.get("returns_with_context")), use_container_width=True, key="chart_returns")
        st.plotly_chart(_figure_from_dict(charts.get("top_vs_bottom")), use_container_width=True, key="chart_top_vs_bottom")

        col1, col2 = st.columns(2)
        col1.plotly_chart(_figure_from_dict(charts.get("seasonal_boxplot")), use_container_width=True, key="chart_seasonal")
        col2.plotly_chart(_figure_from_dict(charts.get("calendar_heatmap")), use_container_width=True, key="chart_calendar")

        st.plotly_chart(_figure_from_dict(charts.get("distribution")), use_container_width=True, key="chart_distribution")

        col3, col4 = st.columns(2)
        col3.plotly_chart(_figure_from_dict(charts.get("correlation")), use_container_width=True, key="chart_correlation")
        col4.plotly_chart(_figure_from_dict(charts.get("volatility")), use_container_width=True, key="chart_volatility")

        st.plotly_chart(_figure_from_dict(charts.get("monthly_returns")), use_container_width=True, key="chart_monthly")
        st.plotly_chart(_figure_from_dict(charts.get("acf_pacf")), use_container_width=True, key="chart_acf_pacf")

    with tab_decomp:
        if decomp_data:
            dep_model = decomp_data.get("model", "additive")
            dep_period = decomp_data.get("period", 52)
            st.info(f"Modelo detectado: **{dep_model}**  ·  Período sazonal: **{dep_period}**")
            st.caption("Additive = flutuação constante  |  Multiplicative = flutuação proporcional ao nível")
            fig = _build_decomp_figure(decomp_data, entity)
            st.plotly_chart(fig, use_container_width=True, key="chart_decomp")
        else:
            st.info("Decomposição não disponível para este ativo.")

    with tab_model:
        st.subheader("Testes de Estacionaridade")
        if model_data:
            stat = model_data.get("stationarity", {})
            stat_df = pd.DataFrame([{
                "Test": "ADF",
                "P-Value": f"{stat.get('adf_pval', 0):.4f}",
                "d sugerido": stat.get("d_suggested", 0),
            }, {
                "Test": "KPSS",
                "P-Value": f"{stat.get('kpss_pval', 0):.4f}",
                "d sugerido": stat.get("d_suggested", 0),
            }])
            st.dataframe(stat_df, hide_index=True, use_container_width=True)

            order_str = str(model_data.get("order", "—"))
            seas_order_str = str(model_data.get("seasonal_order", "—"))
            aic = model_data.get("aic")
            bic = model_data.get("bic")
            st.info(f"**ARIMA{order_str}**  ·  Sazonal: {seas_order_str}")
            c1, c2 = st.columns(2)
            c1.metric("AIC", f"{aic:.2f}" if aic else "—",
                      help="Akaike Information Criterion — quanto menor, melhor o ajuste")
            c2.metric("BIC", f"{bic:.2f}" if bic else "—",
                      help="Bayesian Information Criterion — penaliza mais complexidade")
        else:
            st.info("Modelo não disponível para este ativo.")

        comp_ranking = data.get("model_comparison_ranking", [])
        if len(comp_ranking) > 1:
            st.subheader("Comparação entre Modelos (AIC)")
            comp_df = pd.DataFrame(comp_ranking)
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                x=comp_df["aic"], y=comp_df["entity"],
                orientation="h", marker_color=STORY_COLORS[:len(comp_df)],
                text=comp_df["aic"], textposition="outside",
            ))
            fig_comp.update_layout(title="AIC por Ativo (menor = melhor)", height=300, xaxis_title="AIC")
            st.plotly_chart(fig_comp, use_container_width=True, key="chart_model_comp")

    with tab_forecast:
        if fc_data:
            fc_dates = [pd.Timestamp(d) for d in fc_data.get("dates", [])]
            fc_vals = fc_data.get("forecast", [])
            price_fc = fc_data.get("price_forecast", [])
            price_lower = fc_data.get("price_lower", [])
            price_upper = fc_data.get("price_upper", [])
            series_info = entities_series.get(entity, {})
            hist_dates = [pd.Timestamp(d) for d in series_info.get("dates", [])]
            hist_close = series_info.get("Close", [])

            if price_fc and hist_close:
                last_price = hist_close[-1] if hist_close else 0.0
                fc_end = price_fc[-1] if price_fc else 0.0
                fc_change = (fc_end / last_price - 1) * 100 if last_price else 0.0
                st.subheader(f"Projeção: Último preço R${last_price:.2f} → R${fc_end:.2f} ({fc_change:+.1f}%)")
                st.caption("Intervalo de 95% de confiança. Quanto maior o horizonte, maior a incerteza.")

                fig_fc = go.Figure()
                fig_fc.add_trace(go.Scatter(x=hist_dates, y=hist_close, mode="lines",
                                            name="Histórico", line=dict(color=STORY_COLORS[0], width=2)))
                fig_fc.add_trace(go.Scatter(x=fc_dates, y=price_fc, mode="lines+markers",
                                            name="Forecast", line=dict(color=STORY_COLORS[1], width=2)))
                fig_fc.add_trace(go.Scatter(x=fc_dates, y=price_upper, fill=None,
                                            mode="lines", line=dict(width=0), showlegend=False))
                fig_fc.add_trace(go.Scatter(x=fc_dates, y=price_lower,
                                            fill="tonexty", mode="lines", line=dict(width=0),
                                            name="IC 95%", fillcolor="rgba(30,86,219,0.12)"))
                fig_fc.add_annotation(x=fc_dates[-1], y=fc_end,
                                      text=f"R${fc_end:.2f}", showarrow=True, arrowhead=1)
                fig_fc.update_layout(title="Projeção de Preço", height=400)
                st.plotly_chart(fig_fc, use_container_width=True, key="chart_forecast")

            st.subheader("Tabela do Forecast")
            fc_df = pd.DataFrame({
                "forecast": fc_vals,
                "lower_bound": fc_data.get("lower_bound", []),
                "upper_bound": fc_data.get("upper_bound", []),
            }).round(4)
            st.dataframe(fc_df, use_container_width=True)

            if fc_data.get("rmse") is not None:
                with st.expander("📊 Métricas de Confiabilidade", expanded=False):
                    rmse_val = fc_data["rmse"]
                    cv_rmse_val = fc_data.get("cv_rmse")
                    has_resid_auto = fc_data.get("has_residual_autocorrelation", True)
                    lb_pval = fc_data.get("ljung_box_pval", 0)
                    jb_pval = fc_data.get("jarque_bera_pval", 0)
                    mape_val = fc_data.get("mape")

                    cv_diff = abs(cv_rmse_val - rmse_val) / rmse_val if cv_rmse_val and rmse_val else 0
                    is_healthy = not has_resid_auto and cv_diff < 0.5
                    verdict = "✅ Modelo confiável" if is_healthy else "⚠️ Requer atenção"
                    caption = f"Ljung-Box p={lb_pval:.4f} · RMSE={rmse_val:.4f}"
                    if cv_rmse_val:
                        caption += f" · CV RMSE={cv_rmse_val:.4f}"

                    st.markdown(f"### {verdict}")
                    st.caption(caption)
                    st.divider()

                    lc, rc = st.columns(2)
                    with lc:
                        st.markdown("**📈 Ajuste do Modelo**")
                        r1, r2, r3 = st.columns(3)
                        r1.metric("RMSE", f"{rmse_val:.4f}")
                        r2.metric("MAE", f"{fc_data.get('mae', 0):.4f}")
                        r3.metric("MAPE", f"{mape_val:.2f}%" if mape_val else "—")

                    with rc:
                        st.markdown("**🔬 Diagnóstico dos Resíduos**")
                        d1, d2 = st.columns(2)
                        d1.metric("Ljung-Box", f"p={lb_pval:.4f}")
                        d2.metric("Jarque-Bera", f"p={jb_pval:.4f}")
                        badge = "✅ Resíduos ok" if not has_resid_auto else "⚠️ Possível má especificação"
                        rc.markdown(badge)

                    st.divider()

                    if cv_rmse_val is not None:
                        st.markdown("**🔄 Validação Cruzada**")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("CV RMSE", f"{cv_rmse_val:.4f}")
                        c2.metric("In-sample RMSE", f"{rmse_val:.4f}")
                        c3.metric("Diferença", f"{cv_diff:+.0%}")
                        cv_note = "✅ Modelo generaliza bem" if cv_diff < 0.5 else "⚠️ Overfitting possível"
                        st.caption(cv_note)
                        st.divider()

                    ci_widths = fc_data.get("avg_ci_width", [])
                    if ci_widths:
                        avg_ci = [v for v in ci_widths if v is not None]
                        if avg_ci:
                            st.markdown("**📉 Incerteza por Horizonte**")
                            step_labels = [f"Passo {i+1}" for i in range(len(avg_ci))]
                            ci_fig = go.Figure()
                            ci_fig.add_trace(go.Scatter(
                                x=step_labels, y=avg_ci, mode="lines+markers",
                                name="Largura IC 95%",
                                line=dict(color="#FF5630", width=2),
                                marker=dict(size=6),
                            ))
                            first_w = avg_ci[0]
                            last_w = avg_ci[-1]
                            pct_change = ((last_w - first_w) / first_w) * 100 if first_w else 0
                            ci_fig.add_annotation(
                                x=step_labels[0], y=first_w,
                                text=f"Passo 1: R${first_w:.2f}",
                                showarrow=True, arrowhead=1, ax=-40, ay=-30,
                            )
                            ci_fig.add_annotation(
                                x=step_labels[-1], y=last_w,
                                text=f"Passo {len(avg_ci)}: R${last_w:.2f}  +{pct_change:.0f}%",
                                showarrow=True, arrowhead=1, ax=40, ay=-60,
                            )
                            ci_fig.update_layout(
                                title="Incerteza por Horizonte",
                                height=250, margin=dict(l=0, r=0, t=30, b=0),
                                yaxis_title="Amplitude (R$)",
                            )
                            st.plotly_chart(ci_fig, use_container_width=True, key="chart_ci_width")
                            if pct_change > 100:
                                st.caption("⚠️ Incerteza cresce rápido com o horizonte — use projeções longas com cautela")
                            else:
                                st.caption("✅ Incerteza estável ao longo do horizonte")
        else:
            st.info("Forecast não disponível para este ativo.")

    with tab_comparison:
        if _old_flat:
            st.info("Disponível apenas após regenerar os dados com o pipeline mais recente.")
        elif not fc_models or len(fc_models) < 1:
            st.info("Comparação não disponível para este ativo.")
        else:
            model_names = sorted(fc_models.keys())

            st.subheader("Comparação entre Modelos — " + entity)

            metrics_keys = ["rmse", "mae", "mape", "smape", "r2", "cv_rmse", "training_time_s"]
            metric_labels = {"rmse": "RMSE", "mae": "MAE", "mape": "MAPE (%)",
                             "smape": "SMAPE (%)", "r2": "R²",
                             "cv_rmse": "CV RMSE", "training_time_s": "Tempo (s)"}
            metric_decimal = {"rmse": 4, "mae": 4, "mape": 2, "smape": 2, "r2": 4, "cv_rmse": 4, "training_time_s": 1}

            comp_rows = []
            for m in model_names:
                fc_m = fc_models.get(m, {})
                row = {"Modelo": m}
                for k in metrics_keys:
                    v = fc_m.get(k)
                    if v is None:
                        row[metric_labels[k]] = "—"
                    elif k == "training_time_s":
                        row[metric_labels[k]] = f"{v:.1f}"
                    elif k == "r2":
                        row[metric_labels[k]] = f"{v:.4f}"
                    elif k in ("mape", "smape"):
                        row[metric_labels[k]] = f"{v:.2f}"
                    else:
                        row[metric_labels[k]] = f"{v:.4f}"
                comp_rows.append(row)

            comp_df = pd.DataFrame(comp_rows)
            best_model = comp_data.get("best_model", model_names[0]) if comp_data else model_names[0]

            def _highlight_best(val):
                return "background-color: rgba(14, 159, 110, 0.15); color: var(--green-light, #34d399); font-weight: 600"

            def _style_row(row):
                is_best = row["Modelo"] == best_model
                return [_highlight_best(v) if is_best else "" for v in row]

            styled = comp_df.style.apply(_style_row, axis=1)
            st.dataframe(styled, use_container_width=True, hide_index=True)

            if best_model:
                st.success(f"✅ **Melhor modelo (menor RMSE): {best_model}**")

            mape_warn = any(
                fc_models.get(m, {}).get("mape") is not None and fc_models[m]["mape"] > 100
                for m in model_names
            )
            if mape_warn:
                st.warning(
                    "⚠️ **MAPE elevado (>100%)** — o MAPE é calculado sobre retornos logarítmicos "
                    "(valores tipicamente entre -0.05 e 0.05), onde a divisão por valores "
                    "próximos de zero inflaciona a métrica. "
                    "**SMAPE** (Symmetric MAPE) resolve esse problema usando denominador "
                    "simétrico e é mais confiável para séries com retornos."
                )

            st.divider()

            numeric_vals = {}
            for k in ["rmse", "mae", "cv_rmse", "smape", "r2"]:
                vals = {m: fc_models.get(m, {}).get(k) for m in model_names}
                if any(v is not None for v in vals.values()):
                    numeric_vals[k] = vals

            if numeric_vals:
                fig_comp = go.Figure()
                for k, vals in numeric_vals.items():
                    clean = {m: v for m, v in vals.items() if v is not None}
                    decimals = metric_decimal.get(k, 4)
                    fig_comp.add_trace(go.Bar(
                        name=metric_labels.get(k, k),
                        x=list(clean.keys()),
                        y=list(clean.values()),
                        text=[f"{v:.{decimals}f}" for v in clean.values()],
                        textposition="outside",
                    ))
                fig_comp.update_layout(
                    title="Métricas por Modelo",
                    barmode="group",
                    height=400,
                    yaxis_title="Valor",
                )
                st.plotly_chart(fig_comp, use_container_width=True, key="chart_model_compare")

            st.subheader("Forecast Sobreposto")
            series_info = entities_series.get(entity, {})
            hist_dates = [pd.Timestamp(d) for d in series_info.get("dates", [])]
            hist_close = series_info.get("Close", [])

            fig_overlay = go.Figure()
            fig_overlay.add_trace(go.Scatter(
                x=hist_dates, y=hist_close, mode="lines",
                name="Histórico", line=dict(color="#1A56DB", width=2),
            ))

            colors = {"ARIMA": "#E02424", "Prophet": "#0E9F6E", "LSTM": "#F59E0B"}
            for m in model_names:
                fc_m = fc_models.get(m, {})
                fc_dates = [pd.Timestamp(d) for d in fc_m.get("dates", [])]
                price_fc = fc_m.get("price_forecast", [])
                if price_fc and fc_dates:
                    fig_overlay.add_trace(go.Scatter(
                        x=fc_dates, y=price_fc, mode="lines+markers",
                        name=m, line=dict(color=colors.get(m, "#7E3AF2"), width=2, dash="dash"),
                    ))

            fig_overlay.update_layout(title="Projeção — Todos os Modelos", height=400)
            st.plotly_chart(fig_overlay, use_container_width=True, key="chart_forecast_overlay")

    with tab_anomalies:
        st.subheader("Outliers em Lote")
        out_count = out_data.get("count", 0)
        if out_count > 0:
            out_dates = [pd.Timestamp(d) for d in out_data.get("dates", [])]
            out_vals = out_data.get("values", [])
            out_sevs = out_data.get("severities", [])
            series_info = entities_series.get(entity, {})
            hist_dates = [pd.Timestamp(d) for d in series_info.get("dates", [])]
            hist_close = series_info.get("Close", [])

            sev_counts = pd.Series(out_sevs).value_counts()
            sev_fig = go.Figure(data=[go.Pie(
                labels=sev_counts.index.tolist(), values=sev_counts.values.tolist(),
                marker=dict(colors=["#F59E0B", "#FF5630", "#E02424", "#0E9F6E", "#1A56DB"]),
                hole=0.4,
            )])
            sev_fig.update_layout(title="Proporção por Severidade", height=300)

            col_a1, col_a2 = st.columns([1, 2])
            col_a1.plotly_chart(sev_fig, use_container_width=True, key="chart_severity_pie")
            col_a2.metric("Total de Outliers", out_count)
            col_a2.metric("% do Total", f"{out_data.get('pct_total', 0):.1f}%")

            fig_out = go.Figure()
            fig_out.add_trace(go.Scatter(x=hist_dates, y=hist_close, mode="lines",
                                         name=config.VALUE_COLUMN, line=dict(color=STORY_COLORS[0], width=2)))
            fig_out.add_trace(go.Scatter(x=out_dates, y=out_vals, mode="markers", name="Anomalias",
                                         marker=dict(color="#E02424", size=8, symbol="x")))
            fig_out.update_layout(title=f"Anomalias Detectadas — {entity}", height=400)
            st.plotly_chart(fig_out, use_container_width=True, key="chart_outliers")
        else:
            st.success("Nenhum outlier detectado para este ativo.")

        st.subheader("Verificação em Tempo Real")
        series_info = entities_series.get(entity, {})
        hist_close = series_info.get("Close", [])
        last_close = hist_close[-1] if hist_close else 0.0

        col_in1, col_in2 = st.columns(2)
        with col_in1:
            new_price = st.number_input("Novo valor:", value=float(last_close), format="%.2f")
        with col_in2:
            if st.button("Verificar Anomalia"):
                result = detect_anomaly_realtime(new_price, res_stats)
                verdict = "🚨 ANOMALIA" if result["is_anomaly"] else "✅ Normal"
                sev_map = {"high": "🔴 Alta", "medium": "🟡 Média", "none": "🟢 Nenhuma"}
                st.metric("Veredito", verdict)
                st.metric("Severidade", sev_map.get(result["severity"], result["severity"]))
                st.metric("Desvio", f"{result['deviation']:.4f}")
                st.metric("Threshold", f"{result['threshold']:.4f}")

                if "anomaly_log" not in state:
                    state.anomaly_log = []
                state.anomaly_log.append({
                    "timestamp": pd.Timestamp.now().isoformat(), "entity": entity,
                    "value": new_price, "is_anomaly": result["is_anomaly"],
                    "severity": result["severity"],
                })

        if "anomaly_log" in state and state.anomaly_log:
            st.subheader("Log de Anomalias")
            st.dataframe(pd.DataFrame(state.anomaly_log), hide_index=True, use_container_width=True)
            if st.button("Limpar Log"):
                state.anomaly_log = []


def _build_decomp_figure(d: dict, title: str = "") -> go.Figure:
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        subplot_titles=("Observed", "Trend", "Seasonal", "Residual"),
                        vertical_spacing=0.05)
    for i, key in enumerate(["observed", "trend", "seasonal", "resid"], 1):
        sd = d.get(key, {})
        dates = [pd.Timestamp(x) for x in sd.get("dates", [])]
        vals = sd.get("values", [])
        if dates and any(v is not None for v in vals):
            clean_vals = [v if v is not None else float("nan") for v in vals]
            fig.add_trace(go.Scatter(x=dates, y=clean_vals, mode="lines", showlegend=False), row=i, col=1)
    fig.update_layout(title=title or f"Decomposition ({d.get('model', 'additive')}, period={d.get('period', 52)})",
                      height=700)
    return fig


if __name__ == "__main__":
    main()
