"""
1Crypten - eAssets & External Intel Session Recorder
Inspirado no kalil0321/reverse-api-engineer e adaptado ao ecossistema 1Crypten.
Abre um navegador real (Playwright Chromium) com stealth ativo, grava o arquivo HAR
e extrai automaticamente todos os endpoints de dados e APIs REST/WebSocket.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Garante saída UTF-8 no console Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

OUTPUT_DIR = Path("backend/data/har_captures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_and_summarize_har(har_path: Path):
    print(f"\n[ANALISADOR] Processando arquivo HAR: {har_path.name}")
    try:
        with open(har_path, "r", encoding="utf-8") as f:
            har_data = json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao ler HAR: {e}")
        return

    entries = har_data.get("log", {}).get("entries", [])
    print(f"[ANALISADOR] Total de requisições capturadas: {len(entries)}")

    api_endpoints = {}
    ignored_exts = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".css")

    for entry in entries:
        req = entry.get("request", {})
        resp = entry.get("response", {})
        url = req.get("url", "")
        method = req.get("method", "GET")

        # Ignora assets estáticos conhecidos
        if any(url.split("?")[0].lower().endswith(ext) for ext in ignored_exts):
            continue

        status = resp.get("status", 0)
        content_type = ""
        for h in resp.get("headers", []):
            if h.get("name", "").lower() == "content-type":
                content_type = h.get("value", "")
                break

        # Filtra chamadas de API, JSON ou chamadas para domínios relevantes
        is_api = (
            "application/json" in content_type
            or "/api/" in url
            or "/v1/" in url
            or "api.eassets.ai" in url
            or "eassets.ai" in url
        )

        if is_api:
            # Chave normalizada (método + URL sem query)
            base_url = url.split("?")[0]
            key = f"{method} {base_url}"

            if key not in api_endpoints:
                # Captura headers de interesse (Authorization, x-*, tokens)
                req_headers = {
                    h["name"]: h["value"]
                    for h in req.get("headers", [])
                    if h["name"].lower() in ("authorization", "cookie", "x-api-key")
                    or h["name"].lower().startswith("x-")
                }

                # Tenta capturar resposta em JSON
                resp_body_sample = None
                resp_text = resp.get("content", {}).get("text", "")
                if resp_text and ("application/json" in content_type or resp_text.startswith("{") or resp_text.startswith("[")):
                    try:
                        parsed_body = json.loads(resp_text)
                        # Guarda apenas as chaves principais se for grande
                        if isinstance(parsed_body, dict):
                            resp_body_sample = {k: type(v).__name__ for k, v in list(parsed_body.items())[:15]}
                        elif isinstance(parsed_body, list) and len(parsed_body) > 0 and isinstance(parsed_body[0], dict):
                            resp_body_sample = [{k: type(v).__name__ for k, v in list(parsed_body[0].items())[:15]}]
                    except Exception:
                        resp_body_sample = "RAW_TEXT_OR_COMPRESSED"

                api_endpoints[key] = {
                    "method": method,
                    "url": url,
                    "base_url": base_url,
                    "status": status,
                    "content_type": content_type,
                    "auth_headers": req_headers,
                    "response_schema_sample": resp_body_sample,
                }

    summary_file = har_path.with_suffix(".api_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(api_endpoints, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCESSO] Mapeados {len(api_endpoints)} endpoints de API/dados únicos.")
    print(f"[ARQUIVO] Sumário salvo em: {summary_file}")
    print("\n--- ENDPOINTS DESTAQUE ---")
    for k, v in list(api_endpoints.items())[:20]:
        print(f"[{v['status']}] {k}")


def start_capture_session(target_url: str = "https://eassets.ai/pt-BR"):
    from playwright.sync_api import sync_playwright

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    har_filename = OUTPUT_DIR / f"eassets_capture_{timestamp}.har"

    print("=" * 70)
    print("1CRYPTEN — SESSÃO DE CAPTURA & ENGENHARIA REVERSA DE API")
    print(f"Alvo: {target_url}")
    print(f"Destino do HAR: {har_filename}")
    print("=" * 70)
    print("\n[INSTRUÇÃO PARA O OPERADOR]")
    print("1. A janela do navegador vai abrir automaticamente.")
    print("2. Faça login se tiver conta, navegue pelas telas do Screener, OI, Funding e Indicadores.")
    print("3. Quando terminar de explorar os dados que deseja capturar, BASTA FECHAR A JANELA DO NAVEGADOR.")
    print("4. O script finalizará a gravação e gerará o sumário de endpoints automaticamente.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
        )

        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            record_har_path=str(har_filename),
            record_har_content="attach",
        )

        page = context.new_page()

        # Injeta evasão stealth básica
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

        print(f"[REDE] Conectando a {target_url}...")
        try:
            page.goto(target_url, wait_until="domcontentloaded")
            print("[STATUS] Navegador aberto! Aguardando interação... (feche a janela ao concluir)")
            # Aguarda o fechamento da página pelo usuário
            page.wait_for_event("close", timeout=0)
        except Exception as e:
            print(f"[AVISO] Sessão encerrada ou interrompida: {e}")
        finally:
            context.close()
            browser.close()

    if har_filename.exists():
        parse_and_summarize_har(har_filename)
    else:
        print("[AVISO] Nenhum arquivo HAR foi gerado.")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://eassets.ai/pt-BR"
    start_capture_session(url)
