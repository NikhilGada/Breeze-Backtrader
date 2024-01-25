<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtrader with Breeze API Integration</title>
</head>
<body>

<h1>Backtrader with Breeze API Integration</h1>

<p>Integrate Backtrader with the Breeze API for live stock data and strategy visualization.</p>

<p>This project demonstrates the integration of Backtrader, a popular Python library for backtesting and live trading, with the Breeze API provided by ICICI Securities. By combining Backtrader's flexible backtesting capabilities with real-time stock data from the Breeze API, you can develop and test trading strategies efficiently.</p>

<h4 id="virtualenv">Setup virtual environment in your Machine</h4>

You must install the virtualenv package via pip
```
pip install virtualenv
```

You should create breeze virtual environment via virtualenv
```
virtualenv -p python breezevenv
```

And then, You can activate virtual environment via source
```
cd breezevenv
.\Scripts\activate
```

<h4 id="clientinstall">Installing the client</h4>

You can install the latest release via pip

```
pip install breeze-connect
```

```
pip install backtrader
```

```
pip install matplotlib
```

<h4 id="apiusage"> API Usage</h4>

<h2>Table Of Content</h2>
<ul>
    <li><a href="#import">Import necessary libraries</a></li>
    <li><a href="#api-credentials">API credentials</a></li>
    <li><a href="#lists">Lists to store tick data</a></li>
    <li><a href="#sma-periods">Simple Moving Average periods</a></li>
    <li><a href="#cerebro-engine">Create a Backtrader Cerebro engine</a></li>
    <li><a href="#strategy">Define a Backtrader strategy using two SMAs</a></li>
    <li><a href="#pandas-data-feed">Define a custom PandasData feed for Backtrader</a></li>
    <li><a href="#make-pd-data">Function to convert tick data to Pandas DataFrame</a></li>
    <li><a href="#on-ticks">Callback function for handling incoming ticks</a></li>
    <li><a href="#update-plot">Function to update the plot using Matplotlib animation</a></li>
    <li><a href="#breeze-login">Function to log in to the Breeze API</a></li>
    <li><a href="#main-block">Main execution block</a></li>
</ul>

<h3 id="import">Import necessary libraries</h3>
<pre><code>import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from datetime import datetime
import backtrader as bt
from breeze_connect import BreezeConnect
from matplotlib.animation import FuncAnimation
</code></pre>

<h3 id="api-credentials">API credentials</h3>
<pre><code>api_key = "APP KEY"
api_secret = "SECRET KEY"
api_session = "SESSION KEY"
</code></pre>

<h3 id="lists">Lists to store tick data</h3>
<pre><code>ticks_list = []
timestamps = []
opens = []
highs = []
lows = []
closes = []
volumes = []
openinterests = []
</code></pre>

<h3 id="sma-periods">Simple Moving Average periods</h3>
<pre><code># Simple Moving Average periods
sma_shortperiod = 10
sma_longperiod = 15
</code></pre>

<h3 id="cerebro-engine">Create a Backtrader Cerebro engine</h3>
<pre><code># Create a Backtrader Cerebro engine
cerebro = bt.Cerebro()
</code></pre>

<h3 id="strategy">Define a Backtrader strategy using two SMAs</h3>
<pre><code>class SMAStrategy(bt.Strategy):
    params = (
        ("sma_period1", sma_shortperiod),
        ("sma_period2", sma_longperiod),  # Add a second period for the second SMA
    )

    def __init__(self):
        # Create two Simple Moving Averages with different periods
        self.sma1 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period1)
        self.sma2 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period2)
        self.strategy_data = pd.DataFrame(columns=['Datetime', 'Close', 'SMA1', 'SMA2', 'Action'])  # Add a column for the second SMA
</code></pre>

<h3 id="pandas-data-feed">Define a custom PandasData feed for Backtrader</h3>
<pre><code>class PandasData(bt.feeds.PandasData):
    params = (
        ('datetime', 'datetime'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
    )
</code></pre>

<h3 id="make-pd-data">Function to convert tick data to Pandas DataFrame</h3>
<pre><code>def makepddata():
    ticks_data = pd.DataFrame({
        'datetime': timestamps,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes,
        'openinterest': openinterests,
    })
    ticks_data[['open', 'high', 'low', 'close', 'volume']] = ticks_data[['open', 'high', 'low', 'close', 'volume']].astype(float)
    ticks_data['datetime'] = pd.to_datetime(ticks_data['datetime'])
    return ticks_data
</code></pre>

<h3 id="on-ticks">Callback function for handling incoming ticks</h3>
<pre><code>def on_ticks(ticks):
    global ticks_list
    timestamps.append(ticks['datetime'])
    opens.append(ticks['open'])
    highs.append(ticks['high'])
    lows.append(ticks['low'])
    closes.append(ticks['close'])
    volumes.append(ticks['volume'])
    openinterests.append(0)
    ticks_list.append(ticks)
</code></pre>

<h3 id="update-plot">Function to update the plot using Matplotlib animation</h3>
<pre><code>def update_plot(frame):
    global fig, ax  # Use global variables for the figure and axis
    if (len(ticks_list) % sma_longperiod == 0 and len(ticks_list) > 0): 
        df = makepddata()
        data0 = PandasData(dataname=df)
        cerebro = bt.Cerebro()  # Create a new cerebro object
        cerebro.adddata(data0)
        cerebro.addstrategy(SMAStrategy)
        cerebro.addobserver(bt.observers.BuySell)
        cerebro.addobserver(bt.observers.Value)
        strategies = cerebro.run()  # This returns a list of Strategy objects
        strategy = strategies[0]  # Get the first (and in this case, only) strategy
        ax.clear()
        ax.plot(df['datetime'], df['close'], label='Close Price', color='yellow')
        sma_values1 = strategy.sma1.get(size=len(df))  # Get the SMA1 values from the strategy
        sma_values2 = strategy.sma2.get(size=len(df))  # Get the SMA2 values from the strategy
        ax.plot(df['datetime'], sma_values1, label=f'{SMAStrategy.params.sma_period1}-period SMA', color='orange')
        ax.plot(df['datetime'], sma_values2, label=f'{SMAStrategy.params.sma_period2}-period SMA', color='blue')
        locator = ticker.MaxNLocator(nbins=10)
        ax.xaxis.set_major_locator(locator)
        ax.legend()
        plt.draw()
        print("Plotting.....")
</code></pre>

<h3 id="breeze-login">Function to log in to the Breeze API</h3>
<pre><code>def breezelogin():
    api = BreezeConnect(api_key=api_key)
    api.generate_session(api_secret=api_secret, session_token=api_session)
    api.ws_connect()
    api.on_ticks = on_ticks
    api.subscribe_feeds(stock_token="4.1!2885", interval="1second")
</code></pre>

<h3 id="main-block">Main execution block</h3>
<pre><code>if __name__ == "__main__":
    # Log in to Breeze API and set up initial plot
    breezelogin()
    fig, ax = plt.subplots()  # Create an initial plot
    plt.show(block=False)  # Ensure the initial plot is displayed
    
    # Set up Matplotlib animation
    ani = FuncAnimation(fig, update_plot, interval=1000, blit=False)  # Update every second
    plt.show()
</code></pre>

</body>
</html>
