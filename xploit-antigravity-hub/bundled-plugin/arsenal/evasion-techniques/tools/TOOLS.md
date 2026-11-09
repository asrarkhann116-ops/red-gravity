# EVASION TOOLS
# =============

## AMSI Fail
# Purpose: Test if AMSI is active
# Usage: Invoke expression with common malicious signature

## ETW Trace
# Purpose: Check ETW provider status
# Usage: logman query providers

## Hook Check  
# Purpose: Detect user-mode hooks
# Usage: Compare in-memory vs disk NTDLL

## Sandbox Tester
# Purpose: Check environment indicators
# Usage: Run all checks, exit if sandbox detected

## Syscall Resolver
# Purpose: Get syscall numbers dynamically
# Usage: Parse ntdll from disk, extract syscall IDs
