---
name: rea-reverse-engineering
description: Reverse engineer any app, binary, APK, .NET assembly, website or Electron bundle using the REA framework.
---

# 🛠️ REA: Reverse Engineer Anything (Skill Protocol)

> Framework: `morluto/rea` (`rea-agents`)
> Integration: MCP Server (`rea`) + CLI

---

## 🎯 What REA Does

REA enables AI agents to inspect and reverse-engineer apps, binaries, and websites **without access to source code**:
- **Native Binaries:** Inspect PE/ELF/Mach-O binaries via Ghidra, Hopper, or IDA decompiler hooks.
- **Electron & JS Apps:** Unpack `.asar` archives, decompile bundled scripts, deobfuscate minified JS, and extract hidden APIs/tokens.
- **Android APKs / Resources:** Extract schemas, assets, manifest, string tables, and API endpoints.
- **.NET Assemblies:** Decompile C#/VB .NET binaries to readable source.
- **Web Applications:** Trace network calls, reverse client-side logic, crack dynamic payload encoders.

---

## ⚡ MCP Server Details

Configured in [`.agents/mcp_config.json`](file:///e:/asrar/projects/.agents/mcp_config.json):
```json
"rea": {
  "command": "npx",
  "args": ["-y", "rea-agents@latest", "mcp"],
  "env": {
    "REA_MCP_INPUT_SCHEMA_PROFILE": "compact"
  }
}
```

---

## 🚀 Core Workflows & Direct Commands

If running via CLI / scripts:
```bash
# Setup & Agent Verification
npx rea-agents setup

# Analyze a target binary or directory
npx rea-agents inspect <path-to-target>

# Unpack and inspect an Electron app
npx rea-agents electron unpack <app.asar>
```

---

## 🧠 Methodology for AI Reverse Engineering

1. **Recon:** Identify file type, architecture, packing, obfuscation techniques.
2. **Decompile / Unpack:** Extract resources, bundles, and symbols.
3. **Trace Logic:** Pinpoint target logic (e.g. auth routines, encryption keys, network APIs, license checks).
4. **Recreate / Reconstruct:** Write clean, modular, modern implementation matching target behavior.

---

## 📚 Local Repo References (Full Source Available)

Full `morluto/rea` repo cloned at: `.agents/skills/rea-reverse-engineering/repo/`

Key files to read for deep context:
- **Agent Instructions:** `.agents/skills/rea-reverse-engineering/repo/AGENTS.md`
- **Full Guide:** `.agents/skills/rea-reverse-engineering/repo/README.md`
- **Source Code:** `.agents/skills/rea-reverse-engineering/repo/src/`
- **Bridge Tools (Ghidra/IDA/Hopper):** `.agents/skills/rea-reverse-engineering/repo/bridge/`
- **Native Bindings:** `.agents/skills/rea-reverse-engineering/repo/native/`
- **Docs:** `.agents/skills/rea-reverse-engineering/repo/docs/`
