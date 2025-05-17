#Momentum-Based Crypto Portfolio (Monthly Rebalancing Strategy)

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# STEP 1: Setting up the configuration
folder_path = "/Users/ishaangupta/Downloads/cryptocurrency/cryptocurrency_quotes_historical" #add your own local path
#Here I  have downloaded and used the CoinMarketCap Historical quotes data

initial_investment = 10000
lookback_days = 30  # Look back period to calculate momentum (past 30-day return)
top_n = 10          # Number of top momentum coins to invest in

#STEP 2: Load all crypto files from the local folder
all_data = []
for filename in os.listdir(folder_path):

    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)
        try:
            df_coin = pd.read_csv(file_path)
            if 'coin_name' not in df_coin.columns:
                df_coin['coin_name'] = filename.replace('.csv', '')
            all_data.append(df_coin)

        except Exception as e:
            print(f"Skipping {filename}: {e}")

if not all_data:
    raise ValueError("No valid CSV files found in the specified folder.")

# Concatenate all coin df into one single df
df = pd.concat(all_data, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df[['coin_name', 'timestamp', 'market_cap', 'price']]
df.dropna(subset=['market_cap', 'price'], inplace=True)
df.set_index('timestamp', inplace=True)
df.sort_index(inplace=True)

# STEP 3: Initialise portfolio value tracking
portfolio_value = initial_investment
performance_log = []
months = pd.date_range(start=df.index.min(), end=df.index.max(), freq='MS')

#  Began loop which fascilitates monthly rebalancing
for current_month in months:

    # Define previous 30-day window for momentum calculation
    momentum_start = current_month - pd.Timedelta(days=lookback_days)
    past_data = df[(df.index >= momentum_start) & (df.index < current_month)]

    # Skip if there's not enough data
    if past_data.empty:
        continue

    # Calculate return = (last price - first price) / first price for each coin
    first_prices = past_data.groupby('coin_name').first()['price']
    last_prices = past_data.groupby('coin_name').last()['price']
    momentum_returns = ((last_prices - first_prices) / first_prices).dropna()

    # Rank and pick top-N momentum coins
    top_momentum_coins = momentum_returns.nlargest(top_n).index.tolist()

    # Get price at start of month to calculate units purchased
    month_start_prices = df[(df.index == current_month) & df['coin_name'].isin(top_momentum_coins)]
    if month_start_prices.empty:
        continue

    # Equal weight allocation
    equal_weight = 1 / top_n
    allocations = {coin: portfolio_value * equal_weight for coin in top_momentum_coins}

    # Units = investment / price
    month_start_prices = month_start_prices.set_index('coin_name')
    units = {coin: allocations[coin] / month_start_prices.at[coin, 'price']
             for coin in top_momentum_coins if coin in month_start_prices.index}

    # Get end-of-month price to evaluate portfolio
    month_end = current_month + pd.offsets.MonthEnd(0)
    month_end_prices = df[(df.index == month_end) & df['coin_name'].isin(units.keys())]
    month_end_prices = month_end_prices.set_index('coin_name')

    # Calculate end value of portfolio
    portfolio_value = sum(units[coin] * month_end_prices.at[coin, 'price']
                          for coin in units if coin in month_end_prices.index)

    performance_log.append({
        'date': current_month,
        'portfolio_value': portfolio_value
    })

# Plotting the monthly portfolio worth
performance_df = pd.DataFrame(performance_log)
performance_df.set_index('date', inplace=True)

plt.figure(figsize=(12, 6))
plt.plot(performance_df.index, performance_df['portfolio_value'], marker='o', linestyle='-')
plt.title('📊 Momentum-Based Top 10 Crypto Portfolio')
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($)')
plt.grid(True)
plt.tight_layout()
plt.show()
