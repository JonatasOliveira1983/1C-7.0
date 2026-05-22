
import firebase_admin
from firebase_admin import credentials, db
import os

def direct_firebase_wipe():
    print("--- INICIANDO WIPE DIRETO FIREBASE ---")
    
    cred_path = "serviceAccountKey.json"
    if not os.path.exists(cred_path):
        print(f"ERROR: {cred_path} nao encontrado.")
        return

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://projeto-teste-firestore-3b00e-default-rtdb.europe-west1.firebasedatabase.app'
        })
        
        print("DONE: Conectado ao Firebase.")
        
        # 1. Zerar live_pnl
        db.reference("live_pnl").set({
            "total_float_roi": 0,
            "total_float_pnl": 0,
            "active_count": 0,
            "slots_roi": {},
            "slots_pnl": {},
            "updated_at": 0
        })
        print("DONE: live_pnl zerado.")

        # 2. Resetar system_pulse
        db.reference("system_pulse").update({
            "global_pnl_usd": 0,
            "global_pnl_percent": 0,
            "equity": 100.0,
            "balance": 100.0,
            "resultado_global": 0
        })
        print("DONE: system_pulse purificado.")

        # 3. Resetar banca_status
        db.reference("banca_status").update({
            "saldo_total": 100.0,
            "lucro_ciclo": 0.0,
            "lucro_total_acumulado": 0.0,
            "risco_real_percent": 0.0
        })
        print("DONE: banca_status sincronizada em $100.")

        print("FINISH: WIPE CONCLUIDO COM SUCESSO.")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")

if __name__ == "__main__":
    direct_firebase_wipe()
