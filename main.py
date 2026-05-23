import time
from alpaca_client import AlpacaClient
from strategy import MovingAverageCrossoverStrategy

if __name__ == '__main__':
    client = AlpacaClient()
    strategy = MovingAverageCrossoverStrategy(client)
    while True:
        strategy.run()
        time.sleep(60)
        