import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']


# ─────────────────────────────────────────────────────────────────────────────
# Metric helpers
# ─────────────────────────────────────────────────────────────────────────────

def calculate_rsi(close, period=14):
    """Wilder's RSI using EWM — pandas only, no extra libraries."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_sharpe(portfolio_series, risk_free_rate=0.045):
    returns = portfolio_series.pct_change().dropna()
    if len(returns) < 2 or returns.std() == 0:
        return 0.0
    daily_rf = risk_free_rate / 252
    excess   = returns - daily_rf
    return round((excess.mean() / returns.std()) * (252 ** 0.5), 2)


def calculate_max_drawdown(portfolio_series):
    rolling_max = portfolio_series.cummax()
    drawdown    = (portfolio_series - rolling_max) / rolling_max * 100
    return round(float(drawdown.min()), 2)


# ─────────────────────────────────────────────────────────────────────────────
# Single-stock backtest
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(symbol='AAPL', initial_cash=10_000.0,
                 short_window=10, long_window=200,
                 period='5y', interval='1d',
                 rsi_period=14, rsi_overbought=70,
                 stop_loss_pct=0.05, risk_free_rate=0.045):

    data = yf.download(symbol, period=period, interval=interval, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    close = data['Close'].squeeze()
    data = data.copy()
    data['ShortMA'] = close.rolling(window=short_window).mean()
    data['LongMA']  = close.rolling(window=long_window).mean()
    data['RSI']     = calculate_rsi(close, rsi_period)
    data = data.dropna(subset=['ShortMA', 'LongMA', 'RSI']).copy()

    if len(data) < 2:
        return None

    # ── Buy-and-hold benchmark (same start date as strategy) ─────────────────
    bah_entry  = float(data.iloc[0]['Close'])
    bah_shares = initial_cash / bah_entry
    bah_values = pd.Series(
        [bah_shares * float(data.iloc[i]['Close']) for i in range(len(data))],
        index=data.index,
    )

    # ── Strategy simulation ───────────────────────────────────────────────────
    cash = initial_cash
    shares    = 0.0
    in_pos    = False
    buy_price = None
    trades    = []
    port_dates  = [data.index[0]]
    port_vals   = [initial_cash]

    for i in range(1, len(data)):
        prev  = data.iloc[i - 1]
        curr  = data.iloc[i]
        price = float(curr['Close'])
        date  = data.index[i]
        rsi   = float(curr['RSI'])

        # Stop loss
        if in_pos and buy_price is not None and price <= buy_price * (1 - stop_loss_pct):
            cash = shares * price
            trades.append({'Date': date.date(), 'Action': 'SELL (stop loss)',
                           'Price': round(price, 2), 'Shares': round(shares, 4),
                           'Portfolio Value': round(cash, 2), 'RSI': round(rsi, 1)})
            shares = 0.0
            in_pos = False
            buy_price = None

        # Golden cross + RSI filter
        elif (not in_pos
              and prev['ShortMA'] < prev['LongMA']
              and curr['ShortMA']  > curr['LongMA']
              and rsi < rsi_overbought):
            shares    = cash / price
            cash      = 0.0
            in_pos    = True
            buy_price = price
            trades.append({'Date': date.date(), 'Action': 'BUY',
                           'Price': round(price, 2), 'Shares': round(shares, 4),
                           'Portfolio Value': round(shares * price, 2), 'RSI': round(rsi, 1)})

        # Death cross
        elif (in_pos
              and prev['ShortMA'] > prev['LongMA']
              and curr['ShortMA']  < curr['LongMA']):
            cash = shares * price
            trades.append({'Date': date.date(), 'Action': 'SELL',
                           'Price': round(price, 2), 'Shares': round(shares, 4),
                           'Portfolio Value': round(cash, 2), 'RSI': round(rsi, 1)})
            shares = 0.0
            in_pos = False
            buy_price = None

        port_dates.append(date)
        port_vals.append(cash + shares * price)

    final_price  = float(data.iloc[-1]['Close'])
    final_value  = cash + shares * final_price
    trades_df    = pd.DataFrame(trades) if trades else pd.DataFrame()
    portfolio_s  = pd.Series(port_vals, index=port_dates)

    # Trade stats
    buys  = [t for t in trades if t['Action'] == 'BUY']
    sells = [t for t in trades if 'SELL' in t['Action']]
    pnl   = [s['Portfolio Value'] - b['Portfolio Value'] for b, s in zip(buys, sells)]
    win_rate = round(sum(1 for p in pnl if p > 0) / len(pnl) * 100, 1) if pnl else 0.0

    return {
        'symbol':        symbol,
        'short_window':  short_window,
        'long_window':   long_window,
        'interval':      interval,
        'initial_cash':  initial_cash,
        'final_value':   round(final_value, 2),
        'total_return':  round((final_value - initial_cash) / initial_cash * 100, 2),
        'num_trades':    len(trades),
        'win_rate':      win_rate,
        'sharpe':        calculate_sharpe(portfolio_s, risk_free_rate),
        'max_drawdown':  calculate_max_drawdown(portfolio_s),
        'bah_final':     round(float(bah_values.iloc[-1]), 2),
        'bah_return':    round((float(bah_values.iloc[-1]) - initial_cash) / initial_cash * 100, 2),
        'trades':        trades_df,
        'data':          data,
        'portfolio':     portfolio_s,
        'bah_portfolio': bah_values,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Multi-stock backtest
# ─────────────────────────────────────────────────────────────────────────────

def run_multi_backtest(symbols=None, initial_cash=10_000.0, **kwargs):
    if symbols is None:
        symbols = SYMBOLS
    per_stock = initial_cash / len(symbols)
    results = {}
    for sym in symbols:
        print(f'  {sym} ... ', end='', flush=True)
        r = run_backtest(symbol=sym, initial_cash=per_stock, **kwargs)
        results[sym] = r
        if r:
            print(f'${r["final_value"]:>8,.0f}  ({r["total_return"]:+.1f}%)')
        else:
            print('no data')
    return results


def combined_stats(results_dict, initial_cash=10_000.0):
    valid = {k: v for k, v in results_dict.items() if v}
    if not valid:
        return None

    combined_final   = sum(r['final_value'] for r in valid.values())
    combined_bah     = sum(r['bah_final']   for r in valid.values())
    combined_return  = (combined_final - initial_cash) / initial_cash * 100
    bah_return       = (combined_bah   - initial_cash) / initial_cash * 100

    port = pd.concat([r['portfolio']     for r in valid.values()], axis=1).ffill().bfill().sum(axis=1)
    bah  = pd.concat([r['bah_portfolio'] for r in valid.values()], axis=1).ffill().bfill().sum(axis=1)

    return {
        'final_value':   round(combined_final, 2),
        'total_return':  round(combined_return, 2),
        'bah_final':     round(combined_bah, 2),
        'bah_return':    round(bah_return, 2),
        'sharpe':        calculate_sharpe(port),
        'max_drawdown':  calculate_max_drawdown(port),
        'portfolio':     port,
        'bah_portfolio': bah,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Plotting
# ─────────────────────────────────────────────────────────────────────────────

def plot_backtest(results):
    data   = results['data']
    trades = results['trades']
    sym    = results['symbol']
    sw, lw = results['short_window'], results['long_window']

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(data.index, data['Close'].squeeze(),   color='#1f77b4', lw=1.2, label=sym)
    ax.plot(data.index, data['ShortMA'].squeeze(), color='orange',  lw=1.4, label=f'{sw}-day MA')
    ax.plot(data.index, data['LongMA'].squeeze(),  color='red',     lw=1.4, label=f'{lw}-day MA')
    ax.plot(results['bah_portfolio'].index, results['bah_portfolio'],
            color='gray', lw=1.0, ls='--', label='Buy & Hold value', alpha=0.7)

    if not trades.empty:
        t = trades.copy()
        t['Date'] = pd.to_datetime(t['Date'])
        buys  = t[t['Action'] == 'BUY']
        sells = t[t['Action'].str.contains('SELL')]
        ax.scatter(buys['Date'],  buys['Price'],  marker='^', color='green', s=110, zorder=6, label='Buy')
        ax.scatter(sells['Date'], sells['Price'], marker='v', color='red',   s=110, zorder=6, label='Sell')

    ax.set_title(f'{sym} — {sw}/{lw} MA Crossover + RSI + Stop Loss')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price / Portfolio Value (USD)')
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


def plot_portfolio_growth(combined):
    port = combined['portfolio']
    bah  = combined['bah_portfolio']

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(port.index, port, color='#30d158', lw=2,   label='Strategy (5 stocks)')
    ax.plot(bah.index,  bah,  color='#86868b', lw=1.5, ls='--', label='Buy & Hold (5 stocks)')
    ax.fill_between(port.index, port, bah,
                    where=(port >= bah), color='#30d158', alpha=0.08)
    ax.fill_between(port.index, port, bah,
                    where=(port <  bah), color='#ff453a', alpha=0.08)
    ax.axhline(y=10_000, color='#555', lw=0.8, ls=':')
    ax.set_ylabel('Portfolio Value (USD)')
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    INITIAL = 10_000.0

    print('=' * 62)
    print(f'  FRIDAY TRADER — Multi-Stock Backtest  (5y daily, 10/200 MA)')
    print(f'  RSI filter < 70   |   5% stop loss   |   $10,000 capital')
    print('=' * 62)

    print('\nRunning backtests...')
    results = run_multi_backtest(initial_cash=INITIAL)
    combo   = combined_stats(results, INITIAL)

    # ── Per-stock table ───────────────────────────────────────────────────────
    W = 78
    print(f'\n{"─"*W}')
    print(f"{'Symbol':>7} {'Return':>8} {'Final $':>10} {'B&H':>8} "
          f"{'Sharpe':>7} {'Max DD':>8} {'Win%':>6} {'Trades':>7}")
    print(f'{"─"*W}')
    for sym, r in results.items():
        if not r:
            print(f'{sym:>7}   no data')
            continue
        print(f'{sym:>7} {r["total_return"]:>+7.1f}% '
              f'${r["final_value"]:>9,.0f} '
              f'{r["bah_return"]:>+7.1f}% '
              f'{r["sharpe"]:>7.2f} '
              f'{r["max_drawdown"]:>+7.1f}% '
              f'{r["win_rate"]:>5.0f}% '
              f'{r["num_trades"]:>7}')

    # ── Combined ─────────────────────────────────────────────────────────────
    if combo:
        print(f'{"─"*W}')
        print(f'{"COMBINED":>7} {combo["total_return"]:>+7.1f}% '
              f'${combo["final_value"]:>9,.0f} '
              f'{combo["bah_return"]:>+7.1f}% '
              f'{combo["sharpe"]:>7.2f} '
              f'{combo["max_drawdown"]:>+7.1f}%')
        print(f'{"─"*W}')
        print(f'\n  Initial capital : ${INITIAL:,.0f}')
        print(f'  Final value     : ${combo["final_value"]:,.2f}')
        print(f'  Net profit      : ${combo["final_value"] - INITIAL:,.2f}')
        print(f'  vs Buy & Hold   : ${combo["bah_final"]:,.2f}  ({combo["bah_return"]:+.1f}%)')
        print(f'  Sharpe ratio    : {combo["sharpe"]}')
        print(f'  Max drawdown    : {combo["max_drawdown"]}%')

    # ── Per-stock trade logs ──────────────────────────────────────────────────
    for sym, r in results.items():
        if r and not r['trades'].empty:
            print(f'\n  {sym} Trades:')
            print(r['trades'].to_string(index=False))

    fig = plot_portfolio_growth(combo)
    plt.show()
