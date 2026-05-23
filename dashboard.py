import streamlit as st
import yfinance as yf
import pandas as pd
from alpaca_client import AlpacaClient
from backtest import run_backtest, plot_backtest


def live_page():
    try:
        client = AlpacaClient()
    except KeyError as e:
        st.error(f'Missing environment variable: {e}. Set ALPACA_API_KEY and ALPACA_SECRET_KEY.')
        return

    # Account info
    try:
        account = client.get_account()
        col1, col2 = st.columns(2)
        col1.metric('Portfolio Value', f'${float(account.portfolio_value):,.2f}')
        col2.metric('Cash', f'${float(account.cash):,.2f}')
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
    data = yf.download('AAPL', period='200d', interval='1d', progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data['50MA'] = data['Close'].rolling(window=50).mean()
    data['200MA'] = data['Close'].rolling(window=200).mean()
    st.line_chart(data[['Close', '50MA', '200MA']])


def backtest_page():
    st.header('Backtest: MA Crossover Strategy')
    st.write('Simulates the 50/200-day moving average crossover strategy on 5 years of AAPL data starting with $10,000.')

    if st.button('Run Backtest'):
        with st.spinner('Downloading data and running simulation...'):
            results = run_backtest()

        # Summary metrics
        st.subheader('Results')
        col1, col2, col3 = st.columns(3)
        col1.metric('Final Portfolio Value', f"${results['final_value']:,.2f}")
        delta_color = 'normal' if results['total_return'] >= 0 else 'inverse'
        col2.metric('Total Return', f"{results['total_return']:.2f}%",
                    delta=f"{results['total_return']:.2f}%")
        col3.metric('Number of Trades', results['num_trades'])

        # Chart
        st.subheader('Price Chart with Signals')
        fig = plot_backtest(results)
        st.pyplot(fig)

        # Trade history
        st.subheader('Trade History')
        if not results['trades'].empty:
            st.dataframe(results['trades'], use_container_width=True)
        else:
            st.write('No trades were triggered in this period.')


def main():
    st.set_page_config(page_title='Friday Trader', layout='wide')
    st.title('Friday Trader Dashboard')

    page = st.sidebar.radio('Navigation', ['Live Trading', 'Backtest'])

    if page == 'Live Trading':
        live_page()
    else:
        backtest_page()


if __name__ == '__main__':
    main()
