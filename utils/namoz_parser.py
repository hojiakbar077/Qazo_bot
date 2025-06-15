import requests
import json
import logging


def get_prayer_times(city="Tashkent"):
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Uzbekistan"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if data.get("code") != 200:
            logging.error(f"API error: city={city}, code={data.get('code')}, message={data.get('status')}")
            return None

        timings = data["data"]["timings"]
        logging.info(f"Prayer times fetched: city={city}")
        return timings
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: city={city}, {e}")
        return None
    except requests.RequestException as e:
        logging.error(f"Request error: city={city}, {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in get_prayer_times: city={city}, {e}")
        return None