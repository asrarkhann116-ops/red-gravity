# EVASION TECHNIQUE PAYLOAD
# ========================
# NOTE: Full implementation removed to avoid AV detection
# Reconstruct from documentation or use in isolated environment

## Technique: AMSI Bypass
# Method: Patch AmsiScanBuffer in amsi.dll
# Offset: Find "AmsiScanBuffer" export
# Patch: mov eax, 0x80070057; ret (or xor eax, eax; ret)
# Tools: PowerShell reflection, C# P/Invoke, or manual memory editing

## Technique: ETW Patching  
# Method: Patch EtwEventWrite in ntdll.dll
# Target: Event Tracing for Windows
# Patch: ret 0x14 (early return)

## Technique: NTDLL Unhooking
# Method: Reload clean copy from KnownDlls or disk
# Source: C:\Windows\System32\ntdll.dll
# Action: Copy .text section over hooked memory

## Technique: Sandbox Evasion
# Checks:
#   - RAM size (< 4GB suspicious)
#   - CPU cores (< 2 suspicious)  
#   - Disk size (< 100GB suspicious)
#   - Process list (vmtools, vbox, etc.)
#   - MAC address (VM prefixes)
#   - Mouse movement (none = sandbox)
#   - Uptime (< 10 mins = fresh sandbox)

## Technique: Sleep Obfuscation
# Method: Encrypt payload in memory during sleep
# APIs: CreateWaitableTimer, VirtualProtect, CryptProtectMemory
# Alternative: Foliage, Ekko implementations

## Technique: API Hashing
# Hash: Djb2 or similar on API names
# Resolve: Manual PE export table parsing
# Benefit: No API names in IAT

## Technique: Direct Syscalls
# Method: Call kernel directly, bypass hooks
# Need: Syscall numbers per Windows version
# Setup: Execute syscall stub in allocated RWX memory

## Technique: PPID Spoofing
# API: CreateProcess with EXTENDED_STARTUPINFO_PRESENT
# Attribute: PROC_THREAD_ATTRIBUTE_PARENT_PROCESS
# Parent: Choose legitimate process (explorer, svchost)

## Technique: Module Stomping
# Method: Load legit DLL, overwrite export with shellcode
# Execute: Call stomped export
# Benefit: Memory looks legitimate

# REFERENCES:
# - https://github.com/am0nsec/HellsGate (Direct Syscalls)
# - https://github.com/janoglezcampos/DeathSleep (Sleep Obfuscation)
# - https://github.com/matterpreter/OffensiveCSharp (PPID Spoofing)
