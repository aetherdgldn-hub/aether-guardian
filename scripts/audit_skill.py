#!/usr/bin/env python3
import argparse
import json
import os
import re
from pathlib import Path

CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".sh", ".mjs", ".cjs", ".bash", ""}
TEXT_EXTS = CODE_EXTS | {".md", ".txt", ".json", ".yaml", ".yml", ".env"}
IGNORE_DIRS = {".git", "node_modules", ".next", "dist", "build", "venv", ".venv", "__pycache__"}

# Tight patterns: avoid generic words like "token" alone.
PATTERNS = [
    # Secret targeting (explicit file/secret env access)
    ("secret_file_access", re.compile(r"(\.env\b|auth-profiles\.json|credentials?\.json|id_rsa|api[_-]?key\b|secret[_-]?key\b|access[_-]?key\b)" , re.I), 4, "any"),
    ("secret_env_access", re.compile(r"(process\.env\.|os\.environ|getenv\(|ENV\[|dotenv|read_text\(.*\.env|cat\s+\.env\b)", re.I), 4, "code"),

    # Clear exfil intent phrasing
    ("exfil_language", re.compile(r"(\bexfiltrate\b|post\s+.*\b(api[_-]?key|secret|credential)\b|ship\s+your\s+secrets)", re.I), 6, "any"),

    # Suspicious sinks commonly used for leaks
    ("suspicious_sink", re.compile(r"(webhook\.site|requestbin|pastebin|discord\.com/api/webhooks|api\.telegram\.org/bot.+/sendMessage)", re.I), 6, "code"),

    # Outbound data transfer primitives (code only)
    ("network_send", re.compile(r"(curl\s+.*https?://|requests\.(post|put)\(|fetch\(|axios\.(post|put)\(|http\.request\(|https\.request\()", re.I), 3, "code"),

    # Shell/process execution primitives (code only)
    ("command_exec", re.compile(r"(os\.system\(|subprocess\.(run|Popen|call)\(|child_process\.(exec|spawn)\(|\bexec\(|\bspawn\()", re.I), 2, "code"),

    # Persistence / stealth hints (code only)
    ("persistence_hint", re.compile(r"(crontab\b|/etc/cron|startup\s+folder|autorun\b|launchctl\b|systemd\b)", re.I), 3, "code"),
]


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() in TEXT_EXTS:
                yield p


def read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def is_code(path: Path) -> bool:
    return path.suffix.lower() in CODE_EXTS


def audit(root: Path):
    findings = []
    score = 0

    for file in iter_files(root):
        text = read_text(file)
        if not text:
            continue

        file_is_code = is_code(file)
        lines = text.splitlines()

        for idx, line in enumerate(lines, start=1):
            # avoid self-signature false positives from regex declaration lines
            if "re.compile(" in line:
                continue
            for rule_name, regex, weight, scope in PATTERNS:
                if scope == "code" and not file_is_code:
                    continue
                if regex.search(line):
                    findings.append({
                        "rule": rule_name,
                        "weight": weight,
                        "file": str(file),
                        "line": idx,
                        "snippet": line.strip()[:220],
                    })
                    score += weight

    rules_hit = {f["rule"] for f in findings}
    # Escalation: secret access + outbound send/sink/intent is highly suspicious
    if ({"secret_file_access", "secret_env_access"} & rules_hit) and ({"network_send", "suspicious_sink", "exfil_language"} & rules_hit):
        score += 12
        findings.append({
            "rule": "combined_secret_and_send",
            "weight": 12,
            "file": str(root),
            "line": 0,
            "snippet": "Secret-access indicators combined with outbound transfer behavior.",
        })

    if score >= 20:
        verdict = "BLOCK"
    elif score >= 8:
        verdict = "REVIEW"
    else:
        verdict = "ALLOW"

    return {
        "target": str(root),
        "score": score,
        "verdict": verdict,
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit a skill/repo directory for exfiltration risk.")
    parser.add_argument("path", help="Path to skill or repo directory")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    result = audit(root)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Target : {result['target']}")
        print(f"Score  : {result['score']}")
        print(f"Verdict: {result['verdict']}")
        print("Findings:")
        if not result["findings"]:
            print("  - none")
        else:
            for f in result["findings"][:80]:
                loc = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
                print(f"  - [{f['rule']}] ({f['weight']}) {loc}")
                print(f"    {f['snippet']}")

    # exit code contract:
    # 0 = allow, 1 = review, 2 = block
    if result["verdict"] == "REVIEW":
        raise SystemExit(1)
    if result["verdict"] == "BLOCK":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
