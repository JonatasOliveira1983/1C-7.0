import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('frontend/cockpit.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

changes = []

# Identify lines to remove based on content patterns
remove_indices = set()

for i, line in enumerate(lines):
    # Neural Map (href=/intel/neural)
    if '/intel/neural' in line and 'href=' in line:
        # Remove this line and surrounding lines until the closing </a>
        remove_indices.add(i)
        # Walk forward to find </a>
        for j in range(i, min(i+10, len(lines))):
            remove_indices.add(j)
            if '</a>' in lines[j]:
                break
        changes.append(f'Neural Map removed at line {i+1}')

    # Observar (href=/observatory)  
    if '/observatory' in line and 'href=' in line:
        remove_indices.add(i)
        for j in range(i, min(i+10, len(lines))):
            remove_indices.add(j)
            if '</a>' in lines[j]:
                break
        changes.append(f'Observar removed at line {i+1}')

    # Wiki Intel (href=/intel/wiki)
    if '/intel/wiki' in line and 'href=' in line:
        remove_indices.add(i)
        for j in range(i, min(i+10, len(lines))):
            remove_indices.add(j)
            if '</a>' in lines[j]:
                break
        changes.append(f'Wiki Intel removed at line {i+1}')

    # Floating Chat action (to=/chat with floating class)
    if 'to=\"/chat\"' in line and 'floating' in line.lower():
        remove_indices.add(i)
        # This is a Link component - find the closing tag
        for j in range(i, min(i+12, len(lines))):
            remove_indices.add(j)
        changes.append(f'Chat action removed at line {i+1}')

    # Second/Duplicate Config NavItem
    if 'to=\"/config\"' in line and 'NavItem' in line:
        # Check if we've already seen one (there should be only one)
        if 'Config' in line or 'settings' in line:
            # Count how many Config NavItems we've seen
            pass

# Actually, let me do this more carefully. Let me use string replacement on the whole content
# to handle the patterns precisely

with open('frontend/cockpit.html', 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Remove Neural Map block
# Pattern: <a\n                                href="/intel/neural"\n                                ...</a>
import re

# Remove the full neural map link block
pattern_nm = r'<a\s*\n\s*href="/intel/neural"[^>]*>.*?</a>'
count_before = len(content)
content = re.sub(pattern_nm, '', content, flags=re.DOTALL)
if len(content) != count_before:
    changes_made.append('Removed Neural Map')

# Remove Observar block
pattern_obs = r'<a\s*\n\s*href="/observatory"[^>]*>.*?</a>'
count_before = len(content)
content = re.sub(pattern_obs, '', content, flags=re.DOTALL)
if len(content) != count_before:
    changes_made.append('Removed Observar')

# Remove Wiki Intel block
pattern_wiki = r'<a\s*\n\s*href="/intel/wiki"[^>]*>.*?</a>'
count_before = len(content)
content = re.sub(pattern_wiki, '', content, flags=re.DOTALL)
if len(content) != count_before:
    changes_made.append('Removed Wiki Intel')

# Remove floating Chat action link
pattern_chat = r'<Link\s*\n\s*to="/chat"[^>]*>.*?</Link>'
count_before = len(content)
content = re.sub(pattern_chat, '', content, flags=re.DOTALL)
if len(content) != count_before:
    changes_made.append('Removed floating Chat action')

# Remove duplicate Config NavItem (the second one)
# Find all NavItem to="/config" occurrences
config_items = list(re.finditer(r'<NavItem\s+to="/config"[^>]*/>', content))
if len(config_items) >= 2:
    # Remove the second one (last one)
    second = config_items[-1]
    content = content[:second.start()] + content[second.end():]
    changes_made.append('Removed duplicate Config NavItem')

# Cleanup empty lines left behind (multiple consecutive newlines)
content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

with open('frontend/cockpit.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Changes made:')
for c in changes_made:
    print(f'  ✅ {c}')

if not changes_made:
    print('  ❌ No changes were made!')

# Verify - show the nav section
idx = content.find('className="flex flex-row lg:flex-col items-center gap-4 lg:gap-6 w-full"')
if idx >= 0:
    # Show what's in the nav now
    section = content[idx:idx+2000]
    print('\n=== BOTTOM NAV AFTER CLEANUP ===')
    for line in section.split('\n'):
        stripped = line.strip()
        if stripped and ('NavItem' in stripped or 'href=' in stripped or 'to=' in stripped or 'material-icons' in stripped):
            print(f'  {stripped[:120]}')
