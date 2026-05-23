import pandas as pd
import yfinance as yf

SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']


def calculate_rsi(close, period=14):
    """Wilder's RSI using EWM smoothing — no extra libraries needed."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


class MovingAverageCrossoverStrategy:
    def __init__(self, client):
        self.client = client
        self._buy_prices = {}   # symbol → entry price, used for stop loss

    def _get_data(self, symbol):
        data = yf.download(symbol, period='400d', interval='1d', progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data

    def _run_symbol(self, symbol):
        data = self._get_data(symbol)
        close = data['Close'].squeeze()
        data['10MA']  = close.rolling(10).mean()
        data['200MA'] = close.rolling(200).mean()
        data['RSI']   = calculate_rsi(close)
        data = data.dropna(subset=['10MA', '200MA', 'RSI'])

        if len(data) < 2:
            return

        latest = data.iloc[-1]
        prev   = data.iloc[-2]
        price  = float(latest['Close'])
        rsi    = float(latest['RSI'])

        # ── Stop loss (5%) ────────────────────────────────────────────────────
        if symbol in self._buy_prices:
            if price <= self._buy_prices[symbol] * 0.95:
                self.client.submit_order(symbol, 1, 'sell')
                loss_pct = (price - self._buy_prices[symbol]) / self._buy_prices[symbol] * 100
                print(f'[STOP LOSS] {symbol} @ ${price:.2f}  '
                      f'(entry ${self._buy_prices[symbol]:.2f}, {loss_pct:.1f}%)  RSI: {rsi:.1f}')
                del self._buy_prices[symbol]
                return

        # ── Golden cross + RSI not overbought → BUY ───────────────────────────
        if (symbol not in self._buy_prices
                and prev['10MA'] < prev['200MA']
                and latest['10MA'] > latest['200MA']
                and rsi < 70):
            self.client.submit_order(symbol, 1, 'buy')
            self._buy_prices[symbol] = price
            print(f'[BUY]  {symbol} @ ${price:.2f}  RSI: {rsi:.1f}')

        # ── Death cross → SELL ────────────────────────────────────────────────
        elif (symbol in self._buy_prices
              and prev['10MA'] > prev['200MA']
              and latest['10MA'] < latest['200MA']):
            self.client.submit_order(symbol, 1, 'sell')
            pnl_pct = (price - self._buy_prices[symbol]) / self._buy_prices[symbol] * 100
            print(f'[SELL] {symbol} @ ${price:.2f}  RSI: {rsi:.1f}  P&L: {pnl_pct:+.1f}%')
            del self._buy_prices[symbol]

    def run(self):
        for symbol in SYMBOLS:
            try:
                self._run_symbol(symbol)
            except Exception as e:
                print(f'[ERROR] {symbol}: {e}')
