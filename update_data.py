import json
import datetime
import yfinance as yf

ASSETS = {
    "qld": ("QLD", "QLD"),
    "qqq": ("QQQ", "QQQ"),
    "voo": ("VOO", "VOO"),
    "brkb": ("BRK-B", "BRK.B"),
    "visa": ("V", "Visa"),
}

def latest_price(ticker):
    try:
        h = yf.Ticker(ticker).history(period="1d", interval="5m", prepost=False)
        if not h.empty:
            return round(float(h["Close"].dropna().iloc[-1]), 4)
    except Exception as e:
        print(f"{ticker} intraday error: {e}")
    try:
        h = yf.Ticker(ticker).history(period="5d", interval="1d")
        if not h.empty:
            return round(float(h["Close"].dropna().iloc[-1]), 4)
    except Exception as e:
        print(f"{ticker} daily fallback error: {e}")
    return 0

def get_market_data():
    print("Market data fetching started...")
    fx_rate = fx_change = fx_pct = 0
    try:
        fx_hist = yf.Ticker("KRW=X").history(period="10d")
        if len(fx_hist) >= 2:
            current_fx = float(fx_hist["Close"].iloc[-1])
            prev_fx = float(fx_hist["Close"].iloc[-2])
            if current_fx == prev_fx and len(fx_hist) >= 3:
                prev_fx = float(fx_hist["Close"].iloc[-3])
            fx_rate = round(current_fx, 2)
            fx_change = round(current_fx - prev_fx, 2)
            if prev_fx > 0:
                fx_pct = round(((current_fx - prev_fx) / prev_fx) * 100, 2)
    except Exception as e:
        print(f"FX Fetch Error: {e}")

    ndx_price = ndx_change = ndx_pct = sma_120 = sma_200 = 0
    try:
        ndx_hist = yf.Ticker("^NDX").history(period="18mo")
        if len(ndx_hist) >= 200:
            current_close = float(ndx_hist["Close"].iloc[-1])
            prev_close = float(ndx_hist["Close"].iloc[-2])
            if current_close == prev_close and len(ndx_hist) >= 3:
                prev_close = float(ndx_hist["Close"].iloc[-3])
            ndx_price = round(current_close, 2)
            ndx_change = round(current_close - prev_close, 2)
            if prev_close > 0:
                ndx_pct = round(((current_close - prev_close) / prev_close) * 100, 2)
            sma_120 = round(float(ndx_hist["Close"].rolling(120).mean().iloc[-1]), 2)
            sma_200 = round(float(ndx_hist["Close"].rolling(200).mean().iloc[-1]), 2)
    except Exception as e:
        print(f"NDX Fetch Error: {e}")

    now_kst = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S KST")
    prices = {}
    for key, (ticker, name) in ASSETS.items():
        prices[key] = {"ticker": ticker, "name": name, "price": latest_price(ticker), "currency": "USD", "unit": "주", "updated_at": now_kst}

    # KRX 금 현물은 Yahoo의 다른 금 상품으로 임의 대체하지 않는다.
    prices["gold"] = {"ticker": None, "name": "KRX 금", "price": 0, "currency": "KRW", "unit": "g", "updated_at": now_kst, "status": "unavailable"}

    data = {
        "updated_at": now_kst,
        "fx_rate": fx_rate,
        "fx_change": fx_change,
        "fx_pct": fx_pct,
        "ndx": {"price": ndx_price, "change": ndx_change, "pct": ndx_pct, "sma_120": sma_120, "sma_200": sma_200},
        "prices": prices,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("data.json updated successfully!")

if __name__ == "__main__":
    get_market_data()
