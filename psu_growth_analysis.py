import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# -------------------------------
# Configuration
# -------------------------------
# PSU Stocks (Public Sector Undertakings)
PSU_STOCKS = [
    "SBIN.NS", "NTPC.NS", "ONGC.NS", "HAL.NS", "BEL.NS", 
    "COALINDIA.NS", "POWERGRID.NS", "BPCL.NS", "IOC.NS", "PFC.NS"
]

# High Growth Stocks (Consistently growing over last 5 years)
GROWTH_STOCKS = [
    "BAJFINANCE.NS", "TITAN.NS", "TRENT.NS", "VBL.NS", 
    "PIIND.NS", "ASTRAL.NS", "POLYCAB.NS", "DIXON.NS", "KPITTECH.NS", "LTIM.NS"
]

ALL_STOCKS = PSU_STOCKS + GROWTH_STOCKS

def analyze_stock_pattern(symbol):
    """
    Analyze the stock for the 'First 2 Weeks vs Last 2 Weeks' pattern over the last 5 years.
    """
    print(f"Fetching data for {symbol}...")
    
    # Fetch 5 years of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    
    try:
        df = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if df.empty:
            print(f"No data found for {symbol}")
            return None
            
        # Ensure index is datetime
        df.index = pd.to_datetime(df.index)
        
        # Add Year and Month columns
        df['Year'] = df.index.year
        df['Month'] = df.index.month
        df['Day'] = df.index.day
        
        monthly_stats = []
        
        # Group by Year and Month
        for (year, month), group in df.groupby(['Year', 'Month']):
            # First 2 Weeks (Days 1-15)
            first_half = group[group['Day'] <= 15]
            
            # Last 2 Weeks (Days 16-End)
            second_half = group[group['Day'] > 15]
            
            if not first_half.empty and not second_half.empty:
                avg_first = first_half['Close'].mean().item()
                avg_second = second_half['Close'].mean().item()
                
                # Calculate return/change
                change_pct = ((avg_second - avg_first) / avg_first) * 100
                
                monthly_stats.append({
                    'Year': year,
                    'Month': month,
                    'Avg_First_Half': avg_first,
                    'Avg_Second_Half': avg_second,
                    'Change_Pct': change_pct,
                    'Trend': 'Up' if change_pct > 0 else 'Down'
                })
        
        if not monthly_stats:
            return None
            
        stats_df = pd.DataFrame(monthly_stats)
        
        # Calculate overall statistics
        avg_monthly_change = stats_df['Change_Pct'].mean()
        win_rate = (stats_df[stats_df['Change_Pct'] > 0].shape[0] / stats_df.shape[0]) * 100
        
        # Recent Trend (Last 6 months)
        recent_stats = stats_df.tail(6)
        recent_avg_change = recent_stats['Change_Pct'].mean()
        
        return {
            'Symbol': symbol,
            'Category': 'PSU' if symbol in PSU_STOCKS else 'Growth',
            'Avg_Monthly_Change': avg_monthly_change,
            'Win_Rate': win_rate, # Percentage of months where 2nd half > 1st half
            'Recent_Trend_6M': recent_avg_change,
            'Total_Months': len(stats_df)
        }
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

def main():
    print("="*80)
    print("STOCK PATTERN ANALYSIS: First 2 Weeks vs Last 2 Weeks (Last 5 Years)")
    print("="*80)
    
    results = []
    
    for symbol in ALL_STOCKS:
        result = analyze_stock_pattern(symbol)
        if result:
            results.append(result)
            
    # Create DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by Win Rate (Consistency)
    results_df = results_df.sort_values(by='Win_Rate', ascending=False)
    
    print("\n" + "="*80)
    print("ANALYSIS RESULTS (Sorted by Consistency)")
    print("="*80)
    print("Win Rate: % of months where Last 2 Weeks Price > First 2 Weeks Price")
    print("-" * 80)
    
    # Format for display
    display_df = results_df.copy()
    display_df['Avg_Monthly_Change'] = display_df['Avg_Monthly_Change'].map('{:+.2f}%'.format)
    display_df['Win_Rate'] = display_df['Win_Rate'].map('{:.1f}%'.format)
    display_df['Recent_Trend_6M'] = display_df['Recent_Trend_6M'].map('{:+.2f}%'.format)
    
    print(display_df[['Symbol', 'Category', 'Win_Rate', 'Avg_Monthly_Change', 'Recent_Trend_6M']].to_string(index=False))
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"stock_pattern_analysis_{timestamp}.csv"
    results_df.to_csv(filename, index=False)
    print(f"\n✅ Detailed results saved to: {filename}")
    
    # Top Picks
    print("\n" + "="*80)
    print("TOP PICKS (Best Pattern)")
    print("="*80)
    top_picks = results_df.head(5)
    for _, row in top_picks.iterrows():
        print(f"⭐ {row['Symbol']} ({row['Category']})")
        print(f"   Consistency: {row['Win_Rate']:.1f}% of months")
        print(f"   Avg Gain (2nd Half vs 1st Half): {row['Avg_Monthly_Change']:+.2f}%")
        print("-" * 40)

if __name__ == "__main__":
    main()
