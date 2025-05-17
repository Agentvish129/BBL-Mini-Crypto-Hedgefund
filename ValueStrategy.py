#Value-Based Crypto Portfolio (Monthly Rebalancing Strategy)

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#STEP 1: Setting up the configuration
folder_path = "/Users/ishaangupta/Downloads/cryptocurrency/cryptocurrency_quotes_historical"  #Add your own path
#Here I  have downloaded and used the CoinMarketCap Historical data

initial_investment = 10000
lookback_top_n = 150  # Consider top 150 coins by market cap of our data
portfolio_size = 10   # How many coins to invest in each month

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
    raise ValueError("No valid CSV files found in the specified local folder.")

# Concatenate all coin df into one single df
df = pd.concat(all_data, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df[['coin_name', 'timestamp', 'market_cap', 'volume_24h', 'price']]
df.dropna(subset=['market_cap', 'volume_24h', 'price'], inplace=True)
df.set_index('timestamp', inplace=True)
df.sort_index(inplace=True)

#STEP 3: Initialise portfolio value tracking
portfolio_value = initial_investment
performance_log = []
months = pd.date_range(start=df.index.min(), end=df.index.max(), freq='MS')

# Began loop which fascilitates monthly rebalancing
for current_month in months:
    # Get snapshot of all coins on the first day of the month
    month_snapshot = df[df.index == current_month]
    if month_snapshot.empty:
        continue

    # Filter top N coins by market cap
    top_coins = month_snapshot.groupby('coin_name').first().nlargest(lookback_top_n, 'market_cap')

    # Calculate Value Score = market_cap / volume_24h (lower is better)
    top_coins = top_coins.copy()
    top_coins['value_score'] = top_coins['market_cap'] / top_coins['volume_24h']

    # Select top coins with lowest value_score
    selected = top_coins.nsmallest(portfolio_size, 'value_score')
    selected_coins = selected.index.tolist()

    # Equal-weighted investment allocation
    equal_weight = 1 / portfolio_size
    allocations = {coin: portfolio_value * equal_weight for coin in selected_coins}

    # Get start-of-month prices
    start_prices = month_snapshot.set_index('coin_name').loc[selected_coins]['price']
    units = {coin: allocations[coin] / start_prices[coin] for coin in selected_coins}

    # Get end-of-month prices
    month_end = current_month + pd.offsets.MonthEnd(0)
    month_end_snapshot = df[(df.index == month_end) & df['coin_name'].isin(units.keys())]
    month_end_prices = month_end_snapshot.set_index('coin_name')['price']

    # Calculate new portfolio value
    portfolio_value = sum(
        units[coin] * month_end_prices[coin]
        for coin in units if coin in month_end_prices
    )

    performance_log.append({
        'date': current_month,
        'portfolio_value': portfolio_value
    })

# Plotting the monthly portfolio worth
performance_df = pd.DataFrame(performance_log)
performance_df.set_index('date', inplace=True)

plt.figure(figsize=(12, 6))
plt.plot(performance_df.index, performance_df['portfolio_value'], marker='o', linestyle='-')
plt.title('📊 Value-Based Top 10 Crypto Portfolio')
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($)')
plt.grid(True)
plt.tight_layout()
plt.show()
