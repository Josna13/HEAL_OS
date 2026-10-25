with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'self.lifecycle_engine.set_scheduling_algorithm(algo, q)'
replacement = '''if hasattr(self.lifecycle_engine, "set_algorithm"):
                    self.lifecycle_engine.set_algorithm(algo, q)
                elif hasattr(self.lifecycle_engine, "set_scheduling_algorithm"):
                    self.lifecycle_engine.set_scheduling_algorithm(algo, q)'''

if target in text:
    text = text.replace(target, replacement)
    with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced successfully!")
else:
    print("Target not found!")
