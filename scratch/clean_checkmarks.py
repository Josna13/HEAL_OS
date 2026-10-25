with open('scratch/test_all_features.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('✓', '[OK]')

with open('scratch/test_all_features.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Cleaned checkmarks in test_all_features.py")
