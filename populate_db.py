import os
from enum import Enum
from pprint import pprint

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_URL")
CSV_PATH = os.getenv("CSV_UPANISHADS")
UPANISHADS = os.getenv("UPANISHADS")

class Language(str, Enum):
    sa = "sa"
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

def get_projects():
    url = f"{BASE_URL}/projects/"
    response = requests.get(url)
    return response.json()

def add_audio_file(upanishad: str, chapter: int, sutra_no: int, mode: str, token: str):
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
    if upanishad == 'isha': file_path = f"audio/{upanishad}/{sutra_no}_{file_suffix}.mp3"
    else: file_path = f"audio/{upanishad}/{chapter}/{sutra_no}_{file_suffix}.mp3"

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Audio file not found: {file_path}")
        return

    # Prepare the URL - note that mode is now a query parameter
    url = f"{BASE_URL}/{upanishad}/sutras/{upanishad}/{chapter}/{sutra_no}/audio"

    # Prepare the files for multipart/form-data
    files = {"file": ("audio.mp3", open(file_path, "rb"), "audio/mpeg")}

    # Add mode as a query parameter
    params = {"mode": mode}

    # Make the request
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, files=files, params=params, headers=headers)

    if response.status_code == 201:
        print(f"Successfully uploaded audio for upanishad {upanishad} chapter {chapter} sutra {sutra_no} in {mode} mode")
        return response.json()
    else:
        print(f"Failed to upload audio for upanishad {upanishad} chapter {chapter} sutra {sutra_no} in {mode} mode")
        print(f"Status code: {response.status_code}")
        print(response.text)
        return None

def process_sutra_data(entry: dict, token: str):
    sutra_no = int(entry.get("sutra_no", "0"))
    chapter = int(entry.get("chapter","0"))
    upanishad = str(entry.get("name", "isha"))
    add_entry(
        f"/{upanishad}/sutras", {"project":{"name": upanishad}, "sutra":{"chapter": chapter, "number": sutra_no, "text": entry.get("sutra", "")}}, token
    )

    # Add transliterations in all languages
    for lang in Language:
        transliteration_text = entry.get(f"transliteration_{lang.value}", "")
        add_entry(
            f"/{upanishad}/sutras/{upanishad}/{chapter}/{sutra_no}/transliteration",
            {"language": lang, "text": transliteration_text},
            token,
        )

    # Add meanings in all languages
    for lang in Language:
        meaning_text = entry.get(f"meaning_{lang.value}", "")
        add_entry(
            f"/{upanishad}/sutras/{upanishad}/{chapter}/{sutra_no}/meaning",
            {"language": lang, "text": meaning_text},
            token,
        )
        # for lang in Language:  # 🔥 Fix: Loop through all languages, not just Sanskrit
        for philosophy in Philosophy:
            bhashyam_text = entry.get(f"bhashyam_sa_{philosophy.value}", "")
            if bhashyam_text:
                add_entry(
                    f"/{upanishad}/sutras/{upanishad}/{chapter}/{sutra_no}/bhashyam",
                    {"language": "sa", "text": bhashyam_text, "philosophy": philosophy.value},
                    token,
                )
            else:
                print(f"Bhashyam not found for {upanishad} chapter {chapter} Sutra {sutra_no} (sa - {philosophy.value})")

    # Add interpretations for all language and philosophy combinations
    for lang in Language:
        for philosophy in Philosophy:
            interpretation_text = entry.get(
                f"tellmemore_{lang.value}_{philosophy.value}", ""
            )
            add_entry(
                f"/{upanishad}/sutras/{upanishad}/{chapter}/{sutra_no}/interpretation",
                {
                    "language": lang,
                    "text": interpretation_text,
                    "philosophy": philosophy,
                },
                token,
            )

    # if upanishad=='isha':
    # Add audio files
    # Chant mode
    add_audio_file(upanishad, chapter, sutra_no, "chant", token)
    # Teaching mode
    add_audio_file(upanishad, chapter, sutra_no, "teach_me", token)

def main():
    token = get_access_token()
    if token is None:
        print("Exiting due to failure in obtaining access token.")
        return

    projects = get_projects()
    # print(f'list {projects}')

    for item in UPANISHADS.split(','):
        name, description = item.split('/')
        # add project with description if it does not exist
        projectnames = []
        for item in projects: projectnames.append(item['name'])
        # print(f'names {projectnames}')
        if name not in projectnames: add_entry(f"/projects?name={name}&description={description}", {"name":f"{name}", "description":f"{description}"}, token)
    # Load CSV data, replacing NaN values with empty strings
    df = pd.read_csv(CSV_PATH).fillna("")
    for entry in df.to_dict(orient="records"): process_sutra_data(entry, token)
    
if __name__ == "__main__":
    main()
