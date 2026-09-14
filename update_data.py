import json
import datetime
import yfinance as yf

def get_market_data():
    print("Market data fetching started...")
    
    # 1. 환율 (USD/KRW) 수집 및 전일 대비 계산
    fx_rate = 0
    fx_change = 0
    fx_pct = 0
    try:
        fx = yf.Ticker("KRW=X")
        fx_hist = fx.history(period="5d")
        if len(fx_hist) >= 2:
            current_fx = float(fx_hist['Close'].iloc[-1])
            prev_fx = float(fx_hist['Close'].iloc[-2])
            fx_rate = round(current_fx, 2)
            fx_change = round(current_fx - prev_fx, 2)
            fx_pct = round(((current_fx - prev_fx) / prev_fx) * 100, 2)
    except Exception as e:
        print(f"FX Fetch Error: {e}")

    # 2. QQQ 종가, 전일대비 %, 120일/200일 이평선 수집
    qqq_close = 0
    qqq_change = 0
    qqq_pct = 0
    sma_120 = 0
    sma_200 = 0
    try:
        qqq = yf.Ticker("QQQ")
        qqq_hist = qqq.history(period="1y")
        if len(qqq_hist) >= 200:
            current_close = float(qqq_hist['Close'].iloc[-1])
            prev_close = float(qqq_hist['Close'].iloc[-2])
            
            qqq_close = round(current_close, 2)
            qqq_change = round(current_close - prev_close, 2)
            qqq_pct = round(((current_close - prev_close) / prev_close) * 100, 2)
            
            sma_120 = round(float(qqq_hist['Close'].rolling(window=120).mean().iloc[-1]), 2)
            sma_200 = round(float(qqq_hist['Close'].rolling(window=200).mean().iloc[-1]), 2)
    except Exception as e:
        print(f"QQQ Fetch Error: {e}")

    # 3. JSON 데이터 구조화
    now_kst = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S KST")
    
    data = {
        "updated_at": now_kst,
        "fx_rate": fx_rate,
        "fx_change": fx_change,
        "fx_pct": fx_pct,
        "QQQ": {
            "close": qqq_close,
            "change": qqq_change,
            "pct": qqq_pct,
            "sma_120": sma_120,
            "sma_200": sma_200
        }
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print("data.json updated successfully!")

if __name__ == "__main__":
    get_market_data()
