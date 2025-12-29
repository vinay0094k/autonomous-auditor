# GitHub Actions Integration

## Drop-in CI Gate

Add autonomous auditing to any repository with zero configuration.

## Basic Setup

```yaml
# .github/workflows/audit.yml
name: Autonomous Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install auditor
      run: pip install autonomous-auditor
    
    - name: Run audit
      run: autonomous-auditor --mode codebase_auditor "Audit this repo" --format json --out audit.json
    
    - name: Enforce policy
      run: |
        if [ $? -ne 0 ]; then
          echo "❌ Audit failed"
          exit 1
        fi
        echo "✅ Audit passed"
```

## Specialization Examples

### Repo Hygiene Gate
```yaml
- name: Run Repo Hygiene Audit
  run: |
    autonomous-auditor \
      --mode repo_hygiene \
      "Audit this repo" \
      --format json \
      --out hygiene-report.json

- name: Enforce hygiene policy
  run: |
    # Exit code enforcement
    if [ $? -eq 2 ]; then
      echo "❌ Critical hygiene failures"
      exit 1
    elif [ $? -eq 1 ]; then
      echo "⚠️ Hygiene warnings detected"
    fi
    
    # JSON policy enforcement
    jq -e '.failures == 0' hygiene-report.json || exit 1
```

### Config Inspector Gate
```yaml
- name: Run Config Audit
  run: |
    autonomous-auditor \
      --mode config_inspector \
      "Audit configuration files" \
      --format json \
      --out config-report.json

- name: Check for secrets
  run: |
    if jq -e '.result | contains("password") or contains("secret")' config-report.json; then
      echo "❌ Potential secrets in config"
      exit 1
    fi
```

## Policy Enforcement Patterns

### TODO Density Control
```yaml
- name: Check TODO density
  run: |
    autonomous-auditor --mode codebase_auditor "Search for TODO pattern" --format json --out todo-report.json
    TODO_COUNT=$(jq -r '.matches | length' todo-report.json)
    if [ "$TODO_COUNT" -gt 30 ]; then
      echo "❌ Too many TODOs: $TODO_COUNT (max: 30)"
      exit 1
    elif [ "$TODO_COUNT" -gt 10 ]; then
      echo "⚠️ High TODO count: $TODO_COUNT"
      exit 1
    fi
```

### Artifact Collection
```yaml
- name: Upload audit artifacts
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: audit-reports
    path: |
      audit.json
      hygiene-report.json
      config-report.json
```

## Exit Code Contract

- `0` → Success (no issues)
- `1` → Warning (issues found, but not blocking)
- `2` → Failure (critical issues, block merge)

## Pre-commit Integration

```yaml
# .github/workflows/pre-commit.yml
name: Pre-commit Audit
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  quick-audit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Quick hygiene check
      run: |
        autonomous-auditor --mode repo_hygiene "Quick audit" --format summary
        # Exit code automatically enforced
```

## Enterprise Features

### Compliance Reporting
```yaml
- name: Generate compliance report
  run: |
    autonomous-auditor \
      --mode codebase_auditor \
      "Full compliance audit" \
      --format json \
      --out compliance-$(date +%Y%m%d).json
    
    # Include metadata
    echo "Audit completed at $(date)" >> compliance-$(date +%Y%m%d).json
```

### Change Tracking
```yaml
- name: Track audit changes
  run: |
    git log -1 --format="%H %s" > commit-info.txt
    autonomous-auditor "Audit changes" --format json --out audit-${{ github.sha }}.json
```
