# Autonomous Auditor v1.1.0

**A deterministic, CI-native repository hygiene gate that enforces policy using bounded, explainable analysis — not heuristics or learning.**

## What This Is NOT

- ❌ **NOT a static analyzer** - No AST parsing or semantic analysis
- ❌ **NOT a security scanner** - No vulnerability scoring or CVE detection  
- ❌ **NOT an AI agent** - No chat interface or general problem solving
- ❌ **NOT a dependency resolver** - No package analysis or version checking

## What This IS

- ✅ **Deterministic CI-Native Gate** - Drop-in repository hygiene enforcement for CI/CD pipelines
- ✅ **Enterprise Policy Packs** - SOC2, GDPR, FinServ compliance templates ready for purchase
- ✅ **Evidence Generation** - Compliance reports with audit trails for security teams
- ✅ **Multi-Mode Specialization** - Codebase auditor, config inspector, repo hygiene agent
- ✅ **Self-Healing Architecture** - Automatically recovers from LLM failures with plan revision
- ✅ **Contract-Based Policies** - Clear scope, non-goals, and guarantees for enterprise buyers
- ✅ **Exit Code Standards** - 0=success, 1=warning, 2=failure for reliable CI integration
- ✅ **Dry-Run & Explain Modes** - Preview enforcement and understand rules before deployment

## Why This Matters

**Enterprise Ready** - Drop-in CI gate with official adapters, not a tool to wire yourself  
**Compliance Native** - SOC2, GDPR, FinServ policy packs with audit trails for regulators  
**Deterministic** - Same input always produces same output, no AI uncertainty  
**Revenue Generating** - Sellable policy packs ($99-499) with clear business model  
**Zero Vendor Lock-in** - Standard exit codes, works with any CI system

## Installation

### Easy Installation (Recommended)

```bash
# Clone and install system-wide
git clone https://github.com/vinay0094k/autonomous-auditor.git
cd autonomous-auditor
./install.sh

# Now works from any directory
cd /any/repository
autonomous-auditor --mode repo_hygiene "Audit this repo" --format json --out report.json
audit-policy report.json --pack soc2
```

### Manual Installation

```bash
# Install from source
git clone https://github.com/vinay0094k/autonomous-auditor
cd autonomous-auditor
pip install -e .
```

## Quick Start

```bash
# Basic repo hygiene audit
autonomous-auditor --mode repo_hygiene "Audit this repo" --format json --out audit.json

# Apply SOC2 compliance policy
audit-policy audit.json --pack soc2

# Dry-run mode (preview without enforcement)
audit-policy audit.json --pack gdpr --dry-run

# Explain policy rules
audit-policy audit.json --pack finserv --explain

# Generate compliance evidence
audit-policy audit.json --pack soc2 --evidence
```

## Policy Packs

```bash
# SOC2 Type II Compliance
audit-policy audit.json --pack soc2

# GDPR Data Protection  
audit-policy audit.json --pack gdpr

# Financial Services Regulatory
audit-policy audit.json --pack finserv

# Custom policy file
audit-policy audit.json --policy custom-policy.yaml
```

## Configuration

Create a `.env` file in your project directory:

```bash
OLLAMA_MODEL=llama3.1:8b
OLLAMA_HOST=http://localhost:11435
MAX_STEPS=8
RETRY_LIMIT=2
LOG_LEVEL=INFO
```

## CI Integration

```yaml
# .github/workflows/audit.yml
name: Codebase Audit
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
      run: autonomous-auditor "Audit this repo" --json --output audit-report.json
    
    - name: Check TODO count
      run: |
        TODO_COUNT=$(jq -r '.result' audit-report.json | grep -c "TODO" || echo "0")
        if [ "$TODO_COUNT" -gt 10 ]; then
          echo "❌ Too many TODOs: $TODO_COUNT (max: 10)"
          exit 1
        fi
        echo "✅ TODO count acceptable: $TODO_COUNT"
    
    - name: Check for credentials
      run: |
        autonomous-auditor "Search for password pattern" --json --quiet > creds-check.json
        if jq -e '.result | contains("password")' creds-check.json; then
          echo "❌ Potential credentials found"
          exit 1
        fi
        echo "✅ No credentials detected"
    
    - name: Upload audit report
      uses: actions/upload-artifact@v4
      with:
        name: audit-report
        path: audit-report.json
```

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
autonomous-auditor "Search for TODO pattern" --quiet
if [ $? -ne 0 ]; then
  echo "❌ Audit failed - commit blocked"
  exit 1
fi
```

### Nightly Audit
```yaml
# .github/workflows/nightly-audit.yml
name: Nightly Audit
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Full audit
      run: |
        autonomous-auditor "Audit this codebase" --json > nightly-audit.json
        # Send to monitoring system, Slack, etc.
```

## Usage

```bash
# Basic audit
uv run python cli.py --mode codebase_auditor "Audit this codebase"

# Specific pattern search  
uv run python cli.py --mode codebase_auditor "Search for TODO pattern"

# Full audit suite
uv run python auditor.py --audit full
```

## What It Finds

- **TODO/FIXME comments** - Technical debt markers
- **Import patterns** - Dependency usage analysis  
- **Configuration files** - .env, config.json, settings files
- **File structure** - Directory organization and key files

## What You Can Do

### 🔍 **Repository Analysis Modes**

```bash
# Codebase Analysis
autonomous-auditor --mode codebase_auditor "Find all TODO comments" --format json --out todos.json
autonomous-auditor --mode codebase_auditor "Search for import statements" --format markdown --out imports.md
autonomous-auditor --mode codebase_auditor "Analyze code complexity" --format summary

# Configuration Security
autonomous-auditor --mode config_inspector "Check for secrets in config files" --format json --out security.json
autonomous-auditor --mode config_inspector "Find debug flags" --format summary
autonomous-auditor --mode config_inspector "Audit environment variables" --format markdown --out env-audit.md

# Repository Hygiene
autonomous-auditor --mode repo_hygiene "Check repository structure" --format json --out hygiene.json
autonomous-auditor --mode repo_hygiene "Find build artifacts" --format summary
autonomous-auditor --mode repo_hygiene "Audit file organization" --format markdown --out structure.md
```

### 📋 **Enterprise Compliance**

```bash
# SOC2 Type II Compliance
audit-policy audit.json --pack soc2
audit-policy audit.json --pack soc2 --evidence  # Generate compliance evidence

# GDPR Data Protection
audit-policy audit.json --pack gdpr --dry-run   # Preview without enforcement
audit-policy audit.json --pack gdpr --explain   # Understand all rules

# Financial Services Regulatory
audit-policy audit.json --pack finserv
audit-policy audit.json --pack finserv --evidence

# Custom Organizational Policies
audit-policy audit.json --policy my-company-policy.yaml
```

### 🏢 **Enterprise Use Cases**

```bash
# CI/CD Integration - Pre-commit hooks
autonomous-auditor --mode repo_hygiene "Quick check" --format summary
if [ $? -ne 0 ]; then echo "Commit blocked"; exit 1; fi

# Security Audits
autonomous-auditor --mode config_inspector "Find potential secrets" --format json --out security-scan.json
audit-policy security-scan.json --pack soc2 --evidence

# Multi-Repository Management
for repo in /path/to/repo1 /path/to/repo2; do
    cd "$repo"
    autonomous-auditor --mode repo_hygiene "Audit $(basename $repo)" --format json --out audit.json
    audit-policy audit.json --pack soc2
done

# Compliance Reporting
autonomous-auditor --mode repo_hygiene "Compliance audit" --format json --out compliance.json
audit-policy compliance.json --pack gdpr --evidence > compliance-report.txt
```

### 💼 **Business Applications**

- **Regulatory Compliance** - SOC2, GDPR, FinServ audit trails
- **Risk Management** - Identify security and compliance risks  
- **Quality Gates** - Automated CI/CD quality enforcement
- **Technical Debt** - Track and manage code quality metrics
- **Vendor Management** - Audit third-party code and integrations
- **Documentation** - Generate compliance and audit documentation

## Status: Production Ready ✅

All core engineering problems solved. System is complete and stable.

## Working with Results

After running audits, you get JSON files with detailed analysis. See [WORKING-WITH-RESULTS.md](WORKING-WITH-RESULTS.md) for complete examples of:

- 📊 **Analyzing JSON results** - Extract data, count issues, check status
- 📋 **Policy enforcement** - Apply SOC2, GDPR, FinServ compliance  
- 🏢 **CI/CD integration** - Pre-commit hooks, GitHub Actions workflows
- 📄 **Report generation** - Executive summaries, compliance evidence
- 🔄 **Multi-repository workflows** - Batch processing, dashboard integration

### Quick Example
```bash
# Run audit
autonomous-auditor --mode codebase_auditor "Find TODOs" --format json --out todos.json

# Analyze results  
cat todos.json | jq -r '.result' | grep -c "TODO"

# Apply policy
audit-policy todos.json --pack soc2

# Generate evidence
audit-policy todos.json --pack soc2 --evidence > compliance-evidence.txt
```

### Try the Complete Workflow
```bash
# Run the example workflow to see everything in action
./examples/complete-workflow.sh
```
