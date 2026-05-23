import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from backtest import run_backtest, run_multi_backtest, combined_stats, SYMBOLS

st.set_page_config(
    page_title='Friday Trader',
    page_icon='◈',
    layout='wide',
    initial_sidebar_state='collapsed',
)

# ─────────────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
*, *::before, *::after { box-sizing: border-box; }
.stApp {
    background: #000 !important;
    color: #f5f5f7;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
                 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
}
#MainMenu, footer, header,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="collapsedControl"], .stDeployButton { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Hero ───────────────────────────────────────────────────────────────── */
.hero {
    padding: 120px 60px 80px;
    text-align: center;
    background: radial-gradient(ellipse 90% 55% at 50% -5%,
                rgba(0,113,227,.20) 0%, transparent 65%), #000;
    border-bottom: 1px solid #1d1d1f;
}
.hero-eye   { font-size:12px; font-weight:600; letter-spacing:.22em;
              text-transform:uppercase; color:#0071e3; margin-bottom:22px; }
.hero-title { font-size:clamp(72px,9vw,112px); font-weight:700;
              letter-spacing:-.04em; line-height:1; color:#f5f5f7; margin-bottom:20px; }
.hero-sub   { font-size:clamp(17px,2vw,23px); font-weight:300; color:#86868b;
              margin-bottom:64px; }

/* ── Stats bar ──────────────────────────────────────────────────────────── */
.stats { display:flex; justify-content:center; max-width:1100px; margin:0 auto;
         background:#0a0a0a; border:1px solid #1d1d1f; border-radius:22px; overflow:hidden; }
.stat  { flex:1; padding:30px 18px; text-align:center; border-right:1px solid #1d1d1f; }
.stat:last-child { border-right:none; }
.stat-val { font-size:clamp(22px,2.8vw,38px); font-weight:600; letter-spacing:-.03em;
            color:#f5f5f7; line-height:1; margin-bottom:8px; }
.stat-lbl { font-size:11px; font-weight:500; letter-spacing:.12em;
            text-transform:uppercase; color:#86868b; }
.up   { color:#30d158 !important; }
.down { color:#ff453a !important; }

/* ── Divider / Section ──────────────────────────────────────────────────── */
.divider { height:1px; background:#1d1d1f; }
.section { padding:80px 80px 56px; max-width:1400px; margin:0 auto; }
.section-eye { font-size:12px; font-weight:600; letter-spacing:.20em;
               text-transform:uppercase; color:#0071e3; margin-bottom:12px; }
.section-h   { font-size:clamp(32px,4vw,52px); font-weight:700; letter-spacing:-.03em;
               color:#f5f5f7; margin-bottom:8px; line-height:1.05; }
.section-sub { font-size:18px; font-weight:300; color:#86868b; margin-bottom:44px; }

/* ── Result cards ───────────────────────────────────────────────────────── */
.cards { display:flex; gap:16px; margin-bottom:48px; flex-wrap:wrap; }
.card  { flex:1; min-width:130px; background:#0d0d0d; border:1px solid #1d1d1f;
         border-radius:20px; padding:28px 24px; }
.card-val { font-size:clamp(24px,2.6vw,36px); font-weight:600; letter-spacing:-.025em;
            color:#f5f5f7; line-height:1; margin-bottom:10px; }
.card-lbl { font-size:11px; font-weight:500; letter-spacing:.10em;
            text-transform:uppercase; color:#86868b; }

/* ── 5-stock grid ───────────────────────────────────────────────────────── */
.stock-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:16px; margin-bottom:48px; }
.stock-card { background:#0d0d0d; border:1px solid #1d1d1f; border-radius:20px; padding:28px 20px; }
.stock-sym  { font-size:22px; font-weight:700; letter-spacing:-.01em; color:#f5f5f7;
              margin-bottom:16px; }
.stock-ret  { font-size:32px; font-weight:600; letter-spacing:-.03em; margin-bottom:4px; }
.stock-meta { font-size:12px; color:#86868b; line-height:1.9; }

/* ── Trade table ────────────────────────────────────────────────────────── */
.tbl-wrap  { margin-top:52px; }
.tbl-title { font-size:22px; font-weight:600; letter-spacing:-.015em;
             color:#f5f5f7; margin-bottom:20px; }
table.trades { width:100%; border-collapse:collapse; font-size:14px;
               font-variant-numeric:tabular-nums; }
table.trades th { text-align:left; padding:10px 20px; font-size:11px; font-weight:600;
                  letter-spacing:.12em; text-transform:uppercase; color:#86868b;
                  border-bottom:1px solid #1d1d1f; }
table.trades td { padding:14px 20px; color:#f5f5f7; border-bottom:1px solid #0f0f0f; }
table.trades tr:last-child td { border-bottom:none; }
table.trades tr:hover td { background:#080808; }
.badge { display:inline-block; padding:3px 10px; border-radius:30px; font-size:11px;
         font-weight:700; letter-spacing:.07em; text-transform:uppercase; }
.badge-buy  { background:rgba(48,209,88,.15);  color:#30d158; }
.badge-sell { background:rgba(255,69,58,.15);  color:#ff453a; }
.badge-stop { background:rgba(255,149,0,.15);  color:#ff9500; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_live_price():
    hist = yf.download('AAPL', period='5d', interval='1d', progress=False)
    if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = hist.columns.get_level_values(0)
    price  = float(hist['Close'].iloc[-1])
    prev   = float(hist['Close'].iloc[-2])
    return price, (price - prev) / prev * 100

@st.cache_data(ttl=3600)
def load_chart_data():
    data = yf.download('AAPL', period='400d', interval='1d', progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data['10MA']  = data['Close'].rolling(10).mean()
    data['200MA'] = data['Close'].rolling(200).mean()
    return data

@st.cache_data(ttl=3600)
def load_backtest():
    return run_backtest()

@st.cache_data(ttl=3600)
def load_multi():
    results = run_multi_backtest()
    combo   = combined_stats(results)
    return results, combo


# ─────────────────────────────────────────────────────────────────────────────
# Chart builders (dark Apple theme)
# ─────────────────────────────────────────────────────────────────────────────

_BG = '#000000'

def _dark(fig, ax):
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    for sp in ax.spines.values():
        sp.set_edgecolor('#1d1d1f')
    ax.tick_params(colors='#555', labelsize=10)
    ax.grid(True, color='#161616', linewidth=0.8)
    ax.set_axisbelow(True)

def price_chart(data):
    fig, ax = plt.subplots(figsize=(16, 4.5))
    _dark(fig, ax)
    ax.plot(data.index, data['Close'].squeeze(),  color='#f5f5f7', lw=1.5, label='AAPL')
    ax.plot(data.index, data['10MA'].squeeze(),   color='#0071e3', lw=1.1, label='10-day MA')
    ax.plot(data.index, data['200MA'].squeeze(),  color='#ff453a', lw=1.1, label='200-day MA')
    ax.legend(frameon=False, labelcolor='#86868b', fontsize=11, loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    plt.xticks(color='#555'); plt.yticks(color='#555')
    fig.tight_layout(pad=1.2)
    return fig

def backtest_chart(bt):
    data   = bt['data']
    trades = bt['trades']
    fig, ax = plt.subplots(figsize=(16, 4.5))
    _dark(fig, ax)
    ax.plot(data.index, data['Close'].squeeze(),   color='#f5f5f7', lw=1.4, label='AAPL Close')
    ax.plot(data.index, data['ShortMA'].squeeze(), color='#0071e3', lw=1.0, label='10-day MA')
    ax.plot(data.index, data['LongMA'].squeeze(),  color='#ff453a', lw=1.0, label='200-day MA')
    ax.plot(bt['bah_portfolio'].index, bt['bah_portfolio'],
            color='#86868b', lw=1.0, ls='--', label='Buy & Hold', alpha=0.8)
    if not trades.empty:
        t = trades.copy()
        t['Date'] = pd.to_datetime(t['Date'])
        buys  = t[t['Action'] == 'BUY']
        sells = t[t['Action'].str.contains('SELL')]
        ax.scatter(buys['Date'],  buys['Price'],  marker='^', color='#30d158', s=90, zorder=6, label='Buy')
        ax.scatter(sells['Date'], sells['Price'], marker='v', color='#ff453a', s=90, zorder=6, label='Sell')
    ax.legend(frameon=False, labelcolor='#86868b', fontsize=11, loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    plt.xticks(color='#555'); plt.yticks(color='#555')
    fig.tight_layout(pad=1.2)
    return fig

def portfolio_growth_chart(combo):
    port = combo['portfolio']
    bah  = combo['bah_portfolio']
    fig, ax = plt.subplots(figsize=(16, 4.5))
    _dark(fig, ax)
    ax.plot(port.index, port, color='#30d158', lw=2.0, label='Strategy — 5 stocks')
    ax.plot(bah.index,  bah,  color='#86868b', lw=1.5, ls='--', label='Buy & Hold — 5 stocks')
    ax.fill_between(port.index, port, bah, where=(port >= bah), color='#30d158', alpha=0.07)
    ax.fill_between(port.index, port, bah, where=(port <  bah), color='#ff453a', alpha=0.07)
    ax.axhline(y=10_000, color='#333', lw=0.8, ls=':')
    ax.legend(frameon=False, labelcolor='#86868b', fontsize=11, loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    plt.xticks(color='#555'); plt.yticks(color='#555')
    fig.tight_layout(pad=1.2)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Render
# ─────────────────────────────────────────────────────────────────────────────

price, change = load_live_price()
chart_data    = load_chart_data()
bt            = load_backtest()
multi, combo  = load_multi()

c_cls  = 'up' if change           >= 0 else 'down'
r_cls  = 'up' if bt['total_return'] >= 0 else 'down'
c_sign = '+' if change           >= 0 else ''
r_sign = '+' if bt['total_return'] >= 0 else ''

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <div class="hero-eye">Multi-Stock Algo · AAPL MSFT GOOGL NVDA TSLA · 10/200 MA + RSI + Stop Loss</div>
  <div class="hero-title">Friday Trader</div>
  <div class="hero-sub">Strategy-driven. Data-first. Built to outperform.</div>

  <div class="stats">
    <div class="stat">
      <div class="stat-val">${price:,.2f}</div>
      <div class="stat-lbl">AAPL Price</div>
    </div>
    <div class="stat">
      <div class="stat-val {c_cls}">{c_sign}{change:.2f}%</div>
      <div class="stat-lbl">Day Change</div>
    </div>
    <div class="stat">
      <div class="stat-val {r_cls}">{r_sign}{bt['total_return']:.1f}%</div>
      <div class="stat-lbl">AAPL 5yr Return</div>
    </div>
    <div class="stat">
      <div class="stat-val">{bt['sharpe']}</div>
      <div class="stat-lbl">Sharpe Ratio</div>
    </div>
    <div class="stat">
      <div class="stat-val down">{bt['max_drawdown']:.1f}%</div>
      <div class="stat-lbl">Max Drawdown</div>
    </div>
    <div class="stat">
      <div class="stat-val">{bt['win_rate']:.0f}%</div>
      <div class="stat-lbl">Win Rate</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Price Chart ───────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="section">
  <div class="section-eye">Live Data · AAPL</div>
  <div class="section-h">Price & Moving Averages</div>
  <div class="section-sub">400 days of daily price with 10-day and 200-day MAs.</div>
</div>""", unsafe_allow_html=True)
st.pyplot(price_chart(chart_data), use_container_width=True)

# ── AAPL Backtest ─────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

buys_  = bt['trades'][bt['trades']['Action'] == 'BUY'] if not bt['trades'].empty else pd.DataFrame()
sells_ = bt['trades'][bt['trades']['Action'].str.contains('SELL')] if not bt['trades'].empty else pd.DataFrame()
pnl_   = [s - b for b, s in zip(
    buys_['Portfolio Value'].tolist(),
    sells_['Portfolio Value'].tolist()
)] if not buys_.empty and not sells_.empty else []

ret_sign = '+' if bt['total_return'] >= 0 else ''
ret_cls  = 'up' if bt['total_return'] >= 0 else 'down'
bah_sign = '+' if bt['bah_return'] >= 0 else ''

st.markdown(f"""
<div class="section">
  <div class="section-eye">Strategy Simulation · AAPL</div>
  <div class="section-h">Backtest Results</div>
  <div class="section-sub">5 years · daily · 10/200 MA crossover · RSI &lt; 70 filter · 5% stop loss · $10,000 capital.</div>
  <div class="cards">
    <div class="card">
      <div class="card-val">${bt['final_value']:,.2f}</div>
      <div class="card-lbl">Final Value</div>
    </div>
    <div class="card">
      <div class="card-val {ret_cls}">{ret_sign}{bt['total_return']:.2f}%</div>
      <div class="card-lbl">Total Return</div>
    </div>
    <div class="card">
      <div class="card-val">${bt['final_value'] - bt['initial_cash']:,.2f}</div>
      <div class="card-lbl">Net Profit</div>
    </div>
    <div class="card">
      <div class="card-val">{bt['sharpe']}</div>
      <div class="card-lbl">Sharpe Ratio</div>
    </div>
    <div class="card">
      <div class="card-val down">{bt['max_drawdown']:.1f}%</div>
      <div class="card-lbl">Max Drawdown</div>
    </div>
    <div class="card">
      <div class="card-val">{bt['win_rate']:.0f}%</div>
      <div class="card-lbl">Win Rate</div>
    </div>
    <div class="card">
      <div class="card-val">{bah_sign}{bt['bah_return']:.1f}%</div>
      <div class="card-lbl">Buy &amp; Hold</div>
    </div>
    <div class="card">
      <div class="card-val">{bt['num_trades']}</div>
      <div class="card-lbl">Total Trades</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
st.pyplot(backtest_chart(bt), use_container_width=True)

# trade table
if not bt['trades'].empty:
    rows = ''
    for _, row in bt['trades'].iterrows():
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
                 f'<td>{row["RSI"]:.1f}</td></tr>')
    st.markdown(f"""
    <div class="section" style="padding-top:0">
      <div class="tbl-wrap">
        <div class="tbl-title">Trade History</div>
        <table class="trades">
          <thead><tr>
            <th>Date</th><th>Action</th><th>Price</th>
            <th>Shares</th><th>Portfolio Value</th><th>RSI</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>""", unsafe_allow_html=True)

# ── Portfolio Growth ──────────────────────────────────────────────────────────
if combo:
    co_sign = '+' if combo['total_return'] >= 0 else ''
    co_cls  = 'up' if combo['total_return'] >= 0 else 'down'
    bh_sign = '+' if combo['bah_return'] >= 0 else ''

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="section">
      <div class="section-eye">Multi-Stock Portfolio</div>
      <div class="section-h">$10,000 Portfolio Growth</div>
      <div class="section-sub">$2,000 allocated to each of 5 stocks · strategy vs buy &amp; hold.</div>
      <div class="cards">
        <div class="card">
          <div class="card-val">${combo['final_value']:,.2f}</div>
          <div class="card-lbl">Combined Final Value</div>
        </div>
        <div class="card">
          <div class="card-val {co_cls}">{co_sign}{combo['total_return']:.2f}%</div>
          <div class="card-lbl">Combined Return</div>
        </div>
        <div class="card">
          <div class="card-val">{combo['sharpe']}</div>
          <div class="card-lbl">Portfolio Sharpe</div>
        </div>
        <div class="card">
          <div class="card-val down">{combo['max_drawdown']:.1f}%</div>
          <div class="card-lbl">Portfolio Max DD</div>
        </div>
        <div class="card">
          <div class="card-val">{bh_sign}{combo['bah_return']:.1f}%</div>
          <div class="card-lbl">Buy &amp; Hold</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)
    st.pyplot(portfolio_growth_chart(combo), use_container_width=True)

    # ── 5-Stock Breakdown ─────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    stock_cards = ''
    STOCK_COLORS = {'AAPL':'#0071e3','MSFT':'#30d158','GOOGL':'#ff9f0a',
                    'NVDA':'#bf5af2','TSLA':'#ff453a'}
    for sym in SYMBOLS:
        r = multi.get(sym)
        if not r:
            continue
        color    = STOCK_COLORS.get(sym, '#f5f5f7')
        ret_s    = '+' if r['total_return'] >= 0 else ''
        ret_c    = 'up' if r['total_return'] >= 0 else 'down'
        bah_s    = '+' if r['bah_return'] >= 0 else ''
        stock_cards += f"""
        <div class="stock-card">
          <div class="stock-sym" style="color:{color}">{sym}</div>
          <div class="stock-ret {ret_c}">{ret_s}{r['total_return']:.1f}%</div>
          <div class="stock-meta">
            Final: ${r['final_value']:,.0f}<br>
            B&H: {bah_s}{r['bah_return']:.1f}%<br>
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
    </div>
    <div style="height:80px"></div>""", unsafe_allow_html=True)
