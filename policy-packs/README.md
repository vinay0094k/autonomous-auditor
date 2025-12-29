# Policy Packs - Ecosystem Expansion

## SOC2 Compliance Pack
```yaml
# policy-packs/soc2.yaml
name: "SOC2 Type II Compliance"
version: "1.0.0"
description: "SOC2 security and availability controls"

repo_hygiene:
  missing_license: fail
  missing_readme: fail
  missing_security_md: fail
  log_files: fail
  build_artifacts: fail
  
codebase_auditor:
  todo_density:
    warn: 5
    fail: 15
  secrets_detected: fail
  hardcoded_credentials: fail
  
config_inspector:
  debug_flags: fail
  localhost_references: fail
  missing_env_example: fail
  unencrypted_secrets: fail

custom_rules:
  required_files:
    - "SECURITY.md"
    - "PRIVACY.md" 
    - ".github/CODEOWNERS"
  forbidden_patterns:
    - "console.log"
    - "print("
    - "TODO:"
```

## GDPR Compliance Pack
```yaml
# policy-packs/gdpr.yaml
name: "GDPR Data Protection"
version: "1.0.0"
description: "GDPR privacy and data protection controls"

repo_hygiene:
  missing_privacy_policy: fail
  missing_data_retention: warn
  
config_inspector:
  data_collection_flags: warn
  analytics_tracking: warn
  cookie_settings: warn
  
custom_rules:
  required_files:
    - "PRIVACY.md"
    - "DATA_RETENTION.md"
  data_patterns:
    - pattern: "email"
      severity: warn
      message: "Email collection detected"
    - pattern: "personal_data"
      severity: fail
      message: "Personal data handling requires review"
```

## Financial Services Pack
```yaml
# policy-packs/finserv.yaml
name: "Financial Services Compliance"
version: "1.0.0"
description: "Banking and financial regulatory controls"

repo_hygiene:
  missing_license: fail
  missing_audit_log: fail
  
codebase_auditor:
  todo_density:
    warn: 0
    fail: 1
  financial_patterns:
    - "credit_card"
    - "ssn"
    - "account_number"
    
config_inspector:
  encryption_required: fail
  audit_logging: fail
  
custom_rules:
  required_files:
    - "AUDIT.md"
    - "COMPLIANCE.md"
    - "SECURITY.md"
  forbidden_patterns:
    - "test_card"
    - "dummy_ssn"
```

## Healthcare Pack (HIPAA)
```yaml
# policy-packs/hipaa.yaml
name: "HIPAA Healthcare Compliance"
version: "1.0.0"
description: "Healthcare data protection and privacy controls"

repo_hygiene:
  missing_hipaa_notice: fail
  phi_data_detected: fail
  
config_inspector:
  encryption_at_rest: fail
  encryption_in_transit: fail
  audit_logging: fail
  
custom_rules:
  required_files:
    - "HIPAA_NOTICE.md"
    - "PHI_HANDLING.md"
  phi_patterns:
    - "patient_id"
    - "medical_record"
    - "diagnosis"
    - "treatment"
```
