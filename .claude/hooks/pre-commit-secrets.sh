#!/usr/bin/env bash
# Pre-commit secret detection hook
# Scans staged files for potential secrets before allowing commits

set -euo pipefail

# Patterns that indicate secrets
SECRET_PATTERNS=(
  'AKIA[0-9A-Z]{16}'                    # AWS Access Key
  'AIza[0-9A-Za-z\-_]{35}'              # Google API Key
  'sk-[0-9a-zA-Z]{48}'                  # OpenAI/Stripe Secret Key
  'sk-ant-[0-9a-zA-Z\-]{90,}'           # Anthropic API Key
  'ghp_[0-9a-zA-Z]{36}'                 # GitHub Personal Access Token
  'gho_[0-9a-zA-Z]{36}'                 # GitHub OAuth Token
  'glpat-[0-9a-zA-Z\-_]{20}'            # GitLab PAT
  'xoxb-[0-9]{10,}-[0-9a-zA-Z]{24}'     # Slack Bot Token
  'xoxp-[0-9]{10,}-[0-9a-zA-Z]{24}'     # Slack User Token
  'SG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}' # SendGrid
  'password\s*[:=]\s*["\x27][^"\x27]{8,}'       # Hardcoded passwords
  'secret\s*[:=]\s*["\x27][^"\x27]{8,}'         # Hardcoded secrets
  'api[_-]?key\s*[:=]\s*["\x27][^"\x27]{8,}'    # API keys
  'private[_-]?key\s*[:=]\s*["\x27]'            # Private keys
  'BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY'       # PEM private keys
)

# Files to always skip
SKIP_EXTENSIONS='\.lock$|\.min\.js$|\.min\.css$|\.map$|\.png$|\.jpg$|\.gif$|\.ico$|\.woff'

# Get the tool input (file being committed) from environment or stdin
INPUT="${TOOL_INPUT:-}"

FOUND_SECRETS=0

# Check if we're in a git context
if command -v git &>/dev/null && git rev-parse --git-dir &>/dev/null 2>&1; then
  # Scan staged files
  STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || echo "")

  for file in $STAGED_FILES; do
    # Skip binary and lock files
    if echo "$file" | grep -qE "$SKIP_EXTENSIONS"; then
      continue
    fi

    # Skip if file doesn't exist
    [ -f "$file" ] || continue

    for pattern in "${SECRET_PATTERNS[@]}"; do
      if grep -qEi "$pattern" "$file" 2>/dev/null; then
        echo "SECRET DETECTED in $file matching pattern: $pattern" >&2
        FOUND_SECRETS=1
      fi
    done
  done
fi

# Also check the current tool input if provided
if [ -n "$INPUT" ]; then
  for pattern in "${SECRET_PATTERNS[@]}"; do
    if echo "$INPUT" | grep -qEi "$pattern" 2>/dev/null; then
      echo "SECRET DETECTED in tool input matching pattern: $pattern" >&2
      FOUND_SECRETS=1
    fi
  done
fi

if [ "$FOUND_SECRETS" -eq 1 ]; then
  echo "BLOCKED: Potential secrets found. Remove them before committing." >&2
  exit 2
fi

exit 0
