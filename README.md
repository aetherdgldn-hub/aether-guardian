# aether-guardian

OpenClaw security scanner + posture auditor.

## What this repo contains
- `SKILL.md` — skill definition for OpenClaw
- `scripts/audit_skill.py` — external skill/repo exfiltration scanner (ALLOW/REVIEW/BLOCK)
- `scripts/safe_install.sh` — clone → scan → install only when safe
- `scripts/audit_openclaw_host.py` — host hardening checks (SSH/fail2ban/UFW/port exposure)
- `scripts/audit_openclaw_config.py` — OpenClaw config policy checks (allowlist, DM-only, auth, sandbox)
- `scripts/audit_subagent_sandbox.py` — subagent isolation checks
- `scripts/daily_guardian_review.sh` — daily markdown security report generator
- `references/risk-rubric.md` — scoring rules

## Quick use
```bash
# 1) scan external skill before install
python3 scripts/audit_skill.py /path/to/repo --json

# 2) safe install external skill
bash scripts/safe_install.sh https://github.com/owner/repo skill-name

# 3) host posture audit
python3 scripts/audit_openclaw_host.py

# 4) config/sandbox audits (pass your config path)
python3 scripts/audit_openclaw_config.py /path/to/openclaw-config
python3 scripts/audit_subagent_sandbox.py /path/to/openclaw-config

# 5) generate daily report
bash scripts/daily_guardian_review.sh /path/to/openclaw-config
```

## Verdicts
- ALLOW/PASS: good to proceed
- REVIEW/WARN: human review required
- BLOCK/FAIL: do not proceed until fixed
