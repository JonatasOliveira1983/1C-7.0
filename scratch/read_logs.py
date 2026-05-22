import os

def extract_logs():
    log_file = "c:\\Users\\spcom\\Desktop\\10D REAL 5.0\\1CRYPTEN_SPACE_V4.0\\backend\\debug_out.txt"
    out_file = "c:\\Users\\spcom\\Desktop\\10D REAL 5.0\\scratch\\extracted_slot_logs.txt"
    if not os.path.exists(log_file):
        print(f"Log não encontrado em {log_file}")
        # Tentar em outro log de backend
        log_file = "c:\\Users\\spcom\\Desktop\\10D REAL 5.0\\1CRYPTEN_SPACE_V4.0\\backend\\backend_v110_173.log"
        if not os.path.exists(log_file):
            print(f"Log alternativo não encontrado em {log_file}")
            return
            
    print(f"Lendo de {log_file}...")
    lines_found = []
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "SlotOperatorAgent" in line or "[SLOT-" in line:
                lines_found.append(line)
                
    print(f"Encontradas {len(lines_found)} linhas. Escrevendo em {out_file}...")
    with open(out_file, "w", encoding="utf-8") as f_out:
        f_out.writelines(lines_found)

if __name__ == "__main__":
    extract_logs()
