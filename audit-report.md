# Audit Report

**Status**: ✅ Success  
**Mode**: repo_hygiene  
**Task**: Search for TODO pattern  
**Steps Completed**: 2  
**Failures**: 0  

## Plan Executed
✅ 1. search_text .

## Result
```
SUCCESS: Found 31 matches (searched 50 files):
./README.md:45:autonomous-auditor --mode codebase_auditor "Search for TODO pattern"
./README.md:91:- name: Check TODO count
./README.md:93:TODO_COUNT=$(jq -r '.result' audit-report.json | grep -c "TODO" || echo "0")
./README.md:94:if [ "$TODO_COUNT" -gt 10 ]; then
./README.md:95:echo "❌ Too many TODOs: $TODO_COUNT (max: 10)"
./README.md:98:echo "✅ TODO count acceptable: $TODO_COUNT"
./README.md:120:autonomous-auditor "Search for TODO pattern" --quiet
./README.md:153:uv run python cli.py --mode codebase_auditor "Search for TODO pattern"
./README.md:161:- **TODO/FIXME comments** - Technical debt markers
./agent.py:197:Prefer search_text for TODO, FIXME, import, and config patterns.
./agent.py:211:Prefer search_text for README, LICENSE, .log, TODO, and artifact patterns.
./test_guarantees.py:14:valid_json = '{"steps": [{"action": "search_text", "pattern": "TODO", "target": ".", "max_results": 
./SPECIALIZATION.md:8:- Identify TODO and FIXME comments
./CHANGELOG.md:12:- **Canonical Pattern Matching** - TODO, FIXME, import, and config file detection
./auditor.py:20:"todos": "Find all TODO, FIXME, HACK comments that need attention",
./auditor.py:53:("todos", "Find TODO comments"),
./auditor.py:113:%(prog)s --audit todos --quiet
./cli.py:218:if "todo" in final_result.lower():
./cli.py:219:console.print("• TODO comments detected")
./cli.py:253:if "TODO" in final_result:
./cli.py:254:todo_count = final_result.count("TODO")
./cli.py:255:console.print(f"• TODO markers found: {todo_count}")
./cli.py:316:%(prog)s --mode codebase_auditor "Find TODO comments"
./prompts/repo_hygiene.txt:10:- You focus on missing files, large files, TODO density, and committed artifacts.
./prompts/repo_hygiene.txt:25:- TODO density:
./prompts/repo_hygiene.txt:26:pattern: "TODO"
./prompts/codebase_auditor.txt:10:- You focus on TODO, FIXME, imports, and config files.
./prompts/codebase_auditor.txt:19:- TODO comments:
./prompts/codebase_auditor.txt:20:pattern: "TODO"
./__pycache__/agent.cpython-312.pyc:72:Prefer search_text for TODO, FIXME, import, and config patterns.
./__pycache__/agent.cpython-312.pyc:82:Prefer search_text for README, LICENSE, .log, TODO, and artifact patterns.
```
