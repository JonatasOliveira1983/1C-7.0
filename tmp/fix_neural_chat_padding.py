import re

with open('frontend/cockpit.html', 'r', encoding='utf-8') as f:
    content = f.read()

old = '<Route path="/neural-chat" element={<div className="w-full h-full"><iframe src="/neural-chat.html" className="w-full h-full border-none" title="Neural Chat Interface" /></div>} />'

new = '<Route path="/neural-chat" element={<div className="w-full h-full lg:pl-[80px] pb-[70px] lg:pb-0 overflow-hidden"><iframe src="/neural-chat.html" className="w-full h-full border-none" title="Neural Chat Interface" /></div>} />'

if old in content:
    content = content.replace(old, new)
    with open('frontend/cockpit.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Padding applied successfully!")
else:
    print("[ERROR] String not found!")
    # Try to find similar patterns
    if 'neural-chat' in content:
        for i, line in enumerate(content.split('\n')):
            if 'neural-chat' in line:
                print(f"  Found near line {i+1}: {line.strip()[:100]}...")
