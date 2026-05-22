import json
import os

JSON_PATH = r"c:\Users\spcom\Desktop\10D REAL 5.0\graphify-out\graph.json"
ORPHANS_LIST_PATH = r"c:\Users\spcom\Desktop\10D REAL 5.0\orphans_list.txt"

def cleanup_json():
    if not os.path.exists(JSON_PATH):
        print("Erro: graph.json nao encontrado.")
        return
    
    if not os.path.exists(ORPHANS_LIST_PATH):
        print("Erro: orphans_list.txt nao encontrado.")
        return

    # Carrega a lista de orfaos (arquivos que foram movidos)
    with open(ORPHANS_LIST_PATH, "r", encoding="utf-16") as f: # PowerShell salva em UTF-16 as vezes
        content = f.read()
    
    # Se falhar o utf-16, tenta utf-8
    if not content:
        with open(ORPHANS_LIST_PATH, "r", encoding="utf-8") as f:
            content = f.read()

    # Extrai os nomes dos arquivos
    orphan_files = []
    for line in content.splitlines():
        if "[!] " in line:
            orphan_files.append(line.split("[!] ")[1].strip())

    print(f"Lendo {JSON_PATH}...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_nodes = len(data["nodes"])
    original_links = len(data["links"])

    # Filtra os nos
    new_nodes = []
    removed_ids = set()
    
    for node in data["nodes"]:
        src_file = node.get("source_file", "")
        # Se o arquivo original do no esta na lista de orfaos, removemos
        if any(src_file == orphan or src_file.endswith("/" + orphan) or src_file.endswith("\\" + orphan) for orphan in orphan_files):
            removed_ids.add(node["id"])
        else:
            new_nodes.append(node)

    # Filtra os links
    new_links = []
    for link in data["links"]:
        if link["source"] not in removed_ids and link["target"] not in removed_ids:
            new_links.append(link)

    data["nodes"] = new_nodes
    data["links"] = new_links

    print(f"Limpeza concluida:")
    print(f" - Nos: {original_nodes} -> {len(new_nodes)} (Removidos: {original_nodes - len(new_nodes)})")
    print(f" - Links: {original_links} -> {len(new_links)} (Removidos: {original_links - len(new_links)})")

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Arquivo graph.json atualizado com sucesso!")

if __name__ == "__main__":
    cleanup_json()
