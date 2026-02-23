# aether-guardian

Working OpenClaw skill-security scanner.

## What this repo contains
- `SKILL.md` — skill definition for OpenClaw
- `scripts/audit_skill.py` — exfiltration risk scanner (ALLOW/REVIEW/BLOCK)
- `scripts/safe_install.sh` — clone → scan → install only when safe
- `references/risk-rubric.md` — scoring rules

## Quick use
```bash
python3 scripts/audit_skill.py /path/to/repo --json
bash scripts/safe_install.sh https://github.com/owner/repo skill-name
```

## Verdicts
- ALLOW: install
- REVIEW: require explicit override
- BLOCK: deny by default
