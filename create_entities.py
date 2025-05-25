import os
import json
import requests
import sys
import time

# === Configuration ===
ORION_URL = "http://orion:1026/v2/entities"
ENTITIES_DIR = "./entities"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


get_delete_headers = {
    "Accept": "application/json"
}

def delete_all_entities():
    print("[INFO] Deleting all existing entities...")
    try:
        list_url = f"{ORION_URL}?options=keyValues"
        response = requests.get(list_url, headers=get_delete_headers)

        if response.status_code == 200:
            entities = response.json()
            for entity in entities:
                entity_id = entity.get("id")
                if entity_id:
                    delete_url = f"{ORION_URL}/{entity_id}"
                    del_resp = requests.delete(delete_url, headers=get_delete_headers)
                    if del_resp.status_code in [204, 404]:
                        print(f"[OK] Deleted entity: {entity_id}")
                    else:
                        print(f"[ERROR] Failed to delete {entity_id}: {del_resp.status_code}")
        else:
            print(f"[ERROR] Failed to fetch entities: {response.status_code}")
            print(f"        {response.text}")
    except Exception as e:
        print(f"[EXCEPTION] Error deleting entities: {e}")

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

def esperar_orion_disponivel(max_tentativas=100, intervalo=5):
    print("[INFO] Verificando disponibilidade do Orion...")
    
    url_teste = "http://orion:1026/version"

    for tentativa in range(max_tentativas):
        try:
            resposta = requests.get(url_teste)
            if resposta.status_code == 200:
                print(f"[OK] Orion respondeu na tentativa {tentativa + 1}")
                return
        except requests.exceptions.RequestException as e:
            print(f"[AGUARDANDO] Orion ainda não está pronto: {e}")
        time.sleep(intervalo)
    print("[FALHA] Orion não respondeu a tempo.")
    sys.exit(1)

from datetime import datetime, timedelta, timezone

def atualizar_horario_turma():
    turma_id = "CourseInstance:PPGTI3001-2025"  # Altere para o ID da sua turma

    print(f"[INFO] Atualizando horário da turma {turma_id}...")

    update_url = f"{ORION_URL}/{turma_id}/attrs/classSchedule"
    
    agora = datetime.now(timezone.utc)
    novo_dia = agora.strftime("%A")
    novo_inicio = (agora + timedelta(hours=1, minutes=30)).strftime("%H:%M")
    novo_fim = (agora + timedelta(hours=2, minutes=30)).strftime("%H:%M")

    print(f"[INFO] Novo dia: {novo_dia}")
    print(f"[INFO] Horário início: {novo_inicio}")
    print(f"[INFO] Horário fim: {novo_fim}")

    novo_horario = {
        "value": [
            {
                "day": novo_dia,
                "startTime": novo_inicio,
                "endTime": novo_fim
            }
        ],
        "type": "StructuredValue"
    }

    try:
        response = requests.put(update_url, headers=headers, json=novo_horario)
        if response.status_code in [204, 201]:
            print(f"[OK] Horário da turma {turma_id} atualizado com sucesso.")
        else:
            print(f"[ERRO] Falha ao atualizar horário: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[EXCEPTION] Erro ao atualizar horário: {e}")

def main():
    esperar_orion_disponivel()
    if not os.path.isdir(ENTITIES_DIR):
        print(f"[ERROR] Folder '{ENTITIES_DIR}' not found.")
        return
    
    delete_all_entities()

    for filename in os.listdir(ENTITIES_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(ENTITIES_DIR, filename)
            create_entity_from_file(filepath)
    
    atualizar_horario_turma()
    print("[INFO] All entities created and updated successfully.")

if __name__ == "__main__":
    main()
