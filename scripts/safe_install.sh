#!/usr/bin/env bash
set -euo pipefail

# safe-install: clone -> scan -> install only if allowed (or explicit override)
# Usage:
#   safe_install.sh <repo-url> [dest-name]
#   safe_install.sh <repo-url> [dest-name] --allow-review
#   safe_install.sh <repo-url> [dest-name] --allow-review --allow-block

ROOT="/home/hex/.openclaw/workspace"
SCANNER="$ROOT/skills/skill-guardian/scripts/audit_skill.py"
SKILLS_DIR="$ROOT/skills/imported"
TMP_BASE="$ROOT/.tmp/skill-guardian"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <repo-url> [dest-name] [--allow-review] [--allow-block]"
  exit 64
fi

REPO_URL="$1"
shift || true

DEST_NAME=""
ALLOW_REVIEW=0
ALLOW_BLOCK=0

for arg in "$@"; do
  case "$arg" in
    --allow-review) ALLOW_REVIEW=1 ;;
    --allow-block) ALLOW_BLOCK=1 ;;
    *)
      if [[ -z "$DEST_NAME" ]]; then
        DEST_NAME="$arg"
      else
        echo "Unknown extra argument: $arg"
        exit 64
      fi
      ;;
  esac
done

if [[ -z "$DEST_NAME" ]]; then
  base="$(basename "$REPO_URL")"
  DEST_NAME="${base%.git}"
fi

mkdir -p "$TMP_BASE" "$SKILLS_DIR"
WORK_DIR="$(mktemp -d "$TMP_BASE/scan-XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

TARGET_CLONE="$WORK_DIR/repo"
echo "[1/4] Cloning $REPO_URL"
git clone --depth 1 "$REPO_URL" "$TARGET_CLONE" >/dev/null 2>&1 || {
  echo "Clone failed for: $REPO_URL"
  exit 1
}

echo "[2/4] Scanning repo"
SCAN_JSON="$WORK_DIR/scan.json"
python3 "$SCANNER" "$TARGET_CLONE" --json > "$SCAN_JSON"
VERDICT="$(python3 -c "import json;print(json.load(open('$SCAN_JSON'))['verdict'])")"
SCORE="$(python3 -c "import json;print(json.load(open('$SCAN_JSON'))['score'])")"

echo "Scan verdict: $VERDICT (score $SCORE)"

if [[ "$VERDICT" == "BLOCK" && "$ALLOW_BLOCK" -ne 1 ]]; then
  echo "[3/4] Install denied: BLOCK verdict."
  echo "Use --allow-block only if you explicitly accept high risk."
  cat "$SCAN_JSON"
  exit 2
fi

if [[ "$VERDICT" == "REVIEW" && "$ALLOW_REVIEW" -ne 1 ]]; then
  echo "[3/4] Install paused: REVIEW verdict."
  echo "Use --allow-review to proceed with accepted risk."
  cat "$SCAN_JSON"
  exit 1
fi

DEST_PATH="$SKILLS_DIR/$DEST_NAME"
if [[ -e "$DEST_PATH" ]]; then
  echo "Destination already exists: $DEST_PATH"
  exit 1
fi

echo "[3/4] Verdict accepted. Installing to $DEST_PATH"
mkdir -p "$DEST_PATH"
cp -a "$TARGET_CLONE"/. "$DEST_PATH"/

# basic safety cleanup
rm -rf "$DEST_PATH/.git"

echo "[4/4] Installed successfully"
echo "Installed path: $DEST_PATH"
echo "Verdict: $VERDICT"
echo "Score: $SCORE"
