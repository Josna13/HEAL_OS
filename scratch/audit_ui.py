import sys, re
sys.path.insert(0, '.')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("Total file size:", len(text))

# Extract all HTML element IDs
ids = re.findall(r'id=["\']([^"\']+)["\']', text)
print(f"\nTotal HTML IDs: {len(ids)}")

# Extract all function names from JS
funcs = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', text)
print(f"\nTotal JS functions: {len(funcs)}")

# Find CSS variables defined
css_vars = re.findall(r'--([a-zA-Z0-9-]+)\s*:', text)
print(f"\nCSS variables used: {set(css_vars)}")

# Find main tabs
tabs = re.findall(r'id=["\']tab-([^"\']+)["\']', text)
print(f"\nTabs found: {tabs}")

# Check for memory leak section
print(f"\nMemory leak section present: {'memory-leak' in text or 'memLeak' in text}")
print(f"Guided demo present: {'guided-demo' in text or 'tourStep' in text or 'TOUR_STORY' in text}")
print(f"Sound toggle present: {'soundEnabled' in text}")
