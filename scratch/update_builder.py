with open('scratch/build_crash_recovery_ui.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'self.lifecycle_engine.set_scheduling_algorithm(algo, q)'
replacement = '''if hasattr(self.lifecycle_engine, "set_algorithm"):
                    self.lifecycle_engine.set_algorithm(algo, q)
                elif hasattr(self.lifecycle_engine, "set_scheduling_algorithm"):
                    self.lifecycle_engine.set_scheduling_algorithm(algo, q)'''

if target in text:
    text = text.replace(target, replacement)
    with open('scratch/build_crash_recovery_ui.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Builder script updated successfully!")
else:
    print("Target not found in builder script!")
