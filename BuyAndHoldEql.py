import os
import pandas as pd
import matplotlib.pyplot as plt

# Update this to the local path where your crypto CSVs are stored
folder_path = "/Users/ishaangupta/Downloads/cryptocurrency/cryptocurrency_quotes_historical" # Change this to your actual folder path

#Load and combine all crypto files
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
            print(f" We are Skipping {filename}: {e}")

# Make sure we have valid data
if not all_data:
    raise ValueError("No valid CSV files found in the specified folder.")

# Combine all data
df = pd.concat(all_data, ignore_index=True)

# Preprocess the DataFrame
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df[['coin_name', 'timestamp', 'market_cap', 'price']]
df.dropna(subset=['market_cap', 'price'], inplace=True)
df.set_index('timestamp', inplace=True)
df.sort_index(inplace=True)

# Initialize portfolio simulation
initial_investment = 10000
portfolio_value = initial_investment
monthly_portfolio_values = []

# Generate list of monthly dates (1st of each month)
months = pd.date_range(start=df.index.min(), end=df.index.max(), freq='MS')

# STEP 5: Loop through each month and rebalance
for current_month in months:
    # a. First day of the month for each coin
    month_data = df[df.index.to_period('M') == current_month.to_period('M')]
    first_day = month_data.groupby('coin_name').first().reset_index()
    top10 = first_day.nlargest(10, 'market_cap').copy()

    if top10.empty:
        continue

    num_assets = len(top10)
    equal_weight = 1 / num_assets

    # Equal allocation
    top10['weight'] = equal_weight
    top10['investment'] = equal_weight * portfolio_value
    top10['units'] = top10['investment'] / top10['price']

    # b. Get end-of-month price
    last_day = month_data.groupby('coin_name').last().reset_index()
    last_day.set_index('coin_name', inplace=True)
    top10.set_index('coin_name', inplace=True)
    top10 = top10.join(last_day[['price']], rsuffix='_end')

    top10['end_value'] = top10['units'] * top10['price_end']
    portfolio_value = top10['end_value'].sum()

    # c. Store result
    monthly_portfolio_values.append({
        'date': current_month,
        'portfolio_value': portfolio_value
    })

#Plotting the monthly portfolio worth
performance_df = pd.DataFrame(monthly_portfolio_values)
performance_df.set_index('date', inplace=True)

plt.figure(figsize=(12, 6))
plt.plot(performance_df.index, performance_df['portfolio_value'], marker='o', color='green')
plt.title('Monthly Portfolio Value (Top 10 Equal-Weighted Strategy)')
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($)')
plt.grid(True)
plt.tight_layout()
plt.show()
