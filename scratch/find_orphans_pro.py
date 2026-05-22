import json
import os

GRAPH_PATH = r"c:\Users\spcom\Desktop\10D REAL 5.0\graphify-out\graph.json"

def find_real_orphans():
    if not os.path.exists(GRAPH_PATH):
        print("Erro: graph.json nao encontrado.")
        return

    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    links = data.get("links", [])

    # Mapeia quais IDs estao conectados
    connected_ids = set()
    for link in links:
        connected_ids.add(link["source"])
        connected_ids.add(link["target"])

    # Agrupa nos por arquivo de origem
    file_nodes = {}
    for node in nodes:
        src = node.get("source_file", "unknown")
        if src not in file_nodes:
            file_nodes[src] = []
        file_nodes[src].append(node)

    orphans = []
    for filename, internal_nodes in file_nodes.items():
        if filename == "unknown" or not filename: continue
        
        # Um arquivo so e orfao se NENHUM de seus nos (arquivo, funcoes, classes) tiver conexoes externas
        is_orphaned = True
        for n in internal_nodes:
            if n["id"] in connected_ids:
                is_orphaned = False
                break
        
        if is_orphaned:
            # Ignora o que ja sabemos que e temporario
            if not any(x in filename for x in [".venv", ".git", "node_modules", "graphify-out"]):
                orphans.append(filename)

    print(f"Auditoria Concluida: {len(orphans)} arquivos 100% isolados encontrados.\n")
    
    # Lista por categorias
    categories = {
        "RAIZ (Antigos)": [],
        "BACKEND (Scripts de Reset/Diagnostico)": [],
        "SCRATCH (Testes Temporarios)": [],
        "OUTROS": []
    }

    for o in sorted(orphans):
        if "/" not in o or "\\" not in o:
            if "1CRYPTEN" in o: categories["BACKEND (Scripts de Reset/Diagnostico)"].append(o)
            else: categories["RAIZ (Antigos)"].append(o)
        elif "scratch" in o.lower(): categories["SCRATCH (Testes Temporarios)"].append(o)
        elif "backend" in o.lower(): categories["BACKEND (Scripts de Reset/Diagnostico)"].append(o)
        else: categories["OUTROS"].append(o)

    for cat, files in categories.items():
        if files:
            print(f"--- {cat} ---")
            for f in files:
                print(f"  [!] {f}")
            print("")

if __name__ == "__main__":
    find_real_orphans()
