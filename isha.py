import os
from enum import Enum
from pprint import pprint

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_URL")
CSV_PATH = "./data/isha.csv"


class Language(str, Enum):
    en = "en"
    kn = "kn"
    ta = "ta"
    te = "te"
    hi = "hi"


class Philosophy(str, Enum):
    advaita = "adv"
    dvaita = "dva"
    vishishtadvaita = "vis"


def get_access_token(login_url: str, username: str, password: str):
    response = requests.post(
        login_url,
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if response.status_code == 200:
        print("Access token received successfully.")
        return response.json().get("access_token")
    else:
        print(f"Failed to get access token. Status code: {response.status_code}")
        print(response.text)
        return None


def base_query(url: str, data: dict, token: str):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print("Request successful!")
        return response.json()
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(response.text)
        return None


def add_entry(url_suffix: str, data: dict, token: str):
    url = f"{BASE_URL}{url_suffix}"
    response_data = base_query(url, data, token)
    if response_data:
        pprint(response_data)


def process_sutra_data(entry: dict, token: str):
    sutra_no = int(entry.get("sutra_no", ""))
    add_entry(
        "/isha/sutras", {"number": sutra_no, "text": entry.get("sutra", "")}, token
    )

    # Add transliterations in all languages
    for lang in Language:
        transliteration_text = entry.get(f"transliteration_{lang.value}", "")
        add_entry(
            f"/isha/sutras/{sutra_no}/transliteration",
            {"language": lang, "text": transliteration_text},
            token,
        )

    # Add meanings in all languages
    for lang in Language:
        meaning_text = entry.get(f"meaning_{lang.value}", "")
        add_entry(
            f"/isha/sutras/{sutra_no}/meaning",
            {"language": lang, "text": meaning_text},
            token,
        )

    # Add interpretations for all language and philosophy combinations
    for lang in Language:
        for philosophy in Philosophy:
            interpretation_text = entry.get(
                f"tellmemore_{lang.value}_{philosophy.value}", ""
            )
            add_entry(
                f"/isha/sutras/{sutra_no}/interpretation",
                {
                    "language": lang,
                    "text": interpretation_text,
                    "philosophy": philosophy,
                },
                token,
            )


def main():
    username = os.getenv("USERNAME", "")
    password = os.getenv("PASSWORD", "")
    token = get_access_token(f"{BASE_URL}/auth/login", username, password)
    if token is None:
        print("Exiting due to failure in obtaining access token.")
        return

    # Load CSV data, replacing NaN values with empty strings
    df = pd.read_csv(CSV_PATH).fillna("")
    for entry in df.to_dict(orient="records"):
        process_sutra_data(entry, token)


if __name__ == "__main__":
    main()
