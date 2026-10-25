with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('scratch/sch_visuals_snippet2.txt', 'w', encoding='utf-8') as out:
    for j in range(3630, min(3800, len(lines))):
        out.write(f"{j+1}: {lines[j]}")

print("Dumped 3630 to 3800")
