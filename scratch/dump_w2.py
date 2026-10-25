with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('scratch/sch_render_w2.txt', 'w', encoding='utf-8') as out:
    for j in range(3270, min(3340, len(lines))):
        out.write(f"{j+1}: {lines[j]}")

print("Dumped renderWorkspace2")
