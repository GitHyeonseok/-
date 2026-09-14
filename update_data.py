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
        fx_hist = fx.history(period="10d")
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

    # 2. NASDAQ-100(^NDX) 종가, 전일 대비 %, 120일/200일 이동평균선 수집
    ndx_price = 0
    ndx_change = 0
    ndx_pct = 0
    sma_120 = 0
    sma_200 = 0
    try:
        ndx = yf.Ticker("^NDX")
        # 200거래일을 안정적으로 확보하기 위해 18개월 수집
        ndx_hist = ndx.history(period="18mo")

        if len(ndx_hist) >= 200:
            current_close = float(ndx_hist["Close"].iloc[-1])
            prev_close = float(ndx_hist["Close"].iloc[-2])

            if current_close == prev_close and len(ndx_hist) >= 3:
                prev_close = float(ndx_hist["Close"].iloc[-3])

            ndx_price = round(current_close, 2)
            ndx_change = round(current_close - prev_close, 2)
            if prev_close > 0:
                ndx_pct = round(((current_close - prev_close) / prev_close) * 100, 2)

            sma_120 = round(float(ndx_hist["Close"].rolling(window=120).mean().iloc[-1]), 2)
            sma_200 = round(float(ndx_hist["Close"].rolling(window=200).mean().iloc[-1]), 2)
        else:
            print(f"NDX Fetch Error: not enough history ({len(ndx_hist)} rows)")
    except Exception as e:
        print(f"NDX Fetch Error: {e}")

    # 3. index.html과 키를 통일한 JSON 구조
    now_kst = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)
    ).strftime("%Y-%m-%d %H:%M:%S KST")

    data = {
        "updated_at": now_kst,
        "fx_rate": fx_rate,
        "fx_change": fx_change,
        "fx_pct": fx_pct,
        "ndx": {
            "price": ndx_price,
            "change": ndx_change,
            "pct": ndx_pct,
            "sma_120": sma_120,
            "sma_200": sma_200,
        },
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("data.json updated successfully!")


if __name__ == "__main__":
    get_market_data()
