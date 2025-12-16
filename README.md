# AI-Powered-Stock-Prediction-Analysis
AI-powered stock prediction tool for NSE India combining technical analysis with LLM-based sentiment insights.


This project automates the selection and analysis of top stocks from the NSE (National Stock Exchange of India) using a combination of technical indicators and AI-powered sentiment analysis.

## 🚀 Key Features

*   **Automated Data Fetching**: Downloads the latest "Bhavcopy" (daily market report) directly from the NSE archives.
*   **Smart Filtering**: Filters stocks based on specific price ranges (default: ₹950 - ₹1050) and selects the top 5 by closing price.
*   **Technical Analysis**: Calculates standard Pivot Points, Support (S1), and Resistance (R1) levels for the next trading day.
*   **AI Predictions**: Integrates with an AWS SageMaker endpoint (hosting a Large Language Model like `gpt-oss-20b-vllm`) to analyze market context and predict target prices.
*   **Live Tracking**: Fetches real-time live prices from NSE to compare with previous close.

## 📂 Project Structure

*   `stock_top5_with_ai.py`: **(Main Script)** The core logic for downloading data, analyzing stocks, and querying the AI model.
*   `stock_top5.py`: A lighter version of the script focusing purely on technical analysis without the AI component.
*   `psu_growth_analysis.py`: Specialized script for analyzing Public Sector Undertaking (PSU) stocks.
*   `test_nse_api.py`: Utility to test connectivity with NSE APIs.

## 🛠️ Prerequisites

Ensure you have Python 3.x installed along with the following libraries:

```bash
pip install pandas requests boto3
```

### AWS Configuration (For AI Features)
The `stock_top5_with_ai.py` script uses `boto3` to communicate with an AWS SageMaker endpoint. You must have AWS credentials configured with access to SageMaker.

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and Region (default: us-east-1)
```

## 📖 Detailed Workflow: `stock_top5_with_ai.py`

This script operates in four distinct steps:

### 1. Data Acquisition (`download_bhavcopy`)
*   Determines the date for the latest available data (usually the previous trading day).
*   Constructs the NSE URL for the CSV file.
*   Downloads and saves the file locally (e.g., `cm15DEC2025bhav.csv`).

### 2. Context Gathering (`get_stock_context`)
*   For each of the top 5 selected stocks, it calculates:
    *   **Pivot Point**: (High + Low + Close) / 3
    *   **Resistance (R1)**: (2 * Pivot) - Low
    *   **Support (S1)**: (2 * Pivot) - High
    *   **Volatility**: Percentage difference between High and Low.
*   Prepares a text summary (Context) to feed into the AI.

### 3. AI Prediction (`predict_target_with_ai`)
*   Sends the prepared context to the specified AWS SageMaker endpoint (`gpt-oss-20b-vllm`).
*   **Prompt**: Asks the AI to act as a stock market expert, analyze the trend (Bullish/Bearish), predict a closing price, and provide a confidence score.
*   **Fallback**: If the AI request fails or returns invalid JSON, the script automatically falls back to using the calculated Technical Pivot Points (R1/S1).

### 4. Live Validation (`get_live_price`)
*   Connects to the NSE website to fetch the real-time price of the stock.
*   Compares the live price with the previous close to show immediate performance.

## 🚀 Usage

Run the main script:

```bash
python3 stock_top5_with_ai.py
```

### Output
The script will print a detailed analysis for each stock to the console and save a summary CSV file (e.g., `ai_stock_predictions_YYYYMMDD_HHMMSS.csv`) containing:
*   Symbol
*   Close Price
*   Target Price (AI or Pivot)
*   Stop Loss
*   Sentiment & Reasoning

---
*Disclaimer: This tool is for educational purposes only. Stock market investments are subject to market risks. Please consult with a certified financial advisor before making any investment decisions.*
