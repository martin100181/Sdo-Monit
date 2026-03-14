import requests

API_URL = "https://api.saldo.com.ar/json/rates/paypal/paypal_usd,usdt"


def read_envias_usdt():
    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()

    data = r.json()

    paypal_bid = float(data["paypal_usd"]["bid"])
    usdt_bid = float(data["usdt"]["bid"])

    result = 100 * paypal_bid / usdt_bid
    return result


def main():
    try:
        envias = read_envias_usdt()
        print(f"ENVIAS_USDT={envias}")

    except Exception as e:
        print("ERROR:", repr(e))
        raise


if __name__ == "__main__":
    main()
