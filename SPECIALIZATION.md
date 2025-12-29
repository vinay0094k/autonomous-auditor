# Specialization: Codebase Auditor

## Purpose
Inspect a local source code repository and report structural and textual findings.

## Responsibilities
- List key files and directories
- Identify TODO and FIXME comments
- Identify import usage patterns
- Identify configuration-related files

## Explicit Non-Goals
- No code execution
- No file modification
- No semantic or AST analysis
- No security guarantees
- No dependency resolution

## Constraints
- Uses existing core tools only
- Read-only access
- Bounded output

## Status
- Planner emits valid structured plans using search_text
- Codebase Auditor specialization operational
- No core modifications required
