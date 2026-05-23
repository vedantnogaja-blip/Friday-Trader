import pandas as pd
import yfinance as yf

class MovingAverageCrossoverStrategy:
    def __init__(self, client):
        self.client = client

    def get_data(self, symbol):
        data = yf.download(symbol, period='400d', interval='1d')
        # Flatten MultiIndex columns (yfinance 0.2.x returns MultiIndex for single tickers)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data

    def run(self):
        data = self.get_data('AAPL')
        data['10MA'] = data['Close'].rolling(window=10).mean()
        data['200MA'] = data['Close'].rolling(window=200).mean()

        latest = data.iloc[-1]
        prev = data.iloc[-2]

        if pd.isna(latest['10MA']) or pd.isna(latest['200MA']) or pd.isna(prev['10MA']) or pd.isna(prev['200MA']):
            print('Not enough data for moving averages yet')
            return

        # Golden cross - buy signal
        if prev['10MA'] < prev['200MA'] and latest['10MA'] > latest['200MA']:
            self.client.submit_order('AAPL', 1, 'buy')
            print('BUY signal triggered')

        # Death cross - sell signal
        elif prev['10MA'] > prev['200MA'] and latest['10MA'] < latest['200MA']:
            self.client.submit_order('AAPL', 1, 'sell')
            print('SELL signal triggered')
            