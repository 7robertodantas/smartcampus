import os
import json
import requests
import fiware
from datetime import datetime, timedelta, timezone

# === Configuration ===
ORION_URL = os.environ.get("ORION_URL")
ENTITIES_DIR = os.environ.get("ENTITIES_DIR")

headers = {"Content-Type": "application/json", "Accept": "application/json"}

get_delete_headers = {"Accept": "application/json"}


def create_entity_from_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            entity = json.load(file)
            fiware.create_entity(entity)
    except Exception as e:
        print(f"[EXCEPTION] Error processing {filepath}: {e}")


def update_course_schedule():
    course_id = "CourseInstance:PPGTI3001-2025"  # Change to your course ID

    print(f"[INFO] Updating schedule for course {course_id}...")

    update_url = f"{ORION_URL}/v2/entities/{course_id}/attrs/classSchedule"

    now = datetime.now(timezone.utc)
    new_day = now.strftime("%A")
    new_start = (now + timedelta(hours=1, minutes=30)).strftime("%H:%M")
    new_end = (now + timedelta(hours=2, minutes=30)).strftime("%H:%M")

    print(f"[INFO] New day: {new_day}")
    print(f"[INFO] Start time: {new_start}")
    print(f"[INFO] End time: {new_end}")

    new_schedule = {
        "value": [{"day": new_day, "startTime": new_start, "endTime": new_end}],
        "type": "StructuredValue",
    }

    try:
        response = requests.put(update_url, headers=headers, json=new_schedule)
        if response.status_code in [204, 201]:
            print(f"[OK] Schedule for course {course_id} updated successfully.")
        else:
            print(f"[ERROR] Failed to update schedule: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[EXCEPTION] Error updating schedule: {e}")


def main():
    if not os.path.isdir(ENTITIES_DIR):
        print(f"[ERROR] Folder '{ENTITIES_DIR}' not found.")
        return

    fiware.delete_all_entities()

    for filename in os.listdir(ENTITIES_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(ENTITIES_DIR, filename)
            create_entity_from_file(filepath)

    update_course_schedule()
    print("[INFO] All entities created and updated successfully.")


if __name__ == "__main__":
    fiware.wait_for_orion()
    main()
