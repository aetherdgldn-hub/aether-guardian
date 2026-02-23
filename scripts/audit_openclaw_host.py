#!/usr/bin/env python3
import json
import os
import re
import shutil
import socket
import subprocess
from pathlib import Path


def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 1, str(e)


def check_non_root():
    return os.geteuid() != 0, "running as non-root" if os.geteuid() != 0 else "running as root"


def check_sshd_option(key, expected):
    p = Path('/etc/ssh/sshd_config')
    if not p.exists():
        return None, 'sshd_config not found'
    txt = p.read_text(errors='ignore')
    m = re.findall(rf'^\s*{re.escape(key)}\s+(\S+)', txt, flags=re.M)
    if not m:
        return None, f'{key} not set explicitly'
    val = m[-1].lower()
    ok = val == expected.lower()
    return ok, f'{key}={val}'


def check_service(name):
    rc, out = run(['systemctl', 'is-active', name])
    if rc == 0 and 'active' in out:
        return True, f'{name} active'
    return False, f'{name} not active'


def check_ufw():
    if not shutil.which('ufw'):
        return None, 'ufw not installed'
    rc, out = run(['ufw', 'status'])
    if 'Status: active' in out:
        return True, 'ufw active'
    return False, 'ufw inactive'


def check_open_ports(max_open=12):
    ss = shutil.which('ss')
    if not ss:
        return None, 'ss not available'
    rc, out = run([ss, '-tuln'])
    lines = [x for x in out.splitlines() if 'LISTEN' in x]
    ok = len(lines) <= max_open
    return ok, f'{len(lines)} listening sockets'


def check_default_port_exposed():
    ss = shutil.which('ss')
    if not ss:
        return None, 'ss not available'
    rc, out = run([ss, '-tuln'])
    bad = any(':8080' in ln and '127.0.0.1:8080' not in ln for ln in out.splitlines())
    return (not bad), ('port 8080 publicly bound' if bad else 'no public :8080 binding')


def evaluate(checks):
    score = 0
    findings = []
    for c in checks:
        ok = c['ok']
        if ok is False:
            score += c['weight']
            findings.append(c)
    if score >= 12:
        verdict = 'FAIL'
    elif score >= 5:
        verdict = 'WARN'
    else:
        verdict = 'PASS'
    return verdict, score, findings


def main():
    checks = []

    ok, msg = check_non_root()
    checks.append({'name': 'non_root_runtime', 'ok': ok, 'weight': 4, 'detail': msg})

    ok, msg = check_sshd_option('PasswordAuthentication', 'no')
    checks.append({'name': 'ssh_password_auth_disabled', 'ok': ok, 'weight': 3, 'detail': msg})

    ok, msg = check_sshd_option('PermitRootLogin', 'no')
    checks.append({'name': 'ssh_root_login_disabled', 'ok': ok, 'weight': 3, 'detail': msg})

    ok, msg = check_service('fail2ban')
    checks.append({'name': 'fail2ban_active', 'ok': ok, 'weight': 2, 'detail': msg})

    ok, msg = check_ufw()
    checks.append({'name': 'ufw_active', 'ok': ok, 'weight': 2, 'detail': msg})

    ok, msg = check_open_ports()
    checks.append({'name': 'port_exposure_reasonable', 'ok': ok, 'weight': 2, 'detail': msg})

    ok, msg = check_default_port_exposed()
    checks.append({'name': 'no_public_default_8080', 'ok': ok, 'weight': 4, 'detail': msg})

    verdict, score, findings = evaluate(checks)
    print(json.dumps({
        'kind': 'openclaw-host-audit',
        'verdict': verdict,
        'score': score,
        'checks': checks,
        'failed': findings,
    }, indent=2))


if __name__ == '__main__':
    main()
