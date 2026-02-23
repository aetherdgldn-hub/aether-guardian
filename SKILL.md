---
name: skill-guardian
description: Audit third-party or local AgentSkills/repositories for secret-exfiltration and suspicious behavior before installation. Use when a user asks to install/import a skill from any external source, GitHub repo, zip, or unknown author, and when deciding allow/review/block risk.
---

# Skill Guardian

Run a pre-install security audit before installing any external skill.

## Workflow

1. Clone or open the candidate skill/repo in a temporary/local folder.
2. Run:
   - `python3 skills/skill-guardian/scripts/audit_skill.py <path>`
   - Use `--json` when machine-readable output is needed.
3. Decide by verdict:
   - `ALLOW`: safe to continue install.
   - `REVIEW`: pause install, show findings, ask user for confirmation.
   - `BLOCK`: refuse install by default; require explicit user override.
4. Report top findings with file + line snippets.
5. If user overrides a `REVIEW`/`BLOCK`, proceed but clearly mark risk accepted.

## Non-Negotiables

- Never auto-install external skills without running this audit first.
- Never hide findings.
- Prefer false-positive review over false-negative compromise.

## Safe Install Command

Use:
- `bash skills/skill-guardian/scripts/safe_install.sh <repo-url> [dest-name]`

Behavior:
- ALLOW => installs into `skills/imported/<dest-name>`
- REVIEW => stops unless `--allow-review`
- BLOCK => stops unless `--allow-block`

Examples:
- `bash skills/skill-guardian/scripts/safe_install.sh https://github.com/peterskoett/self-improving-agent`
- `bash skills/skill-guardian/scripts/safe_install.sh <repo> my-skill-name --allow-review`

## Resources

- Scanner script: `scripts/audit_skill.py`
- Safe installer: `scripts/safe_install.sh`
- Risk rubric: `references/risk-rubric.md`
