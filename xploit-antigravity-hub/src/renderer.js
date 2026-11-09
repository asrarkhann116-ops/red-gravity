const API_BASE = 'http://127.0.0.1:4242/api';

const logBox = document.getElementById('console-output');
const pathInput = document.getElementById('target-gemini-path');
const detectedPathsBox = document.getElementById('detected-tags');
const searchInput = document.getElementById('component-search');
const componentList = document.getElementById('component-list');

let allItems = [];
let currentTab = 'all';

function addLog(msg, type = 'info') {
  const time = new Date().toLocaleTimeString();
  const line = document.createElement('div');
  line.className = `console-line ${type}`;
  line.textContent = `[${time}] ${msg}`;
  logBox.appendChild(line);
  logBox.scrollTop = logBox.scrollHeight;
}

// Fetch system status and metrics
async function loadStatus() {
  try {
    const res = await fetch(`${API_BASE}/status`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    pathInput.value = data.geminiPath || 'C:\\Users\\Test\\.gemini';
    document.getElementById('metric-agents').textContent = data.agentsCount || 39;
    document.getElementById('metric-skills').textContent = data.skillsCount || 70;
    document.getElementById('metric-arsenal').textContent = data.arsenalCount || 19;

    const rulesHealth = document.getElementById('metric-rules-health');
    const rulesDetail = document.getElementById('metric-rules-detail');
    if (data.bloatedRuleFilesDetected > 0) {
      rulesHealth.textContent = `${data.bloatedRuleFilesDetected} Bloated`;
      rulesDetail.textContent = `Size: ${Math.round(data.totalRuleBytes / 1024)} KB`;
    } else {
      rulesHealth.textContent = 'Optimal';
      rulesDetail.textContent = `Size: ${Math.round(data.totalRuleBytes / 1024)} KB (No Overflows)`;
    }

    updateProfileUI(data.currentProfile);
    addLog(`Daemon linked: Target is ${data.geminiPath} (${data.isPluginInstalled ? 'Installed' : 'Ready'})`, 'info');
  } catch (err) {
    addLog(`Daemon connection failure: ${err.message}`, 'error');
  }
}

// Fetch inventory of all subagents, skills, and arsenal
async function loadInventory() {
  try {
    const res = await fetch(`${API_BASE}/inventory`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    allItems = [];

    // Tag and push agents
    (data.agents || []).forEach(a => {
      allItems.push({
        kind: 'agents',
        kindLabel: 'AGENT',
        id: a.id,
        name: a.name,
        desc: a.description,
        trigger: `@${a.id}`
      });
    });

    // Tag and push skills
    (data.skills || []).forEach(s => {
      allItems.push({
        kind: 'skills',
        kindLabel: 'SKILL',
        id: s.id,
        name: s.name,
        desc: s.description,
        trigger: `/${s.id}`
      });
    });

    // Tag and push arsenal
    (data.arsenal || []).forEach(ar => {
      allItems.push({
        kind: 'arsenal',
        kindLabel: 'ARSENAL',
        id: ar.id,
        name: ar.name,
        desc: ar.description,
        trigger: `arsenal/${ar.id}`
      });
    });

    // Update counts
    document.getElementById('count-all').textContent = allItems.length;
    document.getElementById('count-agents').textContent = (data.agents || []).length;
    document.getElementById('count-skills').textContent = (data.skills || []).length;
    document.getElementById('count-arsenal').textContent = (data.arsenal || []).length;

    renderComponents();
  } catch (err) {
    addLog(`Inventory fetch error: ${err.message}`, 'error');
  }
}

// Render filtered components
function renderComponents() {
  const query = (searchInput.value || '').toLowerCase().trim();

  const filtered = allItems.filter(item => {
    const matchesTab = (currentTab === 'all' || item.kind === currentTab);
    const matchesQuery = !query ||
      item.name.toLowerCase().includes(query) ||
      item.id.toLowerCase().includes(query) ||
      item.desc.toLowerCase().includes(query);
    return matchesTab && matchesQuery;
  });

  componentList.innerHTML = '';

  if (filtered.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = query
      ? `No components matched "${query}".`
      : 'No components available in this category.';
    componentList.appendChild(empty);
    return;
  }

  filtered.forEach(item => {
    const card = document.createElement('div');
    card.className = 'component-card';

    const header = document.createElement('div');
    header.className = 'comp-header';

    const name = document.createElement('span');
    name.className = 'comp-name';
    name.textContent = item.name;

    const kind = document.createElement('span');
    kind.className = 'comp-kind';
    kind.textContent = item.kindLabel;

    header.appendChild(name);
    header.appendChild(kind);

    const desc = document.createElement('p');
    desc.className = 'comp-desc';
    desc.textContent = item.desc;

    const footer = document.createElement('div');
    footer.className = 'comp-footer';

    const trigger = document.createElement('span');
    trigger.className = 'comp-trigger';
    trigger.textContent = item.trigger;

    const copyBtn = document.createElement('button');
    copyBtn.className = 'comp-copy-btn';
    copyBtn.textContent = 'Copy Trigger';
    copyBtn.onclick = (e) => {
      e.stopPropagation();
      navigator.clipboard.writeText(item.trigger);
      copyBtn.textContent = 'Copied';
      setTimeout(() => { copyBtn.textContent = 'Copy Trigger'; }, 1200);
      addLog(`Copied trigger to clipboard: ${item.trigger}`, 'info');
    };

    footer.appendChild(trigger);
    footer.appendChild(copyBtn);

    card.appendChild(header);
    card.appendChild(desc);
    card.appendChild(footer);

    componentList.appendChild(card);
  });
}

function filterTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => {
    if (b.getAttribute('data-tab') === tab) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });
  renderComponents();
}

searchInput.addEventListener('input', () => {
  renderComponents();
});

// Auto-detect system paths
async function detectPaths() {
  addLog('Scanning storage drives for Antigravity installations...', 'info');
  try {
    const res = await fetch(`${API_BASE}/detect-paths`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    detectedPathsBox.innerHTML = '';

    if (data.geminiLocations && data.geminiLocations.length) {
      data.geminiLocations.forEach(loc => {
        const chip = document.createElement('span');
        chip.className = 'path-chip';
        chip.textContent = loc;
        chip.title = 'Click to set target path';
        chip.onclick = () => {
          pathInput.value = loc;
          addLog(`Target changed to: ${loc}`, 'info');
        };
        detectedPathsBox.appendChild(chip);
      });
    }

    if (data.ideLocations && data.ideLocations.length) {
      data.ideLocations.forEach(loc => {
        const chip = document.createElement('span');
        chip.className = 'path-chip';
        chip.textContent = `IDE: ${loc}`;
        detectedPathsBox.appendChild(chip);
      });
    }

    addLog(`Pathfinder completed: ${data.geminiLocations.length} target(s) located.`, 'success');
  } catch (err) {
    addLog(`Pathfinder error: ${err.message}`, 'error');
  }
}

function updateProfileUI(profileName) {
  const currentDisplay = document.getElementById('current-profile-display');
  currentDisplay.textContent = `Profile: ${profileName}`;

  document.querySelectorAll('.profile-card').forEach(card => {
    const key = card.getAttribute('data-profile');
    const badge = card.querySelector('.profile-badge');

    const matches = (
      (key === 'phantom' && profileName.includes('Phantom')) ||
      (key === 'rea' && profileName.includes('REA')) ||
      (key === 'clean' && profileName.includes('Clean'))
    );

    if (matches) {
      card.classList.add('active');
      badge.textContent = 'ACTIVE';
    } else {
      card.classList.remove('active');
      badge.textContent = 'SELECT';
    }
  });
}

async function switchProfile(profileKey) {
  addLog(`Switching active profile to: ${profileKey}...`, 'info');
  try {
    const res = await fetch(`${API_BASE}/switch-profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile: profileKey })
    });
    const data = await res.json();
    if (data.success) {
      addLog(`Profile successfully switched to: ${data.activeProfile}`, 'success');
      updateProfileUI(data.activeProfile);
    }
  } catch (err) {
    addLog(`Profile switch fault: ${err.message}`, 'error');
  }
}

async function deployPlugin() {
  const target = pathInput.value.trim();
  addLog(`Initiating deployment to: ${target}...`, 'info');

  try {
    const res = await fetch(`${API_BASE}/install`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ targetPath: target })
    });
    const data = await res.json();
    if (data.success) {
      addLog(`Deployment completed: ${data.message}`, 'success');
      loadStatus();
      loadInventory();
    } else {
      addLog(`Deployment failed: ${data.error}`, 'error');
    }
  } catch (err) {
    addLog(`Network fault during deployment: ${err.message}`, 'error');
  }
}

async function optimizeRules() {
  addLog('Auditing and optimizing rule definitions...', 'info');
  try {
    const res = await fetch(`${API_BASE}/optimize-rules`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      addLog(data.message, 'success');
      loadStatus();
    }
  } catch (err) {
    addLog(`Rule audit error: ${err.message}`, 'error');
  }
}

async function cleanCache() {
  addLog('Purging temporary brain cache...', 'info');
  try {
    const res = await fetch(`${API_BASE}/clean-cache`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      addLog(data.message, 'success');
    }
  } catch (err) {
    addLog(`Cache cleanup error: ${err.message}`, 'error');
  }
}

async function openFolder() {
  const folder = pathInput.value.trim();
  try {
    const res = await fetch(`${API_BASE}/open-folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: folder })
    });
    const data = await res.json();
    if (data.success) {
      addLog(`Opened Explorer: ${folder}`, 'info');
    }
  } catch (err) {
    addLog(`Failed to open explorer: ${err.message}`, 'error');
  }
}

// Bind top-level buttons
document.getElementById('btn-deploy-top').onclick = deployPlugin;
document.getElementById('btn-detect-paths').onclick = detectPaths;
document.getElementById('btn-open-folder').onclick = openFolder;
document.getElementById('btn-optimize').onclick = optimizeRules;
document.getElementById('btn-clean-cache').onclick = cleanCache;
document.getElementById('btn-clear-log').onclick = () => { logBox.innerHTML = ''; };
document.getElementById('btn-set-custom-path').onclick = () => {
  addLog(`Target path manually set to: ${pathInput.value}`, 'info');
};

// Initialize
loadStatus();
detectPaths();
loadInventory();
