import os
import alpaca_trade_api as tradeapi

class AlpacaClient:
    def __init__(self):
        self.api_key = os.environ['ALPACA_API_KEY']
        self.secret_key = os.environ['ALPACA_SECRET_KEY']
        self.base_url = os.environ.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        self.api = tradeapi.REST(self.api_key, self.secret_key, self.base_url, api_version='v2')
    
    def submit_order(self, symbol, qty, side, order_type='market'):
        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force='gtc')
    
    def get_positions(self):
        return self.api.list_positions()
    
    def get_account(self):
        return self.api.get_account()
        