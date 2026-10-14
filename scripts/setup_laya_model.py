import os
import shutil
import subprocess

src = r"C:\Users\jonat\Desktop\J&J Consultoria\backend\app\data\models\laya-multilingual"
dst = os.path.abspath(r"backend/app/data/models/laya-multilingual")
os.makedirs(os.path.dirname(dst), exist_ok=True)

if not os.path.exists(dst):
    cmd = f'cmd /c mklink /J "{dst}" "{src}"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("mklink result:", res.stdout, res.stderr)
    if not os.path.exists(dst):
        print("Fallback to copy...")
        shutil.copytree(src, dst)

print("Target exists:", os.path.exists(dst))
if os.path.exists(dst):
    print("Files in target:", os.listdir(dst))
