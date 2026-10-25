C:\Windows\System32\wsl.exe bash -c "cd /mnt/e/HealOs && source venv/bin/activate && python3 -m py_compile dashboard/web_server.py && pytest tests/ -q"
