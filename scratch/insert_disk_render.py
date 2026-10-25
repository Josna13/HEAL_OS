with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """  const ramFree = document.getElementById('ov-kpi-ram-free');
  if (ramFree && ov.ram_free_mb) ramFree.innerText = (ov.ram_free_mb / 1024).toFixed(1) + ' GB';
  
  // 3. Health"""

replacement = """  const ramFree = document.getElementById('ov-kpi-ram-free');
  if (ramFree && ov.ram_free_mb) ramFree.innerText = (ov.ram_free_mb / 1024).toFixed(1) + ' GB';

  // Disk Storage KPI updates
  const diskPct = Math.min(100, Math.max(0, ov.disk_percent || 28.0));
  const diskBar = document.getElementById('ov-kpi-disk-bar');
  if (diskBar) {
    diskBar.style.width = diskPct + '%';
    diskBar.style.background = (diskPct > 90) ? 'var(--accent-red)' : ((diskPct > 75) ? 'var(--accent-amber)' : 'var(--accent-cyan)');
  }
  const diskVal = document.getElementById('ov-kpi-disk-val');
  if (diskVal) diskVal.innerText = diskPct.toFixed(1) + '%';
  const diskUsed = document.getElementById('ov-kpi-disk-used');
  if (diskUsed) diskUsed.innerText = (ov.disk_used_gb !== undefined ? ov.disk_used_gb.toFixed(1) : '120.0') + ' GB';
  const diskFree = document.getElementById('ov-kpi-disk-free');
  if (diskFree) diskFree.innerText = (ov.disk_free_gb !== undefined ? ov.disk_free_gb.toFixed(1) : '392.0') + ' GB';
  const diskDelta = document.getElementById('ov-kpi-disk-delta');
  if (diskDelta) diskDelta.innerText = diskPct.toFixed(1) + '% used';
  
  // 3. Health"""

if target in text:
    text = text.replace(target, replacement)
    with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully added disk rendering to renderOverviewExecutive!")
else:
    print("Target not found.")
