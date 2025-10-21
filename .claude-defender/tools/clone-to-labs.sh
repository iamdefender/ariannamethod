#!/usr/bin/env bash
# Claude Defender → Clone to Labs
# Clone repository to sandbox for consilium evaluation
# Part of Mission #5: Consilium

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <repo_url>"
    echo "Example: $0 https://github.com/user/repo"
    exit 1
fi

REPO_URL=$1
REPO_NAME=$(basename "$REPO_URL" .git)
LAB_DIR="$HOME/ariannamethod/.labs/$REPO_NAME"
TIMESTAMP=$(date --iso-8601=seconds)

echo "🔬 Cloning $REPO_NAME to labs..."

# Create labs directory
mkdir -p "$HOME/ariannamethod/.labs"

# Clone repository (shallow clone to save space)
if [ -d "$LAB_DIR" ]; then
    echo "⚠️  Lab already exists: $LAB_DIR"
    echo "Use: rm -rf $LAB_DIR  to re-clone"
    exit 1
fi

git clone --depth 1 "$REPO_URL" "$LAB_DIR" 2>&1 | head -10

cd "$LAB_DIR"

# Generate security audit report
AUDIT_FILE="$LAB_DIR/audit.md"

cat > "$AUDIT_FILE" <<EOF
# Security Audit: $REPO_NAME

**Cloned:** $(date)
**Repository:** $REPO_URL
**Lab Location:** $LAB_DIR

---

## 🔍 SECURITY SCAN

### Dangerous Commands
EOF

# Check for suspicious patterns
echo "" >> "$AUDIT_FILE"
if grep -r "rm -rf" --include="*.py" --include="*.sh" . 2>/dev/null | head -5 >> "$AUDIT_FILE"; then
    echo "⚠️  Found 'rm -rf' commands" >> "$AUDIT_FILE"
else
    echo "✅ No dangerous delete commands found" >> "$AUDIT_FILE"
fi

echo "" >> "$AUDIT_FILE"
if grep -r "eval(" --include="*.py" . 2>/dev/null | head -5 >> "$AUDIT_FILE"; then
    echo "⚠️  Found eval() usage" >> "$AUDIT_FILE"
else
    echo "✅ No eval() usage" >> "$AUDIT_FILE"
fi

echo "" >> "$AUDIT_FILE"
if grep -r "exec(" --include="*.py" . 2>/dev/null | head -5 >> "$AUDIT_FILE"; then
    echo "⚠️  Found exec() usage" >> "$AUDIT_FILE"
else
    echo "✅ No exec() usage" >> "$AUDIT_FILE"
fi

# Python dependencies
echo "" >> "$AUDIT_FILE"
echo "### Python Dependencies" >> "$AUDIT_FILE"
if [ -f requirements.txt ]; then
    echo "\`\`\`" >> "$AUDIT_FILE"
    cat requirements.txt >> "$AUDIT_FILE"
    echo "\`\`\`" >> "$AUDIT_FILE"
elif [ -f setup.py ]; then
    echo "Uses setup.py (check manually)" >> "$AUDIT_FILE"
elif [ -f pyproject.toml ]; then
    echo "Uses pyproject.toml (check manually)" >> "$AUDIT_FILE"
else
    echo "No dependency file found" >> "$AUDIT_FILE"
fi

# File statistics
echo "" >> "$AUDIT_FILE"
echo "### Repository Stats" >> "$AUDIT_FILE"
echo "\`\`\`" >> "$AUDIT_FILE"
echo "Python files: $(find . -name "*.py" | wc -l)" >> "$AUDIT_FILE"
echo "Total files: $(find . -type f | wc -l)" >> "$AUDIT_FILE"
echo "Repository size: $(du -sh . | cut -f1)" >> "$AUDIT_FILE"
echo "\`\`\`" >> "$AUDIT_FILE"

echo ""
echo "✅ Audit complete: $AUDIT_FILE"
echo "📂 Lab ready: $LAB_DIR"

# Send notification
termux-notification \
    -t "🔬 Lab Audit Complete" \
    -c "$REPO_NAME cloned and audited. Check: $LAB_DIR/audit.md" \
    --priority high

echo ""
echo "Next step: Initiate consilium discussion in resonance.sqlite3"
