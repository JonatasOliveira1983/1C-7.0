import firebase_admin
from firebase_admin import credentials, firestore, db
import os
import json

def check_firebase():
    cert_path = "1CRYPTEN_SPACE_V4.0/backend/serviceAccountKey.json"
    if not os.path.exists(cert_path):
        print("Error: Credentials not found.")
        return

    try:
        cred = credentials.Certificate(cert_path)
        database_url = "https://projeto-teste-firestore-3b00e-default-rtdb.europe-west1.firebasedatabase.app"
        
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
        
        firestore_db = firestore.client()
        rtdb = db.reference()

        print("--- FIRESTORE (slots_ativos) ---")
        slots_ref = firestore_db.collection("slots_ativos")
        docs = slots_ref.stream()
        for doc in docs:
            d = doc.to_dict()
            print(f"Slot {doc.id}: {d.get('symbol')} ({d.get('status_risco')})")

        print("\n--- REALTIME DATABASE (live_slots) ---")
        live_slots = rtdb.child("live_slots").get()
        if live_slots:
            for sid, sdata in live_slots.items():
                print(f"Slot {sid}: {sdata.get('symbol')} ({sdata.get('status_risco')})")
        else:
            print("No live_slots in RTDB.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_firebase()
