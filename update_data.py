import yfinance as yf
import requests
import json
from datetime import datetime

def fetch_market_data():
    # 1. QQQ 주가 및 이동평균선 수집
    qqq = yf.Ticker("QQQ")
    df = qqq.history(period="1y")
    
    if df.empty:
        raise Exception("QQQ 데이터를 가져오지 못했습니다.")

    latest_close = float(df['Close'].iloc[-1])
    sma_120 = float(df['Close'].rolling(window=120).mean().iloc[-1])
    sma_200 = float(df['Close'].rolling(window=200).mean().iloc[-1])
    
    qqq_is_up = (latest_close > sma_120) and (latest_close > sma_200)

    # 2. 원/달러 환율 수집 (USDKRW=X)
    usdkrw = yf.Ticker("USDKRW=X")
    fx_df = usdkrw.history(period="5d")
    latest_fx = float(fx_df['Close'].iloc[-1]) if not fx_df.empty else 1350.0

    # 3. JSON 데이터 구성
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "qqq": {
            "price": round(latest_close, 2),
            "sma_120": round(sma_120, 2),
            "sma_200": round(sma_200, 2),
            "is_above_ma": qqq_is_up
        },
        "fx_rate": round(latest_fx, 2)
    }

    # data.json 파일 저장
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print("시장 데이터 수집 및 data.json 업데이트 완료.")

if __name__ == "__main__":
    fetch_market_data()
