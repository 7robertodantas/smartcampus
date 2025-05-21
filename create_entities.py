import os
import json
import requests

# === Configuration ===
ORION_URL = "http://localhost:1026/v2/entities"
ENTITIES_DIR = "./entities"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def create_entity_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            entity = json.load(file)

            print(f"[INFO] Sending entity from: {filepath}")
            response = requests.post(ORION_URL, headers=headers, json=entity)

            if response.status_code == 201:
                print(f"[OK] Created entity from {filepath}")
            elif response.status_code == 422:
                print(f"[WARN] Entity already exists or invalid: {filepath}")
                print(f"       {response.text}")
            else:
                print(f"[ERROR] Failed to create entity from {filepath}: {response.status_code}")
                print(f"        {response.text}")
    except Exception as e:
        print(f"[EXCEPTION] Error processing {filepath}: {e}")

def main():
    if not os.path.isdir(ENTITIES_DIR):
        print(f"[ERROR] Folder '{ENTITIES_DIR}' not found.")
        return

    for filename in os.listdir(ENTITIES_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(ENTITIES_DIR, filename)
            create_entity_from_file(filepath)

if __name__ == "__main__":
    main()
