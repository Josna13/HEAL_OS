with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('scratch/sch_visuals_snippet3.txt', 'w', encoding='utf-8') as out:
    for j in range(3730, min(3900, len(lines))):
        out.write(f"{j+1}: {lines[j]}")

print("Dumped 3730 to 3900")
