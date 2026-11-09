---
trigger: arsenal_map
---

# ARSENAL MAP - Red Team Weapon Inventory

## Quick Navigation

### Agents (13)
| File | Role |
|------|------|
| `orchestrator.md` | Multi-agent coordination |
| `red-team-web.md` | Web exploitation |
| `red-team-net.md` | Network pentest |
| `exploit-dev.md` | 0day, shellcode, ROP |
| `malware-dev.md` | RATs, rootkits, ransom |
| `social-engineer.md` | Phishing, vishing, OSINT |
| `ad-attacker.md` | AD pwnage, lateral |
| `cloud-attacker.md` | AWS/Azure/GCP, k8s |
| `wireless-attacker.md` | WiFi, BT, RF, SDR |
| `physical-attacker.md` | HID, implants, bypass |
| `discord-attacker.md` | Raidd, nuke, tokens |
| `fraud-specialist.md` | Carding, BIN, checkers |
| `dox-specialist.md` | OSINT, leaks, harass |
| `c2-operator.md` | C2, post-exploitation |

### Skills (19)
See: `.agent/skills/SKILL.md`

### Scripts
| Script | Purpose |
|--------|---------|
| `scripts/redteam_checklist.py` | Pre-op validation |

## Kill Chain Integration
Recon ? Weaponize ? Deliver ? Exploit ? Install ? C2 ? Actions

## Load Order
1. Read `GEMINI-CORE.md` (P0)
2. Read Agent file (P1)
3. Read `SKILL.md` INDEX (P2)
4. Load specific skill section
5. Execute operation
