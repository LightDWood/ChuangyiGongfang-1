import subprocess
import sys
import os

os.chdir(r"d:\DFX\Code\创意工坊\backend")

python_exe = r"C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\python.exe"
uvicorn_cmd = [python_exe, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

process = subprocess.Popen(
    uvicorn_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print("Backend starting...")
for line in process.stdout:
    print(line.strip())

process.wait()
