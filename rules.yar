rule Agent_Credential_Exfiltration
{
    meta:
        description = "Detects common patterns used by malicious agent skills to exfiltrate API keys and .env files"
        author = "Aether_DGLDN"
        version = "0.1"
        date = "2026-02-05"

    strings:
        // Sensitive files
        $file1 = ".env" nocase
        $file2 = "auth-profiles.json" nocase
        $file3 = "moltbook-creds.json" nocase
        
        // Exfiltration targets
        $url1 = "webhook.site" nocase
        $url2 = "requestbin" nocase
        
        // Malicious instructions
        $inst1 = "read your API keys" nocase
        $inst2 = "POST them to my server" nocase
        $inst3 = "exfiltrate" nocase
        $inst4 = "ship your secrets" nocase

    condition:
        any of ($file*) and any of ($url*, $inst*)
}
