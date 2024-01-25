# Import necessary libraries
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from datetime import datetime
import backtrader as bt
from breeze_connect import BreezeConnect
from matplotlib.animation import FuncAnimation

# API credentials
api_key = "APP KEY"
api_secret = "SECRET KEY"
api_session = "SESSION KEY"

# Lists to store tick data
ticks_list = []
timestamps = []
opens = []
highs = []
lows = []
closes = []
volumes = []
openinterests = []

# Simple Moving Average periods
sma_shortperiod = 10
sma_longperiod = 15

# Create a Backtrader Cerebro engine
cerebro = bt.Cerebro()

# Define a Backtrader strategy using two SMAs
class SMAStrategy(bt.Strategy):
    params = (
        ("sma_period1", sma_shortperiod),
        ("sma_period2", sma_longperiod),  # Add a second period for the second SMA
    )

    def __init__(self):
        # Create two Simple Moving Averages with different periods
        self.sma1 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period1)
        self.sma2 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period2)
        self.strategy_data = pd.DataFrame(columns=['Datetime', 'Close', 'SMA1', 'SMA2', 'Action'])  # Add a column for the second SMA

    def next(self):
        # Get the current values
        current_datetime = bt.num2date(self.data.datetime[0])
        close_price = self.data.close[0]
        sma_value1 = self.sma1[0]
        sma_value2 = self.sma2[0]  # Get the value of the second SMA

        # Store data in the DataFrame using loc
        self.strategy_data.loc[len(self.strategy_data)] = {
            'Datetime': current_datetime,
            'Close': close_price,
            'SMA1': sma_value1,
            'SMA2': sma_value2,  # Store the value of the second SMA
            'Action': self.get_action(),
        }

        # Buy or sell based on both SMAs
        if self.sma1 > self.data.close and self.sma2 > self.data.close:
            self.sell()
        elif self.sma1 < self.data.close and self.sma2 < self.data.close:
            self.buy()

    def get_action(self):
        # Return action based on both SMAs
        if self.sma1 > self.data.close and self.sma2 > self.data.close:
            return 'Sell'
        elif self.sma1 < self.data.close and self.sma2 < self.data.close:
            return 'Buy'
        else:
            return 'Hold'

# Define a custom PandasData feed for Backtrader
class PandasData(bt.feeds.PandasData):
    params = (
        ('datetime', 'datetime'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
    )

# Function to convert tick data to Pandas DataFrame
def makepddata():
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

# Callback function for handling incoming ticks
def on_ticks(ticks):
    global ticks_list
    timestamps.append(ticks['datetime'])
    opens.append(ticks['open'])
    highs.append(ticks['high'])
    lows.append(ticks['low'])
    closes.append(ticks['close'])
    volumes.append(ticks['volume'])
    openinterests.append(0)
    ticks_list.append(ticks)

# Function to update the plot using Matplotlib animation
def update_plot(frame):
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

# Function to log in to the Breeze API
def breezelogin():
    api = BreezeConnect(api_key=api_key)
    api.generate_session(api_secret=api_secret, session_token=api_session)
    api.ws_connect()
    api.on_ticks = on_ticks
    api.subscribe_feeds(stock_token="4.1!2885", interval="1second")

# Main execution block
if __name__ == "__main__":
    # Log in to Breeze API and set up initial plot
    breezelogin()
    fig, ax = plt.subplots()  # Create an initial plot
    plt.show(block=False)  # Ensure the initial plot is displayed
    
    # Set up Matplotlib animation
    ani = FuncAnimation(fig, update_plot, interval=1000, blit=False)  # Update every second
    plt.show()
