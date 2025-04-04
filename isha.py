import os
from enum import Enum
from operator import truediv
from pprint import pprint

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_URL")
CSV_PATH = os.getenv("CSV_PATH")
UPANISHAD = os.getenv("UPANISHAD_NAME")
UPANISHAD_DESCRIPTION = os.getenv("UPANISHAD_DESCRIPTION")
CHAPTER = os.getenv("CHAPTER")
print(f"read {CSV_PATH} for {UPANISHAD} {UPANISHAD_DESCRIPTION} upanishad chapter {CHAPTER}")

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


def get_access_token():
    username = os.getenv("EMAIL", "")
    password = os.getenv("PASSWORD", "")
    # print(username, password)
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if response.status_code == 200:
        print(f"login {username} - Access token received successfully.")
        return response.json().get("access_token")
    else:
        data = {"first_name": "placeholder_first_name",
                    "last_name": "placeholder_last_name",
                    "email": username,
                    "phone_no": "placeholder_phone_no",
                    "password": password}
        headers = {"accept":"application/json", "Content-Type": "application/json"}
        url = f"{BASE_URL}/auth/create-admin"
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            print(f"Created admin user {username}")
            response = requests.post(
                f"{BASE_URL}/auth/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if response.status_code == 200:
                print(f"login {username} - Access token received successfully.")
                return response.json().get("access_token")
            else:
                print(f"Failed to get access token. Status code: {response.status_code}")
                print(response.text)
                return None
        else:
            print(f"Failed to create admin user {username}")
            return None


def base_query(url: str, data: dict, token: str):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code in [200, 201]:
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
        return True
    else: return False


def add_audio_file(sutra_no: int, mode: str, token: str):
    """
    Add audio file for a given sutra number and mode.

    Args:
        sutra_no: int - The sutra number (-1 to 18)
        mode: str - Either 'chant' or 'teach_me'
        token: str - Authentication token
    """
    # Determine the file suffix based on mode
    file_suffix = "A" if mode == "chant" else "B"

    # Construct the file path
    file_path = f"audio/{UPANISHAD}/{sutra_no}_{file_suffix}.mp3"

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Audio file not found: {file_path}")
        return

    # Prepare the URL - note that mode is now a query parameter
    url = f"{BASE_URL}/{UPANISHAD}/sutras/{UPANISHAD}/0/{sutra_no}/audio"

    # Prepare the files for multipart/form-data
    files = {"file": ("audio.mp3", open(file_path, "rb"), "audio/mpeg")}

    # Add mode as a query parameter
    params = {"mode": mode}

    # Make the request
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, files=files, params=params, headers=headers)

    if response.status_code == 201:
        print(f"Successfully uploaded audio for sutra {sutra_no} in {mode} mode")
        return response.json()
    else:
        print(f"Failed to upload audio for sutra {sutra_no} in {mode} mode")
        print(f"Status code: {response.status_code}")
        print(response.text)
        return None


def process_sutra_data(entry: dict, token: str):
    sutra_no = int(entry.get("sutra_no", ""))
    add_entry(
        f"/{UPANISHAD}/sutras", {"project":{"name":f"{UPANISHAD}"}, "sutra":{"chapter": f"{CHAPTER}", "number": sutra_no, "text": entry.get("sutra", "")}}, token
    )

    # Add transliterations in all languages
    for lang in Language:
        transliteration_text = entry.get(f"transliteration_{lang.value}", "")
        add_entry(
            f"/{UPANISHAD}/sutras/{UPANISHAD}/{CHAPTER}/{sutra_no}/transliteration",
            {"language": lang, "text": transliteration_text},
            token,
        )

    # Add meanings in all languages
    for lang in Language:
        meaning_text = entry.get(f"meaning_{lang.value}", "")
        add_entry(
            f"/{UPANISHAD}/sutras/{UPANISHAD}/{CHAPTER}/{sutra_no}/meaning",
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
                f"/{UPANISHAD}/sutras/{UPANISHAD}/{CHAPTER}/{sutra_no}/interpretation",
                {
                    "language": lang,
                    "text": interpretation_text,
                    "philosophy": philosophy,
                },
                token,
            )


    if UPANISHAD=='isha':
        # Add audio files
        # Chant mode
        add_audio_file(sutra_no, "chant", token)
        # Teaching mode
        add_audio_file(sutra_no, "teach_me", token)


def main():
    token = get_access_token()
    if token is None:
        print("Exiting due to failure in obtaining access token.")
        return

    # add project with description if it does not exist
    if add_entry(f"/projects?name={UPANISHAD}&description={UPANISHAD_DESCRIPTION}", {"name":f"{UPANISHAD}", "description":f"{UPANISHAD_DESCRIPTION}"}, token):
        # Load CSV data, replacing NaN values with empty strings
        df = pd.read_csv(CSV_PATH).fillna("")
        for entry in df.to_dict(orient="records"):
            # print(f"processing {entry}")
            process_sutra_data(entry, token)


if __name__ == "__main__":
    main()
