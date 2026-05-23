#!/usr/bin/env python3
"""
Friday Trader — Signal Alerts
Polls every 60 seconds and prints BUY / SELL / STOP LOSS notifications
for AAPL, MSFT, GOOGL, NVDA, TSLA to the terminal.
"""

import time
from datetime import datetime
import pandas as pd
import yfinance as yf

SYMBOLS        = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']
CHECK_INTERVAL = 60   # seconds
SHORT_WINDOW   = 10
LONG_WINDOW    = 200
RSI_PERIOD     = 14
RSI_OB         = 70   # overbought threshold
STOP_LOSS_PCT  = 0.05

# Track entry prices for stop-loss logic across iterations
_buy_prices: dict[str, float] = {}

GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
RESET  = '\033[0m'
BOLD   = '\033[1m'
GRAY   = '\033[90m'


def calculate_rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs       = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def ts() -> str:
    return datetime.now().strftime('%H:%M:%S')


def check_signals() -> bool:
    any_signal = False

    for symbol in SYMBOLS:
        try:
            data = yf.download(symbol, period='400d', interval='1d', progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            close = data['Close'].squeeze()
            data['ShortMA'] = close.rolling(SHORT_WINDOW).mean()
            data['LongMA']  = close.rolling(LONG_WINDOW).mean()
            data['RSI']     = calculate_rsi(close)
            data = data.dropna(subset=['ShortMA', 'LongMA', 'RSI'])

            if len(data) < 2:
                continue

            latest = data.iloc[-1]
            prev   = data.iloc[-2]
            price  = float(latest['Close'])
            rsi    = float(latest['RSI'])

            # ── Stop loss ─────────────────────────────────────────────────────
            if symbol in _buy_prices and price <= _buy_prices[symbol] * (1 - STOP_LOSS_PCT):
                entry   = _buy_prices.pop(symbol)
                loss_pct = (price - entry) / entry * 100
                print(f'{YELLOW}{BOLD}[{ts()}] STOP LOSS  {symbol:<5}{RESET}'
                      f'  Price: {YELLOW}${price:.2f}{RESET}'
                      f'  Entry: ${entry:.2f}'
                      f'  P&L: {RED}{loss_pct:+.1f}%{RESET}'
                      f'  RSI: {rsi:.1f}')
                any_signal = True
                continue

            # ── Golden cross + RSI filter → BUY ──────────────────────────────
            if (symbol not in _buy_prices
                    and prev['ShortMA'] < prev['LongMA']
                    and latest['ShortMA'] > latest['LongMA']
                    and rsi < RSI_OB):
                _buy_prices[symbol] = price
                print(f'{GREEN}{BOLD}[{ts()}] BUY        {symbol:<5}{RESET}'
                      f'  Price: {GREEN}${price:.2f}{RESET}'
                      f'  RSI: {rsi:.1f}'
                      f'  Signal: {SHORT_WINDOW}/{LONG_WINDOW} golden cross')
                any_signal = True

            # ── Death cross → SELL ────────────────────────────────────────────
            elif (symbol in _buy_prices
                  and prev['ShortMA'] > prev['LongMA']
                  and latest['ShortMA'] < latest['LongMA']):
                entry   = _buy_prices.pop(symbol)
                pnl_pct = (price - entry) / entry * 100
                color   = GREEN if pnl_pct >= 0 else RED
                print(f'{RED}{BOLD}[{ts()}] SELL       {symbol:<5}{RESET}'
                      f'  Price: ${price:.2f}'
                      f'  Entry: ${entry:.2f}'
                      f'  P&L: {color}{pnl_pct:+.1f}%{RESET}'
                      f'  RSI: {rsi:.1f}')
                any_signal = True

        except Exception as exc:
            print(f'{GRAY}[{ts()}] ERROR {symbol}: {exc}{RESET}')

    return any_signal


def main():
    print(f'\n{BOLD}Friday Trader Alerts{RESET}')
    print(f'Watching: {", ".join(SYMBOLS)}')
    print(f'Strategy: {SHORT_WINDOW}/{LONG_WINDOW} MA crossover · RSI < {RSI_OB} · {STOP_LOSS_PCT*100:.0f}% stop loss')
    print(f'Interval: every {CHECK_INTERVAL}s\n')
    print('─' * 60)

    iteration = 0
    while True:
        iteration += 1
        print(f'{GRAY}[{ts()}] Check #{iteration} — scanning {len(SYMBOLS)} stocks...{RESET}',
              end='\r', flush=True)
        found = check_signals()
        if not found:
            # Keep the "no signal" status on the same line
            pass
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f'\n{GRAY}Alerts stopped.{RESET}')
