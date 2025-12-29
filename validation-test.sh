# REAL-WORLD VALIDATION TEST

# Step 1: Run audit and policy (should fail)
echo '🔍 BEFORE: Running SOC2 audit (expecting failures)...'
uv run python cli.py --mode repo_hygiene 'Audit this repo' --format json --out validation-before.json --quiet
uv run python policy.py validation-before.json --pack soc2 --format json > soc2-before.json
echo 'Exit code:' $?

# Show failures
echo '❌ FAILURES DETECTED:'
cat soc2-before.json | jq -r '.violations[].message'

echo
echo '📋 EVIDENCE REPORT:'
uv run python policy.py validation-before.json --pack soc2 --evidence
# Step 2: Fix violations and re-test

echo '🔧 FIXING VIOLATIONS...'
echo 'Removing log files and build artifacts:'

# Remove violations (simulate fixing)
rm -f agent.log
rm -rf __pycache__

echo '✅ Violations fixed!'
echo

# Re-run audit
echo '🔍 AFTER: Running SOC2 audit (expecting success)...'
uv run python cli.py --mode repo_hygiene 'Audit this repo' --format json --out validation-after.json --quiet
uv run python policy.py validation-after.json --pack soc2 --format json > soc2-after.json
echo 'Exit code:' $?

echo
echo '✅ FINAL RESULT:'
cat soc2-after.json | jq -r '.status'

echo
echo '📋 EVIDENCE REPORT (AFTER):'
uv run python policy.py validation-after.json --pack soc2 --evidence
