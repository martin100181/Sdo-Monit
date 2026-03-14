import requests

API_URL = "https://api.saldo.com.ar/json/rates/palpal/usdt"


def read_envias_usdt():

    usd_amount = 100

    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()

    data = r.json()

    ask = float(data["usdt"]["ask"])

    usdt = usd_amount / ask

    return round(usdt, 2)

def main():
    try:
        envias = read_envias_usdt()
        print(f"ENVIAS_USDT={envias}")

    except Exception as e:
        print("ERROR:", repr(e))
        raise


if __name__ == "__main__":
    main()
