"""
Build an interactive one-page dashboard (a single HTML file) from the SQLite database.

Sections:
  1. KPI cards and a KPI table (from sql/kpis.sql, plus volatility and drawdown in pandas)
  2. Performance comparison: every stock rebased to 100, benchmark dashed
  3. Candlestick chart with 20- and 50-day moving averages and volume, one stock at a time
  4. Correlation of daily returns between stocks
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

NAVY = "#1f3a68"
PALETTE = ["#1f3a68", "#2a7f8f", "#c0392b", "#e67e22", "#8e44ad", "#27ae60", "#7f8c8d"]


def load_data(db_path, kpi_sql_path):
    con = sqlite3.connect(db_path)
    prices = pd.read_sql("SELECT * FROM fact_daily_price ORDER BY ticker, trade_date", con,
                         parse_dates=["trade_date"])
    kpis = pd.read_sql(Path(kpi_sql_path).read_text(), con)
    tickers = pd.read_sql("SELECT * FROM dim_ticker", con)
    con.close()
    return prices, kpis, tickers


def add_risk_metrics(prices, kpis):
    """Annualized volatility and max drawdown over the last 365 days, per stock."""
    rows = []
    for ticker, g in prices.groupby("ticker"):
        last_year = g[g["trade_date"] > g["trade_date"].max() - pd.Timedelta(days=365)]
        returns = last_year["close"].pct_change().dropna()
        running_peak = last_year["close"].cummax()
        drawdown = (last_year["close"] / running_peak - 1).min()
        rows.append({"ticker": ticker,
                     "volatility": returns.std() * np.sqrt(252),
                     "max_drawdown": drawdown})
    return kpis.merge(pd.DataFrame(rows), on="ticker", how="left")


def kpi_cards_html(kpis):
    stocks = kpis[kpis["is_benchmark"] == 0]
    bench = kpis[kpis["is_benchmark"] == 1].iloc[0]
    best = stocks.loc[stocks["return_1y"].idxmax()]
    riskiest = stocks.loc[stocks["volatility"].idxmax()]
    beat = int((stocks["return_1y"] > bench["return_1y"]).sum())
    cards = [
        ("Best 1-year return", f"{best['return_1y']:+.1%}", f"{best['ticker']} · {best['company_name']}"),
        ("Benchmark (SPY) 1-year", f"{bench['return_1y']:+.1%}", "S&P 500 ETF"),
        ("Stocks beating SPY", f"{beat} of {len(stocks)}", "over the last year"),
        ("Most volatile", f"{riskiest['volatility']:.0%}", f"{riskiest['ticker']} · annualized"),
    ]
    return "".join(
        f'<div class="card"><div class="t">{t}</div><div class="v">{v}</div><div class="s">{s}</div></div>'
        for t, v, s in cards)


def kpi_table_html(kpis):
    show = kpis.copy()
    fmt = {
        "last_close": "${:,.2f}", "return_1y": "{:+.1%}", "high_52w": "${:,.2f}",
        "low_52w": "${:,.2f}", "volatility": "{:.1%}", "max_drawdown": "{:.1%}",
    }
    for col, f in fmt.items():
        show[col] = show[col].map(lambda x, f=f: f.format(x) if pd.notna(x) else "–")
    header = ["Ticker", "Company", "Sector", "Last close", "1-yr return",
              "52-wk high", "52-wk low", "Volatility", "Max drawdown"]
    cols = ["ticker", "company_name", "sector", "last_close", "return_1y",
            "high_52w", "low_52w", "volatility", "max_drawdown"]
    body = "".join("<tr>" + "".join(f"<td>{r[c]}</td>" for c in cols) + "</tr>"
                   for _, r in show.iterrows())
    return "<table><tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr>" + body + "</table>"


def performance_chart(prices, tickers):
    """Every stock rebased to 100 on the first day, so different prices are comparable."""
    bench = tickers.loc[tickers["is_benchmark"] == 1, "ticker"].iloc[0]
    fig = go.Figure()
    for i, (ticker, g) in enumerate(prices.groupby("ticker")):
        rebased = g["close"] / g["close"].iloc[0] * 100
        is_bench = ticker == bench
        fig.add_trace(go.Scatter(
            x=g["trade_date"], y=rebased, name=ticker, mode="lines",
            line=dict(width=3 if is_bench else 1.8, dash="dash" if is_bench else "solid",
                      color="#333" if is_bench else PALETTE[i % len(PALETTE)])))
    fig.update_layout(title="Performance comparison (start = 100)", height=420,
                      yaxis_title="Growth of 100", hovermode="x unified", template="plotly_white",
                      margin=dict(l=50, r=20, t=60, b=40))
    return fig


def candlestick_chart(prices, tickers):
    """Candlestick + moving averages + volume, with a dropdown to switch stocks."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25],
                        vertical_spacing=0.03)
    names = list(prices["ticker"].unique())
    traces_per_stock = 4
    for i, ticker in enumerate(names):
        g = prices[prices["ticker"] == ticker].tail(252)  # last ~1 trading year
        full = prices[prices["ticker"] == ticker]
        ma20 = full["close"].rolling(20).mean().loc[g.index]
        ma50 = full["close"].rolling(50).mean().loc[g.index]
        visible = i == 0
        fig.add_trace(go.Candlestick(x=g["trade_date"], open=g["open"], high=g["high"],
                                     low=g["low"], close=g["close"], name=ticker,
                                     visible=visible, showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=g["trade_date"], y=ma20, name="20-day avg",
                                 line=dict(color="#e67e22", width=1.5), visible=visible), row=1, col=1)
        fig.add_trace(go.Scatter(x=g["trade_date"], y=ma50, name="50-day avg",
                                 line=dict(color=NAVY, width=1.5), visible=visible), row=1, col=1)
        fig.add_trace(go.Bar(x=g["trade_date"], y=g["volume"], name="Volume",
                             marker_color="#9aa5b4", visible=visible, showlegend=False), row=2, col=1)
    buttons = []
    for i, ticker in enumerate(names):
        vis = [False] * len(names) * traces_per_stock
        vis[i * traces_per_stock:(i + 1) * traces_per_stock] = [True] * traces_per_stock
        buttons.append(dict(label=ticker, method="update",
                            args=[{"visible": vis}, {"title": f"{ticker}: last 12 months"}]))
    fig.update_layout(title=f"{names[0]}: last 12 months", height=560, template="plotly_white",
                      xaxis_rangeslider_visible=False,
                      updatemenus=[dict(buttons=buttons, x=1, xanchor="right", y=1.12)],
                      legend=dict(orientation="h", y=1.04, x=0),
                      margin=dict(l=50, r=20, t=80, b=40))
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    return fig


def correlation_chart(prices):
    """How closely daily returns move together over the last year (1 = identical)."""
    recent = prices[prices["trade_date"] > prices["trade_date"].max() - pd.Timedelta(days=365)]
    wide = recent.pivot(index="trade_date", columns="ticker", values="close").pct_change()
    corr = wide.corr().round(2)
    fig = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1,
                               colorscale="RdBu", reversescale=True, text=corr.values,
                               texttemplate="%{text}"))
    fig.update_layout(title="Correlation of daily returns (last 12 months)", height=420,
                      template="plotly_white", margin=dict(l=50, r=20, t=60, b=40))
    return fig


def build_dashboard(db_path, kpi_sql_path, out_path):
    prices, kpis, tickers = load_data(db_path, kpi_sql_path)
    kpis = add_risk_metrics(prices, kpis)
    last = prices["trade_date"].max().strftime("%b %d, %Y")
    first = prices["trade_date"].min().strftime("%b %d, %Y")

    charts = [performance_chart(prices, tickers), candlestick_chart(prices, tickers),
              correlation_chart(prices)]
    # Include the plotly library once (first chart) so the file works offline
    chart_html = "".join(
        f'<div class="panel">{fig.to_html(full_html=False, include_plotlyjs=(i == 0))}</div>'
        for i, fig in enumerate(charts))

    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Stock Performance Dashboard</title>
<style>
 body{{font-family:Segoe UI,Arial,sans-serif;background:#f4f6fa;margin:0;padding:24px;color:#222}}
 h1{{color:{NAVY};margin:0}} .sub{{color:#666;margin:4px 0 18px}}
 .cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}}
 .card{{background:#fff;border:1px solid #d5dbe5;border-radius:8px;padding:14px}}
 .t{{color:#666;font-size:13px}} .v{{font-size:28px;font-weight:700;color:{NAVY}}} .s{{color:#888;font-size:12px}}
 .panel{{background:#fff;border:1px solid #d5dbe5;border-radius:8px;padding:8px;margin-bottom:16px}}
 table{{border-collapse:collapse;width:100%;font-size:13px}}
 th{{background:#e8edf5;text-align:left}} th,td{{padding:6px 8px;border-bottom:1px solid #e3e7ee}}
 .foot{{color:#888;font-size:12px}}
</style></head><body>
<h1>Stock Performance Dashboard</h1>
<div class="sub">Daily prices {first} – {last} · Source: Yahoo Finance via yfinance · Benchmark: SPY</div>
<div class="cards">{kpi_cards_html(kpis)}</div>
<div class="panel"><h3 style="margin:6px 8px;color:{NAVY}">Key metrics (last 12 months)</h3>{kpi_table_html(kpis)}</div>
{chart_html}
<div class="foot">Prices are adjusted for splits and dividends. For learning and analysis, not investment advice.</div>
</body></html>"""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(html, encoding="utf-8")
    return out_path
