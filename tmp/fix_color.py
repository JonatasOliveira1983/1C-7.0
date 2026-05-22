import os, sys
sys.stdout.reconfigure(encoding='utf-8')

path = os.path.join('frontend', 'cockpit.html')
with open(path, 'rb') as f:
    raw = f.read()

# Normalize line endings
text = raw.replace(b'\r\n', b'\n').decode('utf-8')

# Fix: text-cyan-400 hover:text-cyan-300 -> text-gray-400 hover:text-white
old = 'text-cyan-400 hover:text-cyan-300 hover:bg-white/5'
new = 'text-gray-400 hover:text-white hover:bg-white/5'

count = text.count(old)
if count > 0:
    text = text.replace(old, new, 1)
    with open(path, 'wb') as f:
        f.write(text.encode('utf-8'))
    print(f'✅ Fixed {count} occurrence(s) - cyan -> gray')
else:
    print('❌ Pattern not found')
    # Debug: find nearby patterns
    idx = text.find('Neural Chat')
    if idx >= 0:
        # Show 200 chars before and after
        start = max(0, idx - 200)
        end = min(len(text), idx + 200)
        snippet = text[start:end]
        print(f'Context around Neural Chat:\n---\n{snippet}\n---')
