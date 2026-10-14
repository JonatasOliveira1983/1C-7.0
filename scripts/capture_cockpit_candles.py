from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 2560, 'height': 1080})
        page.goto('http://127.0.0.1:8085/cockpit.html', wait_until='load', timeout=30000)
        
        # Wait until prices load
        try:
            page.wait_for_function("() => document.getElementById('hud-live-price-0') && document.getElementById('hud-live-price-0').textContent !== '--'", timeout=25000)
        except Exception as e:
            print("Timeout waiting for price 0, continuing...", e)
            
        time.sleep(4)
        
        info = page.evaluate("""() => {
            return {
                prices: [0, 1, 2, 3].map(i => {
                    const el = document.getElementById('hud-live-price-' + i);
                    return el ? el.textContent : '';
                }),
                badges: [0, 1, 2, 3].map(i => {
                    const el = document.getElementById('chart-header-badge-' + i);
                    return el ? el.textContent : '';
                }),
                activeSlots: window._activeSlotsData ? window._activeSlotsData.length : 0,
                activeCountText: document.getElementById('active-slots-count') ? document.getElementById('active-slots-count').textContent : ''
            };
        }""")
        print("PAGE INFO:", info)
        
        path = 'C:/Users/jonat/.gemini/antigravity/brain/01891ee5-f218-4f66-9357-6ff67adca6e0/cockpit_candles_verified_live.png'
        page.screenshot(path=path)
        print("SCREENSHOT_SAVED_TO:", path)
        browser.close()

if __name__ == '__main__':
    run()
