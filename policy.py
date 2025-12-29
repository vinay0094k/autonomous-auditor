#!/usr/bin/env python3
"""
Policy Enforcement Layer
Interprets audit results and enforces organizational policies.
"""

import json
import yaml
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

class PolicyEngine:
    """Policy interpreter for audit results"""
    
    def __init__(self, policy_file: str = "policy.yaml"):
        self.policy = self.load_policy(policy_file)
        self.metadata = getattr(self, 'metadata', {})
    
    def load_policy(self, policy_file: str) -> Dict[str, Any]:
        """Load policy configuration with contract validation"""
        default_policy = {
            "repo_hygiene": {
                "missing_license": "fail",
                "missing_readme": "warn", 
                "todo_density": {"warn": 10, "fail": 30},
                "log_files": "warn",
                "build_artifacts": "fail"
            },
            "codebase_auditor": {
                "todo_density": {"warn": 10, "fail": 30},
                "fixme_comments": "warn",
                "import_count": {"warn": 50, "fail": 100}
            },
            "config_inspector": {
                "secrets_detected": "fail",
                "debug_flags": "warn",
                "localhost_references": "warn",
                "missing_env_example": "warn"
            }
        }
        
        if Path(policy_file).exists():
            with open(policy_file) as f:
                if policy_file.endswith('.yaml') or policy_file.endswith('.yml'):
                    user_policy = yaml.safe_load(f)
                else:
                    user_policy = json.load(f)
                
                # Extract and validate metadata if present
                if 'metadata' in user_policy:
                    self.metadata = user_policy['metadata']
                    # Remove metadata from policy rules
                    user_policy = {k: v for k, v in user_policy.items() if k != 'metadata'}
                
                # Merge with defaults
                for mode, rules in user_policy.items():
                    if mode in default_policy:
                        default_policy[mode].update(rules)
                    else:
                        default_policy[mode] = rules
        
        return default_policy
    
    def evaluate(self, audit_result: Dict[str, Any]) -> Tuple[int, List[str]]:
        """Evaluate audit result against policy"""
        mode = audit_result.get("specialization", audit_result.get("mode", "codebase_auditor"))
        result_text = audit_result.get("result", "").lower()
        
        if mode not in self.policy:
            return 0, [f"No policy defined for mode: {mode}"]
        
        policy_rules = self.policy[mode]
        violations = []
        evidence = []
        max_severity = 0  # 0=success, 1=warn, 2=fail
        
        # Evaluate each rule
        for rule_name, rule_config in policy_rules.items():
            severity, message = self.evaluate_rule(rule_name, rule_config, result_text, audit_result)
            
            # Record evidence of check
            evidence.append({
                "rule": rule_name,
                "checked": True,
                "passed": severity == 0,
                "severity": ["info", "warning", "critical"][severity] if severity <= 2 else "critical"
            })
            
            if message:
                violations.append({
                    "rule": rule_name,
                    "message": message,
                    "category": self.get_rule_category(rule_name),
                    "severity": ["info", "warning", "critical"][severity] if severity <= 2 else "critical"
                })
            max_severity = max(max_severity, severity)
        
        # Store evidence for later retrieval
        self.evidence = evidence
        
        return max_severity, violations
    
    def evaluate_rule(self, rule_name: str, rule_config: Any, result_text: str, audit_result: Dict[str, Any]) -> Tuple[int, str]:
        """Evaluate a single policy rule"""
        
        # Get environment facts for file detection
        env_facts = audit_result.get("environment_facts", "").lower()
        combined_text = (result_text + " " + env_facts).lower()
        
        if rule_name == "missing_license":
            # Check for LICENSE file in various forms
            if any(license_indicator in combined_text for license_indicator in ["license", "licence", "copying", "copyright"]):
                return 0, ""  # Found license
            return self.severity_to_code(rule_config), "LICENSE file not found"
        
        elif rule_name == "missing_readme":
            # Check for README file in various forms
            if any(readme_indicator in combined_text for readme_indicator in ["readme", "read_me", "readme.md", "readme.txt"]):
                return 0, ""  # Found readme
            return self.severity_to_code(rule_config), "README file not found"
        
        elif rule_name == "todo_density":
            todo_count = combined_text.count("todo")
            if isinstance(rule_config, dict):
                if todo_count >= rule_config.get("fail", 999):
                    return 2, f"TODO count too high: {todo_count} (max: {rule_config['fail']})"
                elif todo_count >= rule_config.get("warn", 999):
                    return 1, f"High TODO count: {todo_count} (threshold: {rule_config['warn']})"
            else:
                if todo_count > 0:
                    return self.severity_to_code(rule_config), f"TODOs found: {todo_count}"
        
        elif rule_name == "fixme_comments":
            if "fixme" in combined_text:
                fixme_count = combined_text.count("fixme")
                return self.severity_to_code(rule_config), f"FIXME comments found: {fixme_count}"
        
        elif rule_name == "secrets_detected":
            secret_indicators = ["password", "secret", "key", "token", "api_key"]
            for indicator in secret_indicators:
                if indicator in combined_text:
                    return self.severity_to_code(rule_config), f"Potential secret detected: {indicator}"
        
        elif rule_name == "debug_flags":
            debug_indicators = ["debug=true", "debug: true", "debug_mode"]
            for indicator in debug_indicators:
                if indicator in combined_text:
                    return self.severity_to_code(rule_config), f"Debug flag detected: {indicator}"
        
        elif rule_name == "localhost_references":
            if "localhost" in combined_text or "127.0.0.1" in combined_text:
                return self.severity_to_code(rule_config), "Localhost references found"
        
        elif rule_name == "log_files":
            if ".log" in combined_text:
                return self.severity_to_code(rule_config), "Log files detected in repository"
        
        elif rule_name == "build_artifacts":
            artifacts = [".class", ".tmp", ".cache", "node_modules", "__pycache__"]
            for artifact in artifacts:
                if artifact in combined_text:
                    return self.severity_to_code(rule_config), f"Build artifact detected: {artifact}"
        
        elif rule_name == "import_count":
            import_count = combined_text.count("import")
            if isinstance(rule_config, dict):
                if import_count >= rule_config.get("fail", 999):
                    return 2, f"Import count too high: {import_count} (max: {rule_config['fail']})"
                elif import_count >= rule_config.get("warn", 999):
                    return 1, f"High import count: {import_count} (threshold: {rule_config['warn']})"
        
        return 0, ""
    
    def get_rule_category(self, rule_name: str) -> str:
        """Categorize rule for failure taxonomy"""
        categories = {
            "missing_license": "documentation",
            "missing_readme": "documentation", 
            "todo_density": "code_quality",
            "fixme_comments": "code_quality",
            "secrets_detected": "data_exposure",
            "debug_flags": "configuration",
            "localhost_references": "configuration",
            "log_files": "data_exposure",
            "build_artifacts": "repository_hygiene",
            "import_count": "code_complexity"
        }
        return categories.get(rule_name, "custom")
    
    def severity_to_code(self, severity: str) -> int:
        """Convert severity string to exit code"""
        if severity == "fail":
            return 2
        elif severity == "warn":
            return 1
        else:
            return 0

def main():
    parser = argparse.ArgumentParser(description="Policy enforcement for audit results")
    parser.add_argument("audit_file", help="JSON audit result file")
    parser.add_argument("--policy", default="policy.yaml", help="Policy configuration file")
    parser.add_argument("--pack", help="Use predefined policy pack (soc2, gdpr, finserv)")
    parser.add_argument("--format", choices=["console", "json"], default="console", help="Output format")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be enforced without failing")
    parser.add_argument("--explain", action="store_true", help="Explain policy rules and their purpose")
    parser.add_argument("--evidence", action="store_true", help="Generate compliance evidence report")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    # Handle policy packs
    policy_file = args.policy
    if args.pack:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        pack_file = script_dir / "policy-packs" / f"{args.pack}.yaml"
        if pack_file.exists():
            policy_file = str(pack_file)
        else:
            print(f"Error: Policy pack '{args.pack}' not found at {pack_file}", file=sys.stderr)
            sys.exit(2)
    
    # Handle explain mode
    if args.explain:
        engine = PolicyEngine(policy_file)
        explain_policy(engine, policy_file, args.format)
        sys.exit(0)
    
    # Load audit result
    try:
        with open(args.audit_file) as f:
            audit_result = json.load(f)
    except Exception as e:
        print(f"Error loading audit file: {e}", file=sys.stderr)
        sys.exit(2)
    
    # Evaluate policy
    engine = PolicyEngine(policy_file)
    exit_code, violations = engine.evaluate(audit_result)
    
    # Handle evidence mode
    if args.evidence:
        generate_evidence_report(engine, audit_result, policy_file, args.format)
        sys.exit(0)
    
    # Handle dry-run mode
    if args.dry_run:
        exit_code = 0  # Never fail in dry-run
        if not args.quiet:
            print("🔍 DRY RUN MODE - No enforcement, showing what would happen:")
    
    # Output results
    if args.format == "json":
        output = {
            "exit_code": exit_code,
            "status": ["success", "warning", "failure"][exit_code],
            "violations": violations,
            "policy_file": policy_file,
            "audit_file": args.audit_file
        }
        
        # Include metadata if available
        if hasattr(engine, 'metadata') and engine.metadata:
            output["metadata"] = engine.metadata
        
        # Include dry-run flag
        if args.dry_run:
            output["dry_run"] = True
            output["note"] = "Dry run mode - no enforcement applied"
            
        print(json.dumps(output, indent=2))
    else:
        if not args.quiet:
            status_icons = ["✅", "⚠️", "❌"]
            status_names = ["SUCCESS", "WARNING", "FAILURE"]
            
            if args.dry_run:
                print(f"🔍 DRY RUN: Would be {status_names[exit_code]}")
            else:
                print(f"{status_icons[exit_code]} Policy Evaluation: {status_names[exit_code]}")
            
            if violations:
                print("\nViolations:" if not args.dry_run else "\nWould violate:")
                for violation in violations:
                    if isinstance(violation, dict):
                        prefix = "  • " if not args.dry_run else "  ⚠️ "
                        print(f"{prefix}{violation['rule']}: {violation['message']}")
                    else:
                        prefix = "  • " if not args.dry_run else "  ⚠️ "
                        print(f"{prefix}{violation}")
            else:
                print("No policy violations detected")
        else:
            if violations:
                for violation in violations:
                    if isinstance(violation, dict):
                        prefix = "" if not args.dry_run else "DRY-RUN: "
                        print(f"{prefix}{violation['rule']}: {violation['message']}")
                    else:
                        prefix = "" if not args.dry_run else "DRY-RUN: "
                        print(f"{prefix}{violation}")
    
    sys.exit(exit_code)

def explain_policy(engine: PolicyEngine, policy_file: str, format_type: str = "console"):
    """Explain policy rules and their purpose"""
    
    explanations = {
        "missing_license": "Ensures repository has proper licensing documentation for legal compliance",
        "missing_readme": "Validates presence of README file for project documentation standards", 
        "todo_density": "Controls technical debt by limiting TODO/FIXME comments in codebase",
        "log_files": "Prevents accidental commit of log files that may contain sensitive data",
        "build_artifacts": "Blocks build artifacts from being committed to version control",
        "secrets_detected": "Scans for potential secrets, passwords, or API keys in configuration",
        "debug_flags": "Identifies debug flags that should not be enabled in production",
        "localhost_references": "Finds localhost URLs that indicate development configuration",
        "fixme_comments": "Tracks FIXME comments that indicate known issues requiring attention",
        "import_count": "Monitors import statement density as code complexity indicator"
    }
    
    if format_type == "json":
        output = {
            "policy_file": policy_file,
            "metadata": getattr(engine, 'metadata', {}),
            "rules": {}
        }
        
        for mode, rules in engine.policy.items():
            output["rules"][mode] = {}
            for rule_name, rule_config in rules.items():
                output["rules"][mode][rule_name] = {
                    "config": rule_config,
                    "explanation": explanations.get(rule_name, "Custom rule - no explanation available")
                }
        
        print(json.dumps(output, indent=2))
    else:
        print(f"📋 Policy Explanation: {policy_file}")
        
        # Show metadata if available
        if hasattr(engine, 'metadata') and engine.metadata:
            metadata = engine.metadata
            print(f"\n🏷️  Standard: {metadata.get('standard', 'Custom')}")
            print(f"🎯 Scope: {metadata.get('scope', 'Not specified')}")
            
            if 'non_goals' in metadata:
                print(f"\n❌ Non-Goals:")
                for non_goal in metadata['non_goals']:
                    print(f"   • {non_goal}")
            
            if 'guarantees' in metadata:
                print(f"\n🔒 Guarantees:")
                for guarantee in metadata['guarantees']:
                    print(f"   • {guarantee}")
        
        print(f"\n📖 Rules Explained:")
        for mode, rules in engine.policy.items():
            if isinstance(rules, dict):
                print(f"\n  {mode.upper()}:")
                for rule_name, rule_config in rules.items():
                    explanation = explanations.get(rule_name, "Custom rule")
                    severity = "FAIL" if rule_config == "fail" else "WARN" if rule_config == "warn" else str(rule_config)
                    print(f"    • {rule_name} [{severity}]: {explanation}")

def generate_evidence_report(engine: PolicyEngine, audit_result: Dict[str, Any], policy_file: str, format_type: str = "console"):
    """Generate compliance evidence report"""
    import datetime
    
    timestamp = datetime.datetime.now().isoformat()
    evidence = getattr(engine, 'evidence', [])
    
    if format_type == "json":
        output = {
            "evidence_report": {
                "timestamp": timestamp,
                "policy_file": policy_file,
                "audit_file": audit_result.get("task", "unknown"),
                "version": "v1.0.0",
                "checks_performed": len(evidence),
                "files_inspected": audit_result.get("environment_facts", "").count("[text]"),
                "rules_evaluated": evidence,
                "metadata": getattr(engine, 'metadata', {})
            }
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"📋 Compliance Evidence Report")
        print(f"Generated: {timestamp}")
        print(f"Policy: {policy_file}")
        print(f"Version: v1.0.0")
        
        if hasattr(engine, 'metadata') and engine.metadata:
            metadata = engine.metadata
            print(f"Standard: {metadata.get('standard', 'Custom')}")
        
        print(f"\n📊 Summary:")
        print(f"  • Checks performed: {len(evidence)}")
        print(f"  • Files inspected: {audit_result.get('environment_facts', '').count('[text]')}")
        
        passed = sum(1 for e in evidence if e['passed'])
        failed = len(evidence) - passed
        print(f"  • Rules passed: {passed}")
        print(f"  • Rules failed: {failed}")
        
        print(f"\n🔍 Detailed Evidence:")
        for item in evidence:
            status = "✅ PASS" if item['passed'] else "❌ FAIL"
            print(f"  {status} {item['rule']} [{item['severity']}]")

if __name__ == "__main__":
    main()
