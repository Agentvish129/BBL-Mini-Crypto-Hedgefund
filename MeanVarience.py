#Mean-Variance Efficient Crypto Portfolio (Monthly Rebalancing Strategy)

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

#STEP 1: Setting up the configuration
folder_path = "/Users/ishaangupta/Downloads/cryptocurrency/cryptocurrency_quotes_historical"
#Here I  have downloaded and used the CoinMarketCap Historical quotes data

initial_investment = 10000
lookback_days = 30  # Past 30 days of prices used to calculate returns


# STEP 2: Load all crypto files from the local folder
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

#  STEP 3: Initialise portfolio value tracking
portfolio_value = initial_investment
performance_log = []
months = pd.date_range(start=df.index.min(), end=df.index.max(), freq='MS')

# Began loop which fascilitates monthly rebalancing
for current_month in months:

    prev_start = current_month - pd.Timedelta(days=lookback_days)
    price_window = df[(df.index >= prev_start) & (df.index < current_month)]

    # Identify top 10 by market cap on current month start
    snapshot = df[df.index == current_month]
    if snapshot.empty:
        continue

    top10 = snapshot.groupby('coin_name').first().nlargest(10, 'market_cap')
    top10_names = top10.index.tolist()

    # Pull price data for those top 10
    price_data = price_window[price_window['coin_name'].isin(top10_names)]
    price_matrix = price_data.pivot_table(values='price', index=price_data.index, columns='coin_name')
    price_matrix.dropna(axis=1, inplace=True)
    if price_matrix.shape[1] < 2:
        continue

    # Calculate return matrix
    returns_matrix = price_matrix.pct_change().dropna()
    mean_returns = returns_matrix.mean().values
    cov_matrix = returns_matrix.cov().values
    n = len(mean_returns)

    # Optimization done here to get the best weighst which balance both risk and returns
    def neg_sharpe(weights, mean_returns, cov_matrix):
        port_return = weights @ mean_returns
        port_vol = np.sqrt(weights @ cov_matrix @ weights)
        return -port_return / port_vol if port_vol != 0 else np.inf

    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    bounds = [(0, 1)] * n
    init_guess = np.array([1/n] * n)

    result = minimize(neg_sharpe, init_guess, args=(mean_returns, cov_matrix),
                      method='SLSQP', bounds=bounds, constraints=constraints)

    if not result.success:
        continue

    weights = result.x
    selected_coins = price_matrix.columns.tolist()

    # Allocate investment and compute units bought
    start_prices = price_matrix.iloc[-1].values
    allocations = weights * portfolio_value
    units = allocations / start_prices

    # === STEP 6: PORTFOLIO EVALUATION ===
    month_end = current_month + pd.offsets.MonthEnd(0)
    end_snapshot = df[(df.index == month_end) & (df['coin_name'].isin(selected_coins))]

    if end_snapshot.empty:
        continue

    end_prices = end_snapshot.set_index('coin_name')['price'].reindex(selected_coins).values
    portfolio_value = np.sum(units * end_prices)

    performance_log.append({
        'date': current_month,
        'portfolio_value': portfolio_value
    })

#Plotting the monthly portfolio worth
performance_df = pd.DataFrame(performance_log)
performance_df.set_index('date', inplace=True)

plt.figure(figsize=(12, 6))
plt.plot(performance_df.index, performance_df['portfolio_value'], marker='o')
plt.title('📊 Mean-Variance Optimized Top 10 Crypto Portfolio')
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($)')
plt.grid(True)
plt.tight_layout()
plt.show()
