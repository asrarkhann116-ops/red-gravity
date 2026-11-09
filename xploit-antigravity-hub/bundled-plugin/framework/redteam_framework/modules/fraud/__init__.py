"""
The Forge — Fraud Module
Functions: Credit Card BIN Checking and format validation 
"""
import urllib.request
import json
import re

def register(registry):
    registry.register("fraud_ops", FraudOps, metadata={
        "description": "Financial Operations & Drop mgmt",
        "author": "The Forge API"
    })

class FraudOps:
    def check_bin(self, bin_number):
        """Fetch BIN data via public lookup API"""
        # Validate format
        if not re.match(r"^[0-9]{6,8}$", str(bin_number)):
            return "[-] Error: Invalid BIN format. Require first 6-8 digits of card."
            
        try:
            req = urllib.request.Request(f"https://lookup.binlist.net/{bin_number}", headers={"Accept-Version": "3"})
            res = urllib.request.urlopen(req, timeout=10)
            data = json.loads(res.read())
            
            return {
                "status": "[+] Success",
                "scheme": data.get("scheme"),
                "type": data.get("type"),
                "brand": data.get("brand"),
                "bank": data.get("bank", {}).get("name"),
                "country": data.get("country", {}).get("name")
            }
        except Exception as e:
            return f"[-] BIN Lookup Failed: {e}"
