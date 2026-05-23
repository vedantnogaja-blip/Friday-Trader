import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def run_backtest(symbol='AAPL', initial_cash=10_000.0, short_window=20, long_window=50):
    data = yf.download(symbol, period='7d', interval='1m', progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data['50MA'] = data['Close'].rolling(window=short_window).mean()
    data['200MA'] = data['Close'].rolling(window=long_window).mean()
    data = data.dropna(subset=['50MA', '200MA'])

    cash = initial_cash
    shares = 0.0
    in_position = False
    trades = []

    for i in range(1, len(data)):
        prev = data.iloc[i - 1]
        curr = data.iloc[i]
        price = float(curr['Close'])
        date = data.index[i]

        # Golden cross → buy all in
        if not in_position and prev['50MA'] < prev['200MA'] and curr['50MA'] > curr['200MA']:
            shares = cash / price
            cash = 0.0
            in_position = True
            trades.append({
                'Date': date.date(),
                'Action': 'BUY',
                'Price': round(price, 2),
                'Shares': round(shares, 4),
                'Portfolio Value': round(shares * price, 2),
            })

        # Death cross → sell everything
        elif in_position and prev['50MA'] > prev['200MA'] and curr['50MA'] < curr['200MA']:
            cash = shares * price
            trades.append({
                'Date': date.date(),
                'Action': 'SELL',
                'Price': round(price, 2),
                'Shares': round(shares, 4),
                'Portfolio Value': round(cash, 2),
            })
            shares = 0.0
            in_position = False

    final_price = float(data.iloc[-1]['Close'])
    final_value = cash + shares * final_price
    total_return = (final_value - initial_cash) / initial_cash * 100

    return {
        'symbol': symbol,
        'initial_cash': initial_cash,
        'final_value': round(final_value, 2),
        'total_return': round(total_return, 2),
        'num_trades': len(trades),
        'trades': pd.DataFrame(trades) if trades else pd.DataFrame(),
        'data': data,
    }


def plot_backtest(results):
    data = results['data']
    trades_df = results['trades']
    symbol = results['symbol']

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(data.index, data['Close'], label=symbol, color='#1f77b4', linewidth=1.2)
    ax.plot(data.index, data['50MA'], label='20-min MA', color='orange', linewidth=1.5)
    ax.plot(data.index, data['200MA'], label='50-min MA', color='red', linewidth=1.5)

    if not trades_df.empty:
        # Convert Date column back to datetime for plotting
        trades_df = trades_df.copy()
        trades_df['Date'] = pd.to_datetime(trades_df['Date'])
        buys = trades_df[trades_df['Action'] == 'BUY']
        sells = trades_df[trades_df['Action'] == 'SELL']
        ax.scatter(buys['Date'], buys['Price'], marker='^', color='green',
                   s=120, zorder=5, label='Buy')
        ax.scatter(sells['Date'], sells['Price'], marker='v', color='red',
                   s=120, zorder=5, label='Sell')

    ax.set_title(f'{symbol} — Moving Average Crossover Backtest (7 Days, 1-Minute)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price (USD)')
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=8))
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


if __name__ == '__main__':
    results = run_backtest()
    print(f"Initial Investment : ${results['initial_cash']:>10,.2f}")
    print(f"Final Value        : ${results['final_value']:>10,.2f}")
    print(f"Total Return       : {results['total_return']:>10.2f}%")
    print(f"Number of Trades   : {results['num_trades']:>10}")
    if not results['trades'].empty:
        print('\nTrade History:')
        print(results['trades'].to_string(index=False))
    fig = plot_backtest(results)
    plt.show()
