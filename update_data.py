import os
import json
import datetime
import requests
import yfinance as yf

ASSETS = {
    "qld": ("QLD", "QLD"),
    "qqq": ("QQQ", "QQQ"),
    "voo": ("VOO", "VOO"),
    "brkb": ("BRK-B", "BRK.B"),
    "visa": ("V", "Visa"),
}

KRX_GOLD_URL = "https://data-dbg.krx.co.kr/svc/apis/gen/gold_bydd_trd"


def now_kst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))


def clean_number(value):
    if value is None:
        return 0.0
    s = str(value).replace(",", "").strip()
    if not s or s == "-":
        return 0.0
    return float(s)


def latest_price(ticker):
    try:
        h = yf.Ticker(ticker).history(period="1d", interval="5m", prepost=False)
        close = h["Close"].dropna() if not h.empty else []
        if len(close):
            return round(float(close.iloc[-1]), 4)
    except Exception as e:
        print(f"{ticker} intraday error: {e}")

    try:
        h = yf.Ticker(ticker).history(period="5d", interval="1d")
        close = h["Close"].dropna() if not h.empty else []
        if len(close):
            return round(float(close.iloc[-1]), 4)
    except Exception as e:
        print(f"{ticker} daily fallback error: {e}")

    return 0


def fetch_krx_gold():
    """
    KRX 금시장 '금 99.99_1kg'의 가장 최근 거래일 종가(원/g)를 반환.
    주말/휴장일/당일 데이터 미게시 상황을 고려해 최근 10일을 역순 조회한다.
    """
    auth_key = os.getenv("KRX_API_KEY", "").strip()
    if not auth_key:
        print("KRX_API_KEY is missing.")
        return None

    headers = {"AUTH_KEY": auth_key}
    today = now_kst().date()

    for days_back in range(0, 10):
        d = today - datetime.timedelta(days=days_back)
        if d.weekday() >= 5:
            continue

        bas_dd = d.strftime("%Y%m%d")
        try:
            r = requests.get(
                KRX_GOLD_URL,
                headers=headers,
                params={"basDd": bas_dd},
                timeout=20,
            )
            r.raise_for_status()
            payload = r.json()
            rows = payload.get("OutBlock_1", [])

            if not isinstance(rows, list) or not rows:
                print(f"KRX gold: no rows for {bas_dd}")
                continue

            # 정확히 '금 99.99_1kg' 우선. 표기 차이가 있으면 1kg + 99.99 조합으로 보조 탐색.
            target = next(
                (x for x in rows if str(x.get("ISU_NM", "")).strip() == "금 99.99_1kg"),
                None,
            )
            if target is None:
                target = next(
                    (
                        x for x in rows
                        if "1kg" in str(x.get("ISU_NM", ""))
                        and "99.99" in str(x.get("ISU_NM", ""))
                    ),
                    None,
                )

            if target is None:
                print(f"KRX gold: target product not found for {bas_dd}. "
                      f"Products={[x.get('ISU_NM') for x in rows]}")
                continue

            price = clean_number(target.get("TDD_CLSPRC"))
            if price <= 0:
                print(f"KRX gold: invalid close for {bas_dd}: {target}")
                continue

            return {
                "ticker": target.get("ISU_CD"),
                "name": target.get("ISU_NM", "금 99.99_1kg"),
                "price": round(price, 2),
                "currency": "KRW",
                "unit": "g",
                "market_date": target.get("BAS_DD", bas_dd),
                "change": clean_number(target.get("CMPPREVDD_PRC")),
                "pct": clean_number(target.get("FLUC_RT")),
                "status": "ok",
            }

        except requests.HTTPError as e:
            print(f"KRX gold HTTP error for {bas_dd}: {e} / body={r.text[:300]}")
            # 인증/승인 오류라면 날짜를 바꿔도 해결되지 않으므로 중단
            if r.status_code in (401, 403):
                break
        except Exception as e:
            print(f"KRX gold error for {bas_dd}: {e}")

    return None


def get_market_data():
    print("Market data fetching started...")

    fx_rate = fx_change = fx_pct = 0
    try:
        fx_hist = yf.Ticker("KRW=X").history(period="10d")
        if len(fx_hist) >= 2:
            current_fx = float(fx_hist["Close"].iloc[-1])
            prev_fx = float(fx_hist["Close"].iloc[-2])
            fx_rate = round(current_fx, 2)
            fx_change = round(current_fx - prev_fx, 2)
            if prev_fx > 0:
                fx_pct = round((current_fx - prev_fx) / prev_fx * 100, 2)
    except Exception as e:
        print(f"FX Fetch Error: {e}")

    # 전략 기준: QQQ 종가 + 120/200일 이동평균
    qqq_price = qqq_change = qqq_pct = sma_120 = sma_200 = 0
    try:
        qqq_hist = yf.Ticker("QQQ").history(period="18mo", interval="1d")
        closes = qqq_hist["Close"].dropna()
        if len(closes) >= 200:
            current_close = float(closes.iloc[-1])
            prev_close = float(closes.iloc[-2])
            qqq_price = round(current_close, 2)
            qqq_change = round(current_close - prev_close, 2)
            if prev_close > 0:
                qqq_pct = round((current_close - prev_close) / prev_close * 100, 2)
            sma_120 = round(float(closes.rolling(120).mean().iloc[-1]), 2)
            sma_200 = round(float(closes.rolling(200).mean().iloc[-1]), 2)
        else:
            print(f"QQQ Fetch Error: not enough history ({len(closes)} rows)")
    except Exception as e:
        print(f"QQQ Fetch Error: {e}")

    # VXN은 매매 필수조건이 아니라 QLD 변동성 위험을 보는 보조지표
    vxn_price = vxn_change = vxn_pct = 0
    try:
        vxn_hist = yf.Ticker("^VXN").history(period="10d", interval="1d")
        vxn_closes = vxn_hist["Close"].dropna()
        if len(vxn_closes) >= 2:
            current_vxn = float(vxn_closes.iloc[-1])
            prev_vxn = float(vxn_closes.iloc[-2])
            vxn_price = round(current_vxn, 2)
            vxn_change = round(current_vxn - prev_vxn, 2)
            if prev_vxn > 0:
                vxn_pct = round((current_vxn - prev_vxn) / prev_vxn * 100, 2)
    except Exception as e:
        print(f"VXN Fetch Error: {e}")

    stamp = now_kst().strftime("%Y-%m-%d %H:%M:%S KST")

    prices = {}
    for key, (ticker, name) in ASSETS.items():
        prices[key] = {
            "ticker": ticker,
            "name": name,
            "price": latest_price(ticker),
            "currency": "USD",
            "unit": "주",
            "updated_at": stamp,
        }

    gold = fetch_krx_gold()
    if gold:
        gold["updated_at"] = stamp
        prices["gold"] = gold
        print(f"KRX Gold OK: {gold['name']} {gold['price']:,.0f} KRW/g "
              f"(market date {gold['market_date']})")
    else:
        prices["gold"] = {
            "ticker": None,
            "name": "KRX 금",
            "price": 0,
            "currency": "KRW",
            "unit": "g",
            "updated_at": stamp,
            "status": "unavailable",
        }
        print("KRX Gold unavailable.")

    data = {
        "updated_at": stamp,
        "fx_rate": fx_rate,
        "fx_change": fx_change,
        "fx_pct": fx_pct,
        "qqq": {
            "price": qqq_price,
            "change": qqq_change,
            "pct": qqq_pct,
            "sma_120": sma_120,
            "sma_200": sma_200,
        },
        "vxn": {
            "price": vxn_price,
            "change": vxn_change,
            "pct": vxn_pct,
        },
        "prices": prices,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("data.json updated successfully!")


if __name__ == "__main__":
    get_market_data()
