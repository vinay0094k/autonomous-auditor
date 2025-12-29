# Running Autonomous Auditor on Other Repositories

## Quick Setup for Any Repository

### 1. Clone the Auditor
```bash
git clone https://github.com/vinay0094k/autonomous-auditor.git
cd autonomous-auditor
pip install -e .
```

### 2. Navigate to Target Repository
```bash
cd /path/to/your/target-repository
```

### 3. Run Audit from Any Directory
```bash
# Basic repo hygiene check
python /path/to/autonomous-auditor/cli.py --mode repo_hygiene "Audit this repo" --format json --out audit-report.json

# Apply compliance policy
python /path/to/autonomous-auditor/policy.py audit-report.json --pack soc2

# Or use relative path if auditor is in parent directory
python ../autonomous-auditor/cli.py --mode repo_hygiene "Audit this repo"
```

## Portable Installation

### Option 1: System-wide Installation
```bash
cd autonomous-auditor
pip install -e .

# Now run from anywhere
cd /any/repository
autonomous-auditor --mode repo_hygiene "Audit this repo"
```

### Option 2: Alias for Easy Access
```bash
# Add to ~/.bashrc or ~/.zshrc
alias audit-repo="python /path/to/autonomous-auditor/cli.py"
alias audit-policy="python /path/to/autonomous-auditor/policy.py"

# Usage from any directory
cd /any/repository
audit-repo --mode repo_hygiene "Audit this repo" --format json --out report.json
audit-policy report.json --pack soc2
```

### Option 3: Wrapper Script
```bash
#!/bin/bash
# audit-any-repo.sh
AUDITOR_PATH="/path/to/autonomous-auditor"
TARGET_DIR="${1:-.}"  # Use provided directory or current directory

cd "$TARGET_DIR"
python "$AUDITOR_PATH/cli.py" --mode repo_hygiene "Audit this repo" --format json --out audit-report.json
python "$AUDITOR_PATH/policy.py" audit-report.json --pack soc2

echo "Audit complete for: $(pwd)"
```

## Multi-Repository Batch Auditing

### Audit Multiple Repositories
```bash
#!/bin/bash
# batch-audit.sh
REPOS=(
    "/path/to/repo1"
    "/path/to/repo2" 
    "/path/to/repo3"
)

for repo in "${REPOS[@]}"; do
    echo "Auditing: $repo"
    cd "$repo"
    
    python /path/to/autonomous-auditor/cli.py \
        --mode repo_hygiene \
        "Audit this repo" \
        --format json \
        --out "audit-$(basename $repo).json"
    
    python /path/to/autonomous-auditor/policy.py \
        "audit-$(basename $repo).json" \
        --pack soc2
    
    echo "Exit code: $?"
    echo "---"
done
```

## CI Integration for Other Repos

### Add to Any Repository's CI
```yaml
# .github/workflows/audit.yml
name: Repository Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Checkout auditor
      uses: actions/checkout@v4
      with:
        repository: vinay0094k/autonomous-auditor
        path: auditor
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install auditor
      run: |
        cd auditor
        pip install -e .
    
    - name: Run audit
      run: |
        python auditor/cli.py --mode repo_hygiene "Audit this repo" --format json --out audit.json
        python auditor/policy.py audit.json --pack soc2
```

## Configuration for Different Repositories

### Repository-Specific Policies
```bash
# Create custom policy for specific repo type
cd /path/to/frontend-repo
python /path/to/autonomous-auditor/policy.py audit.json --policy frontend-policy.yaml

cd /path/to/backend-repo  
python /path/to/autonomous-auditor/policy.py audit.json --policy backend-policy.yaml
```

### Environment-Specific Configuration
```bash
# Different configs for different repo types
export OLLAMA_HOST=http://localhost:11435  # For local repos
export OLLAMA_HOST=http://remote-llm:11435 # For CI environments

python /path/to/autonomous-auditor/cli.py --mode repo_hygiene "Audit this repo"
```

## Best Practices

### 1. Standardize Across Organization
```bash
# Place auditor in shared location
/opt/autonomous-auditor/
# Or use Docker for consistency
docker run -v $(pwd):/repo autonomous-auditor --mode repo_hygiene "Audit this repo"
```

### 2. Repository-Specific Ignore Patterns
```bash
# Create .audit-ignore in each repository
echo "node_modules/" >> .audit-ignore
echo "vendor/" >> .audit-ignore
echo "*.min.js" >> .audit-ignore
```

### 3. Compliance by Repository Type
```bash
# Frontend repositories
audit-policy report.json --pack gdpr

# Backend APIs  
audit-policy report.json --pack soc2

# Financial services
audit-policy report.json --pack finserv
```

The auditor works on **any repository** - just point it to the target directory and run the audit commands.
