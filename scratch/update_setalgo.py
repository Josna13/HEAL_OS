with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """function setAlgorithm(algo) {
  postAction('set_scheduler_algo', { algo: algo });
}

function toggleAlgorithmComparison() {
  schedulerComparisonOpen = !schedulerComparisonOpen;
  document.getElementById('algorithm-comparison-panel').style.display = schedulerComparisonOpen ? 'block' : 'none';
}"""

replacement = """function setAlgorithm(algo) {
  ensureAudioContext();
  postAction('set_scheduler_algo', { algo: algo });
}

function toggleAlgorithmComparison() {
  schedulerComparisonOpen = !schedulerComparisonOpen;
  const el = document.getElementById('algorithm-comparison-panel');
  if (el) el.style.display = schedulerComparisonOpen ? 'block' : 'none';
  const btn = document.getElementById('btn-toggle-comparison');
  if (btn) btn.innerText = schedulerComparisonOpen ? '✕ Close Comparison' : '📊 Compare All Algorithms';
}"""

if target in text:
    text = text.replace(target, replacement)
    with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated setAlgorithm and toggleAlgorithmComparison!")
else:
    print("Target not found, checking with normalize...")
    # Try finding function setAlgorithm
    pos = text.find('function setAlgorithm(algo)')
    if pos != -1:
        print(text[pos:pos+250])
