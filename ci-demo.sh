#!/bin/bash
# CI Integration Demo Script
# Shows complete audit + policy enforcement workflow

set -e  # Exit on any error

echo "🚀 Autonomous Auditor CI Integration Demo"
echo "========================================"

# 1. Run repo hygiene audit
echo "📋 Step 1: Repository Hygiene Audit"
uv run python cli.py \
  --mode repo_hygiene \
  "Audit this repo" \
  --format json \
  --out hygiene-report.json \
  --quiet

AUDIT_EXIT_CODE=$?
echo "Audit exit code: $AUDIT_EXIT_CODE"

# 2. Run policy enforcement
echo "📋 Step 2: Policy Enforcement"
uv run python policy.py hygiene-report.json --policy policy.yaml --quiet

POLICY_EXIT_CODE=$?
echo "Policy exit code: $POLICY_EXIT_CODE"

# 3. Determine final result
if [ $POLICY_EXIT_CODE -eq 0 ]; then
    echo "✅ CI PASSED: No policy violations"
    exit 0
elif [ $POLICY_EXIT_CODE -eq 1 ]; then
    echo "⚠️ CI WARNING: Policy warnings detected"
    exit 1
else
    echo "❌ CI FAILED: Policy violations found"
    exit 2
fi
