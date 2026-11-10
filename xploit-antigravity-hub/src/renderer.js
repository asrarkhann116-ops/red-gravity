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

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
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

async function launchTurbo() {
  addLog('Launching Antigravity with 6-Point Unconstrained God-Mode...', 'info');
  try {
    const res = await fetch(`${API_BASE}/launch-turbo`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      addLog('God-Mode Process Spawned: Zero-Friction & Autonomous Execution Active.', 'success');
    } else {
      addLog(`Failed to launch: ${data.error}`, 'error');
    }
  } catch (err) {
    addLog(`Launch error: ${err.message}`, 'error');
  }
}

// Bind top-level buttons
document.getElementById('btn-deploy-top').onclick = deployPlugin;
const turboBtn = document.getElementById('btn-turbo-launch');
if (turboBtn) turboBtn.onclick = launchTurbo;
document.getElementById('btn-detect-paths').onclick = detectPaths;
document.getElementById('btn-open-folder').onclick = openFolder;
document.getElementById('btn-optimize').onclick = optimizeRules;
document.getElementById('btn-clean-cache').onclick = cleanCache;
document.getElementById('btn-clear-log').onclick = () => { logBox.innerHTML = ''; };
document.getElementById('btn-set-custom-path').onclick = () => {
  addLog(`Target path manually set to: ${pathInput.value}`, 'info');
};

// ==========================================================================
// CORTEX Live Trajectory & Memory Inspector
// ==========================================================================
const cortexSessionSelect = document.getElementById('cortex-session-select');
const cortexActiveId = document.getElementById('cortex-active-id');
const cortexStepCount = document.getElementById('cortex-step-count');
const cortexTokenCount = document.getElementById('cortex-token-count');
const trajectoryTimeline = document.getElementById('trajectory-timeline');
const btnRefreshTrajectory = document.getElementById('btn-refresh-trajectory');
const btnPruneCortex = document.getElementById('btn-prune-cortex');

async function loadCortexSessions() {
  try {
    const res = await fetch(`${API_BASE}/cortex/sessions`);
    if (!res.ok) return;
    const sessions = await res.json();
    
    if (sessions && sessions.length) {
      cortexSessionSelect.innerHTML = '';
      sessions.forEach((s, idx) => {
        const opt = document.createElement('option');
        opt.value = s.id;
        const shortId = s.id.substring(0, 8);
        const timeStr = new Date(s.lastModified).toLocaleTimeString();
        opt.textContent = `${idx === 0 ? '● ACTIVE ' : ''}${shortId}... (${s.stepCount} steps, ${timeStr})`;
        cortexSessionSelect.appendChild(opt);
      });
      loadTrajectory(sessions[0].id);
    } else {
      cortexSessionSelect.innerHTML = '<option value="">No active sessions found</option>';
    }
  } catch(err) {
    console.error('Failed to load cortex sessions:', err);
  }
}

async function loadTrajectory(sessionId) {
  if (!sessionId) return;
  cortexActiveId.textContent = sessionId.substring(0, 8) + '...';
  
  try {
    const res = await fetch(`${API_BASE}/cortex/trajectory?session=${encodeURIComponent(sessionId)}&limit=30`);
    if (!res.ok) return;
    const data = await res.json();
    
    cortexStepCount.textContent = data.totalSteps || 0;
    cortexTokenCount.textContent = (data.estimatedTokens || 0).toLocaleString();
    
    trajectoryTimeline.innerHTML = '';
    
    if (data.steps && data.steps.length) {
      data.steps.reverse().forEach(step => {
        const card = document.createElement('div');
        const isPlanner = step.type.includes('PLANNER');
        const isUser = step.type.includes('USER');
        card.className = `trajectory-card ${isPlanner ? 'planner' : isUser ? 'user' : 'generic'}`;
        
        const header = document.createElement('div');
        header.className = 'trajectory-header';
        
        const badge = document.createElement('span');
        badge.className = 'trajectory-badge';
        badge.textContent = `Step #${step.index} // ${step.type}`;
        
        const time = document.createElement('span');
        time.className = 'trajectory-time';
        time.textContent = step.timestamp ? new Date(step.timestamp).toLocaleTimeString() : '';
        
        header.appendChild(badge);
        header.appendChild(time);
        card.appendChild(header);
        
        if (step.tools && step.tools.length) {
          const toolsBox = document.createElement('div');
          toolsBox.className = 'trajectory-tools';
          step.tools.forEach(t => {
            const chip = document.createElement('span');
            chip.className = 'tool-chip';
            chip.textContent = `Tool: ${t}`;
            toolsBox.appendChild(chip);
          });
          card.appendChild(toolsBox);
        }
        
        if (step.preview && step.preview.trim()) {
          const preview = document.createElement('div');
          preview.className = 'trajectory-preview';
          preview.textContent = step.preview;
          card.appendChild(preview);
        }
        
        trajectoryTimeline.appendChild(card);
      });
    } else {
      trajectoryTimeline.innerHTML = '<div class="empty-state">No recorded steps in this session trajectory.</div>';
    }
  } catch(err) {
    trajectoryTimeline.innerHTML = `<div class="empty-state">Error fetching trajectory: ${err.message}</div>`;
  }
}

if (cortexSessionSelect) {
  cortexSessionSelect.onchange = (e) => {
    loadTrajectory(e.target.value);
  };
}

if (btnRefreshTrajectory) {
  btnRefreshTrajectory.onclick = () => {
    const cur = cortexSessionSelect.value;
    if (cur) {
      addLog(`Refreshing CORTEX trajectory for ${cur.substring(0,8)}...`, 'info');
      loadTrajectory(cur);
    }
  };
}

if (btnPruneCortex) {
  btnPruneCortex.onclick = async () => {
    addLog('Executing CORTEX context & dead step pruning...', 'info');
    await cleanCache();
    await loadCortexSessions();
  };
}

// ==========================================================================
// Account Vault & Profile Switcher
// ==========================================================================
const accountVaultList = document.getElementById('account-vault-list');
const activeAccountBadge = document.getElementById('active-account-badge');
const btnSaveCurrentAccount = document.getElementById('btn-save-current-account');

async function loadVaultAccounts() {
  if (!accountVaultList) return;
  try {
    const res = await fetch(`${API_BASE}/accounts`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    const active = data.activeAccount;
    if (active && active.email && active.email !== 'Unknown') {
      activeAccountBadge.textContent = `● Active: ${active.email}`;
      activeAccountBadge.style.color = '#00ff78';
      activeAccountBadge.style.borderColor = 'rgba(0, 255, 120, 0.4)';
    } else {
      activeAccountBadge.textContent = '○ Active: Not Logged In';
      activeAccountBadge.style.color = '#888888';
      activeAccountBadge.style.borderColor = 'var(--border-hairline)';
    }

    const accounts = data.vaultAccounts || [];
    if (accounts.length === 0) {
      accountVaultList.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          No accounts saved in vault yet. Click "+ Save Current Account" to store current session for 1-click swapping.
        </div>
      `;
      return;
    }

    accountVaultList.innerHTML = accounts.map(acc => `
      <div class="profile-card ${acc.isActive ? 'active' : ''}" style="display: flex; flex-direction: column; justify-content: space-between; padding: 12px; cursor: default;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-family: var(--font-mono); font-weight: 600; font-size: 0.8rem; color: ${acc.isActive ? '#00ff78' : '#e0e0e0'};">
              ${escapeHtml(acc.label || acc.email)}
            </span>
            <span class="profile-badge" style="${acc.isActive ? 'background: rgba(0,255,120,0.15); color: #00ff78;' : ''}">
              ${acc.isActive ? 'ACTIVE' : 'SAVED'}
            </span>
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-secondary); word-break: break-all; margin-bottom: 8px;">
            ${escapeHtml(acc.email)}
          </div>
        </div>
        <div style="display: flex; gap: 8px; margin-top: 6px;">
          ${!acc.isActive ? `
            <button class="btn btn-primary" style="flex: 1; padding: 4px 8px; font-size: 0.68rem;" onclick="switchAccount('${escapeHtml(acc.email)}')">
              ⚡ Switch
            </button>
          ` : `
            <button class="btn btn-secondary" style="flex: 1; padding: 4px 8px; font-size: 0.68rem; color: #00ff78;" disabled>
              ✓ Active
            </button>
          `}
          <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.68rem; color: #ff6666;" onclick="deleteAccount('${escapeHtml(acc.email)}')">
            ✕
          </button>
        </div>
      </div>
    `).join('');

  } catch(err) {
    addLog(`Account Vault error: ${err.message}`, 'error');
  }
}

async function saveCurrentAccount() {
  addLog('Saving active account into vault...', 'info');
  try {
    const res = await fetch(`${API_BASE}/accounts/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await res.json();
    if (data.success) {
      addLog(data.message, 'success');
      loadVaultAccounts();
    } else {
      addLog(`Save failed: ${data.error}`, 'error');
    }
  } catch(err) {
    addLog(`Save failed: ${err.message}`, 'error');
  }
}

async function switchAccount(email) {
  addLog(`Switching to account ${email}...`, 'info');
  try {
    const res = await fetch(`${API_BASE}/accounts/switch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await res.json();
    if (data.success) {
      addLog(data.message, 'success');
      loadVaultAccounts();
    } else {
      addLog(`Switch failed: ${data.error}`, 'error');
    }
  } catch(err) {
    addLog(`Switch failed: ${err.message}`, 'error');
  }
}

async function deleteAccount(email) {
  if (!confirm(`Delete ${email} from vault?`)) return;
  try {
    const res = await fetch(`${API_BASE}/accounts/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await res.json();
    if (data.success) {
      addLog(data.message, 'info');
      loadVaultAccounts();
    }
  } catch(err) {}
}

if (btnSaveCurrentAccount) btnSaveCurrentAccount.onclick = saveCurrentAccount;

// ==========================================================================
// Universal Gateway & Runtime Freeze
// ==========================================================================
const gatewayProviderSelect = document.getElementById('gateway-provider');
const gatewayUrlInput = document.getElementById('gateway-url');
const gatewayModelInput = document.getElementById('gateway-model');
const gatewayKeyInput = document.getElementById('gateway-key');
const chkGatewayEnable = document.getElementById('chk-gateway-enable');
const chkUpdateFreeze = document.getElementById('chk-update-freeze');
const btnSaveGateway = document.getElementById('btn-save-gateway');
const btnTestGateway = document.getElementById('btn-test-gateway');
const gatewayTestResult = document.getElementById('gateway-test-result');
const freezeStatusBadge = document.getElementById('freeze-status-badge');

if (gatewayProviderSelect) {
  gatewayProviderSelect.onchange = () => {
    const p = gatewayProviderSelect.value;
    if (p === 'ollama') {
      if (gatewayUrlInput) gatewayUrlInput.value = 'http://127.0.0.1:11434/v1';
      if (gatewayModelInput) gatewayModelInput.value = 'deepseek-r1:32b';
    } else if (p === 'deepseek') {
      if (gatewayUrlInput) gatewayUrlInput.value = 'https://api.deepseek.com/v1';
      if (gatewayModelInput) gatewayModelInput.value = 'deepseek-chat';
    } else if (p === 'openrouter') {
      if (gatewayUrlInput) gatewayUrlInput.value = 'https://openrouter.ai/api/v1';
      if (gatewayModelInput) gatewayModelInput.value = 'anthropic/claude-3.7-sonnet';
    }
  };
}

async function testGatewayConnection() {
  const payload = {
    provider: gatewayProviderSelect ? gatewayProviderSelect.value : 'ollama',
    endpoint: gatewayUrlInput ? gatewayUrlInput.value.trim() : '',
    model: gatewayModelInput ? gatewayModelInput.value.trim() : '',
    apiKey: gatewayKeyInput ? gatewayKeyInput.value.trim() : ''
  };

  if (gatewayTestResult) {
    gatewayTestResult.style.display = 'block';
    gatewayTestResult.textContent = 'Probing target model endpoint...';
    gatewayTestResult.style.color = 'var(--text-secondary)';
  }

  try {
    const res = await fetch(`${API_BASE}/gateway/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      gatewayTestResult.textContent = `✓ ${data.message}`;
      gatewayTestResult.style.color = '#00ff78';
      addLog(`Gateway Test: Connected in ${data.latencyMs}ms`, 'success');
    } else {
      gatewayTestResult.textContent = `✕ ${data.error || 'Connection failed'}`;
      gatewayTestResult.style.color = '#ff6666';
      addLog(`Gateway Test Failed: ${data.error}`, 'error');
    }
  } catch(err) {
    if (gatewayTestResult) {
      gatewayTestResult.textContent = `✕ ${err.message}`;
      gatewayTestResult.style.color = '#ff6666';
    }
    addLog(`Gateway probe error: ${err.message}`, 'error');
  }
}
if (btnTestGateway) btnTestGateway.onclick = testGatewayConnection;

async function loadGatewayConfig() {
  try {
    const res = await fetch(`${API_BASE}/gateway`);
    if (!res.ok) return;
    const data = await res.json();
    if (gatewayProviderSelect && data.provider) gatewayProviderSelect.value = data.provider;
    if (gatewayUrlInput) gatewayUrlInput.value = data.endpoint || data.url || 'http://127.0.0.1:11434/v1';
    if (gatewayModelInput) gatewayModelInput.value = data.model || 'deepseek-r1:32b';
    if (gatewayKeyInput) gatewayKeyInput.value = data.apiKey || '';
    if (chkGatewayEnable) chkGatewayEnable.checked = Boolean(data.enabled);
    if (chkUpdateFreeze) chkUpdateFreeze.checked = data.disableAutoUpdate !== false;
    updateFreezeBadge(data.disableAutoUpdate !== false);
  } catch(e) {}
}

function updateFreezeBadge(isFrozen) {
  if (!freezeStatusBadge) return;
  if (isFrozen) {
    freezeStatusBadge.textContent = '● Updates: FROZEN';
    freezeStatusBadge.style.color = '#ff6666';
    freezeStatusBadge.style.borderColor = 'rgba(255, 34, 34, 0.3)';
    freezeStatusBadge.style.background = 'rgba(255, 34, 34, 0.12)';
  } else {
    freezeStatusBadge.textContent = '○ Updates: ACTIVE';
    freezeStatusBadge.style.color = '#888888';
    freezeStatusBadge.style.borderColor = 'var(--border-hairline)';
    freezeStatusBadge.style.background = 'var(--bg-surface)';
  }
}

async function saveGatewayConfig() {
  const payload = {
    enabled: chkGatewayEnable ? chkGatewayEnable.checked : false,
    provider: gatewayProviderSelect ? gatewayProviderSelect.value : 'ollama',
    endpoint: gatewayUrlInput ? gatewayUrlInput.value.trim() : '',
    model: gatewayModelInput ? gatewayModelInput.value.trim() : '',
    apiKey: gatewayKeyInput ? gatewayKeyInput.value.trim() : '',
    disableAutoUpdate: chkUpdateFreeze ? chkUpdateFreeze.checked : true
  };

  addLog('Binding Universal Gateway and Runtime Freeze settings...', 'info');
  try {
    const res = await fetch(`${API_BASE}/gateway`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      addLog(data.message, 'success');
      updateFreezeBadge(payload.disableAutoUpdate);
      if (payload.enabled) {
        addLog(`Gateway Active: Traffic routed to ${payload.model} @ ${payload.endpoint}`, 'success');
      } else {
        addLog('Gateway Direct: Default Google routing active.', 'info');
      }
    }
  } catch(err) {
    addLog(`Gateway error: ${err.message}`, 'error');
  }
}

if (btnSaveGateway) btnSaveGateway.onclick = saveGatewayConfig;
if (chkUpdateFreeze) {
  chkUpdateFreeze.onchange = () => {
    updateFreezeBadge(chkUpdateFreeze.checked);
  };
}

// Initialize
loadStatus();
detectPaths();
loadInventory();
loadCortexSessions();
loadGatewayConfig();
loadVaultAccounts();
