with open('scratch/api_handler.txt', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('remove_lifecycle_process')
if idx != -1:
    print(text[idx:idx+800])
