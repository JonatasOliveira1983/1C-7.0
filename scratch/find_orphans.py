import json
import os

GRAPH_PATH = r"c:\Users\spcom\Desktop\10D REAL 5.0\graphify-out\graph.json"

def find_orphans():
    if not os.path.exists(GRAPH_PATH):
        print("❌ Erro: graph.json não encontrado.")
        return

    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    links = data.get("links", [])

    # Cria um set de IDs que possuem conexões
    connected_ids = set()
    for link in links:
        connected_ids.add(link["source"])
        connected_ids.add(link["target"])

    orphans = []
    for node in nodes:
        node_id = node["id"]
        # Filtra apenas por arquivos (possuem extensão)
        if "." in node_id and node_id not in connected_ids:
            # Ignora pastas de ambiente virtual ou git
            if not any(x in node_id for x in [".venv", ".git", "node_modules"]):
                orphans.append(node_id)

    print(f"Auditoria Concluida: {len(orphans)} arquivos orfaos encontrados.\n")
    
    # Agrupa por diretório para facilitar a decisão
    orphans_by_dir = {}
    for o in orphans:
        dir_name = os.path.dirname(o) or "Raiz"
        if dir_name not in orphans_by_dir:
            orphans_by_dir[dir_name] = []
        orphans_by_dir[dir_name].append(os.path.basename(o))

    for directory, files in sorted(orphans_by_dir.items()):
        print(f"Dir: {directory}/")
        for f in sorted(files):
            print(f"   - {f}")
        print("")

if __name__ == "__main__":
    find_orphans()
