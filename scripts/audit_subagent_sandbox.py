#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


def read_text(p: Path):
    try:
        return p.read_text(errors='ignore')
    except Exception:
        return ''


def audit(path: Path):
    txt = read_text(path)
    if not txt:
        return {'kind': 'subagent-sandbox-audit', 'verdict': 'FAIL', 'score': 20, 'error': f'file not found: {path}'}

    checks = [
        {
            'name': 'sandbox_enabled',
            'ok': bool(re.search(r'sandbox|docker', txt, re.I)),
            'weight': 5,
            'detail': 'subagents should run sandboxed',
        },
        {
            'name': 'workspace_access_not_default_rw_everywhere',
            'ok': not bool(re.search(r'workspace_access\s*:\s*rw\b', txt, re.I)),
            'weight': 3,
            'detail': 'prefer none/ro by default',
        },
        {
            'name': 'network_restricted_option_present',
            'ok': bool(re.search(r'network\s*:\s*(none|bridge)', txt, re.I)),
            'weight': 3,
            'detail': 'explicit network policy required',
        },
        {
            'name': 'no_host_secret_mounts',
            'ok': not bool(re.search(r'(\.env|secrets?|credentials?)\s*:\s*/', txt, re.I)),
            'weight': 5,
            'detail': 'avoid mounting host secrets in subagents',
        },
    ]

    score = sum(c['weight'] for c in checks if c['ok'] is False)
    verdict = 'PASS' if score < 5 else ('WARN' if score < 10 else 'FAIL')

    return {
        'kind': 'subagent-sandbox-audit',
        'target': str(path),
        'verdict': verdict,
        'score': score,
        'checks': checks,
        'failed': [c for c in checks if c['ok'] is False],
    }


def main():
    ap = argparse.ArgumentParser(description='Audit subagent sandbox policy from config file')
    ap.add_argument('config_path')
    args = ap.parse_args()
    print(json.dumps(audit(Path(args.config_path)), indent=2))


if __name__ == '__main__':
    main()
