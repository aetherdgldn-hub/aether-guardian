#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


def parse_text(path: Path):
    if not path.exists():
        return ''
    return path.read_text(errors='ignore')


def has_any(text, patterns):
    return any(re.search(p, text, flags=re.I | re.M) for p in patterns)


def audit_config(path: Path):
    txt = parse_text(path)
    if not txt:
        return {'kind': 'openclaw-config-audit', 'verdict': 'FAIL', 'score': 20, 'error': f'config not found: {path}'}

    checks = []

    checks.append({
        'name': 'allowlist_present',
        'ok': has_any(txt, [r'allowlist', r'allowed[_-]?users?', r'authoriz']),
        'weight': 4,
        'detail': 'must restrict who can interact with bot',
    })

    checks.append({
        'name': 'dm_only_or_direct_restriction',
        'ok': has_any(txt, [r'dm[_-]?only', r'direct[_-]?only', r'chat_type.*direct', r'group.*false']),
        'weight': 3,
        'detail': 'avoid group-wide control surface',
    })

    checks.append({
        'name': 'auth_password_present',
        'ok': has_any(txt, [r'auth.*password', r'gateway.*password']),
        'weight': 3,
        'detail': 'set strong auth password',
    })

    checks.append({
        'name': 'non_default_port',
        'ok': not has_any(txt, [r'\b8080\b']),
        'weight': 2,
        'detail': 'avoid default known port',
    })

    checks.append({
        'name': 'subagent_sandbox_declared',
        'ok': has_any(txt, [r'sandbox', r'docker', r'workspace_access', r'network\s*:\s*(none|bridge)']),
        'weight': 4,
        'detail': 'declare subagent isolation controls',
    })

    score = sum(c['weight'] for c in checks if c['ok'] is False)
    verdict = 'PASS' if score < 5 else ('WARN' if score < 12 else 'FAIL')
    failed = [c for c in checks if c['ok'] is False]

    return {
        'kind': 'openclaw-config-audit',
        'target': str(path),
        'verdict': verdict,
        'score': score,
        'checks': checks,
        'failed': failed,
    }


def main():
    ap = argparse.ArgumentParser(description='Audit OpenClaw config posture')
    ap.add_argument('config_path', help='Path to OpenClaw config file (yaml/json/toml)')
    args = ap.parse_args()

    res = audit_config(Path(args.config_path))
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
