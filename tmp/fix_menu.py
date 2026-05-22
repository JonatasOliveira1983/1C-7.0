import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('frontend/cockpit.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f'File size: {len(content)} chars')

changes = 0

# 1. SIDEBAR NAV: Change "10D HQ" to "Banca", remove "JARVIS Chat"
old_sidebar = "{ to: '/', icon: 'space_dashboard', label: '10D HQ' },\n                                        { to: '/neural-chat', icon: 'psychology', label: 'Neural Chat' },\n                                        { to: '/chat', icon: 'chat', label: 'JARVIS Chat' },\n                                        { to: '/config', icon: 'settings', label: 'Configurações' }"

new_sidebar = "{ to: '/', icon: 'space_dashboard', label: 'Banca' },\n                                        { to: '/neural-chat', icon: 'psychology', label: 'Neural Chat' },\n                                        { to: '/config', icon: 'settings', label: 'Configurações' }"

if old_sidebar in content:
    content = content.replace(old_sidebar, new_sidebar)
    changes += 1
    print('✅ Sidebar nav updated: "10D HQ" → "Banca", removed JARVIS Chat')
else:
    print('❌ Sidebar pattern not found!')
    # Debug: show what's around there
    idx = content.find("label: '10D HQ'")
    if idx >= 0:
        print(f'Found at position {idx}')
        print(repr(content[idx-100:idx+300]))
    else:
        # Try alternate pattern
        idx = content.find("space_dashboard")
        if idx >= 0:
            print(f'Found space_dashboard at {idx}')
            print(repr(content[idx:idx+400]))

# 2. BOTTOM NAV: Remove Neural Map, Observar, Wiki. Add Config
# We need to find and replace the bottom nav structure

# Pattern for Neural Map link
old_nm = """                            <a
                                href="/intel/neural"
                                target="_blank"
                                className="flex flex-col items-center gap-1 py-3 px-2 rounded-xl transition-all w-full text-gray-400 hover:text-white hover:bg-white/5"
                            >
                                <span className="material-icons-round" style={{ fontSize: '24px' }}>hub</span>
                                <span className="text-[9px] font-bold tracking-widest hidden lg:block uppercase mt-1">Neural Map</span>
                            </a>"""

if old_nm in content:
    content = content.replace(old_nm, '')
    changes += 1
    print('✅ Removed Neural Map from bottom nav')
else:
    print('❌ Neural Map pattern not found!')
    # Debug
    idx = content.find('/intel/neural')
    if idx >= 0:
        print(f'Found /intel/neural at {idx}')
        print(repr(content[idx-50:idx+200]))
    idx = content.find('Neural Map')
    if idx >= 0:
        print(f'Found "Neural Map" at {idx}')
        print(repr(content[idx-200:idx+50]))

# Pattern for Observar link
old_obs = """                            <a
                                href="/observatory"
                                target="_blank"
                                className="flex flex-col items-center gap-1 py-3 px-2 rounded-xl transition-all w-full text-gray-400 hover:text-white hover:bg-white/5"
                            >
                                <span className="material-icons-round" style={{ fontSize: '24px' }}>visibility</span>
                                <span className="text-[9px] font-bold tracking-widest hidden lg:block uppercase mt-1">Observar</span>
                            </a>"""

if old_obs in content:
    content = content.replace(old_obs, '')
    changes += 1
    print('✅ Removed Observar from bottom nav')
else:
    print('❌ Observar pattern not found!')

# Pattern for Wiki link
old_wiki = """                            <a
                                href="/intel/wiki"
                                target="_blank"
                                className="flex flex-col items-center gap-1 py-3 px-2 rounded-xl transition-all w-full text-gray-400 hover:text-white hover:bg-white/5"
                            >
                                <span className="material-icons-round" style={{ fontSize: '24px' }}>menu_book</span>
                                <span className="text-[9px] font-bold tracking-widest hidden lg:block uppercase mt-1">Wiki Intel</span>
                            </a>"""

if old_wiki in content:
    content = content.replace(old_wiki, '')
    changes += 1
    print('✅ Removed Wiki Intel from bottom nav')
else:
    print('❌ Wiki pattern not found!')

# 3. Add Config to bottom nav after Neural Chat
# Find the Neural Chat link closing
old_after_chat = """                            <Link
                                to="/neural-chat"
                                className="flex flex-col items-center gap-1 py-3 px-2 rounded-xl transition-all w-full text-gray-400 hover:text-white hover:bg-white/5"
                            >
                                <span className="material-icons-round" style={{ fontSize: '24px' }}>psychology</span>
                                <span className="text-[9px] font-bold tracking-widest hidden lg:block uppercase mt-1">Neural Chat</span>
                            </Link>"""

new_with_config = """                            <Link
                                to="/neural-chat"
                                className="flex flex-col items-center gap-1 py-3 px-2 rounded-xl transition-all w-full text-gray-400 hover:text-white hover:bg-white/5"
                            >
                                <span className="material-icons-round" style={{ fontSize: '24px' }}>psychology</span>
                                <span className="text-[9px] font-bold tracking-widest hidden lg:block uppercase mt-1">Neural Chat</span>
                            </Link>
                            <NavItem to="/config" icon="settings" label="Config" isActive={location.pathname === '/config'} />"""

if old_after_chat in content:
    content = content.replace(old_after_chat, new_with_config)
    changes += 1
    print('✅ Added Config to bottom nav after Neural Chat')
else:
    print('❌ Neural Chat Link pattern not found!')
    idx = content.find('to=\"/neural-chat\"')
    if idx >= 0:
        print(f'Found /neural-chat at {idx}')
        print(repr(content[idx-100:idx+300]))

# 4. Remove the React Router route for /chat (LogsPage)
old_route_chat = "<Route path=\"/chat\" element={<LogsPage />} />\n                            "
if old_route_chat in content:
    content = content.replace(old_route_chat, '')
    changes += 1
    print('✅ Removed /chat route from React Router')
else:
    print('❌ /chat route pattern not found!')
    idx = content.find('/chat\" element={<LogsPage')
    if idx >= 0:
        print(f'Found /chat route at {idx}')
        print(repr(content[idx:idx+100]))

# Also check if there's an iframe route for /chat - keep the /neural-chat route though
# Need to check for the LogsPage function/component - should keep it or delete?
# Let's check if LogsPage is referenced elsewhere
logspage_count = content.count('LogsPage')
print(f'LogsPage references remaining: {logspage_count}')

# 5. Remove the LogsPage component if only used by the route we just deleted
# Actually, let me check if LogsPage is used anywhere else first

# Write back
with open('frontend/cockpit.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\nTotal changes: {changes}')
print('File written successfully!')
