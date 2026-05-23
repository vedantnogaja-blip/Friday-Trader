import streamlit as st
import yfinance as yf
import pandas as pd
from alpaca_client import AlpacaClient

def main():
    st.title('Friday Trader Dashboard')

    try:
        client = AlpacaClient()
    except KeyError as e:
        st.error(f'Missing environment variable: {e}. Set ALPACA_API_KEY and ALPACA_SECRET_KEY.')
        return

    # Account info
    try:
        account = client.get_account()
        st.metric('Portfolio Value', f'${float(account.portfolio_value):,.2f}')
        st.metric('Cash', f'${float(account.cash):,.2f}')
    except Exception as e:
        st.error(f'Failed to load account info: {e}')

    # Positions
    st.subheader('Current Positions')
    try:
        positions = client.get_positions()
        if positions:
            for p in positions:
                st.write(f'{p.symbol}: {p.qty} shares @ ${float(p.avg_entry_price):,.2f}')
        else:
            st.write('No open positions')
    except Exception as e:
        st.error(f'Failed to load positions: {e}')

    # Price chart
    st.subheader('AAPL Price Chart')
    data = yf.download('AAPL', period='200d', interval='1d')
    # Flatten MultiIndex columns (yfinance 0.2.x returns MultiIndex for single tickers)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data['50MA'] = data['Close'].rolling(window=50).mean()
    data['200MA'] = data['Close'].rolling(window=200).mean()
    st.line_chart(data[['Close', '50MA', '200MA']])

if __name__ == '__main__':
    main()
    