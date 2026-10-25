import sys
import shutil
import subprocess

# Re-run prepare_dl_js.py
subprocess.run(['python', 'scratch/prepare_dl_js.py'], check=True)
shutil.copyfile('scratch/dl_studio_js.txt', 'scratch/dl_studio_test.js')
res = subprocess.run(['node', '--check', 'scratch/dl_studio_test.js'], capture_output=True, text=True)
print("Return code:", res.returncode)
if res.returncode == 0:
    print("SUCCESS: 0 JS syntax errors!")
else:
    print("Stderr:\n", res.stderr)

