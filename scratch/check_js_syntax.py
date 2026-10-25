import re
import subprocess
import sys

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'<script>(.*?)</script>', text, re.DOTALL)
if not m:
    print("Could not find <script> tag!")
    sys.exit(1)

js_code = m.group(1)
with open('scratch/extracted.js', 'w', encoding='utf-8') as f_js:
    f_js.write(js_code)

print("Extracted JS length:", len(js_code))
try:
    res = subprocess.run(['node', '--check', 'scratch/extracted.js'], capture_output=True, text=True)
    if res.returncode == 0:
        print("node --check: JS SYNTAX VALID! (0 errors)")
    else:
        print("node --check failed:")
        print(res.stderr)
except FileNotFoundError:
    print("Node.js not in PATH, will verify with basic checks")
