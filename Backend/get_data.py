import os
import time
import pandas as pd
from threading import Thread
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract


class IBClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []
        self.df = None
        self._done = False

        self.connect("127.0.0.1", 7497, clientId=1)
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    def error(self, req_id, code, msg, misc=''):
        if code not in [2104, 2106, 2158]:
            print(f"Error {code}: {msg}")

    def historicalData(self, req_id, bar):
        try:
            if str(bar.date).isdigit():
                date = pd.to_datetime(int(bar.date), unit='s')
            else:
                date = pd.to_datetime(bar.date)
        except Exception as e:
            print(f"Date parsing error: {bar.date} ({e})")
            return

        self.data.append({
            'date': date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })

    def historicalDataEnd(self, req_id, start, end):
        print(f"Finished receiving data: {start} to {end}")
        self.df = pd.DataFrame(self.data)
        self.df.set_index('date', inplace=True)
        self.df.sort_index(inplace=True)
        self._done = True


# ---- CONFIG ----

symbol = 'AAPL'
duration = '5 D'
bar_size = '1 hour'
folder = 'data'

# Ensure the output folder exists
os.makedirs(folder, exist_ok=True)

csv_filename = os.path.join(
    folder,
    f'{symbol}_{duration.replace(" ", "_")}_{bar_size.replace(" ", "_")}.csv'
)

# ---- RUN ----

client = IBClient()

contract = Contract()
contract.symbol = symbol
contract.secType = 'STK'
contract.exchange = 'SMART'
contract.currency = 'USD'

time.sleep(1)  # Ensure client is ready

client.reqHistoricalData(
    reqId=1,
    contract=contract,
    endDateTime='',
    durationStr=duration,
    barSizeSetting=bar_size,
    whatToShow='TRADES',
    useRTH=True,
    formatDate=2,
    keepUpToDate=False,
    chartOptions=[]
)

timeout = 30
waited = 0
while not client._done and waited < timeout:
    time.sleep(1)
    waited += 1

client.disconnect()

if client.df is not None:
    client.df.to_csv(csv_filename)
    print(f"Data saved to: {csv_filename}")
else:
    print("No data received.")
