import os
import re

HTML_PATH = r"c:\Users\spcom\Desktop\10D REAL 5.0\graphify-out\graph.html"
VAULT_NAME = ".obsidian_intel"

def patch_intel_map():
    if not os.path.exists(HTML_PATH):
        print(f"❌ Erro: {HTML_PATH} não encontrado.")
        return

    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Script JS para injetar o comportamento de clique do Obsidian
    obsidian_js = """
    // --- OBSIDIAN BRIDGE INJECTION ---
    function openInObsidian(d) {
        let name = d.data.name;
        let vault = ".obsidian_intel";
        let path = "";
        
        // Tenta encontrar o caminho baseado na hierarquia (recursivo até o topo)
        let current = d;
        let parts = [];
        while(current && current.data.name !== "/") {
            parts.unshift(current.data.name);
            current = current.parent;
        }
        
        // Se for um arquivo Python ou Agente, mapeia para a nota correspondente
        let fullPath = parts.join("/");
        
        // Regras de mapeamento simplificadas
        let noteFile = "";
        if (fullPath.includes("captain.py")) noteFile = "Agentes/CaptainAgent";
        elif (fullPath.includes("librarian.py")) noteFile = "Agentes/LibrarianAgent";
        elif (fullPath.includes("signal_generator.py")) noteFile = "Agentes/SignalGenerator";
        elif (fullPath.includes("bybit_ws.py")) noteFile = "Codice/BybitWS";
        else {
            // Fallback: Tenta abrir a nota gerada automaticamente no Codice/
            noteFile = "Codice/" + name.replace(".py", "");
        }

        const uri = `obsidian://open?vault=${encodeURIComponent(vault)}&file=${encodeURIComponent(noteFile)}`;
        console.log("Opening Obsidian:", uri);
        window.location.href = uri;
    }

    // Injeta o listener no D3 (espera o SVG carregar)
    setTimeout(() => {
        d3.selectAll(".node")
          .on("contextmenu", (event, d) => {
              event.preventDefault();
              openInObsidian(d);
          });
        console.log("🧬 Obsidian Bridge Active: Right-click nodes to open in Obsidian!");
    }, 1000);
    """

    if "// --- OBSIDIAN BRIDGE INJECTION ---" in content:
        print("ℹ️ O Intel Map já está patcheado.")
        return

    # Insere antes do fechamento do </script>
    new_content = content.replace("</script>", obsidian_js + "\n  </script>")

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ Intel Map patcheado com sucesso! Clique com o botão DIREITO nos nós para abrir no Obsidian.")

if __name__ == "__main__":
    patch_intel_map()
