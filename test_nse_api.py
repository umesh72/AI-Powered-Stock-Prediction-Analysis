import requests
import pandas as pd
from datetime import datetime, timedelta
import time

def get_nse_history(symbol, start_date, end_date):
    # NSE expects date in dd-mm-yyyy format
    base_url = "https://www.nseindia.com/api/historical/cm/equity"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/get-quotes/equity?symbol=" + symbol
    }
    
    params = {
        "symbol": symbol,
        "series": "[\"EQ\"]",
        "from": start_date,
        "to": end_date
    }
    
    try:
        with requests.Session() as s:
            # Visit homepage to get cookies
            s.get("https://www.nseindia.com", headers=headers, timeout=10)
            
            # Fetch data
            print(f"Fetching data for {symbol} from {start_date} to {end_date}...")
            r = s.get(base_url, headers=headers, params=params, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                    return df
                else:
                    print("No data key in response")
                    return None
            else:
                print(f"Error: {r.status_code}")
                return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

# Test with SBIN for last 3 months (NSE usually limits range per request)
end = datetime.now()
start = end - timedelta(days=90)
df = get_nse_history("SBIN", start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y"))

if df is not None:
    print("Success!")
    print(df.head())
    print(df.columns)
else:
    print("Failed to fetch data.")
