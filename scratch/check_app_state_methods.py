with open('dashboard/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('class AppState')
end = text.find('def update_recovery_status', start)
end2 = text.find('def update_decision', end)
print(text[end:end2+400])
