import pandas as pd
import os
from lightweight_charts import Chart

def main():
    symbol = 'AAPL'
    duration = '5 D'
    bar_size = '1 hour'
    folder = 'data'

    csv_filename = os.path.join(
        folder,
        f'{symbol}_{duration.replace(" ", "_")}_{bar_size.replace(" ", "_")}.csv'
    )

    try:
        df = pd.read_csv(csv_filename, index_col='date', parse_dates=True)
    except FileNotFoundError:
        print(f"CSV file not found: {csv_filename}")
        return

    # Format candlestick data
    ohlc = df[['open', 'high', 'low', 'close']].copy()
    ohlc['time'] = ohlc.index.strftime('%Y-%m-%dT%H:%M:%S')
    ohlc = ohlc[['time', 'open', 'high', 'low', 'close']]

    # Create chart
    chart = Chart()
    chart.set(ohlc)

    # Format volume histogram
    volume_data = []
    for time, row in df.iterrows():
        volume_data.append({
            'time': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'value': row['volume'],
            'color': 'green' if row['close'] >= row['open'] else 'red'
        })

    chart.create_histogram(volume_data)

    chart.show()
    input("Press Enter to exit...\n")

if __name__ == '__main__':
    main()
