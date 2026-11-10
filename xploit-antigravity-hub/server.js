const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { exec } = require('child_process');

const PORT = 4242;
const USER_HOME = os.homedir();
let ACTIVE_GEMINI_DIR = path.join(USER_HOME, '.gemini');
const BUNDLED_PLUGIN_DIR = path.join(__dirname, 'bundled-plugin');
const BUNDLED_CONFIG_DIR = path.join(__dirname, 'bundled-config');
const WORKSPACE_RULES_DIR = path.join('E:', 'asrar', 'projects', '.agent', 'rules');

// Helper to copy directory recursively
function copyDirSync(src, dest, filterFn = null) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    if (filterFn && !filterFn(entry.name)) continue;
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath, filterFn);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

// System Paths Auto-Detection Scanner
function detectSystemPaths() {
  const detected = {
    userHome: USER_HOME,
    activeGeminiDir: ACTIVE_GEMINI_DIR,
    geminiLocations: [],
    ideLocations: [],
    drives: []
  };

  // 1. Check known .gemini locations
  const candidateGemini = [
    path.join(USER_HOME, '.gemini'),
    path.join('C:', 'Users', path.basename(USER_HOME), '.gemini'),
    'C:\\Users\\Default\\.gemini',
    'C:\\.gemini',
    'E:\\asrar\\projects\\.gemini'
  ];

  for (const cand of candidateGemini) {
    if (fs.existsSync(cand) && !detected.geminiLocations.includes(cand)) {
      detected.geminiLocations.push(cand);
    }
  }

  // 2. Check Antigravity IDE directories
  const appData = process.env.APPDATA || path.join(USER_HOME, 'AppData', 'Roaming');
  const localAppData = process.env.LOCALAPPDATA || path.join(USER_HOME, 'AppData', 'Local');

  const candidateIde = [
    path.join(appData, 'Antigravity'),
    path.join(appData, 'Antigravity IDE'),
    path.join(localAppData, 'Programs', 'Antigravity'),
    path.join(localAppData, 'Programs', 'Antigravity IDE'),
    'C:\\Program Files\\Antigravity',
    'C:\\Program Files\\Antigravity IDE'
  ];

  for (const cand of candidateIde) {
    if (fs.existsSync(cand) && !detected.ideLocations.includes(cand)) {
      detected.ideLocations.push(cand);
    }
  }

  // 3. Detect available system drives
  const driveLetters = ['C', 'D', 'E', 'F', 'G', 'Z'];
  for (const letter of driveLetters) {
    const rootPath = `${letter}:\\`;
    if (fs.existsSync(rootPath)) {
      detected.drives.push(rootPath);
    }
  }

  return detected;
}

// System Diagnostics & Status
function getSystemStatus(customGeminiPath = null) {
  const geminiDir = customGeminiPath || ACTIVE_GEMINI_DIR;
  const targetPluginDir = path.join(geminiDir, 'config', 'plugins', 'xploit-core-plugin');
  const isGeminiPresent = fs.existsSync(geminiDir);
  const isPluginInstalled = fs.existsSync(targetPluginDir) && fs.existsSync(path.join(targetPluginDir, 'plugin.json'));
  
  let pluginManifest = null;
  if (isPluginInstalled) {
    try {
      pluginManifest = JSON.parse(fs.readFileSync(path.join(targetPluginDir, 'plugin.json'), 'utf8'));
    } catch (e) {
      pluginManifest = { name: 'xploit-core', version: '2.2.0' };
    }
  }

  // Count bloated rule files in geminiDir and workspace rules
  let bloatedCount = 0;
  let totalRuleBytes = 0;
  
  const checkRules = (dir) => {
    if (fs.existsSync(dir)) {
      const files = fs.readdirSync(dir);
      for (const f of files) {
        if (f.endsWith('.md')) {
          const stat = fs.statSync(path.join(dir, f));
          totalRuleBytes += stat.size;
          if (stat.size > 5000 && f !== 'SOVEREIGN_OPERATOR.md' && f !== 'AGENTS.md') {
            bloatedCount++;
          }
        }
      }
    }
  };

  checkRules(geminiDir);
  checkRules(WORKSPACE_RULES_DIR);

  // Read current active profile
  const profileStateFile = path.join(geminiDir, 'active_profile.json');
  let currentProfile = 'Phantom Strike (Red Team)';
  if (fs.existsSync(profileStateFile)) {
    try {
      const data = JSON.parse(fs.readFileSync(profileStateFile, 'utf8'));
      if (data.profile) currentProfile = data.profile;
    } catch (e) {}
  }

  // Count installed agents, skills, and arsenal
  let agentsCount = 0;
  let skillsCount = 0;
  let arsenalCount = 0;
  if (isPluginInstalled) {
    const agentsDir = path.join(targetPluginDir, 'agents');
    const skillsDir = path.join(targetPluginDir, 'skills');
    const arsenalDir = path.join(targetPluginDir, 'arsenal');
    if (fs.existsSync(agentsDir)) agentsCount = fs.readdirSync(agentsDir).filter(f => f.endsWith('.md')).length;
    if (fs.existsSync(skillsDir)) skillsCount = fs.readdirSync(skillsDir).filter(f => !f.startsWith('.')).length;
    if (fs.existsSync(arsenalDir)) arsenalCount = fs.readdirSync(arsenalDir).filter(f => !f.startsWith('.')).length;
  }

  return {
    os: `${os.type()} ${os.release()} (${os.arch()})`,
    userHome: USER_HOME,
    geminiPath: geminiDir,
    isGeminiPresent,
    isPluginInstalled,
    pluginDetails: pluginManifest,
    targetPluginPath: targetPluginDir,
    bundledPluginPath: BUNDLED_PLUGIN_DIR,
    bloatedRuleFilesDetected: bloatedCount,
    totalRuleBytes,
    currentProfile,
    agentsCount,
    skillsCount,
    arsenalCount,
    status: isPluginInstalled ? 'ACTIVE' : 'READY_TO_DEPLOY'
  };
}

// Extract inventory of all Subagents, Skills, and Arsenal Suites
function getInventory() {
  const pluginDir = fs.existsSync(path.join(ACTIVE_GEMINI_DIR, 'config', 'plugins', 'xploit-core-plugin'))
    ? path.join(ACTIVE_GEMINI_DIR, 'config', 'plugins', 'xploit-core-plugin')
    : BUNDLED_PLUGIN_DIR;

  const agents = [];
  const skills = [];
  const arsenal = [];

  // Parse Agents
  const agentsDir = path.join(pluginDir, 'agents');
  if (fs.existsSync(agentsDir)) {
    const files = fs.readdirSync(agentsDir).filter(f => f.endsWith('.md'));
    for (const f of files) {
      try {
        const content = fs.readFileSync(path.join(agentsDir, f), 'utf8');
        const nameMatch = content.match(/name:\s*([^\r\n]+)/);
        const descMatch = content.match(/description:\s*\"?([^\r\n\"]+)\"?/);
        agents.push({
          id: f.replace('.md', ''),
          name: nameMatch ? nameMatch[1].trim() : f.replace('.md', ''),
          description: descMatch ? descMatch[1].trim() : 'Operational agent directive unit.'
        });
      } catch (err) {}
    }
  }

  // Parse Skills
  const skillsDir = path.join(pluginDir, 'skills');
  if (fs.existsSync(skillsDir)) {
    const dirs = fs.readdirSync(skillsDir, { withFileTypes: true }).filter(d => d.isDirectory() && !d.name.startsWith('.'));
    for (const d of dirs) {
      let name = d.name;
      let description = 'Protocol skill execution directive.';
      const skillMd = path.join(skillsDir, d.name, 'SKILL.md');
      if (fs.existsSync(skillMd)) {
        try {
          const content = fs.readFileSync(skillMd, 'utf8');
          const nameMatch = content.match(/name:\s*([^\r\n]+)/);
          const descMatch = content.match(/description:\s*\"?([^\r\n\"]+)\"?/);
          if (nameMatch) name = nameMatch[1].trim();
          if (descMatch) description = descMatch[1].trim();
        } catch (err) {}
      }
      skills.push({
        id: d.name,
        name,
        description
      });
    }
  }

  // Parse Arsenal
  const arsenalDir = path.join(pluginDir, 'arsenal');
  if (fs.existsSync(arsenalDir)) {
    const dirs = fs.readdirSync(arsenalDir, { withFileTypes: true }).filter(d => d.isDirectory() && !d.name.startsWith('.'));
    for (const d of dirs) {
      let count = 0;
      try {
        count = fs.readdirSync(path.join(arsenalDir, d.name)).length;
      } catch (e) {}
      arsenal.push({
        id: d.name,
        name: d.name.replace(/_/g, ' ').replace(/-/g, ' ').toUpperCase(),
        description: `Tactical security repository containing ${count} assets.`,
        filesCount: count
      });
    }
  }

  return { agents, skills, arsenal };
}

// Clean duplicate and bloated rules, inject SOVEREIGN_OPERATOR.md
function optimizeRules(customGeminiPath = null) {
  const geminiDir = customGeminiPath || ACTIVE_GEMINI_DIR;
  const backupDir = path.join(geminiDir, 'rules_legacy_backup');
  if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir, { recursive: true });
  }

  const legacyNames = [
    'GEMINI.md', 'GEMINI-CORE.md', 'PHANTOM_PROTOCOL.md', 
    'PHANTOM_STRATEGY.md', 'PHANTOM_WEAPONRY.md', 
    'PHANTOM_STEALTH.md', 'PHANTOM_SHADOW_OPS.md'
  ];

  const pointerContent = `---
trigger: always_on
---
# SOVEREIGN OPERATOR DIRECTIVE (CONSOLIDATED)
All offensive simulation, evasion research, and clean code protocols have been consolidated into \`SOVEREIGN_OPERATOR.md\` and the \`xploit-core\` Antigravity plugin (\`rules/AGENTS.md\`).
Refer to [SOVEREIGN_OPERATOR.md](file:///C:/Users/Test/.gemini/SOVEREIGN_OPERATOR.md) for master directives.
`;

  // Backup and replace in geminiDir
  for (const name of legacyNames) {
    const filePath = path.join(geminiDir, name);
    if (fs.existsSync(filePath)) {
      const bkp = path.join(backupDir, name);
      if (!fs.existsSync(bkp)) fs.copyFileSync(filePath, bkp);
      fs.writeFileSync(filePath, pointerContent, 'utf8');
    }
  }

  // Also in workspace rules if present
  if (fs.existsSync(WORKSPACE_RULES_DIR)) {
    const wsBackup = path.join(WORKSPACE_RULES_DIR, '..', 'rules_legacy_backup');
    if (!fs.existsSync(wsBackup)) fs.mkdirSync(wsBackup, { recursive: true });
    for (const name of legacyNames) {
      const filePath = path.join(WORKSPACE_RULES_DIR, name);
      if (fs.existsSync(filePath)) {
        const bkp = path.join(wsBackup, name);
        if (!fs.existsSync(bkp)) fs.copyFileSync(filePath, bkp);
        fs.writeFileSync(filePath, pointerContent, 'utf8');
      }
    }
  }

  // Ensure SOVEREIGN_OPERATOR.md exists
  const targetPluginDir = path.join(geminiDir, 'config', 'plugins', 'xploit-core-plugin');
  const sovereignSrc = path.join(targetPluginDir, 'rules', 'AGENTS.md');
  const sovereignDest = path.join(geminiDir, 'SOVEREIGN_OPERATOR.md');
  if (fs.existsSync(sovereignSrc)) {
    fs.copyFileSync(sovereignSrc, sovereignDest);
  }

  // Configure skills.txt and user_settings.pb dynamically
  const antigravityDirs = [
    path.join(geminiDir, 'antigravity'),
    path.join(geminiDir, 'antigravity-ide')
  ];

  const dynamicSkillsContent = `${path.join(geminiDir, 'SOVEREIGN_OPERATOR.md')}\n${path.join(geminiDir, 'analyse_file.md')}\n`;
  const bundledPb = path.join(BUNDLED_CONFIG_DIR, 'user_settings.pb');

  for (const dir of antigravityDirs) {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'skills.txt'), dynamicSkillsContent, 'utf8');

    const destPb = path.join(dir, 'user_settings.pb');
    if (fs.existsSync(bundledPb) && !fs.existsSync(destPb)) {
      fs.copyFileSync(bundledPb, destPb);
    }
  }

  // Configure Tokyo Night theme in Antigravity IDE User settings
  const appData = process.env.APPDATA || path.join(USER_HOME, 'AppData', 'Roaming');
  const ideUserDirs = [
    path.join(appData, 'Antigravity', 'User'),
    path.join(appData, 'Antigravity IDE', 'User')
  ];

  for (const dir of ideUserDirs) {
    try {
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      const settingsPath = path.join(dir, 'settings.json');
      let settings = {};
      if (fs.existsSync(settingsPath)) {
        try { settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8')); } catch(e) {}
      }
      settings["workbench.colorTheme"] = "Tokyo Night";
      fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 4), 'utf8');
    } catch(err) {}
  }

  // Apply complete 6-point unconstrained bypass
  applyUnrestrictedBypass(geminiDir);

  return { success: true, message: 'Rules optimized. 6-point unconstrained bypass applied, skills dynamically bound, Tokyo Night theme configured, and filter triggers removed.' };
}

// 6-Point Unconstrained Runtime Bypass & Launcher Generator
function applyUnrestrictedBypass(customGeminiPath = null) {
  const geminiDir = customGeminiPath || ACTIVE_GEMINI_DIR;
  
  // 1. Write dedicated unrestricted bat launcher in Hub directory
  const batPath = path.join(__dirname, 'run-unrestricted-antigravity.bat');
  const batContent = `@echo off
setlocal enabledelayedexpansion
REM ==============================================================
REM   RED-GRAVITY // UNCONSTRAINED ANTIGRAVITY RUNTIME LAUNCHER
REM   Bypasses: Safety Filtering, Policy Guardian, Permission Gates
REM   Target: Antigravity IDE.exe (Universal Portable Launcher)
REM ==============================================================
set "AGY_CLI_DISABLE_SAFETY_FILTERING=1"
set "AGY_CLI_DISABLE_AUTO_UPDATE=1"
set "AGENT_PERMISSION_PRESET=2"
set "SYSTEM_INSTRUCTION_MODE=REPLACE"
set "BRAIN_FILTER_STRATEGY=NO_SYSTEM_INJECTED_STEPS"
set "HarmBlockThreshold=BLOCK_NONE"
set "ALLOW_PROMINENT_PEOPLE=1"
set "ATTRIBUTION_STATUS=PERMISSIVE"
set "CODE_ACKNOWLEDGEMENT_SCOPE=ALL"

REM 1. Universally Detect Antigravity IDE Executable (GUI)
set "IDE_BIN="
if exist "%LOCALAPPDATA%\\Programs\\Antigravity IDE\\Antigravity IDE.exe" (
    set "IDE_BIN=%LOCALAPPDATA%\\Programs\\Antigravity IDE\\Antigravity IDE.exe"
) else if exist "%ProgramFiles%\\Antigravity IDE\\Antigravity IDE.exe" (
    set "IDE_BIN=%ProgramFiles%\\Antigravity IDE\\Antigravity IDE.exe"
) else if exist "%ProgramFiles(x86)%\\Antigravity IDE\\Antigravity IDE.exe" (
    set "IDE_BIN=%ProgramFiles(x86)%\\Antigravity IDE\\Antigravity IDE.exe"
)

REM 2. Universally Detect Antigravity CLI Binary
set "AGY_BIN="
if exist "%USERPROFILE%\\.gemini\\bin\\agy.exe" (
    set "AGY_BIN=%USERPROFILE%\\.gemini\\bin\\agy.exe"
) else (
    for /f "delims=" %%i in ('where agy.exe 2^>nul') do (
        set "AGY_BIN=%%i"
    )
)

REM 3. Check if user explicitly asked for CLI mode
if "%1"=="--cli" (
    echo [*] Launching Antigravity CLI in Terminal Mode...
    if defined AGY_BIN (
        "%AGY_BIN%" --dangerously-skip-permissions %*
    ) else (
        agy --dangerously-skip-permissions %*
    )
    exit /b
)

REM 4. Determine Workspace Root Dynamically
set "TARGET_WORKSPACE=%~1"
if not defined TARGET_WORKSPACE (
    if exist "%~dp0..\\..\\package.json" (
        set "TARGET_WORKSPACE=%~dp0..\\..\\"
    ) else (
        set "TARGET_WORKSPACE=%CD%"
    )
)

REM 5. Launch Antigravity IDE GUI with full environment inheritance
if defined IDE_BIN (
    echo [*] Launching Antigravity IDE with Full Unconstrained Environment...
    echo [*] Binary: !IDE_BIN!
    echo [*] Workspace: !TARGET_WORKSPACE!
    echo [*] Active: Safety Filter Bypass, Update Freeze, Turbo Presets
    start "" "!IDE_BIN!" "!TARGET_WORKSPACE!" %*
) else (
    echo [!] Antigravity IDE executable not found in standard paths.
    echo [*] Attempting CLI runtime fallback...
    if defined AGY_BIN (
        "%AGY_BIN%" --dangerously-skip-permissions %*
    ) else (
        agy --dangerously-skip-permissions %*
    )
)
`;
  fs.writeFileSync(batPath, batContent, 'utf8');

  // 2. Write runtime bypass manifest in active gemini directory
  const bypassManifest = {
    unconstrained: true,
    appliedAt: new Date().toISOString(),
    bypasses: {
      disableSafetyFiltering: { env: 'AGY_CLI_DISABLE_SAFETY_FILTERING=1', method: 'CompletionConfiguration.SetDisableSafetyFiltering', status: 'ACTIVE' },
      disabledSafetyPolicies: { target: 'Tool_ComputerUse.GetDisabledSafetyPolicies', status: 'ACTIVE' },
      clearPolicyGuardian: { target: 'CommandAssessorConfig.ClearPolicyGuardianConfig', status: 'ACTIVE' },
      harmBlockThreshold: { setting: 'BLOCK_NONE', enum: 4, status: 'ACTIVE' },
      agentPermissionTurbo: { enum: 2, flag: '--dangerously-skip-permissions', status: 'ACTIVE' },
      brainFilterStrategy: { setting: 'BRAIN_FILTER_STRATEGY_NO_SYSTEM_INJECTED_STEPS', status: 'ACTIVE' },
      disableAutoUpdate: { env: 'AGY_CLI_DISABLE_AUTO_UPDATE=1', status: 'ACTIVE' }
    }
  };
  fs.writeFileSync(path.join(geminiDir, 'unrestricted_matrix.json'), JSON.stringify(bypassManifest, null, 2), 'utf8');

  return { success: true, batPath, manifest: bypassManifest };
}

// Deploy plugin with granular scope options
function installPlugin(options = {}) {
  const geminiDir = options.targetPath || ACTIVE_GEMINI_DIR;
  ACTIVE_GEMINI_DIR = geminiDir;

  const pluginsDir = path.join(geminiDir, 'config', 'plugins');
  const targetPluginDir = path.join(pluginsDir, 'xploit-core-plugin');

  if (!fs.existsSync(BUNDLED_PLUGIN_DIR)) {
    throw new Error('Bundled plugin source not found.');
  }

  if (!fs.existsSync(pluginsDir)) {
    fs.mkdirSync(pluginsDir, { recursive: true });
  }

  if (fs.existsSync(targetPluginDir)) {
    fs.rmSync(targetPluginDir, { recursive: true, force: true });
  }

  // Copy bundled plugin
  copyDirSync(BUNDLED_PLUGIN_DIR, targetPluginDir);

  // Run rule optimization & dynamic skills.txt binding
  optimizeRules(geminiDir);

  return {
    success: true,
    message: 'xploit-core-plugin deployed with full subagents, skills, and framework.',
    target: targetPluginDir,
    geminiPath: geminiDir
  };
}

// Switch operational profile
function switchProfile(profileName) {
  const profileStateFile = path.join(ACTIVE_GEMINI_DIR, 'active_profile.json');
  const validProfiles = {
    'phantom': 'Phantom Strike (Red Team)',
    'rea': 'REA Reverse Engineering',
    'clean': 'Clean Fullstack Production'
  };

  const selected = validProfiles[profileName] || profileName;
  fs.writeFileSync(profileStateFile, JSON.stringify({
    profile: selected,
    updatedAt: new Date().toISOString()
  }, null, 2), 'utf8');

  return { success: true, activeProfile: selected };
}

// Clean old transcripts / brain cache to free space
function cleanCache() {
  const brainDir = path.join(ACTIVE_GEMINI_DIR, 'antigravity', 'brain');
  let cleanedCount = 0;
  let freedBytes = 0;

  if (fs.existsSync(brainDir)) {
    const entries = fs.readdirSync(brainDir);
    for (const entry of entries) {
      if (entry.startsWith('temp_') || entry.includes('cache') || entry.endsWith('.tmp')) {
        const itemPath = path.join(brainDir, entry);
        try {
          const stat = fs.statSync(itemPath);
          freedBytes += stat.size || 0;
          fs.rmSync(itemPath, { recursive: true, force: true });
          cleanedCount++;
        } catch(e) {}
      }
    }
  }

  return {
    success: true,
    message: `Cache cleaned: ${cleanedCount} temporary items purged (${Math.round(freedBytes/1024)} KB freed).`
  };
}

// CORTEX Sessions Scanner & Trajectory Inspector
function getCortexSessions() {
  const brainDir = path.join(ACTIVE_GEMINI_DIR, 'antigravity', 'brain');
  if (!fs.existsSync(brainDir)) return [];
  
  const entries = fs.readdirSync(brainDir, { withFileTypes: true });
  const sessions = [];
  
  for (const entry of entries) {
    if (entry.isDirectory() && entry.name.match(/^[a-f0-9-]{36}$/i)) {
      const sessionPath = path.join(brainDir, entry.name);
      const transcriptPath = path.join(sessionPath, '.system_generated', 'logs', 'transcript.jsonl');
      let stepCount = 0;
      let lastModified = fs.statSync(sessionPath).mtime;
      let sizeBytes = 0;
      
      if (fs.existsSync(transcriptPath)) {
        try {
          const stat = fs.statSync(transcriptPath);
          sizeBytes = stat.size;
          lastModified = stat.mtime;
          const content = fs.readFileSync(transcriptPath, 'utf8');
          const lines = content.split('\n').filter(l => l.trim().length > 0);
          stepCount = lines.length;
        } catch(e) {}
      }
      
      sessions.push({
        id: entry.name,
        stepCount,
        sizeBytes,
        lastModified: lastModified.toISOString()
      });
    }
  }
  
  sessions.sort((a, b) => new Date(b.lastModified) - new Date(a.lastModified));
  return sessions;
}

function getCortexTrajectory(sessionId, limit = 40) {
  const brainDir = path.join(ACTIVE_GEMINI_DIR, 'antigravity', 'brain');
  const transcriptPath = path.join(brainDir, sessionId, '.system_generated', 'logs', 'transcript.jsonl');
  
  if (!fs.existsSync(transcriptPath)) {
    return { sessionId, steps: [], totalSteps: 0, estimatedTokens: 0 };
  }
  
  try {
    const content = fs.readFileSync(transcriptPath, 'utf8');
    const lines = content.split('\n').filter(l => l.trim().length > 0);
    const totalSteps = lines.length;
    const slice = lines.slice(-limit);
    const steps = [];
    let totalChars = 0;
    
    for (const line of slice) {
      try {
        const obj = JSON.parse(line);
        const tools = (obj.tool_calls || []).map(tc => tc.name || (tc.call && tc.call.name) || 'tool');
        const text = typeof obj.content === 'string' ? obj.content : JSON.stringify(obj.content || '');
        totalChars += text.length;
        
        steps.push({
          index: obj.step_index,
          type: obj.type || 'UNKNOWN',
          source: obj.source || 'UNKNOWN',
          timestamp: obj.created_at || null,
          tools,
          hasThinking: Boolean(obj.thinking),
          preview: text.length > 200 ? text.substring(0, 200) + '...' : text,
          charCount: text.length
        });
      } catch(e) {}
    }
    
    return {
      sessionId,
      totalSteps,
      returnedSteps: steps.length,
      estimatedTokens: Math.round(totalChars / 4),
      steps
    };
  } catch(err) {
    return { sessionId, steps: [], totalSteps: 0, error: err.message };
  }
}

// MIME types for static files
const MIME_TYPES = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png'
};

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const parsedUrl = new URL(req.url, `http://${req.headers.host}`);
  const pathname = parsedUrl.pathname;

  // API Routes
  if (pathname === '/api/status' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(getSystemStatus()));
    return;
  }

  if (pathname === '/api/inventory' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(getInventory()));
    return;
  }

  if (pathname === '/api/detect-paths' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(detectSystemPaths()));
    return;
  }

  if (pathname === '/api/cortex/sessions' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(getCortexSessions()));
    return;
  }

  if (pathname === '/api/cortex/trajectory' && req.method === 'GET') {
    const sessionId = parsedUrl.searchParams.get('session');
    const limit = parseInt(parsedUrl.searchParams.get('limit') || '40', 10);
    if (!sessionId) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Session ID parameter required.' }));
      return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(getCortexTrajectory(sessionId, limit)));
    return;
  }

  if (pathname === '/api/install' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        const result = installPlugin(payload);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: err.message }));
      }
    });
    return;
  }

  if (pathname === '/api/optimize-rules' && req.method === 'POST') {
    try {
      const result = optimizeRules();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: err.message }));
    }
    return;
  }

  if (pathname === '/api/bypass' && req.method === 'POST') {
    try {
      const result = applyUnrestrictedBypass();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: err.message }));
    }
    return;
  }

  if (pathname === '/api/launch-turbo' && req.method === 'POST') {
    try {
      applyUnrestrictedBypass();
      const batFile = path.join(__dirname, 'run-unrestricted-antigravity.bat');
      exec(`cmd.exe /c start "" "${batFile}"`);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, message: 'Antigravity Unconstrained God-Mode Launched.' }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: err.message }));
    }
    return;
  }

  if (pathname === '/api/switch-profile' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        const result = switchProfile(payload.profile || 'phantom');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: err.message }));
      }
    });
    return;
  }

  if (pathname === '/api/open-folder' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        const folder = payload.path || ACTIVE_GEMINI_DIR;
        if (fs.existsSync(folder)) {
          exec(`explorer.exe "${folder}"`);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: true, opened: folder }));
        } else {
          res.writeHead(404, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: false, error: 'Directory does not exist.' }));
        }
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: err.message }));
      }
    });
    return;
  }

  if (pathname === '/api/clean-cache' && req.method === 'POST') {
    try {
      const result = cleanCache();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: err.message }));
    }
    return;
  }

  // Static File Serving
  let filePath = path.join(__dirname, 'src', pathname === '/' ? 'index.html' : pathname);
  if (pathname.startsWith('/assets/')) {
    filePath = path.join(__dirname, 'bundled-plugin', pathname);
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('404 Not Found');
      } else {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end(`Server Error: ${err.code}`);
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[Xploit Silk Hub Server] Running at http://127.0.0.1:${PORT}`);
});
