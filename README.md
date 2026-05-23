# Friday Trader

An AI-powered paper trading bot that implements a simple moving average crossover strategy using the Alpaca Markets API and yfinance for market data.

## Setup Instructions

1. Create a free paper trading account at [alpaca.markets](https://alpaca.markets)
2. Get your API keys from the Alpaca dashboard
3. Add your keys to `alpaca_client.py`
4. Install dependencies:
```bash
   pip install -r requirements.txt
```
5. Run the trading bot:
```bash
   python main.py
```
6. Launch the dashboard:
```bash
   streamlit run dashboard.py
```

## Strategy

Uses a **Moving Average Crossover** strategy:
- **Buy** when the 50-day MA crosses above the 200-day MA (golden cross)
- **Sell** when the 50-day MA crosses below the 200-day MA (death cross)

## Tech Stack

- Python
- Alpaca Markets API (paper trading)
- yfinance
- Streamlit

## Disclaimer

This is a paper trading bot for educational purposes only. Not financial advice.