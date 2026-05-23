import pandas as pd
import yfinance as yf

SYMBOL = 'AAPL'
INITIAL_CASH = 10_000.0
SHORT_WINDOWS = [5, 10, 20, 50]
LONG_WINDOWS = [50, 100, 200]
INTERVALS = ['1m', '5m', '15m', '1h', '1d']
PERIOD_FOR_INTERVAL = {
    '1m':  '7d',
    '5m':  '60d',
    '15m': '60d',
    '1h':  '2y',
    '1d':  '5y',
}

GREEN  = '\033[92m\033[1m'
YELLOW = '\033[93m'
RESET  = '\033[0m'


def simulate(data, short_window, long_window):
    df = data.copy()
    df['ShortMA'] = df['Close'].rolling(window=short_window).mean()
    df['LongMA']  = df['Close'].rolling(window=long_window).mean()
    df = df.dropna(subset=['ShortMA', 'LongMA'])

    if len(df) < 2:
        return None

    cash = INITIAL_CASH
    shares = 0.0
    in_position = False
    num_trades = 0

    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        price = float(curr['Close'])

        if not in_position and prev['ShortMA'] < prev['LongMA'] and curr['ShortMA'] > curr['LongMA']:
            shares = cash / price
            cash = 0.0
            in_position = True
            num_trades += 1

        elif in_position and prev['ShortMA'] > prev['LongMA'] and curr['ShortMA'] < curr['LongMA']:
            cash = shares * price
            shares = 0.0
            in_position = False
            num_trades += 1

    final_price = float(df.iloc[-1]['Close'])
    final_value = cash + shares * final_price
    return {
        'final_value': round(final_value, 2),
        'total_return': round((final_value - INITIAL_CASH) / INITIAL_CASH * 100, 2),
        'num_trades': num_trades,
    }


def main():
    valid_combos = [(s, l) for s in SHORT_WINDOWS for l in LONG_WINDOWS if s < l]
    total = len(INTERVALS) * len(valid_combos)
    done = 0
    results = []

    for interval in INTERVALS:
        period = PERIOD_FOR_INTERVAL[interval]
        print(f'Downloading {SYMBOL} {interval} data ({period})...', flush=True)

        try:
            data = yf.download(SYMBOL, period=period, interval=interval, progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            print(f'  {len(data):,} bars', flush=True)
        except Exception as e:
            print(f'  FAILED: {e}')
            for short, long in valid_combos:
                done += 1
                results.append({'Interval': interval, 'Short': short, 'Long': long,
                                 'Return %': None, 'Final Value ($)': None, 'Trades': 0})
            continue

        for short, long in valid_combos:
            done += 1
            print(f'  [{done}/{total}] short={short:>3}  long={long:>3}', end='\r', flush=True)
            try:
                r = simulate(data, short, long)
            except Exception:
                r = None

            results.append({
                'Interval':      interval,
                'Short':         short,
                'Long':          long,
                'Return %':      r['total_return']  if r else None,
                'Final Value ($)': r['final_value'] if r else None,
                'Trades':        r['num_trades']    if r else 0,
            })

        print()  # newline after \r progress

    df = pd.DataFrame(results)
    df_valid = df.dropna(subset=['Return %'])
    df_null  = df[df['Return %'].isna()]
    df = pd.concat([
        df_valid.sort_values('Return %', ascending=False),
        df_null,
    ]).reset_index(drop=True)

    # ── print table ──────────────────────────────────────────────────────────
    W = 72
    print('\n' + '=' * W)
    print(f"  OPTIMIZATION RESULTS  ({SYMBOL}, $10,000 starting capital)")
    print('=' * W)
    header = f"{'#':>3}  {'Interval':>8}  {'Short':>5}  {'Long':>5}  {'Return %':>9}  {'Final Value':>12}  {'Trades':>6}"
    print(header)
    print('-' * W)

    for i, row in df.iterrows():
        ret = f"{row['Return %']:+.2f}%" if pd.notna(row['Return %']) else 'N/A'
        val = f"${row['Final Value ($)']:>10,.2f}" if pd.notna(row['Final Value ($)']) else 'N/A'
        trades = int(row['Trades']) if pd.notna(row['Trades']) else 0
        line = (f"{i+1:>3}  {row['Interval']:>8}  {int(row['Short']):>5}  "
                f"{int(row['Long']):>5}  {ret:>9}  {val:>12}  {trades:>6}")
        if i == 0:
            print(f"{GREEN}{line}  ← WINNER{RESET}")
        elif pd.notna(row['Return %']) and row['Return %'] > 0:
            print(f"{YELLOW}{line}{RESET}")
        else:
            print(line)

    print('=' * W)

    best = df.iloc[0]
    print(f"\n{GREEN}WINNER:{RESET}")
    print(f"  Interval     : {best['Interval']}")
    print(f"  Short window : {int(best['Short'])}")
    print(f"  Long window  : {int(best['Long'])}")
    print(f"  Return       : {best['Return %']:+.2f}%")
    print(f"  Final value  : ${best['Final Value ($)']:,.2f}")
    print(f"  Trades       : {int(best['Trades'])}")


if __name__ == '__main__':
    main()
