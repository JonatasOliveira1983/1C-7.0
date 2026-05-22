import json
import os

def build_obsidian_vault(json_path, output_dir):
    if not os.path.exists(json_path):
        print(f"Erro: {json_path} não encontrado.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data.get('nodes', [])
    edges = data.get('edges', [])

    # Mapear conexões
    connections = {}
    for edge in edges:
        src = edge.get('source')
        target = edge.get('target')
        if src not in connections: connections[src] = []
        connections[src].append(target)

    # Criar notas para cada nó
    os.makedirs(output_dir, exist_ok=True)
    for node in nodes:
        node_id = node.get('id')
        node_type = node.get('type', 'generic')
        
        # Limpar nome para arquivo
        file_name = node_id.replace('/', '_').replace('\\', '_')
        if not file_name.endswith('.md'): file_name += '.md'
        
        with open(os.path.join(output_dir, file_name), 'w', encoding='utf-8') as f:
            f.write(f"# Node: {node_id}\n\n")
            f.write(f"**Tipo:** {node_type}\n\n")
            
            # Escrever conexões de saída
            targets = connections.get(node_id, [])
            if targets:
                f.write("## Conexões de Saída\n")
                for t in targets:
                    t_link = t.replace('/', '_').replace('\\', '_')
                    if not t_link.endswith('.md'): t_link += '.md'
                    f.write(f"- [[{t_link}|{t}]]\n")
            
            # Adicionar metadados se houver
            meta = node.get('metadata', {})
            if meta:
                f.write("\n## Metadados\n")
                f.write(f"```json\n{json.dumps(meta, indent=2)}\n```\n")

    print(f"Sucesso! {len(nodes)} notas criadas em {output_dir}")

if __name__ == "__main__":
    build_obsidian_vault('graphify-out/graph.json', '.obsidian_intel/Codice')
