"""
The Forge — OSINT Module
Functions: General target foot-printing (Whois, DNS, Geolocation)
"""
import socket
import urllib.request
import json

def register(registry):
    registry.register("osint_recon", OsintRecon, metadata={
        "description": "General domain footprinting, IP intel.",
        "author": "The Forge API"
    })

class OsintRecon:
    def geolocate_ip(self, ip_address):
        """Perform simple IP geolocation using public API"""
        try:
            # Ensure it resolves if a domain is passed
            ip = socket.gethostbyname(ip_address)
            req = urllib.request.Request(f"http://ip-api.com/json/{ip}")
            res = urllib.request.urlopen(req, timeout=5)
            data = json.loads(res.read())
            if data["status"] == "success":
                return f"[+] Target Loc: {data['city']}, {data['country']} (ISP: {data['isp']})"
            return "[-] Lookup failed."
        except Exception as e:
            return f"[-] Geolocate Error: {e}"

    def port_scan_light(self, target, ports=[21,22,80,443,445,3389]):
        """Perform a quick SYN sweep alternative (connect scan) on top ports"""
        open_ports = []
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex((socket.gethostbyname(target), port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        return f"[+] Open Ports on {target}: {open_ports}"
