# Public Interface Contract - STABLE FOREVER

## CLI Interface (Sacred)
```bash
autonomous-auditor [task] [options]
```

### Required Arguments
- `task`: String describing the audit task

### Options (Stable)
- `--mode {default,codebase_auditor}`: Agent specialization mode
- `--config PATH`: Configuration file path (default: config.json)
- `--log-level {DEBUG,INFO,WARNING,ERROR}`: Logging level
- `--output PATH`: JSON output file path
- `--quiet, -q`: Minimal output mode
- `--verbose, -v`: Detailed output mode

## Exit Codes (Sacred)
- `0`: Success
- `1`: Error (invalid input, system failure)

## Output Schema (Sacred)
### JSON Output Format
```json
{
  "task": "string",
  "status": "success|failed", 
  "steps_completed": "integer",
  "plan_steps": "integer",
  "failures": "integer",
  "result": "string",
  "plan": [{"action": "string", "target": "string"}]
}
```

### Console Summary Format
```
✅ Success
Execution Summary: [table with metrics]
Plan Executed: [checklist with status icons]
```

## Log Format (Sacred)
```
YYYY-MM-DD HH:MM:SS,mmm - LEVEL - MESSAGE
```

## Configuration Schema (Sacred)
```bash
OLLAMA_MODEL=string
OLLAMA_HOST=url
MAX_STEPS=integer
RETRY_LIMIT=integer
LOG_LEVEL=string
```

## Behavioral Guarantees (Sacred)
1. **Planner Contract**: Valid JSON → executes, Invalid JSON → safe fallback
2. **Bounded Output**: search_text respects max_results limits
3. **Binary Safety**: Binary files never decoded as text
4. **Self-Healing**: Plan revision after 2 consecutive failures
5. **Read-Only**: Never modifies files or executes code
6. **Graceful Degradation**: System continues on LLM failures

---
**Everything above is STABLE FOREVER.**
**Everything not listed here may change between versions.**
