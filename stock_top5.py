import pandas as pd
import requests
from datetime import datetime, timedelta
import zipfile
import os

# -------------------------------
# Step 1: Download and Load Bhavcopy
# -------------------------------
def download_bhavcopy(date=None):
    """Download Bhavcopy file from NSE for the given date"""
    if date is None:
        # Use previous working day (assuming today might not have data yet)
        date = datetime.now() - timedelta(days=1)
    
    # Format date for NSE URL (e.g., 01DEC2025)
    date_str = date.strftime("%d%b%Y").upper()
    csv_filename = f"cm{date_str}bhav.csv"
    zip_filename = f"{csv_filename}.zip"
    
    # Check if CSV already exists
    if os.path.exists(csv_filename):
        print(f"Using existing file: {csv_filename}")
        return csv_filename
    
    # NSE Bhavcopy URL
    url = f"https://archives.nseindia.com/products/content/sec_bhavdata_full_{date.strftime('%d%m%Y')}.csv"
    
    print(f"Downloading Bhavcopy for {date_str}...")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save the CSV file
        with open(csv_filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded: {csv_filename}")
        return csv_filename
    except Exception as e:
        print(f"Failed to download: {e}")
        print("Please manually download the Bhavcopy file from NSE website")
        return None

# Download or use existing bhavcopy file
bhavcopy_file = download_bhavcopy()

if bhavcopy_file is None:
    print("ERROR: Could not load Bhavcopy file. Exiting.")
    exit(1)

df = pd.read_csv(bhavcopy_file)

# Clean up column names (remove leading/trailing spaces)
df.columns = df.columns.str.strip()

# Clean up string columns (remove leading/trailing spaces from values)
df['SERIES'] = df['SERIES'].str.strip()

# Filter for equity stocks only
df = df[df['SERIES'] == 'EQ']

# -------------------------------
# Step 2: Filter Top 5 by Price Range
# -------------------------------
price_min = 190
price_max = 210

df_filtered = df[(df['CLOSE_PRICE'] >= price_min) & (df['CLOSE_PRICE'] <= price_max)]
df_sorted = df_filtered.sort_values(by='CLOSE_PRICE', ascending=False)
top5_stocks = df_sorted.head(5)

# Compute stop-loss and target
top5_stocks['STOP_LOSS'] = top5_stocks['CLOSE_PRICE'] * 0.97
top5_stocks['TARGET'] = top5_stocks['CLOSE_PRICE'] * 1.05

print("\nTop 5 Stocks from Yesterday:")
print(top5_stocks[['SYMBOL', 'CLOSE_PRICE', 'STOP_LOSS', 'TARGET']])

# -------------------------------
# Step 3: Fetch Today's Live Price (using NSE India JSON API)
# -------------------------------
def get_live_price(symbol):
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    with requests.Session() as s:
        s.get("https://www.nseindia.com", headers=headers)  # initialize session
        r = s.get(url, headers=headers)
        data = r.json()
        return float(data['priceInfo']['lastPrice'])

# -------------------------------
# Step 4: Compare Yesterday Close vs Today Live
# -------------------------------
for idx, row in top5_stocks.iterrows():
    symbol = row['SYMBOL']
    try:
        live_price = get_live_price(symbol)
        change = live_price - row['CLOSE_PRICE']
        change_percent = (change / row['CLOSE_PRICE']) * 100
        print(f"\n{symbol}: Yesterday Close = {row['CLOSE_PRICE']}, Today Live = {live_price}")
        print(f"Change = {change:.2f} ({change_percent:.2f}%)")
    except:
        print(f"{symbol}: Could not fetch live price.")
