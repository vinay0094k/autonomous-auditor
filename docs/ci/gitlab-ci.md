# GitLab CI Integration

## Drop-in Pipeline Gate

Add autonomous auditing to GitLab repositories with zero configuration.

## Basic Setup

```yaml
# .gitlab-ci.yml
stages:
  - audit
  - test
  - deploy

audit:
  stage: audit
  image: python:3.10
  before_script:
    - pip install autonomous-auditor
  script:
    - autonomous-auditor --mode codebase_auditor "Audit this repo" --format json --out audit.json
  artifacts:
    reports:
      junit: audit.json
    paths:
      - audit.json
    expire_in: 30 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## Specialization Pipelines

### Repo Hygiene Gate
```yaml
repo_hygiene:
  stage: audit
  image: python:3.10
  before_script:
    - pip install autonomous-auditor
  script:
    - |
      autonomous-auditor \
        --mode repo_hygiene \
        "Audit repository hygiene" \
        --format json \
        --out hygiene-report.json
      
      # Exit code enforcement
      EXIT_CODE=$?
      if [ $EXIT_CODE -eq 2 ]; then
        echo "❌ Critical hygiene failures"
        exit 1
      elif [ $EXIT_CODE -eq 1 ]; then
        echo "⚠️ Hygiene warnings detected"
      fi
  artifacts:
    paths:
      - hygiene-report.json
```

### Config Security Gate
```yaml
config_security:
  stage: audit
  image: python:3.10
  before_script:
    - pip install autonomous-auditor
    - apt-get update && apt-get install -y jq
  script:
    - |
      autonomous-auditor \
        --mode config_inspector \
        "Audit configuration security" \
        --format json \
        --out config-report.json
      
      # Check for potential secrets
      if jq -e '.result | contains("password") or contains("secret") or contains("key")' config-report.json; then
        echo "❌ Potential secrets detected in configuration"
        exit 1
      fi
  artifacts:
    paths:
      - config-report.json
```

## Policy Templates

### Merge Request Gate
```yaml
mr_audit:
  stage: audit
  image: python:3.10
  before_script:
    - pip install autonomous-auditor
    - apt-get update && apt-get install -y jq
  script:
    - |
      # TODO density check
      autonomous-auditor --mode codebase_auditor "Search for TODO pattern" --format json --out todo-report.json
      TODO_COUNT=$(jq -r '.matches | length // 0' todo-report.json)
      
      if [ "$TODO_COUNT" -gt 30 ]; then
        echo "❌ Too many TODOs: $TODO_COUNT (max: 30)"
        exit 1
      elif [ "$TODO_COUNT" -gt 10 ]; then
        echo "⚠️ High TODO count: $TODO_COUNT"
      fi
      
      # Hygiene check
      autonomous-auditor --mode repo_hygiene "Quick hygiene check" --format summary
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### Nightly Compliance
```yaml
nightly_audit:
  stage: audit
  image: python:3.10
  before_script:
    - pip install autonomous-auditor
  script:
    - |
      autonomous-auditor \
        --mode codebase_auditor \
        "Full compliance audit" \
        --format json \
        --out compliance-$(date +%Y%m%d).json
      
      # Add metadata
      echo "{\"timestamp\": \"$(date -Iseconds)\", \"commit\": \"$CI_COMMIT_SHA\", \"branch\": \"$CI_COMMIT_BRANCH\"}" > metadata.json
      jq -s '.[0] * .[1]' compliance-$(date +%Y%m%d).json metadata.json > final-report.json
  artifacts:
    paths:
      - final-report.json
    expire_in: 90 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

## Exit Code Handling

GitLab CI automatically fails jobs on non-zero exit codes:

- `0` → Job succeeds (green)
- `1` → Job succeeds with warnings (yellow) 
- `2` → Job fails (red, blocks pipeline)

## Parallel Audits

```yaml
audit:
  stage: audit
  parallel:
    matrix:
      - AUDIT_MODE: codebase_auditor
        AUDIT_QUERY: "Audit this codebase"
      - AUDIT_MODE: repo_hygiene  
        AUDIT_QUERY: "Check repository hygiene"
      - AUDIT_MODE: config_inspector
        AUDIT_QUERY: "Inspect configuration files"
  image: python:3.10
  before_script:
    - pip install autonomous-auditor
  script:
    - |
      autonomous-auditor \
        --mode $AUDIT_MODE \
        "$AUDIT_QUERY" \
        --format json \
        --out ${AUDIT_MODE}-report.json
  artifacts:
    paths:
      - "*-report.json"
```

## Enterprise Integration

### SAST Integration
```yaml
security_audit:
  stage: audit
  image: python:3.10
  before_script:
    - pip install autonomous-auditor
  script:
    - autonomous-auditor --mode config_inspector "Security audit" --format json --out sast-report.json
  artifacts:
    reports:
      sast: sast-report.json
```

### Compliance Artifacts
```yaml
compliance:
  stage: audit
  image: python:3.10
  before_script:
    - pip install autonomous-auditor
  script:
    - |
      autonomous-auditor "Full audit" --format json --out audit-$CI_COMMIT_SHA.json
      # Upload to compliance system
      curl -X POST -H "Content-Type: application/json" \
           -d @audit-$CI_COMMIT_SHA.json \
           $COMPLIANCE_ENDPOINT
  only:
    - main
    - production
```
