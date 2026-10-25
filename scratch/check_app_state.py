with open('dashboard/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('class AppState')
end = text.find('class TerminalDashboard', start)
print(text[start:start+1200])
