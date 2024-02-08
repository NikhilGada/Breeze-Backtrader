# Import necessary libraries
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for Matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from datetime import datetime
import backtrader as bt
from breeze_connect import BreezeConnect  # Import BreezeConnect for API connection
from matplotlib.animation import FuncAnimation

# API credentials
api_key = "APP_KEY"
api_secret = "SECRET_KEY"
api_session = "API_SESSION"

# Lists to store tick data
ticks_list = []
timestamps = []
opens = []
highs = []
lows = []
closes = []
volumes = []
openinterests = []

# Create a Backtrader Cerebro engine
cerebro = bt.Cerebro()

# Define a Backtrader strategy using two SMAs
class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=5,  # period for the fast moving average
        pslow=12   # period for the slow moving average
    )

    def __init__(self):
        self.sma1 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.pfast)  # fast moving average
        self.sma2 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(self.sma1, self.sma2)  # crossover signal
        self.strategy_data = pd.DataFrame(columns=['Datetime', 'Close', 'SMA1', 'SMA2', 'Action'])  # DataFrame for strategy data


    def next(self):
        # Get the current values
        current_datetime = bt.num2date(self.data.datetime[0])
        close_price = self.data.close[0]
        sma_value1 = self.sma1[0]  # Use fast line for SMA1
        sma_value2 = self.sma2[0]  # Use slow line for SMA2

        # Store data in the DataFrame using loc
        self.strategy_data.loc[len(self.strategy_data)] = {
            'Datetime': current_datetime,
            'Close': close_price,
            'SMA1': sma_value1,  # Extract the value from the indicator
            'SMA2': sma_value2,  # Extract the value from the indicator
            'Action': self.get_action(),
        }

        if self.crossover > 0:  # if fast crosses slow to the upside
            #example to placeorder from breeze for buy
            #breeze.place_order(stock_code="ITC",
                    exchange_code="NSE",
                    product="cash",
                    action="buy",
                    order_type="limit",
                    stoploss="",
                    quantity="1",
                    price="305",
                    validity="day"
                )
            self.buy()  # enter long
        elif self.crossover < 0:  # if fast crosses slow to the downside
            #example to placeorder from breeze for sell
            #breeze.square_off(exchange_code="NSE",
                    product="margin",
                    stock_code="NIFTY",
                    quantity="10",
                    price="0",
                    action="sell",
                    order_type="market",
                    validity="day",
                    stoploss="0",
                    disclosed_quantity="0",
                    protection_percentage="",
                    settlement_id="",
                    cover_quantity="",
                    open_quantity="",
                    margin_amount="")
            self.close()  # close long position
  

    def get_action(self):
        if self.crossover > 0:
            return 'Buy'
        elif self.crossover < 0:
            return 'Sell'
        else:
            return 'Hold'

    def stop(self):
        # Save the strategy data to a CSV file when the backtest is complete
        self.strategy_data.to_csv('current.csv', index=False)

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
    # ticks_data[['open', 'high', 'low', 'close', 'volume']] = ticks_data[['open', 'high', 'low', 'close', 'volume']].astype(float)
    # ticks_data['datetime'] = pd.to_datetime(ticks_data['datetime'])
    
    # df = pd.DataFrame(bdata["Success"])
    print(ticks_data)
    ticks_data[['open', 'high', 'low', 'close', 'volume']] = ticks_data[['open', 'high', 'low', 'close', 'volume']].astype(float)
    #ticks_data.dropna(subset=['open', 'high', 'low', 'close', 'volume'], inplace=True)
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
    print(len(ticks_list))
    if (len(ticks_list) % 30 == 0 and len(ticks_list) > 0):
        try: 
            df = makepddata()
            print("---",len(df.tail()))
            data0 = PandasData(dataname=df)
           # Create a new Cerebro engine for each tick to update the plot
            cerebro = bt.Cerebro()
            cerebro.adddata(data0)
            cerebro.addstrategy(SmaCross)

            # Run the engine and plot the chart
            cerebro.run()
            cerebro.plot()  # Adjust the plot style as needed

            # Save the strategy data to CSV
            #strategy_data.to_csv('current.csv', index=False)

            print("plotted")
        except Exception as e:
            print(f"Error during plotting: {e}")
            #strategy_data.to_csv('current.csv', index=False)

# # Function to update the plot using Matplotlib animation
# def update_plot(frame):
#     print(len(ticks_list))
#     try:
#         global fig, ax  # Use global variables for the figure and axis
#         if (len(ticks_list) % SmaCross.params.pslow == 0 and len(ticks_list) > 0): 
#             df = makepddata()
#             print("---",len(df.tail()))
#             data0 = PandasData(dataname=df)
#             cerebro.adddata(data0)
#             cerebro.addstrategy(SmaCross)
#             cerebro.run()  # run it all
#             cerebro.plot()  # and plot it with a single command
#             strategy_data.to_csv('current.csv', index=False)
#             print("plotted")
#     except:
#         strategy_data.to_csv('current.csv', index=False)
# # Function to log in to the Breeze API

def breezelogin():
    api = BreezeConnect(api_key=api_key)
    api.generate_session(api_secret=api_secret, session_token=api_session)
    api.ws_connect()
    api.on_ticks = on_ticks
    api.subscribe_feeds(stock_token="4.1!2885", interval="1second")
    
    while True:
        pass

# Main execution block
if __name__ == "__main__":
    # Log in to Breeze API and set up initial plot
    breezelogin()
    # fig, ax = plt.subplots()  # Create an initial plot
    # plt.show(block=False)  # Ensure the initial plot is displayed
    
    # # Set up Matplotlib animation
    # ani = FuncAnimation(fig, update_plot, interval=1000, blit=False)  # Update every second
    # plt.show()
