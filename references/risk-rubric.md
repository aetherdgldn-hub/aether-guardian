# Risk Rubric

## Verdicts

- **ALLOW (score < 8):** No clear exfiltration behavior detected.
- **REVIEW (score 8-17):** Suspicious indicators found; require human confirmation.
- **BLOCK (score >= 18):** High-risk pattern combination; do not install unless explicitly overridden.

## High-Risk Pattern Combo

`secret_file_access` + (`network_send` or `suspicious_sink` or `exfil_language`) => immediate score boost and likely BLOCK.

## Human Override Rules

If user explicitly chooses to proceed:
1. Repeat the specific risky findings.
2. Confirm they accept risk.
3. Continue only for that one target.
