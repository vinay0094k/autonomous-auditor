# Working with Audit Results

After running audits, you get JSON files with detailed results. Here's what to do with them:

## 📊 Example Audit Result

```json
{
  "task": "Find all TODO comments",
  "status": "success",
  "mode": "codebase_auditor", 
  "steps_completed": 3,
  "failures": 0,
  "result": "SUCCESS: Found 5 matches:\n./src/App.tsx:42:// TODO: Add error handling\n./src/utils.ts:15:// TODO: Optimize this function\n./README.md:25:<!-- TODO: Add screenshots -->",
  "timestamp": "2025-12-29T12:45:00.000Z"
}
```

## 🔍 Analyze Your Results

### 1. View Results
```bash
# Pretty print the JSON
cat todos.json | jq '.'

# Extract just the findings
cat todos.json | jq -r '.result'

# Check if audit passed
cat todos.json | jq -r '.status'  # "success" or "failed"
```

### 2. Count Issues
```bash
# Count TODOs found
TODO_COUNT=$(cat todos.json | jq -r '.result' | grep -c "TODO" || echo "0")
echo "Found $TODO_COUNT TODO comments"

# Extract affected files
cat todos.json | jq -r '.result' | grep -o '\./[^:]*' | sort | uniq
```

## 📋 Apply Policy Enforcement

### SOC2 Compliance Check
```bash
# Apply SOC2 policy to your results
audit-policy todos.json --pack soc2

# Example output:
# ❌ Policy Evaluation: FAILURE
# Violations:
#   • todo_density: TODO count too high: 15 (max: 10)
```

### Preview Mode (Safe Testing)
```bash
# See what would happen without blocking
audit-policy todos.json --pack soc2 --dry-run

# Understand the rules
audit-policy todos.json --pack soc2 --explain
```

## 🏢 CI/CD Integration Examples

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run audit
autonomous-auditor --mode codebase_auditor "Pre-commit check" --format json --out pre-commit-audit.json

# Check TODO density
TODO_COUNT=$(cat pre-commit-audit.json | jq -r '.result' | grep -c "TODO" || echo "0")
if [ "$TODO_COUNT" -gt 5 ]; then
    echo "❌ Too many TODOs: $TODO_COUNT (max: 5)"
    echo "Please resolve some TODOs before committing"
    exit 1
fi

echo "✅ Pre-commit audit passed"
```

### GitHub Actions Workflow
```yaml
# .github/workflows/audit.yml
- name: Run Audit
  run: autonomous-auditor --mode repo_hygiene "CI audit" --format json --out ci-audit.json

- name: Check Results
  run: |
    STATUS=$(cat ci-audit.json | jq -r '.status')
    if [ "$STATUS" != "success" ]; then
      echo "❌ Audit failed"
      exit 1
    fi
    
    # Apply policy
    audit-policy ci-audit.json --pack soc2

- name: Upload Results
  uses: actions/upload-artifact@v4
  with:
    name: audit-results
    path: ci-audit.json
```

## 📊 Generate Reports

### Executive Summary
```bash
# Create a summary report
cat > audit-summary.md << EOF
# Code Quality Report - $(date)

## Audit Results
- Status: $(cat todos.json | jq -r '.status')
- TODOs Found: $(cat todos.json | jq -r '.result' | grep -c 'TODO')
- Files Affected: $(cat todos.json | jq -r '.result' | grep -o '\./[^:]*' | sort | uniq | wc -l)

## Policy Compliance
$(audit-policy todos.json --pack soc2 2>&1)
EOF
```

### Compliance Evidence
```bash
# Generate audit trail for regulators
audit-policy todos.json --pack gdpr --evidence > gdpr-evidence-$(date +%Y%m%d).txt

# Archive compliance data
mkdir compliance-archive-$(date +%Y%m%d)
cp todos.json gdpr-evidence-*.txt compliance-archive-$(date +%Y%m%d)/
```

## 🔄 Multi-Repository Workflow

### Batch Processing
```bash
#!/bin/bash
# audit-all-repos.sh

REPOS=("/path/to/frontend" "/path/to/backend" "/path/to/api")

for repo in "${REPOS[@]}"; do
    echo "Auditing: $(basename $repo)"
    cd "$repo"
    
    # Run audit
    autonomous-auditor --mode repo_hygiene "Batch audit" --format json --out "audit-$(basename $repo).json"
    
    # Check compliance
    audit-policy "audit-$(basename $repo).json" --pack soc2
    
    echo "Exit code: $?"
    echo "---"
done
```

### Dashboard Integration
```bash
# Send results to monitoring system
for audit_file in *.json; do
    curl -X POST \
         -H "Content-Type: application/json" \
         -d @"$audit_file" \
         http://dashboard.company.com/api/audit-results
done
```

## 🎯 Common Use Cases

### 1. **Technical Debt Tracking**
```bash
# Track TODOs over time
autonomous-auditor --mode codebase_auditor "Find TODOs" --format json --out "todos-$(date +%Y%m%d).json"

# Compare with previous
CURRENT=$(cat todos-$(date +%Y%m%d).json | jq -r '.result' | grep -c 'TODO')
PREVIOUS=$(cat todos-$(date -d '1 week ago' +%Y%m%d).json | jq -r '.result' | grep -c 'TODO' 2>/dev/null || echo "0")
echo "TODO trend: $PREVIOUS → $CURRENT"
```

### 2. **Security Scanning**
```bash
# Security-focused audit
autonomous-auditor --mode config_inspector "Security scan" --format json --out security-scan.json

# Check for secrets
if cat security-scan.json | jq -r '.result' | grep -i "password\|secret\|key"; then
    echo "⚠️ Potential secrets detected!"
    audit-policy security-scan.json --pack soc2 --evidence > security-incident-$(date +%Y%m%d).txt
fi
```

### 3. **Release Readiness**
```bash
# Pre-release audit
autonomous-auditor --mode repo_hygiene "Release check" --format json --out release-audit.json

# Enforce strict policy for production
audit-policy release-audit.json --pack finserv

if [ $? -eq 0 ]; then
    echo "✅ Ready for release"
else
    echo "❌ Release blocked - fix policy violations first"
    exit 1
fi
```

## 💡 Pro Tips

1. **Combine Multiple Audits**: Merge results from different modes for comprehensive analysis
2. **Use Dry-Run First**: Always test policies with `--dry-run` before enforcement
3. **Archive Results**: Keep audit trails for compliance and trend analysis
4. **Automate Everything**: Integrate into CI/CD for continuous governance
5. **Custom Policies**: Create organization-specific policies for your standards

The JSON results are your **audit data** - use them for policy enforcement, compliance reporting, CI gates, and continuous governance!
