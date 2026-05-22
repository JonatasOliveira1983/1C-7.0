import os
import firebase_admin
from firebase_admin import credentials, db

# Mock settings or import from config
FIREBASE_DATABASE_URL = "https://projeto-teste-firestore-3b00e-default-rtdb.europe-west1.firebasedatabase.app"

def nuke_visual_ghosts():
    print("[GHOST-BUSTER] Iniciando limpeza atomica do Firebase RTDB...")
    
    cred_path = os.path.join(os.path.dirname(__file__), "..", "serviceAccountKey.json")
    if not os.path.exists(cred_path):
        print("x Erro: serviceAccountKey.json nao encontrado.")
        return

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})

    ref = db.reference("/")
    
    nodes_to_clean = ["live_slots", "live_pnl", "banca_status", "system_state", "radar_pulse"]
    
    for node in nodes_to_clean:
        print(f"Limpar no: {node}...")
        ref.child(node).delete()
        
    print("\n[GHOST-BUSTER] Firebase RTDB limpo com sucesso. O Soberano ira repopular os dados no proximo boot.")

if __name__ == "__main__":
    nuke_visual_ghosts()
