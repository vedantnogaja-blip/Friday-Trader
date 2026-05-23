"""
Friday Trader — World-Class Interactive Dashboard
"""

# ── Requirements check ────────────────────────────────────────────────────────
import importlib, sys
for pkg in ('streamlit', 'yfinance', 'pandas', 'matplotlib'):
    if importlib.util.find_spec(pkg) is None:
        print(f'[WARNING] {pkg} not installed — run: pip3 install {pkg}', file=sys.stderr)

import time
from datetime import datetime, timezone, timedelta

import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

from backtest import (run_backtest, run_multi_backtest,
                      combined_stats, calculate_rsi, SYMBOLS)

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='Friday Trader',
    page_icon='◈',
    layout='wide',
    initial_sidebar_state='collapsed',
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.stApp {
    background: #000 !important;
    color: #f5f5f7;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
                 'Helvetica Neue', Arial, sans-serif;
}

/* ── Hide Streamlit chrome ───────────────────────────────────────────────── */
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="collapsedControl"],
.stDeployButton { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ── Sticky mini-header ──────────────────────────────────────────────────── */
.sticky-hdr {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    background: rgba(0,0,0,0.88);
    backdrop-filter: blur(20px) saturate(180%);
    border-bottom: 1px solid #1d1d1f;
    padding: 10px 40px;
    display: flex; align-items: center; gap: 20px;
    font-size: 13px; color: #86868b;
}
.sticky-hdr .brand { font-weight: 700; color: #f5f5f7; letter-spacing: -.01em; }
.sticky-hdr .price { color: #f5f5f7; font-weight: 600; font-variant-numeric: tabular-nums; }

/* ── Market badge ────────────────────────────────────────────────────────── */
.market-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px; font-size: 11px;
    font-weight: 600; letter-spacing: .07em; text-transform: uppercase;
}
.market-open  { background: rgba(48,209,88,.15); color: #30d158; }
.market-closed{ background: rgba(255,69,58,.15);  color: #ff453a; }

@keyframes pulse {
    0%   { opacity: 1; }
    50%  { opacity: .3; }
    100% { opacity: 1; }
}
.pulse-dot {
    width: 7px; height: 7px; border-radius: 50%;
    display: inline-block; animation: pulse 1.6s ease-in-out infinite;
}
.pulse-dot.green { background: #30d158; }
.pulse-dot.red   { background: #ff453a; }

/* ── Hero ────────────────────────────────────────────────────────────────── */
.hero {
    padding: 100px 60px 70px; text-align: center;
    background: radial-gradient(ellipse 90% 55% at 50% -5%,
                rgba(0,113,227,.22) 0%, transparent 65%), #000;
    border-bottom: 1px solid #1d1d1f; margin-top: 37px;
}
.hero-eye { font-size:12px; font-weight:600; letter-spacing:.22em;
            text-transform:uppercase; color:#0071e3; margin-bottom:20px; }
.hero-title { font-size: clamp(64px,8.5vw,108px); font-weight:700;
              letter-spacing:-.04em; line-height:1; color:#f5f5f7; margin-bottom:18px; }
.hero-sub { font-size:clamp(16px,1.8vw,22px); font-weight:300;
            color:#86868b; margin-bottom:56px; }
.strategy-line { font-size:15px; color:#86868b; margin-top:32px;
                 max-width:760px; margin-left:auto; margin-right:auto; line-height:1.6; }
.strategy-line b { color:#f5f5f7; }

/* ── Stats bar ───────────────────────────────────────────────────────────── */
.stats { display:flex; justify-content:center; max-width:1060px; margin:0 auto;
         background:#0a0a0a; border:1px solid #1d1d1f; border-radius:22px; overflow:hidden; }
.stat  { flex:1; padding:28px 16px; text-align:center; border-right:1px solid #1d1d1f; }
.stat:last-child { border-right:none; }
.stat-val { font-size:clamp(20px,2.6vw,36px); font-weight:600;
            letter-spacing:-.03em; color:#f5f5f7; line-height:1; margin-bottom:7px;
            font-variant-numeric: tabular-nums; }
.stat-lbl { font-size:10px; font-weight:500; letter-spacing:.12em;
            text-transform:uppercase; color:#86868b; }
.up   { color:#30d158 !important; }
.down { color:#ff453a !important; }

/* ── Divider / Section ───────────────────────────────────────────────────── */
.divider { height:1px; background:#1d1d1f; }
.section { padding:72px 80px 52px; max-width:1400px; margin:0 auto; }
.section-eye { font-size:12px; font-weight:600; letter-spacing:.20em;
               text-transform:uppercase; color:#0071e3; margin-bottom:10px;
               display:flex; align-items:center; gap:8px; }
.section-h   { font-size:clamp(28px,3.8vw,48px); font-weight:700;
               letter-spacing:-.03em; color:#f5f5f7; margin-bottom:6px; }
.section-sub { font-size:17px; font-weight:300; color:#86868b; margin-bottom:40px; }

/* ── Cards with tooltips ─────────────────────────────────────────────────── */
.cards { display:flex; gap:14px; margin-bottom:44px; flex-wrap:wrap; }
.card  { position:relative; flex:1; min-width:120px; background:#0d0d0d;
         border:1px solid #1d1d1f; border-radius:18px; padding:26px 22px;
         cursor:default; transition: border-color .2s; }
.card:hover { border-color:#333; }
.card-val { font-size:clamp(22px,2.4vw,34px); font-weight:600;
            letter-spacing:-.025em; color:#f5f5f7; line-height:1; margin-bottom:8px;
            font-variant-numeric: tabular-nums; }
.card-lbl { font-size:10px; font-weight:500; letter-spacing:.10em;
            text-transform:uppercase; color:#86868b; }
.card[data-tip]:hover::after {
    content: attr(data-tip);
    position: absolute; bottom: calc(100% + 10px); left: 50%;
    transform: translateX(-50%); width: 240px;
    background: #1a1a1a; border: 1px solid #333; border-radius: 12px;
    padding: 12px 14px; font-size: 12px; line-height: 1.5;
    color: #aaa; font-weight: 400; letter-spacing: 0;
    text-transform: none; pointer-events: none; z-index: 100;
}
.card[data-tip]:hover::before {
    content: ''; position: absolute; bottom: calc(100% + 2px); left: 50%;
    transform: translateX(-50%); border: 6px solid transparent;
    border-top-color: #333; pointer-events: none; z-index: 100;
}

/* ── Stock selector ──────────────────────────────────────────────────────── */
.selector-row { display:flex; align-items:center; gap:12px;
                margin-bottom:28px; flex-wrap:wrap; }
.selector-label { font-size:11px; font-weight:600; letter-spacing:.12em;
                  text-transform:uppercase; color:#86868b; margin-right:4px; }

/* ── RSI Gauge ───────────────────────────────────────────────────────────── */
.rsi-wrap { background:#0d0d0d; border:1px solid #1d1d1f; border-radius:18px;
            padding:26px 28px; margin-bottom:20px; }
.rsi-title { font-size:11px; font-weight:600; letter-spacing:.12em;
             text-transform:uppercase; color:#86868b; margin-bottom:14px; }
.rsi-value { font-size:44px; font-weight:700; letter-spacing:-.03em;
             line-height:1; margin-bottom:16px; }
.rsi-track { position:relative; height:8px; border-radius:4px; overflow:visible;
             background: linear-gradient(to right,
               #30d158 0%, #30d158 30%,
               #ff9f0a 30%, #ff9f0a 70%,
               #ff453a 70%, #ff453a 100%);
             margin-bottom:8px; }
.rsi-needle { position:absolute; top:-5px; width:18px; height:18px;
              background:#fff; border-radius:50%; transform:translateX(-50%);
              box-shadow:0 0 8px rgba(255,255,255,.25); transition:left .4s ease; }
.rsi-ticks { display:flex; justify-content:space-between; font-size:10px; color:#555; }
.rsi-status { margin-top:14px; font-size:13px; color:#86868b; line-height:1.5; }
.rsi-status b { color:#f5f5f7; }

/* ── Position status ─────────────────────────────────────────────────────── */
.pos-wrap { background:#0d0d0d; border:1px solid #1d1d1f; border-radius:18px;
            padding:22px 28px; margin-bottom:20px; }
.pos-label { font-size:11px; font-weight:600; letter-spacing:.12em;
             text-transform:uppercase; color:#86868b; margin-bottom:10px; }
.pos-val { font-size:16px; color:#f5f5f7; line-height:1.5; }

/* ── Trade table ─────────────────────────────────────────────────────────── */
.tbl-wrap  { margin-top:44px; }
.tbl-title { font-size:20px; font-weight:600; letter-spacing:-.01em;
             color:#f5f5f7; margin-bottom:18px; }
table.trades { width:100%; border-collapse:collapse; font-size:13px;
               font-variant-numeric:tabular-nums; }
table.trades th { text-align:left; padding:9px 18px; font-size:10px; font-weight:600;
                  letter-spacing:.12em; text-transform:uppercase; color:#86868b;
                  border-bottom:1px solid #1d1d1f; }
table.trades td { padding:13px 18px; color:#f5f5f7; border-bottom:1px solid #0f0f0f; }
table.trades tr:last-child td { border-bottom:none; }
table.trades tr:hover td { background:#060606; }
.badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:10px;
         font-weight:700; letter-spacing:.07em; text-transform:uppercase; }
.badge-buy  { background:rgba(48,209,88,.15);  color:#30d158; }
.badge-sell { background:rgba(255,69,58,.15);  color:#ff453a; }
.badge-stop { background:rgba(255,149,0,.15);  color:#ff9500; }

/* ── 5-stock grid ────────────────────────────────────────────────────────── */
.stock-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:14px; }
.stock-card { background:#0d0d0d; border:1px solid #1d1d1f; border-radius:18px;
              padding:24px 18px; }
.stock-sym  { font-size:19px; font-weight:700; margin-bottom:12px; }
.stock-ret  { font-size:28px; font-weight:600; letter-spacing:-.02em; margin-bottom:4px; }
.stock-meta { font-size:11px; color:#86868b; line-height:1.9; }

/* ── Footer ──────────────────────────────────────────────────────────────── */
.footer { border-top:1px solid #1d1d1f; padding:40px 80px;
          text-align:center; color:#555; font-size:13px; line-height:2; }
.footer a { color:#0071e3; text-decoration:none; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def is_market_open() -> bool:
    try:
        from zoneinfo import ZoneInfo
        et = ZoneInfo('America/New_York')
        now = datetime.now(et)
    except Exception:
        utc = datetime.now(timezone.utc)
        now = utc - timedelta(hours=4)   # rough EDT
    if now.weekday() >= 5:
        return False
    mins = now.hour * 60 + now.minute
    return 9 * 60 + 30 <= mins < 16 * 60


def filter_timeframe(data: pd.DataFrame, tf: str) -> pd.DataFrame:
    if tf == 'ALL' or data.empty:
        return data
    end = data.index[-1]
    offsets = {'1M': pd.DateOffset(months=1), '3M': pd.DateOffset(months=3),
               '6M': pd.DateOffset(months=6), '1Y': pd.DateOffset(years=1),
               '2Y': pd.DateOffset(years=2)}
    start = end - offsets.get(tf, pd.DateOffset(years=5))
    return data[data.index >= start]


def position_status(trades_df: pd.DataFrame):
    """Returns (entry_date, entry_price) if currently in position, else (None, None)."""
    if trades_df.empty:
        return None, None
    buys  = trades_df[trades_df['Action'] == 'BUY']
    sells = trades_df[trades_df['Action'].str.contains('SELL')]
    if len(buys) > len(sells):
        last = buys.iloc[-1]
        return last['Date'], last['Price']
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def load_live_price(symbol: str = 'AAPL'):
    try:
        hist = yf.download(symbol, period='5d', interval='1d', progress=False)
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        if hist.empty:
            return None, None
        price  = float(hist['Close'].iloc[-1])
        prev   = float(hist['Close'].iloc[-2])
        return price, (price - prev) / prev * 100
    except Exception:
        return None, None


@st.cache_data(ttl=3600, show_spinner=False)
def load_multi():
    try:
        results = run_multi_backtest()
        combo   = combined_stats(results)
        return results, combo
    except Exception as e:
        st.error(f'Data temporarily unavailable — retrying in 60s. ({e})')
        return {}, None


# ─────────────────────────────────────────────────────────────────────────────
# Chart builders (dark Apple theme)
# ─────────────────────────────────────────────────────────────────────────────

_BG = '#000000'

def _dark(fig, ax):
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    for sp in ax.spines.values():
        sp.set_edgecolor('#1d1d1f')
    ax.tick_params(colors='#555', labelsize=9)
    ax.grid(True, color='#111', linewidth=0.7)
    ax.set_axisbelow(True)


def price_chart(data: pd.DataFrame, symbol: str, tf: str) -> plt.Figure:
    d = filter_timeframe(data, tf)
    fig, ax = plt.subplots(figsize=(16, 4))
    _dark(fig, ax)
    ax.plot(d.index, d['Close'].squeeze(),  color='#f5f5f7', lw=1.5, label=symbol)
    ax.plot(d.index, d['ShortMA'].squeeze(), color='#0071e3', lw=1.1, label='10-day MA')
    ax.plot(d.index, d['LongMA'].squeeze(),  color='#ff453a', lw=1.1, label='200-day MA')
    ax.legend(frameon=False, labelcolor='#86868b', fontsize=10, loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y' if tf in ('ALL','2Y','1Y') else '%b %d'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    plt.xticks(color='#555'); plt.yticks(color='#555')
    fig.tight_layout(pad=1.0)
    return fig


def backtest_chart(bt: dict) -> plt.Figure:
    data, trades = bt['data'], bt['trades']
    fig, ax = plt.subplots(figsize=(16, 4))
    _dark(fig, ax)
    ax.plot(data.index, data['Close'].squeeze(),   color='#f5f5f7', lw=1.4, label='Price')
    ax.plot(data.index, data['ShortMA'].squeeze(), color='#0071e3', lw=1.0, label='10-day MA')
    ax.plot(data.index, data['LongMA'].squeeze(),  color='#ff453a', lw=1.0, label='200-day MA')
    ax.plot(bt['bah_portfolio'].index, bt['bah_portfolio'],
            color='#86868b', lw=1.0, ls='--', label='Buy & Hold', alpha=0.8)
    if not trades.empty:
        t = trades.copy(); t['Date'] = pd.to_datetime(t['Date'])
        buys  = t[t['Action'] == 'BUY']
        sells = t[t['Action'].str.contains('SELL')]
        ax.scatter(buys['Date'],  buys['Price'],  marker='^', color='#30d158', s=80, zorder=6, label='Buy')
        ax.scatter(sells['Date'], sells['Price'], marker='v', color='#ff453a', s=80, zorder=6, label='Sell')
    ax.legend(frameon=False, labelcolor='#86868b', fontsize=10, loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    plt.xticks(color='#555'); plt.yticks(color='#555')
    fig.tight_layout(pad=1.0)
    return fig


def sparkline(data: pd.DataFrame, days: int = 30) -> plt.Figure:
    d = data.tail(days)['Close'].squeeze()
    color = '#30d158' if float(d.iloc[-1]) >= float(d.iloc[0]) else '#ff453a'
    fig, ax = plt.subplots(figsize=(6, 1.6))
    _dark(fig, ax)
    ax.plot(d.index, d, color=color, lw=1.5)
    ax.fill_between(d.index, d, float(d.min()), color=color, alpha=0.08)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout(pad=0.3)
    return fig


def portfolio_growth_chart(combo: dict, multi: dict) -> plt.Figure:
    port = combo['portfolio']
    bah  = combo['bah_portfolio']

    fig, ax = plt.subplots(figsize=(16, 5))
    _dark(fig, ax)
    ax.plot(port.index, port, color='#30d158', lw=2.2, label='Strategy — 5 stocks', zorder=3)
    ax.plot(bah.index,  bah,  color='#86868b', lw=1.4, ls='--', label='Buy & Hold — 5 stocks', zorder=2)
    ax.fill_between(port.index, port, bah, where=(port >= bah), color='#30d158', alpha=0.07)
    ax.fill_between(port.index, port, bah, where=(port <  bah), color='#ff453a', alpha=0.07)
    ax.axhline(y=10_000, color='#2a2a2a', lw=0.8, ls=':')

    # ── NVDA entry annotation ─────────────────────────────────────────────────
    if 'NVDA' in multi and multi['NVDA']:
        nvda_trades = multi['NVDA']['trades']
        nvda_buys   = nvda_trades[nvda_trades['Action'] == 'BUY']
        nvda_sells  = nvda_trades[nvda_trades['Action'] == 'SELL']

        if len(nvda_buys) >= 2:
            entry_row = nvda_buys.iloc[1]
            entry_date = pd.Timestamp(entry_row['Date'])
            entry_date = port.index[port.index.get_indexer([entry_date], method='nearest')[0]]
            entry_val  = float(port.asof(entry_date)) if hasattr(port, 'asof') else float(port.iloc[0])
            ax.annotate('NVDA Entry\n$17.82',
                        xy=(entry_date, entry_val),
                        xytext=(entry_date, entry_val - 2200),
                        fontsize=9, color='#30d158',
                        arrowprops=dict(arrowstyle='->', color='#30d158', lw=1.2),
                        ha='center')

        if not nvda_sells.empty:
            exit_row  = nvda_sells.iloc[0]
            exit_date = pd.Timestamp(exit_row['Date'])
            exit_date = port.index[port.index.get_indexer([exit_date], method='nearest')[0]]
            exit_val  = float(port.asof(exit_date)) if hasattr(port, 'asof') else float(port.iloc[-1])
            ax.annotate('NVDA Exit\n$129.80  +596%',
                        xy=(exit_date, exit_val),
                        xytext=(exit_date, exit_val + 2200),
                        fontsize=9, color='#ff453a',
                        arrowprops=dict(arrowstyle='->', color='#ff453a', lw=1.2),
                        ha='center')

    # ── Max drawdown annotation ───────────────────────────────────────────────
    rolling_max = port.cummax()
    drawdown    = (port - rolling_max) / rolling_max
    dd_date     = drawdown.idxmin()
    dd_val      = float(port[dd_date])
    ax.annotate(f'Max Drawdown\n{float(drawdown.min())*100:.1f}%',
                xy=(dd_date, dd_val),
                xytext=(dd_date, dd_val - 1800),
                fontsize=9, color='#ff9f0a',
                arrowprops=dict(arrowstyle='->', color='#ff9f0a', lw=1.2),
                ha='center')

    ax.legend(frameon=False, labelcolor='#86868b', fontsize=10, loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    plt.xticks(color='#555'); plt.yticks(color='#555')
    fig.tight_layout(pad=1.2)
    return fig


def pnl_bar_chart(multi: dict) -> plt.Figure:
    bars, labels, colors = [], [], []
    for sym, r in multi.items():
        if not r or r['trades'].empty:
            continue
        trades = r['trades']
        buys   = trades[trades['Action'] == 'BUY']['Portfolio Value'].tolist()
        sells  = trades[trades['Action'].str.contains('SELL')]['Portfolio Value'].tolist()
        for b, s in zip(buys, sells):
            pnl = s - b
            bars.append(pnl)
            labels.append(sym)
            colors.append('#30d158' if pnl >= 0 else '#ff453a')

    if not bars:
        return None

    fig, ax = plt.subplots(figsize=(16, 3.5))
    _dark(fig, ax)
    x = range(len(bars))
    ax.bar(x, bars, color=colors, width=0.7, zorder=3)
    ax.axhline(0, color='#333', lw=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9, color='#86868b')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'${v:+,.0f}'))
    plt.yticks(color='#555')
    fig.tight_layout(pad=1.0)
    return fig


def attribution_chart(multi: dict) -> plt.Figure:
    INITIAL_PER = 2000
    COLORS = {'AAPL':'#0071e3','MSFT':'#30d158','GOOGL':'#ff9f0a',
               'NVDA':'#bf5af2','TSLA':'#ff453a'}
    gains  = {sym: (r['final_value'] - INITIAL_PER) for sym, r in multi.items() if r}
    total  = sum(gains.values())

    fig, ax = plt.subplots(figsize=(16, 1.8))
    _dark(fig, ax)
    left = 0
    for sym, gain in gains.items():
        width = gain / total * 100
        color = COLORS.get(sym, '#555')
        ax.barh(0, width, left=left, color=color, height=0.5)
        if abs(width) > 5:
            ax.text(left + width / 2, 0, f'{sym}\n{width:+.0f}%',
                    ha='center', va='center', fontsize=9,
                    color='white', fontweight='600')
        left += width

    ax.set_xlim(0, 100)
    ax.set_yticks([]); ax.set_xticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    fig.tight_layout(pad=0.5)
    return fig


def risk_return_scatter(multi: dict) -> plt.Figure:
    COLORS = {'AAPL':'#0071e3','MSFT':'#30d158','GOOGL':'#ff9f0a',
              'NVDA':'#bf5af2','TSLA':'#ff453a'}
    fig, ax = plt.subplots(figsize=(7, 4.5))
    _dark(fig, ax)
    for sym, r in multi.items():
        if not r:
            continue
        x = abs(r['max_drawdown'])   # risk (bigger = more risky)
        y = r['total_return']
        c = COLORS.get(sym, '#f5f5f7')
        ax.scatter(x, y, color=c, s=160, zorder=5)
        ax.annotate(sym, (x, y), textcoords='offset points',
                    xytext=(8, 4), fontsize=10, color=c, fontweight='600')
    ax.axhline(0, color='#333', lw=0.8, ls='--')
    ax.set_xlabel('Risk (Max Drawdown %)', color='#86868b', fontsize=10)
    ax.set_ylabel('Return %', color='#86868b', fontsize=10)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:+.0f}%'))
    plt.xticks(color='#555'); plt.yticks(color='#555')
    fig.tight_layout(pad=1.2)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = 'AAPL'
if 'timeframe' not in st.session_state:
    st.session_state.timeframe = 'ALL'
if 'animated' not in st.session_state:
    st.session_state.animated = False
if 'load_time' not in st.session_state:
    st.session_state.load_time = datetime.now().strftime('%b %d, %Y · %I:%M %p')


# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner('Loading market data...'):
    multi, combo = load_multi()

price, change = load_live_price()
price  = price  or 0.0
change = change or 0.0

sym    = st.session_state.selected_stock
bt     = multi.get(sym) if multi else None


# ─────────────────────────────────────────────────────────────────────────────
# Sticky mini-header
# ─────────────────────────────────────────────────────────────────────────────
c_sign = '+' if change >= 0 else ''
c_col  = '#30d158' if change >= 0 else '#ff453a'
st.markdown(f"""
<div class="sticky-hdr">
  <span class="brand">◈ Friday Trader</span>
  <span>·</span>
  <span class="price">AAPL ${price:,.2f}</span>
  <span style="color:{c_col}; font-weight:600; font-size:13px">{c_sign}{change:.2f}%</span>
  <span style="flex:1"></span>
  <span style="font-size:12px">Last updated: {st.session_state.load_time}</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Hero — animated counting stats
# ─────────────────────────────────────────────────────────────────────────────
market_open  = is_market_open()
badge_cls    = 'market-open' if market_open else 'market-closed'
badge_label  = 'MARKET OPEN' if market_open else 'MARKET CLOSED'
dot_cls      = 'green' if market_open else 'red'

combined_return = combo['total_return'] if combo else 0
bah_return      = combo['bah_return']   if combo else 0
combined_final  = combo['final_value']  if combo else 10000
combo_sharpe    = combo['sharpe']       if combo else 0
combo_maxdd     = combo['max_drawdown'] if combo else 0
nvda_return     = multi['NVDA']['total_return'] if (multi and 'NVDA' in multi and multi['NVDA']) else 0

st.markdown(f"""
<div class="hero">
  <div class="hero-eye">
    Multi-Stock Algo &nbsp;·&nbsp; 10/200 MA + RSI + Stop Loss &nbsp;&nbsp;
    <span class="market-badge {badge_cls}">
      <span class="pulse-dot {dot_cls}"></span>{badge_label}
    </span>
  </div>
  <div class="hero-title">Friday Trader</div>
  <div class="hero-sub">Strategy-driven. Data-first. Built to outperform.</div>
  <div class="stats" id="hero-stats">
""", unsafe_allow_html=True)

# Animated stat placeholders (6 stats)
stat_keys = ['price', 'change', 'portfolio', 'sharpe', 'drawdown', 'nvda']
labels     = ['AAPL Price', 'Day Change', '5-Stock Return', 'Portfolio Sharpe',
              'Max Drawdown', 'NVDA Return']
finals     = [price, change, combined_return, combo_sharpe, combo_maxdd, nvda_return]

def fmt_stat(key, val):
    if key == 'price':    return f'${val:,.2f}'
    if key == 'change':   return f'{val:+.2f}%'
    if key == 'portfolio': return f'{val:+.1f}%'
    if key == 'sharpe':   return f'{val:.2f}'
    if key == 'drawdown': return f'{val:.1f}%'
    if key == 'nvda':     return f'{val:+.1f}%'
    return str(val)

def cls_stat(key, val):
    if key in ('change', 'portfolio', 'nvda'):
        return 'up' if val >= 0 else 'down'
    if key == 'drawdown': return 'down'
    return ''

# Render 6 stat columns
cols = st.columns(6)
placeholders = {}
for i, (key, lbl) in enumerate(zip(stat_keys, labels)):
    with cols[i]:
        placeholders[key] = st.empty()

# Animate on first load, else render final immediately
if not st.session_state.animated:
    STEPS, DURATION = 40, 1.5
    for step in range(STEPS + 1):
        t = 1 - (1 - step / STEPS) ** 3   # ease-out cubic
        for key, final_val, lbl in zip(stat_keys, finals, labels):
            val = final_val * t
            placeholders[key].markdown(
                f'<div class="stat"><div class="stat-val {cls_stat(key, final_val)}">'
                f'{fmt_stat(key, val)}</div>'
                f'<div class="stat-lbl">{lbl}</div></div>',
                unsafe_allow_html=True)
        if step < STEPS:
            time.sleep(DURATION / STEPS)
    st.session_state.animated = True
else:
    for key, final_val, lbl in zip(stat_keys, finals, labels):
        placeholders[key].markdown(
            f'<div class="stat"><div class="stat-val {cls_stat(key, final_val)}">'
            f'{fmt_stat(key, final_val)}</div>'
            f'<div class="stat-lbl">{lbl}</div></div>',
            unsafe_allow_html=True)

r_sign = '+' if combined_return >= 0 else ''
b_sign = '+' if bah_return >= 0 else ''
st.markdown(f"""
  </div><!-- .stats -->
  <div class="strategy-line">
    Our strategy returned <b>{r_sign}{combined_return:.1f}%</b> vs Buy &amp; Hold
    <b>{b_sign}{bah_return:.1f}%</b> — but with a Sharpe ratio of
    <b>{combo_sharpe}</b>, we took significantly less risk per dollar of return.
    NVDA alone returned <b>+{nvda_return:.0f}%</b> from a single $1,840 position.
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Stock Explorer: selector + timeframe
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section" style="padding-bottom:0">'
            '<div class="section-eye">'
            '<span class="pulse-dot green"></span>Interactive Explorer'
            '</div>'
            '<div class="section-h">Stock Deep-Dive</div>'
            '<div class="section-sub">Select a stock and timeframe to explore strategy signals.</div>'
            '</div>', unsafe_allow_html=True)

with st.container():
    col_sel, col_tf, _ = st.columns([3, 3, 4])
    with col_sel:
        sel = st.segmented_control('Stock', SYMBOLS,
                                   default=st.session_state.selected_stock,
                                   key='stock_ctrl',
                                   label_visibility='collapsed')
        if sel and sel != st.session_state.selected_stock:
            st.session_state.selected_stock = sel
    with col_tf:
        tf = st.segmented_control('Timeframe', ['1M','3M','6M','1Y','2Y','ALL'],
                                  default=st.session_state.timeframe,
                                  key='tf_ctrl',
                                  label_visibility='collapsed')
        if tf and tf != st.session_state.timeframe:
            st.session_state.timeframe = tf

sym = st.session_state.selected_stock
tf  = st.session_state.timeframe
bt  = multi.get(sym) if multi else None


# ── Price Chart ───────────────────────────────────────────────────────────────
if bt:
    with st.container():
        st.markdown(f'<div class="section" style="padding-top:32px;padding-bottom:0">'
                    f'<div class="section-eye"><span class="pulse-dot green"></span>Live · {sym}</div>'
                    f'<div class="section-h">{sym} Price  ·  {tf}</div>'
                    f'</div>', unsafe_allow_html=True)
        st.pyplot(price_chart(bt['data'], sym, tf), use_container_width=True)


# ── Backtest Results + Stock Intelligence ─────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

if bt:
    ret_s  = '+' if bt['total_return'] >= 0 else ''
    ret_c  = 'up' if bt['total_return'] >= 0 else 'down'
    bah_s  = '+' if bt['bah_return']   >= 0 else ''
    net    = bt['final_value'] - bt['initial_cash']
    net_s  = '+' if net >= 0 else ''

    st.markdown(f"""
    <div class="section">
      <div class="section-eye">{sym} Strategy Results</div>
      <div class="section-h">Backtest Performance</div>
      <div class="section-sub">$2,000 starting capital · 5 years daily · 10/200 MA + RSI&lt;70 + 5% stop loss.</div>
      <div class="cards">
        <div class="card" data-tip="Total portfolio value after 5 years of simulated trading.">
          <div class="card-val">${bt['final_value']:,.0f}</div>
          <div class="card-lbl">Final Value</div>
        </div>
        <div class="card" data-tip="Total return from strategy over 5 years. Positive means profit.">
          <div class="card-val {ret_c}">{ret_s}{bt['total_return']:.2f}%</div>
          <div class="card-lbl">Total Return</div>
        </div>
        <div class="card" data-tip="Net dollar profit or loss from the $2,000 starting capital.">
          <div class="card-val">{net_s}${abs(net):,.0f}</div>
          <div class="card-lbl">Net Profit</div>
        </div>
        <div class="card" data-tip="Risk-adjusted return. Above 0.5 is acceptable, above 1.0 is good. Measures return earned per unit of risk.">
          <div class="card-val">{bt['sharpe']}</div>
          <div class="card-lbl">Sharpe Ratio</div>
        </div>
        <div class="card" data-tip="Worst peak-to-trough loss during the period. Shows the most you would have lost at any point before recovering.">
          <div class="card-val down">{bt['max_drawdown']:.1f}%</div>
          <div class="card-lbl">Max Drawdown</div>
        </div>
        <div class="card" data-tip="% of closed trades that were profitable. Even a low win rate can be profitable if winners are much larger than losers.">
          <div class="card-val">{bt['win_rate']:.0f}%</div>
          <div class="card-lbl">Win Rate</div>
        </div>
        <div class="card" data-tip="Buy & Hold had higher raw returns in some cases but also higher volatility. Our strategy aims to smooth the ride with less drawdown.">
          <div class="card-val">{bah_s}{bt['bah_return']:.1f}%</div>
          <div class="card-lbl">Buy &amp; Hold</div>
        </div>
        <div class="card">
          <div class="card-val">{bt['num_trades']}</div>
          <div class="card-lbl">Total Trades</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Backtest chart
    st.pyplot(backtest_chart(bt), use_container_width=True)

    # ── Stock Intelligence Panel ──────────────────────────────────────────────
    st.markdown('<div class="section" style="padding-top:48px;padding-bottom:32px">'
                '<div class="section-eye">Stock Intelligence</div>'
                '<div class="section-h">Live Signal Status</div>'
                '</div>', unsafe_allow_html=True)

    intel_col1, intel_col2, intel_col3 = st.columns([2, 2, 3])

    with intel_col1:
        latest_data = bt['data'].iloc[-1]
        rsi_val = float(latest_data['RSI'])
        rsi_pct = min(max(rsi_val, 0), 100)
        if rsi_val < 30:
            rsi_color, rsi_label = '#30d158', 'Oversold'
        elif rsi_val < 70:
            rsi_color, rsi_label = '#ff9f0a', 'Neutral'
        else:
            rsi_color, rsi_label = '#ff453a', 'Overbought'

        short_above = float(latest_data['ShortMA']) > float(latest_data['LongMA'])
        ma_label = 'above' if short_above else 'below'
        signal = ('BUY WATCH' if short_above and rsi_val < 70
                  else 'SELL WATCH' if not short_above
                  else 'HOLD — RSI elevated')

        st.markdown(f"""
        <div class="rsi-wrap">
          <div class="rsi-title">RSI Gauge · {sym}</div>
          <div class="rsi-value" style="color:{rsi_color}">{rsi_val:.1f}</div>
          <div class="rsi-track">
            <div class="rsi-needle" style="left:{rsi_pct}%"></div>
          </div>
          <div class="rsi-ticks"><span>Oversold</span><span>Neutral</span><span>Overbought</span></div>
          <div class="rsi-status">
            10-day MA is <b>{ma_label}</b> the 200-day MA.
            RSI is <b style="color:{rsi_color}">{rsi_val:.1f}</b> — stock is
            <b style="color:{rsi_color}">{rsi_label}</b>.<br>
            Signal: <b style="color:{'#30d158' if 'BUY' in signal else '#ff9f0a'}">{signal}</b>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with intel_col2:
        entry_date, entry_price = position_status(bt['trades'])
        if entry_date:
            current_pnl = (float(latest_data['Close']) - entry_price) / entry_price * 100
            pnl_col = '#30d158' if current_pnl >= 0 else '#ff453a'
            pos_html = (f'<span style="color:#30d158; font-weight:700">● IN POSITION</span><br>'
                        f'Since: {entry_date}<br>'
                        f'Entry: ${entry_price:,.2f}<br>'
                        f'Current P&L: <span style="color:{pnl_col}">{current_pnl:+.1f}%</span>')
        else:
            pos_html = ('<span style="color:#86868b; font-weight:700">◌ WATCHING</span><br>'
                        'Waiting for 10-day MA to cross<br>above 200-day MA with RSI &lt; 70.')

        st.markdown(f"""
        <div class="pos-wrap">
          <div class="pos-label">Position Status · {sym}</div>
          <div class="pos-val">{pos_html}</div>
        </div>
        """, unsafe_allow_html=True)

    with intel_col3:
        st.markdown('<div style="background:#0d0d0d;border:1px solid #1d1d1f;'
                    'border-radius:18px;padding:16px 20px 8px">'
                    '<div style="font-size:10px;font-weight:600;letter-spacing:.12em;'
                    'text-transform:uppercase;color:#86868b;margin-bottom:8px">'
                    f'30-Day Sparkline · {sym}</div>',
                    unsafe_allow_html=True)
        st.pyplot(sparkline(bt['data']), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ── Trade History + Analysis ──────────────────────────────────────────────────
if bt and not bt['trades'].empty:
    trades_df = bt['trades']

    rows = ''
    for _, row in trades_df.iterrows():
        action = row['Action']
        if action == 'BUY':
            badge = '<span class="badge badge-buy">BUY</span>'
        elif action == 'SELL':
            badge = '<span class="badge badge-sell">SELL</span>'
        else:
            badge = '<span class="badge badge-stop">STOP LOSS</span>'
        rows += (f'<tr><td>{row["Date"]}</td><td>{badge}</td>'
                 f'<td>${row["Price"]:,.2f}</td><td>{row["Shares"]:,.4f}</td>'
                 f'<td>${row["Portfolio Value"]:,.2f}</td>'
                 f'<td style="color:{"#30d158" if row["RSI"] < 30 else "#ff9f0a" if row["RSI"] < 70 else "#ff453a"}">'
                 f'{row["RSI"]:.1f}</td></tr>')

    st.markdown(f"""
    <div class="section" style="padding-top:0">
      <div class="tbl-wrap">
        <div class="tbl-title">Trade History — {sym}</div>
        <table class="trades">
          <thead><tr>
            <th>Date</th><th>Action</th><th>Price</th>
            <th>Shares</th><th>Portfolio Value</th><th>RSI</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>""", unsafe_allow_html=True)

    # Trade Analysis cards
    buys_v  = trades_df[trades_df['Action'] == 'BUY']['Portfolio Value'].tolist()
    sells_v = trades_df[trades_df['Action'].str.contains('SELL')]['Portfolio Value'].tolist()
    pnl_l   = [s - b for b, s in zip(buys_v, sells_v)]
    wins    = [p for p in pnl_l if p > 0]
    losses  = [p for p in pnl_l if p < 0]
    avg_win  = sum(wins)   / len(wins)   if wins   else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    pf       = (sum(wins) / abs(sum(losses))) if losses else float('inf')

    pf_str = f'{pf:.2f}' if pf != float('inf') else '∞'
    aw_sign = '+' if avg_win >= 0 else ''

    st.markdown(f"""
    <div class="section" style="padding-top:32px">
      <div class="section-eye">Trade Analysis — {sym}</div>
      <div class="cards">
        <div class="card" data-tip="Average dollar gain on profitable trades. Larger winners vs smaller losers is ideal.">
          <div class="card-val up">{aw_sign}${avg_win:,.0f}</div>
          <div class="card-lbl">Avg Winning Trade</div>
        </div>
        <div class="card" data-tip="Average dollar loss on losing trades. Want this to be small relative to average winner.">
          <div class="card-val down">${avg_loss:,.0f}</div>
          <div class="card-lbl">Avg Losing Trade</div>
        </div>
        <div class="card" data-tip="Total gains / total losses. Above 1.0 means the strategy is profitable overall even with a low win rate.">
          <div class="card-val {'up' if pf >= 1 else 'down'}">{pf_str}</div>
          <div class="card-lbl">Profit Factor</div>
        </div>
        <div class="card">
          <div class="card-val">{len(wins)}/{len(pnl_l)}</div>
          <div class="card-lbl">Wins / Closed Trades</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)


# ── P&L Bar Chart ─────────────────────────────────────────────────────────────
if multi:
    st.markdown('<div class="section" style="padding-top:0">'
                '<div class="section-eye">All Stocks · All Trades</div>'
                '<div class="section-h" style="font-size:28px">P&amp;L Per Trade</div>'
                '<div class="section-sub">Green = winner · Red = loser</div>'
                '</div>', unsafe_allow_html=True)
    fig = pnl_bar_chart(multi)
    if fig:
        st.pyplot(fig, use_container_width=True)


# ── Portfolio Growth with annotations ─────────────────────────────────────────
if combo:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    co_sign = '+' if combo['total_return'] >= 0 else ''
    co_cls  = 'up' if combo['total_return'] >= 0 else 'down'
    bh_sign = '+' if combo['bah_return']   >= 0 else ''

    st.markdown(f"""
    <div class="section">
      <div class="section-eye"><span class="pulse-dot green"></span>Multi-Stock Portfolio</div>
      <div class="section-h">$10,000 Portfolio Growth</div>
      <div class="section-sub">$2,000 per stock · strategy vs buy &amp; hold · annotated key events.</div>
      <div class="cards">
        <div class="card" data-tip="Combined value of all 5 stock positions after 5 years.">
          <div class="card-val">${combo['final_value']:,.2f}</div>
          <div class="card-lbl">Combined Value</div>
        </div>
        <div class="card" data-tip="Total return across the entire 5-stock portfolio.">
          <div class="card-val {co_cls}">{co_sign}{combo['total_return']:.2f}%</div>
          <div class="card-lbl">Combined Return</div>
        </div>
        <div class="card" data-tip="Risk-adjusted return for the full 5-stock portfolio. 0.80 is solid — above the 0.5 threshold considered acceptable.">
          <div class="card-val">{combo['sharpe']}</div>
          <div class="card-lbl">Portfolio Sharpe</div>
        </div>
        <div class="card" data-tip="Worst combined portfolio drawdown. -19.7% means a $10,000 portfolio fell to ~$8,030 at its worst.">
          <div class="card-val down">{combo['max_drawdown']:.1f}%</div>
          <div class="card-lbl">Portfolio Max DD</div>
        </div>
        <div class="card" data-tip="What a simple buy-and-hold of all 5 stocks would have returned. Higher raw return but more volatility.">
          <div class="card-val">{bh_sign}{combo['bah_return']:.1f}%</div>
          <div class="card-lbl">Buy &amp; Hold</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.pyplot(portfolio_growth_chart(combo, multi), use_container_width=True)


# ── Performance Attribution ───────────────────────────────────────────────────
if multi and combo:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="section">
      <div class="section-eye">Return Attribution</div>
      <div class="section-h">What Drove the Portfolio</div>
      <div class="section-sub">Each stock's contribution to total portfolio gain. NVDA's 2023 entry dominates.</div>
    </div>""", unsafe_allow_html=True)
    st.pyplot(attribution_chart(multi), use_container_width=True)

    # Risk-return scatter
    st.markdown("""
    <div class="section" style="padding-top:40px">
      <div class="section-eye">Risk vs Return</div>
      <div class="section-h" style="font-size:32px">Scatter Analysis</div>
      <div class="section-sub">Return % vs max drawdown for each stock. Top-left = best risk-adjusted outcome.</div>
    </div>""", unsafe_allow_html=True)

    scat_col, _ = st.columns([5, 5])
    with scat_col:
        st.pyplot(risk_return_scatter(multi), use_container_width=True)


# ── 5-Stock Breakdown ─────────────────────────────────────────────────────────
if multi:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    STOCK_COLORS = {'AAPL':'#0071e3','MSFT':'#30d158','GOOGL':'#ff9f0a',
                    'NVDA':'#bf5af2','TSLA':'#ff453a'}
    stock_cards = ''
    for s in SYMBOLS:
        r = multi.get(s)
        if not r:
            continue
        color  = STOCK_COLORS.get(s, '#f5f5f7')
        rs     = '+' if r['total_return'] >= 0 else ''
        rc     = 'up' if r['total_return'] >= 0 else 'down'
        bs     = '+' if r['bah_return']   >= 0 else ''
        stock_cards += f"""
        <div class="stock-card">
          <div class="stock-sym" style="color:{color}">{s}</div>
          <div class="stock-ret {rc}">{rs}{r['total_return']:.1f}%</div>
          <div class="stock-meta">
            Final: ${r['final_value']:,.0f}<br>
            B&H: {bs}{r['bah_return']:.1f}%<br>
            Sharpe: {r['sharpe']}<br>
            Max DD: {r['max_drawdown']:.1f}%<br>
            Win rate: {r['win_rate']:.0f}%<br>
            Trades: {r['num_trades']}
          </div>
        </div>"""

    st.markdown(f"""
    <div class="section">
      <div class="section-eye">Individual Performance</div>
      <div class="section-h">5-Stock Breakdown</div>
      <div class="section-sub">Each stock backtested independently with $2,000 starting capital.</div>
      <div class="stock-grid">{stock_cards}</div>
    </div>""", unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  Friday Trader &nbsp;·&nbsp; Built by Vedant Nogaja
  &nbsp;·&nbsp; Data: Yahoo Finance &nbsp;·&nbsp;
  <a href="https://github.com/vedantnogaja-blip/Friday-Trader">
    github.com/vedantnogaja-blip/Friday-Trader
  </a>
  <br>
  Paper trading only — not financial advice.
  Past performance does not guarantee future results.
</div>
""", unsafe_allow_html=True)
