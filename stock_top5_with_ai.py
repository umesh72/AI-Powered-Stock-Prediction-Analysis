import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import json
import boto3

# -------------------------------
# Configuration
# -------------------------------
ENDPOINT_NAME = "gpt-oss-20b-vllm"
REGION_NAME = "us-east-1"

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

# -------------------------------
# Step 2: Get Stock News/Context
# -------------------------------
def get_stock_context(symbol, close_price, prev_close, volume, high_price, low_price):
    """Gather context including Pivot Points for tomorrow"""
    
    # Calculate Pivot Points (Standard)
    pivot = (high_price + low_price + close_price) / 3
    r1 = (2 * pivot) - low_price
    s1 = (2 * pivot) - high_price
    
    # Calculate technical indicators
    price_change = close_price - prev_close
    price_change_pct = (price_change / prev_close) * 100
    volatility = ((high_price - low_price) / close_price) * 100
    
    context = f"""
Stock: {symbol}
Data for Date: {datetime.now().strftime('%Y-%m-%d')}
--------------------------------
OHLC Data:
Open: {prev_close} (approx)
High: {high_price}
Low: {low_price}
Close: {close_price}
Volume: {volume}
--------------------------------
Technical Analysis (Pivot Points for Tomorrow):
Pivot Point: {pivot:.2f}
Resistance (R1): {r1:.2f}
Support (S1): {s1:.2f}
Volatility: {volatility:.2f}%
--------------------------------
"""
    return context.strip(), r1, s1

# -------------------------------
# Step 3: AI-Powered Sentiment Analysis
# -------------------------------
def predict_target_with_ai(symbol, context, endpoint_name, region_name):
    """Use AWS SageMaker endpoint to predict target price"""
    
    print(f"   [Debug] Calling AI for {symbol}...")
    
    try:
        runtime = boto3.client('sagemaker-runtime', region_name=region_name)
        
        # Simplified Prompt for better compatibility
        prompt = f"""You are a stock market expert. Based on the technical data below, predict the target price for tomorrow.

{context}

Task:
1. Analyze the trend (Bullish/Bearish).
2. Predict tomorrow's closing price.
3. Give a confidence score (1-10).

Output Format (JSON only):
{{
    "sentiment": "Bullish/Bearish",
    "predicted_price": <number>,
    "confidence": <number>,
    "reason": "<short explanation>"
}}
"""
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 150,
                "temperature": 0.1,
                "return_full_text": False
            }
        }
        
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        response_text = response['Body'].read().decode()
        result = json.loads(response_text)
        
        # Handle different response formats
        if isinstance(result, list):
            generated_text = result[0].get('generated_text', '')
        else:
            generated_text = result.get('generated_text', '')
            
        # Extract JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', generated_text)
        
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"   [Warning] AI output format issue. Using Technical Pivot.")
            return None
            
    except Exception as e:
        print(f"   [Error] AI failed: {e}")
        return None

# -------------------------------
# Step 4: Get Live Price
# -------------------------------
def get_live_price(symbol):
    """Fetch current live price from NSE"""
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        with requests.Session() as s:
            s.get("https://www.nseindia.com", headers=headers)  # initialize session
            r = s.get(url, headers=headers, timeout=10)
            data = r.json()
            return float(data['priceInfo']['lastPrice'])
    except Exception as e:
        print(f"Could not fetch live price for {symbol}: {e}")
        return None

# -------------------------------
# Main Execution
# -------------------------------
def main():
    # Download or use existing bhavcopy file
    bhavcopy_file = download_bhavcopy()
    
    if bhavcopy_file is None:
        print("ERROR: Could not load Bhavcopy file. Exiting.")
        return
    
    # Load and clean data
    df = pd.read_csv(bhavcopy_file)
    df.columns = df.columns.str.strip()
    df['SERIES'] = df['SERIES'].str.strip()
    df = df[df['SERIES'] == 'EQ']
    
    # Filter stocks by price range
    price_min = 950
    price_max = 1050
    
    df_filtered = df[(df['CLOSE_PRICE'] >= price_min) & (df['CLOSE_PRICE'] <= price_max)]
    df_sorted = df_filtered.sort_values(by='CLOSE_PRICE', ascending=False)
    top5_stocks = df_sorted.head(5).copy()
    
    print("\n" + "="*80)
    print("AI-POWERED STOCK ANALYSIS")
    print("="*80)
    
    results = []
    
    for idx, row in top5_stocks.iterrows():
        symbol = row['SYMBOL']
        close_price = row['CLOSE_PRICE']
        prev_close = row['PREV_CLOSE']
        high_price = row['HIGH_PRICE']
        low_price = row['LOW_PRICE']
        volume = row['TTL_TRD_QNTY']
        
        print(f"\n{'='*80}")
        print(f"Analyzing: {symbol}")
        print(f"{'='*80}")
        
        # Get stock context and pivots
        context, r1, s1 = get_stock_context(symbol, close_price, prev_close, volume, high_price, low_price)
        print(context)
        
        # Get AI prediction
        print("\n🤖 Getting AI prediction...")
        ai_prediction = predict_target_with_ai(symbol, context, ENDPOINT_NAME, REGION_NAME)
        
        if ai_prediction:
            # Use AI-predicted targets
            target_price = ai_prediction.get('predicted_price', r1)
            sentiment = ai_prediction.get('sentiment', 'Neutral')
            confidence = ai_prediction.get('confidence', 5)
            reasoning = ai_prediction.get('reason', 'Based on technical analysis')
            
            # Calculate stop loss based on S1 or AI logic
            stop_loss = s1 
            
            print(f"\n✨ AI Analysis:")
            print(f"   Sentiment: {sentiment} (Confidence: {confidence}/10)")
            print(f"   Predicted Target: ₹{target_price:.2f}")
            print(f"   Reasoning: {reasoning}")
        else:
            # Fallback to Pivot Points
            target_price = r1
            stop_loss = s1
            sentiment = "Neutral"
            reasoning = "Pivot Point Resistance (R1)"
            
            print(f"\n⚠️ Using Technical Pivot Points:")
            print(f"   Target Price (R1): ₹{target_price:.2f}")
            print(f"   Stop Loss (S1): ₹{stop_loss:.2f}")
        
        # Get live price
        print(f"\n📊 Fetching live price...")
        live_price = get_live_price(symbol)
        
        if live_price:
            change = live_price - close_price
            change_pct = (change / close_price) * 100
            print(f"   Yesterday Close: ₹{close_price}")
            print(f"   Live Price: ₹{live_price}")
            print(f"   Change: ₹{change:.2f} ({change_pct:+.2f}%)")
        else:
            live_price = close_price
            print(f"   Live price unavailable, using close price: ₹{close_price}")
        
        # Store results
        results.append({
            'Symbol': symbol,
            'Close_Price': close_price,
            'Live_Price': live_price,
            'Target_Price': target_price,
            'Stop_Loss': stop_loss,
            'Sentiment': sentiment,
            'Reasoning': reasoning
        })
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY - TOMORROW'S PREDICTIONS (AI + PIVOTS)")
    print("="*80)
    
    summary_df = pd.DataFrame(results)
    print(summary_df.to_string(index=False))
    
    # Save to CSV
    output_file = f"ai_stock_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    summary_df.to_csv(output_file, index=False)
    print(f"\n✅ Results saved to: {output_file}")

if __name__ == "__main__":
    main()
