# RED TEAM FRAMEWORK CORE
# ======================

## Architecture
```
redteam_framework/
├── core/           # Framework engine
├── modules/        # Attack modules
├── payloads/       # Weaponized code
├── config/         # Operation configs
├── logs/           # Operational logs
└── utils/          # Helper utilities
```

## Core Components

### engine.py
Main execution engine. Coordinates modules, handles state management.

### stealth.py
Evasion core. Implements:
- AMSI/ETW bypass loading
- Sandbox detection
- Sleep obfuscation
- API hashing
- Direct syscalls

### c2_hub.py
Multi-channel command & control:
- HTTP/S beaconing
- DNS tunneling
- SMB named pipes
- Discord/Telegram
- GitHub gists

### crypto.py
Operational cryptography:
- Payload encryption
- C2 traffic encryption
- File obfuscation
- Key management

## Module System
Dynamic loading of attack modules based on operation phase.
