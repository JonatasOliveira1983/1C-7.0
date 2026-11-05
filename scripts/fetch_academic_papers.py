"""
Script para download de papers academicos quantitativos para o vault_galaxy/papers.
Padrão 1Crypten: Zero Emojis, logs tecnicos estruturados.
"""
import os
import sys
import urllib.request
import ssl

PAPERS = {
    "stanford_crypto_pairs_trading.pdf": "https://www.stanford.edu/class/msande448/2021/Midterm/gr3.pdf",
    "barry_johnson_algorithmic_trading.pdf": "https://raw.githubusercontent.com/karygauss03/book-1/master/%5BALGO-TRADING%5D%5BAlgorithmic%20Trading%20%26%20DMA-%20An%20introduction%20to%20direct%20access%20trading%20strategies%5D.pdf",
    "ey_crypto_derivatives.pdf": "https://www.ey.com/content/dam/ey-unified-site/ey-com/en-us/insights/financial-services/documents/ey-exploring-crypto-derivatives.pdf",
}

def main():
    target_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vault_galaxy", "papers")
    os.makedirs(target_dir, exist_ok=True)
    
    # SSL context permissive for academic portals
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print(f"[FETCH_PAPERS] Diretorio de destino: {target_dir}")
    
    success_count = 0
    for filename, url in PAPERS.items():
        filepath = os.path.join(target_dir, filename)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 50000:
            print(f"[FETCH_PAPERS] {filename} ja existe ({os.path.getsize(filepath)} bytes). Pulando.")
            success_count += 1
            continue
            
        print(f"[FETCH_PAPERS] Baixando {filename} de {url} ...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                content = resp.read()
                with open(filepath, "wb") as f:
                    f.write(content)
            size = os.path.getsize(filepath)
            print(f"[FETCH_PAPERS] Concluido: {filename} ({size} bytes)")
            success_count += 1
        except Exception as e:
            print(f"[FETCH_PAPERS] Falha ao baixar {filename}: {e}")

    print(f"[FETCH_PAPERS] Total baixados/validados com sucesso: {success_count}/{len(PAPERS)}")

if __name__ == "__main__":
    main()
