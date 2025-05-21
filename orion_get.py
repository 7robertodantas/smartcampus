import json
import requests

# === Configuration ===
ORION_URL = "http://localhost:1026/v2/entities"

headers = {
    "Accept": "application/json"
}

def search_entities(entity_type=None, query=None):
    print(f"[INFO] Searching for entities...", end=' ')
    if entity_type:
        print(f"type='{entity_type}'", end=' ')
    if query:
        print(f"query='{query}'", end=' ')
    print()

    try:
        params = {}
        if entity_type:
            params['type'] = entity_type
        if query:
            params['q'] = query

        response = requests.get(ORION_URL, headers=headers, params=params)

        if response.status_code == 200:
            entities = response.json()
            print(json.dumps(entities, indent=2, ensure_ascii=False))
        else:
            print(f"[ERROR] Failed to retrieve entities: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[EXCEPTION] Error while fetching entities: {e}")

def main():
    search_entities(entity_type="AcademicCourse")

    search_entities(entity_type="AcademicCourse", query="credits>3")

    search_entities(entity_type="AcademicCourse", query='modality==Presencial')

    search_entities(entity_type="AcademicCourse", query='refOrganization==Organization:UFRN')

if __name__ == "__main__":
    main()
