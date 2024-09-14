import ccxt.pro
from asyncio import run


async def main():
    exchange = ccxt.pro.binance({
        'options': {
            'defaultType': 'future',
        },
    })
    result = await exchange.fetch_tickers()
 
run(main())

