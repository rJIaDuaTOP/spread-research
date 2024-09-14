# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
from collections import deque
import ccxt.pro
import asyncio
from threading import Thread

class priceTicker:
    def __init__(self):
        # Deques for time and price from two different sources
        self.ticker_time = deque(maxlen=200)
        self.last_price_1 = deque(maxlen=200)  # For the first symbol (e.g., BTC/USDT)
        self.last_price_2 = deque(maxlen=200)  # For the second symbol (e.g., ETH/USDT)

        # Start the async event loop in a separate thread for non-blocking Dash updates
        loop = asyncio.get_event_loop()
        Thread(target=lambda: loop.run_until_complete(self.socket()), daemon=True).start()

        # Set up the Dash app layout
        self.app = dash.Dash()
        self.app.layout = html.Div(
            [
                dcc.Graph(id='live-graph', animate=True),
                dcc.Interval(
                    id='graph-update',
                    interval=2000,
                    n_intervals=0
                )
            ]
        )
        # Connect the update callback
        self.app.callback(
            Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals')])(self.update_graph)

    async def socket(self):
        # Create the Binance exchange instance
        exchange = ccxt.pro.binance({
            'options': {
                'defaultType': 'future',
            },
        })
        spot_exchange = ccxt.pro.binance({
            'options': {
                'defaultType': 'spot',
            },
        })
        symbol1 = 'BTC/USDT:USDT-240927'  # First symbol (BTC/USDT)
        symbol2 = 'BTC/USDT:USDT-241227'  # Second symbol (ETH/USDT)

        while True:
            try:
                # Fetch order books for both symbols
                orderbook1 = await exchange.watch_order_book(symbol1)
                orderbook2 = await exchange.watch_order_book(symbol2)

                # Update the time and price for the first symbol (BTC/USDT)
                self.ticker_time.append(orderbook1['datetime'])
                self.last_price_1.append((orderbook1['bids'][0][0] + orderbook1['asks'][0][0]) / 2)

                # Update the price for the second symbol (ETH/USDT)
                self.last_price_2.append((orderbook2['bids'][0][0] + orderbook2['asks'][0][0]) / 2)

            except Exception as e:
                print(f"Error: {type(e).__name__}, {str(e)}")

    def update_graph(self, n):
        # First trace (BTC/USDT)
        trace1 = go.Scatter(
            x=list(self.ticker_time),
            y=list(self.last_price_1),
            name='BTC/USDT Price',
            mode='lines+markers'
        )
        
        # Second trace (ETH/USDT)
        trace2 = go.Scatter(
            x=list(self.ticker_time),
            y=list(self.last_price_2),
            name='ETH/USDT Price',
            mode='lines+markers'
        )

        # Return the data and layout to Dash
        return {
            'data': [trace1, trace2],  # Include both traces in the 'data' list
            'layout': go.Layout(
                xaxis=dict(range=[min(self.ticker_time), max(self.ticker_time)]),
                yaxis=dict(range=[
                    min(min(self.last_price_1), min(self.last_price_2)), 
                    max(max(self.last_price_1), max(self.last_price_2))
                ]),
                title="BTC/USDT and ETH/USDT Price Comparison"
            )
        }

def Main():
    # Create the price ticker and run the Dash app
    ticker = priceTicker()
    ticker.app.run_server(debug=True, host='127.0.0.1', port=16452)

if __name__ == '__main__':
    Main()
