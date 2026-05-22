import os
import glob

def find_files_optimized(target_name):
    desktop = "c:\\Users\\spcom\\Desktop"
    if not os.path.exists(desktop):
        print(f"Erro: {desktop} nao existe")
        return []

    # Achar pastas que contem '10D' no Desktop
    subdirs = []
    try:
        for item in os.listdir(desktop):
            path = os.path.join(desktop, item)
            if os.path.isdir(path) and "10d" in item.lower():
                subdirs.append(path)
    except Exception as e:
        print(f"Erro ao listar desktop: {e}")
        return []

    print(f"Pastas 10D encontradas no Desktop: {subdirs}")
    
    matches = []
    for sdir in subdirs:
        print(f"Buscando em {sdir}...")
        for root, dirs, files in os.walk(sdir):
            # Podar pastas lentas
            if any(ignored in root.replace('\\', '/').split('/') for ignored in ["node_modules", ".git", ".next", "venv", "__pycache__", ".aios", ".gsd", "brain"]):
                continue
            for file in files:
                if target_name.lower() in file.lower():
                    full_path = os.path.join(root, file)
                    matches.append(full_path)
    return matches

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "slot_operator.py"
    results = find_files_optimized(target)
    print(f"\nResultados para '{target}':")
    for r in results:
        print(f" - {r}")
