# Agent Architecture - FROZEN

## Core Invariants (DO NOT VIOLATE)

1. **Planner Contract**: Planner MUST emit valid JSON or be rejected
2. **Execution Safety**: Execution ONLY happens from validated plans  
3. **Tool Boundaries**: Tools NEVER accept free-form input
4. **Type Safety**: Binary files are NEVER decoded as text
5. **State Transitions**: All state changes are explicit and tracked
6. **Failure Handling**: Failed steps trigger revision, not crashes
7. **Schema Validation**: All JSON must validate against PLAN_SCHEMA

## System Components

### 1. Planner
- Input: Task + Environment facts
- Output: Validated JSON plan
- Fallback: Safe default plan on failure

### 2. Executor  
- Input: Structured plan steps
- Output: Tool requests
- Contract: One step = one tool call

### 3. Tool Registry
- read_text_file: Text files only
- describe_binary_file: Binary files only
- list_dir: Directory operations
- pwd/whoami: System info

### 4. Memory
- Smart storage: Success/failure semantics
- Retrieval: Context-aware recall
- Persistence: SQLite backend

### 5. State Schema
- Immutable structure
- Explicit failure tracking
- Plan revision capability

## Flow Guarantee
ground → plan → execute → act → observe → [revise_plan] → continue

## Stability Rules
- Boring is better than clever
- Explicit is better than implicit  
- Validated is better than assumed
- Failing safely is better than failing silently

Any change that violates these invariants MUST be rejected.
