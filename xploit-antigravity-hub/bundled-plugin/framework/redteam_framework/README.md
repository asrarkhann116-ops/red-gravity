# RED TEAM FRAMEWORK
# ==================
# Integrated offensive operations platform

## Quick Start
1. Configure: Edit config/operation.ini
2. Load: python core/engine.py --config config/operation.ini
3. Execute: Select module and target
4. Monitor: Check logs/ directory

## Module Loading
```python
from core.engine import Framework
from modules.web import WebExploit

fw = Framework(config="config/operation.ini")
web = fw.load_module("web")
web.scan(target="https://target.com")
```

## Safety Notice
This framework is for authorized red team operations only.
All usage must comply with:
- Rules of Engagement
- Legal authorization
- Ethical boundaries

## Integration
This framework integrates with .agent/ structure:
- Agents: .agent/*.md (operation planning)
- Skills: .agent/skills/*/ (technical capabilities)
- Checklist: .agent/scripts/redteam_checklist.py (pre-op validation)

## Directory Mapping
```
redteam_framework/    → Execution runtime
.agent/               → Planning & methodology
```

## Support
Refer to GEMINI-CORE.md for operational doctrine.
