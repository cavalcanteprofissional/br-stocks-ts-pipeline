import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats as scipy_stats
from statsmodels.tsa.stattools import acf, pacf

from src.config import config

STORY_COLORS = [
    "#1A56DB", "#E02424", "#0E9F6E", "#F59E0B",
    "#7E3AF2", "#00B8D9", "#FF5630", "#36B37E",
    "#6554C0", "#172B4D",
]

EVENTS = [
    ("2020-03-01", "2020-05-01", "COVID-19 Crash", "#E02424"),
    ("2022-02-01", "2022-04-01", "War in Ukraine", "#FF5630"),
    ("2022-10-01", "2022-11-01", "Brazil Election", "#F59E0B"),
]


def _best_worst_entities(entities: dict[str, pd.DataFrame], value_col: str):
    returns = {}
    for eid, df in entities.items():
        series = df[value_col].dropna()
        if len(series) > 1:
            returns[eid] = (series.iloc[-1] / series.iloc[0]) - 1
    if not returns:
        return None, None, {}
    sorted_ents = sorted(returns, key=returns.get)
    return sorted_ents[0], sorted_ents[-1], returns


def plot_series(entities: dict[str, pd.DataFrame]) -> go.Figure:
    value_col = config.VALUE_COLUMN
    fig = go.Figure()

    for entity_id, df in entities.items():
        series = df[value_col]
        fig.add_trace(go.Scatter(
            x=series.index, y=series.values,
            mode="lines", name=entity_id, opacity=0.6,
            line=dict(width=1),
            hovertemplate="%{x}<br>%{y:.2f}<br><b>%{fullData.name}</b><extra></extra>",
        ))

    worst_id, best_id, _ = _best_worst_entities(entities, value_col)
    if best_id is not None:
        for eid, color, label in [(best_id, "#0E9F6E", "Best Performer"), (worst_id, "#E02424", "Worst Performer")]:
            series = entities[eid][value_col]
            fig.add_trace(go.Scatter(
                x=series.index, y=series.values,
                mode="lines", name=f"{eid} ({label})",
                line=dict(width=3, color=color),
                opacity=1,
            ))

    for start, end, label, color in EVENTS:
        fig.add_vrect(x0=start, x1=end, fillcolor=color, opacity=0.08, line_width=0)
        fig.add_annotation(x=start, yref="paper", y=0.98, text=label, showarrow=False,
                           font=dict(size=10, color=color), xanchor="left")

    fig.update_layout(
        title=dict(text="Preço: Quem Lidera e Quem Fica para Trás", font=dict(size=18)),
        xaxis_title="", yaxis_title=value_col,
        hovermode="x unified", height=500,
        legend=dict(orientation="h", y=-0.2),
    )
    return fig


def plot_returns_with_context(entities: dict[str, pd.DataFrame]) -> go.Figure:
    fig = go.Figure()
    colors = iter(STORY_COLORS)

    for entity_id, df in entities.items():
        if "Returns" not in df.columns:
            continue
        c = next(colors)
        r = df["Returns"]
        fig.add_trace(go.Scatter(
            x=r.index, y=r.values,
            mode="lines", name=entity_id, opacity=0.6,
            line=dict(width=1, color=c),
        ))

    first_id = next((e for e in entities if "Returns" in entities[e].columns), None)
    if first_id is None:
        return fig
    r = entities[first_id]["Returns"].dropna()
    if r.empty:
        return fig
    mean = r.mean()
    std = r.std()
    fig.add_hline(y=mean + 2 * std, line=dict(color="#E02424", dash="dash", width=1),
                  annotation_text="+2σ")
    fig.add_hline(y=mean - 2 * std, line=dict(color="#0E9F6E", dash="dash", width=1),
                  annotation_text="-2σ")

    for start, end, label, color in EVENTS:
        fig.add_vrect(x0=start, x1=end, fillcolor=color, opacity=0.06, line_width=0)

    fig.update_layout(
        title=dict(text="Retornos: Volatilidade e Eventos de Mercado", font=dict(size=18)),
        xaxis_title="", yaxis_title="Log Returns",
        hovermode="x unified", height=450,
    )
    return fig


def plot_seasonal_boxplot(entities: dict[str, pd.DataFrame]) -> go.Figure:
    value_col = config.VALUE_COLUMN
    freq = config.RESAMPLE_FREQ
    group_col = "month" if freq in ("D", "W", "M", "ME") else "quarter"

    top_n = min(5, len(entities))
    _, _, returns = _best_worst_entities(entities, value_col)
    top_entities = sorted(returns, key=returns.get, reverse=True)[:top_n]

    fig = go.Figure()
    for i, entity_id in enumerate(top_entities):
        df = entities[entity_id].copy()
        if df.empty:
            continue
        df[group_col] = df.index.to_series().dt.month if group_col == "month" else df.index.to_series().dt.quarter
        c = STORY_COLORS[i % len(STORY_COLORS)]
        for label, group in df.groupby(group_col):
            fig.add_trace(go.Box(
                y=group[value_col].dropna().values,
                name=str(label),
                legendgroup=entity_id,
                marker_color=c,
                showlegend=bool(label == df[group_col].iloc[0]),
            ))

    fig.update_layout(
        title=dict(text=f"Sazonalidade por {group_col.capitalize()} — Top {top_n} Ativos", font=dict(size=18)),
        height=400, legend=dict(orientation="h", y=-0.15),
    )
    return fig


def plot_distribution(entities: dict[str, pd.DataFrame]) -> go.Figure:
    value_col = config.VALUE_COLUMN
    top_n = min(4, len(entities))
    _, _, returns = _best_worst_entities(entities, value_col)
    top_entities = sorted(returns, key=returns.get, reverse=True)[:top_n]

    fig = make_subplots(rows=top_n, cols=2, subplot_titles=[f"{e}" for e in top_entities * 2],
                        horizontal_spacing=0.1, vertical_spacing=0.12)

    for i, entity_id in enumerate(top_entities, 1):
        vals = entities[entity_id][value_col].dropna().values
        if len(vals) == 0:
            continue
        c = STORY_COLORS[(i - 1) % len(STORY_COLORS)]

        hist, bin_edges = np.histogram(vals, bins=30, density=True)
        fig.add_trace(go.Bar(x=bin_edges[:-1], y=hist, width=np.diff(bin_edges),
                             marker_color=c, opacity=0.6, showlegend=False), row=i, col=1)

        kde_x = np.linspace(vals.min(), vals.max(), 200)
        kde = scipy_stats.gaussian_kde(vals)
        fig.add_trace(go.Scatter(x=kde_x, y=kde(kde_x), mode="lines",
                                 line=dict(color=c, width=2), showlegend=False), row=i, col=1)

        scipy_stats.probplot(vals, dist="norm", plot=None)
        osm, osr = scipy_stats.probplot(vals, dist="norm", fit=False)
        fig.add_trace(go.Scatter(x=osm, y=osr, mode="markers",
                                 marker=dict(color=c, size=4), showlegend=False), row=i, col=2)

        slope, intercept, r_val, p_val, std_err = scipy_stats.linregress(osm, osr)
        line_x = np.array([osm.min(), osm.max()])
        line_y = slope * line_x + intercept
        fig.add_trace(go.Scatter(x=line_x, y=line_y, mode="lines",
                                 line=dict(color="#E02424", dash="dash"), showlegend=False), row=i, col=2)

    fig.update_layout(title=dict(text="Distribuição: Normalidade dos Preços", font=dict(size=18)),
                      height=320 * top_n, showlegend=False)
    return fig


def plot_calendar_heatmap(entities: dict[str, pd.DataFrame]) -> go.Figure:
    value_col = config.VALUE_COLUMN
    if not entities:
        return go.Figure()
    entity_id = list(entities.keys())[0]
    df = entities[entity_id].copy()
    if df.empty or df[value_col].dropna().empty:
        return go.Figure()
    df["year"] = df.index.year
    df["month"] = df.index.month
    pivot = df.pivot_table(values=value_col, index="year", columns="month", aggfunc="mean")

    fig = px.imshow(
        pivot.values, x=pivot.columns, y=pivot.index,
        labels=dict(x="Month", y="Year", color=f"Avg {value_col}"),
        title=f"Heatmap Anual — {entity_id}",
        aspect="auto", color_continuous_scale="RdYlBu",
        text_auto=".0f",
    )
    fig.update_layout(height=400,
                      title=dict(text=f"Calendário de Preços: {entity_id}", font=dict(size=18)))
    return fig


def plot_correlation(entities: dict[str, pd.DataFrame]) -> go.Figure:
    if not entities:
        return go.Figure()
    value_col = config.VALUE_COLUMN
    aligned = pd.DataFrame({eid: df[value_col] for eid, df in entities.items()}).dropna()
    if aligned.empty:
        return go.Figure()
    corr = aligned.corr()

    fig = px.imshow(
        corr.values, x=corr.columns, y=corr.columns,
        text_auto=".2f", title="Correlação entre Ativos",
        aspect="auto", color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
    )
    fig.update_layout(
        height=500,
        title=dict(text="Correlação: Quem Anda Junto?", font=dict(size=18)),
    )
    return fig


def plot_acf_pacf(entities: dict[str, pd.DataFrame]) -> go.Figure:
    value_col = config.VALUE_COLUMN
    top_n = min(3, len(entities))
    ents = list(entities.keys())[:top_n]

    fig = make_subplots(rows=top_n, cols=2,
                        subplot_titles=[f"{e}" for e in ents * 2],
                        vertical_spacing=0.12)

    for i, entity_id in enumerate(ents, 1):
        series = entities[entity_id][value_col].dropna()
        if len(series) < 3:
            continue
        nlags = min(30, len(series) // 2 - 1)
        if nlags < 1:
            continue

        acf_vals = acf(series, nlags=nlags)
        pacf_vals = pacf(series, nlags=nlags)
        conf = 1.96 / np.sqrt(len(series))

        fig.add_trace(go.Bar(x=list(range(nlags + 1)), y=acf_vals,
                             marker_color=STORY_COLORS[0], showlegend=False), row=i, col=1)
        fig.add_hline(y=conf, line=dict(color="gray", dash="dash", width=1), row=i, col=1)
        fig.add_hline(y=-conf, line=dict(color="gray", dash="dash", width=1), row=i, col=1)

        fig.add_trace(go.Bar(x=list(range(nlags + 1)), y=pacf_vals,
                             marker_color=STORY_COLORS[1], showlegend=False), row=i, col=2)
        fig.add_hline(y=conf, line=dict(color="gray", dash="dash", width=1), row=i, col=2)
        fig.add_hline(y=-conf, line=dict(color="gray", dash="dash", width=1), row=i, col=2)

    fig.update_layout(
        height=300 * top_n,
        title=dict(text="ACF & PACF: A Memória da Série", font=dict(size=18)),
        showlegend=False,
    )
    return fig


def plot_volatility(entities: dict[str, pd.DataFrame]) -> go.Figure:
    fig = go.Figure()
    colors = iter(STORY_COLORS)
    all_vols = []

    for entity_id, df in entities.items():
        if "Returns" not in df.columns:
            continue
        c = next(colors)
        ret = df["Returns"].dropna()
        if len(ret) < 12:
            continue
        vol = ret.rolling(12).std()
        fig.add_trace(go.Scatter(
            x=vol.index, y=vol.values, mode="lines",
            name=entity_id, opacity=0.7, line=dict(width=1.5, color=c),
        ))
        all_vols.append(vol)

    if all_vols:
        combined = pd.concat(all_vols).dropna()
        threshold = combined.quantile(0.95) if not combined.empty else 0.05
    else:
        threshold = 0.05
    fig.add_hline(y=threshold,
                  line=dict(color="#E02424", dash="dash", width=1),
                  annotation_text="High Vol Threshold")

    for start, end, label, color in EVENTS:
        fig.add_vrect(x0=start, x1=end, fillcolor=color, opacity=0.06, line_width=0)

    fig.update_layout(
        title=dict(text="Volatilidade: Períodos de Turbulência", font=dict(size=18)),
        xaxis_title="", yaxis_title="Rolling Std (12 periods)",
        hovermode="x unified", height=400,
    )
    return fig


def plot_drawdown(entities: dict[str, pd.DataFrame]) -> go.Figure:
    value_col = config.VALUE_COLUMN
    entity_id = list(entities.keys())[0]
    series = entities[entity_id][value_col].dropna()
    rolling_max = series.expanding().max()
    drawdown = (series - rolling_max) / rolling_max * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=drawdown.index, y=drawdown.values,
        mode="lines", name="Drawdown",
        fill="tozeroy", line=dict(color="#E02424", width=2),
        hovertemplate="%{x}<br>Drawdown: %{y:.1f}%<extra></extra>",
    ))

    fig.add_hline(y=-20, line=dict(color="#FF5630", dash="dash", width=1),
                  annotation_text="-20% (Severe)")

    if not drawdown.dropna().empty:
        min_dd = drawdown.min()
        min_date = drawdown.idxmin()
        fig.add_annotation(x=min_date, y=min_dd,
                           text=f"Peak Drawdown: {min_dd:.1f}%",
                           showarrow=True, arrowhead=1,
                           font=dict(color="#E02424", size=12))

    fig.update_layout(
        title=dict(text=f"Drawdown: Risco Histórico — {entity_id}", font=dict(size=18)),
        xaxis_title="", yaxis_title="Drawdown (%)",
        hovermode="x unified", height=400,
        yaxis=dict(ticksuffix="%"),
    )
    return fig


def plot_top_entities_comparison(entities: dict[str, pd.DataFrame]) -> go.Figure:
    value_col = config.VALUE_COLUMN
    _, _, returns = _best_worst_entities(entities, value_col)
    top_3 = sorted(returns, key=returns.get, reverse=True)[:3]
    bottom_3 = sorted(returns, key=returns.get)[:3]
    selected = top_3 + bottom_3

    fig = go.Figure()
    for eid in selected:
        series = entities[eid][value_col]
        if series.dropna().empty:
            continue
        normalized = series / series.iloc[0] * 100
        c = STORY_COLORS[selected.index(eid) % len(STORY_COLORS)]
        dash = "dot" if eid in bottom_3 else "solid"
        width = 2 if eid in top_3 else 1.5
        opacity = 0.9 if eid in top_3 else 0.5
        fig.add_trace(go.Scatter(
            x=normalized.index, y=normalized.values,
            mode="lines", name=eid, line=dict(color=c, width=width, dash=dash),
            opacity=opacity,
            hovertemplate="%{x}<br>%{y:.1f}%<br><b>%{fullData.name}</b><extra></extra>",
        ))

    fig.add_hline(y=100, line=dict(color="gray", dash="dot", width=1),
                  annotation_text="Start (100%)")

    fig.update_layout(
        title=dict(text="Top 3 vs Bottom 3: Comparação de Retorno", font=dict(size=18)),
        xaxis_title="", yaxis_title="Retorno Acumulado (%)",
        hovermode="x unified", height=450,
        legend=dict(orientation="h", y=-0.2),
        yaxis=dict(ticksuffix="%"),
    )
    return fig


def plot_monthly_returns_heatmap(entities: dict[str, pd.DataFrame]) -> go.Figure:
    if not entities:
        return go.Figure()
    entity_id = list(entities.keys())[0]
    df = entities[entity_id].copy()
    if "Returns" not in df.columns or df["Returns"].dropna().empty:
        return go.Figure()

    df["year"] = df.index.year
    df["month"] = df.index.month
    monthly = df.groupby(["year", "month"])["Returns"].mean().unstack() * 100

    fig = px.imshow(
        monthly.values, x=monthly.columns, y=monthly.index,
        labels=dict(x="Month", y="Year", color="Return %"),
        title=f"Retorno Mensal Médio — {entity_id}",
        aspect="auto", color_continuous_scale="RdYlGn",
        text_auto=".1f", zmin=-5, zmax=5,
    )
    fig.update_layout(
        height=400,
        title=dict(text=f"Retornos Mensais: Onde o Dinheiro Entra? — {entity_id}", font=dict(size=18)),
    )
    return fig
