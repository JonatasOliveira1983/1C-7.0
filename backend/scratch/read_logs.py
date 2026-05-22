import sys
import os

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

log_file = 'backend_live.log'
if os.path.exists(log_file):
    with open(log_file, 'rb') as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - 10000))
        content = f.read().decode('utf-8', 'ignore')
        print(content)
else:
    print(f"Log file {log_file} not found")
