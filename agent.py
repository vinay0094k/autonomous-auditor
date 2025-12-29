from typing import TypedDict
from langgraph.graph import StateGraph, END
import ollama
import subprocess
import sqlite3
import datetime
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get model and host from environment
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# Configure Ollama client
import ollama
ollama_client = ollama.Client(host=OLLAMA_HOST)

# Plan schema - single source of truth
PLAN_SCHEMA = {
    "read_text_file": {"requires_target": True},
    "describe_binary_file": {"requires_target": True},
    "search_text": {"requires_target": True},
    "list_dir": {"requires_target": False}, 
    "pwd": {"requires_target": False},
    "whoami": {"requires_target": False}
}

BINARY_EXTENSIONS = {'.db', '.sqlite', '.bin', '.exe', '.so', '.dylib', '.dll', '.jpg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz'}
TEXT_EXTENSIONS = {'.md', '.txt', '.py', '.toml', '.json', '.yaml', '.yml', '.lock', '.gitignore', '.env'}

def classify_file_type(filename: str) -> str:
    """Classify file as text or binary based on extension"""
    if '.' not in filename:
        return 'text'  # Default for files without extension
    
    ext = '.' + filename.split('.')[-1].lower()
    
    if ext in BINARY_EXTENSIONS:
        return 'binary'
    elif ext in TEXT_EXTENSIONS:
        return 'text'
    else:
        return 'text'  # Default to text for unknown extensions

def annotate_environment_facts(raw_facts: str) -> str:
    """Add file type annotations to environment facts"""
    lines = raw_facts.split('\n')
    annotated = []
    
    for line in lines:
        if line.strip() and not line.startswith('total') and not line.startswith('drwx'):
            # Extract filename from ls -la output
            parts = line.split()
            if len(parts) >= 9:
                filename = parts[-1]
                if not filename.startswith('.') or filename in ['.gitignore', '.python-version']:
                    file_type = classify_file_type(filename)
                    line += f" [{file_type}]"
        annotated.append(line)
    
    return '\n'.join(annotated)

def validate_plan(plan_json: str) -> dict:
    """Validate and parse plan JSON"""
    try:
        plan = json.loads(plan_json)
        
        # Check required structure
        if not isinstance(plan, dict) or "steps" not in plan:
            return None
            
        if not isinstance(plan["steps"], list):
            return None
            
        # Validate each step
        for step in plan["steps"]:
            if not isinstance(step, dict) or "action" not in step:
                return None
                
            action = step["action"]
            if action not in PLAN_SCHEMA:
                return None
                
            # Check if target is required
            if PLAN_SCHEMA[action]["requires_target"] and "target" not in step:
                return None
                
            # Validate search_text specific fields
            if action == "search_text":
                if "pattern" not in step:
                    return None
                # Ensure max_results is reasonable
                if "max_results" in step and step["max_results"] > 50:
                    step["max_results"] = 50
                elif "max_results" not in step:
                    step["max_results"] = 20
                
        return plan
        
    except json.JSONDecodeError:
        return None

class AgentState(TypedDict):
    task: str
    thought: str
    result: str
    observation: str
    step_count: int
    tool_request: str
    plan: list
    current_step: int
    environment_facts: str
    step_success: bool
    failure_count: int
    system_prompt: str

# Initialize memory database
def init_memory():
    conn = sqlite3.connect('agent_memory.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS memories 
                    (id INTEGER PRIMARY KEY, timestamp TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def save_memory(content: str):
    conn = sqlite3.connect('agent_memory.db')
    timestamp = datetime.datetime.now().isoformat()
    conn.execute("INSERT INTO memories (timestamp, content) VALUES (?, ?)", (timestamp, content))
    conn.commit()
    conn.close()

def save_smart_memory(task: str, result: str, success: bool):
    # Only save meaningful experiences
    if "output:" in result or "failed" in result or "Cannot" in result:
        status = "SUCCESS" if success else "FAILED"
        memory = f"{status}: {task} -> {result[:100]}"
        save_memory(memory)

def recall_smart_memory(task: str) -> str:
    conn = sqlite3.connect('agent_memory.db')
    # Look for similar tasks or failures
    cursor = conn.execute("""
        SELECT content FROM memories 
        WHERE content LIKE ? OR content LIKE ? OR content LIKE ?
        ORDER BY timestamp DESC LIMIT 2
    """, (f"%{task}%", f"%FAILED%", f"%{task.split(':')[0] if ':' in task else task}%"))
    memories = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if memories:
        return f"Past experience: {' | '.join(memories)}"
    return "No relevant experience"

def ground(state: AgentState) -> AgentState:
    print("🌍 Grounding...")
    
    # Gather environment facts
    try:
        pwd_result = subprocess.run("pwd", shell=True, capture_output=True, text=True, timeout=5)
        ls_result = subprocess.run("ls -la", shell=True, capture_output=True, text=True, timeout=5)
        
        raw_facts = f"Current directory: {pwd_result.stdout.strip()}\nContents: {ls_result.stdout.strip()}"
        state["environment_facts"] = annotate_environment_facts(raw_facts)
    except:
        state["environment_facts"] = "Environment inspection failed"
    
    return state

def load_system_prompt(mode: str = "default") -> str:
    """Load system prompt based on mode"""
    prompt_file = f"prompts/{mode}.txt"
    if Path(prompt_file).exists():
        with open(prompt_file) as f:
            return f.read().strip()
    else:
        return "You are a helpful autonomous agent."

def plan(state: AgentState) -> AgentState:
    print("📋 Planning...")
    
    if not state["plan"]:
        # Get system prompt from state or use default
        system_prompt = state.get("system_prompt", "")
        
        # Create specialization overlay (short and focused)
        specialization_overlay = ""
        if "Codebase Auditor" in system_prompt:
            specialization_overlay = """
SPECIALIZATION CONTEXT:
You are operating in Codebase Auditor mode.
Your goal is to audit a source code repository.
Prefer search_text for TODO, FIXME, import, and config patterns.
"""

        prompt = f"""{specialization_overlay}

Task: {state['task']}
Environment: {state['environment_facts']}

You MUST output ONLY valid JSON.
Do NOT include explanations.
Do NOT include markdown.
Do NOT include backticks.
If unsure, output an empty JSON object {{}}.

MANDATORY RULE: If the user request includes words like "find", "search", "locate", "count", or "where", you MUST use the search_text action.
Do NOT use read_text_file for searching when search_text is available.

Example:
User: Find import statements in Python files
Required plan: {{"steps": [{{"action": "search_text", "pattern": "import", "target": ".", "max_results": 20}}]}}

Valid actions:
- search_text: find plain text in files (pattern: plain string, target: directory/file, max_results: number ≤50)
- read_text_file: for [text] files only (use actual filenames from environment)
- describe_binary_file: for [binary] files only (use actual filenames from environment)  
- list_dir: list directory contents
- pwd: show current directory

Use ONLY files that exist in the environment above.
For search_text: use plain strings only, no regex.
Output ONLY the JSON."""

        for attempt in range(2):
            try:
                response = ollama_client.chat(model=OLLAMA_MODEL, messages=[
                    {'role': 'user', 'content': prompt}
                ])
                
                plan = validate_plan(response['message']['content'].strip())
                if plan:
                    state["plan"] = plan["steps"]
                    state["current_step"] = 0
                    break
                else:
                    print(f"❌ Invalid plan format, attempt {attempt + 1}")
                    
            except Exception as e:
                print(f"❌ Plan generation failed: {e}")
        
        # Fallback if all attempts fail
        if not state["plan"]:
            state["plan"] = [
                {"action": "list_dir"},
                {"action": "read_text_file", "target": "README.md"},
                {"action": "pwd"}
            ]
            state["current_step"] = 0
    
    return state

def execute_step(state: AgentState) -> AgentState:
    print(f"⚙️ Executing step {state['current_step']+1}...")
    
    if state["current_step"] < len(state["plan"]):
        # Execute from structured plan
        step = state["plan"][state["current_step"]]
        action = step["action"]
        target = step.get("target", "")
        
        # Convert to tool request format
        if action == "read_text_file":
            state["tool_request"] = f"read_text:{target}"
        elif action == "describe_binary_file":
            state["tool_request"] = f"describe_binary:{target}"
        elif action == "search_text":
            pattern = step.get("pattern", "")
            max_results = step.get("max_results", 20)
            state["tool_request"] = f"search_text:{pattern}:{target}:{max_results}"
        elif action == "list_dir":
            if target:
                state["tool_request"] = f"ls {target}"
            else:
                state["tool_request"] = "ls"
        elif action == "pwd":
            state["tool_request"] = "pwd"
        elif action == "whoami":
            state["tool_request"] = "whoami"
        else:
            state["tool_request"] = "ls"  # Safe fallback
            
        state["thought"] = f"Executing: {action} {target}".strip()
    else:
        state["thought"] = "Plan completed"
        state["tool_request"] = "ls"
    
    return state

def parse_tool_request(raw_request: str) -> str:
    """Extract single valid tool request from LLM output"""
    lines = raw_request.strip().split('\n')
    
    # Find first valid tool request
    for line in lines:
        line = line.strip()
        if line.startswith('read_text:') or line.startswith('describe_binary:') or line.startswith('search_text:'):
            return line
        elif line in ['ls', 'pwd', 'whoami'] or line.startswith('ls '):
            return line
    
    # Fallback to safe default
    return 'ls'

def search_text_safe(pattern: str, path: str, max_results: int) -> str:
    """Safe text search with hard limits"""
    import os
    import re
    
    # Validate inputs
    if not pattern or len(pattern) > 100:
        return "Invalid pattern"
    
    if not path or '..' in path:
        return "Invalid path"
        
    # Ensure we stay in current directory
    abs_path = os.path.abspath(path)
    current_dir = os.getcwd()
    if not abs_path.startswith(current_dir):
        return "Path outside working directory"
    
    results = []
    files_checked = 0
    max_files = 50
    
    try:
        if os.path.isfile(path):
            # Search single file
            if classify_file_type(path) == 'text':
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.lower() in line.lower():
                            results.append(f"{path}:{line_num}:{line.strip()[:100]}")
                            if len(results) >= max_results:
                                break
        else:
            # Search directory
            for root, dirs, files in os.walk(path):
                for file in files:
                    if files_checked >= max_files:
                        break
                    
                    file_path = os.path.join(root, file)
                    if classify_file_type(file) == 'text':
                        files_checked += 1
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_num, line in enumerate(f, 1):
                                    if pattern.lower() in line.lower():
                                        results.append(f"{file_path}:{line_num}:{line.strip()[:100]}")
                                        if len(results) >= max_results:
                                            break
                        except:
                            continue
                        
                        if len(results) >= max_results:
                            break
                            
                if len(results) >= max_results or files_checked >= max_files:
                    break
        
        if not results:
            return f"No matches found for '{pattern}'"
        
        summary = f"Found {len(results)} matches"
        if len(results) >= max_results:
            summary += f" (limited to {max_results})"
        if files_checked >= max_files:
            summary += f" (searched {max_files} files)"
            
        return summary + ":\n" + "\n".join(results)
        
    except Exception as e:
        return f"Search failed: {str(e)[:50]}"

def act(state: AgentState) -> AgentState:
    print("⚙️ Acting...")
    
    # Parse and validate tool request
    requested = parse_tool_request(state["tool_request"])
    
    try:
        # Handle text file reading
        if requested.startswith("read_text:"):
            filename = requested[10:].strip()
            with open(filename, 'r') as f:
                content = f.read()[:200]
            state["result"] = f"SUCCESS: Read text file {filename} - {content}..."
            
        # Handle binary file description
        elif requested.startswith("describe_binary:"):
            filename = requested[16:].strip()
            import os
            size = os.path.getsize(filename)
            ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
            
            if ext == 'db':
                description = f"SQLite database file, Size: {size} bytes, Purpose: agent memory storage"
            else:
                description = f"Binary file ({ext}), Size: {size} bytes"
                
            state["result"] = f"SUCCESS: {description}"
            
        # Handle text search
        elif requested.startswith("search_text:"):
            parts = requested[12:].split(':', 2)
            if len(parts) >= 3:
                pattern, path, max_results = parts[0], parts[1], int(parts[2])
                search_result = search_text_safe(pattern, path, max_results)
                state["result"] = f"SUCCESS: {search_result}"
            else:
                state["result"] = "FAILED: Invalid search_text format"
            
        # Handle shell commands  
        elif requested in ["ls", "pwd", "whoami"] or requested.startswith("ls "):
            result = subprocess.run(requested, shell=True, capture_output=True, text=True, timeout=5)
            state["result"] = f"SUCCESS: {requested} - {result.stdout.strip()}"
            
        else:
            # Fallback with retry
            result = subprocess.run("ls", shell=True, capture_output=True, text=True, timeout=5)
            state["result"] = f"FALLBACK: Used ls instead - {result.stdout.strip()}"
            
    except Exception as e:
        state["result"] = f"FAILED: {requested} - {str(e)[:100]}"
    
    return state

def revise_plan(state: AgentState) -> AgentState:
    print("🔧 Revising plan...")
    
    failed_step = state["plan"][state["current_step"]]
    remaining_steps = state["plan"][state["current_step"]+1:]
    
    prompt = f"""The step {failed_step} failed repeatedly.
Task: {state['task']}
Environment: {state['environment_facts']}
Remaining steps: {remaining_steps}

Create a revised plan that skips the failed step and continues the task.
Output ONLY valid JSON:
{{"steps": [{{"action": "list_dir"}}, {{"action": "read_text_file", "target": "actual_file.py"}}]}}

Valid actions: read_text_file, describe_binary_file, list_dir, pwd, whoami
Use ONLY actual files from environment."""

    try:
        response = ollama_client.chat(model=OLLAMA_MODEL, messages=[
            {'role': 'user', 'content': prompt}
        ])
        
        revised_plan = validate_plan(response['message']['content'].strip())
        if revised_plan:
            state["plan"] = revised_plan["steps"]
            state["current_step"] = 0
            state["failure_count"] = 0
            print(f"✅ Plan revised with {len(revised_plan['steps'])} steps")
        else:
            # Safe fallback revision
            state["plan"] = [{"action": "list_dir"}, {"action": "pwd"}]
            state["current_step"] = 0
            state["failure_count"] = 0
            print("✅ Used fallback revised plan")
            
    except Exception as e:
        # Emergency fallback
        state["plan"] = [{"action": "pwd"}]
        state["current_step"] = 0
        state["failure_count"] = 0
        print(f"✅ Emergency plan revision: {e}")
    
    return state
    print("👁️ Observing...")
    
    # Verify step completion
    state["step_success"] = state["result"].startswith("SUCCESS:")
    
    if state["step_success"]:
        step = state["plan"][state["current_step"]]
        print(f"✅ Step {state['current_step']+1} completed: {step['action']} {step.get('target', '')}")
        state["current_step"] += 1
        state["failure_count"] = 0  # Reset failure count on success
    else:
        step = state["plan"][state["current_step"]]
        state["failure_count"] += 1
        print(f"❌ Step {state['current_step']+1} failed ({state['failure_count']}/2): {step['action']} {step.get('target', '')}")
        # Keep current_step same to retry
    
    state["observation"] = f"Step {state['step_count']} done - Success: {state['step_success']}"
    
    # Smart memory: save with success status
    if state["current_step"] <= len(state["plan"]):
        step_desc = f"{state['plan'][min(state['current_step']-1, len(state['plan'])-1)]['action']}"
        save_smart_memory(step_desc, state['result'], state['step_success'])
    
    state["step_count"] += 1
    return state

def observe(state: AgentState) -> AgentState:
    print("👁️ Observing...")
    
    # Verify step completion
    state["step_success"] = state["result"].startswith("SUCCESS:")
    
    if state["step_success"]:
        step = state["plan"][state["current_step"]]
        print(f"✅ Step {state['current_step']+1} completed: {step['action']} {step.get('target', '')}")
        state["current_step"] += 1
        state["failure_count"] = 0  # Reset failure count on success
    else:
        step = state["plan"][state["current_step"]]
        state["failure_count"] += 1
        print(f"❌ Step {state['current_step']+1} failed ({state['failure_count']}/2): {step['action']} {step.get('target', '')}")
    
    state["observation"] = f"Step {state['step_count']} done - Success: {state['step_success']}"
    
    # Smart memory: save with success status
    if state["current_step"] <= len(state["plan"]):
        step_desc = f"{state['plan'][min(state['current_step'] if state['step_success'] else state['current_step'], len(state['plan'])-1)]['action']}"
        save_smart_memory(step_desc, state['result'], state['step_success'])
    
    state["step_count"] += 1
    return state

def should_continue(state: AgentState) -> str:
    # Check if current step failed too many times
    if state["failure_count"] >= 2:
        print("🔧 Too many failures - triggering plan revision")
        return "revise_plan"
    
    # Stop when plan is complete or max steps reached
    if state["current_step"] >= len(state["plan"]):
        print("🛑 Stopping - plan completed")
        return END
    elif state["step_count"] >= 8:
        print("🛑 Stopping - reached max steps")
        return END
    else:
        remaining = len(state["plan"]) - state["current_step"]
        print(f"🔄 Continuing... ({remaining} steps remaining)")
        return "execute_step"

# Initialize memory on startup
init_memory()

graph = StateGraph(AgentState)

graph.add_node("ground", ground)
graph.add_node("plan", plan)
graph.add_node("execute_step", execute_step)
graph.add_node("act", act)
graph.add_node("observe", observe)
graph.add_node("revise_plan", revise_plan)

graph.add_edge("ground", "plan")
graph.add_edge("plan", "execute_step")
graph.add_edge("execute_step", "act")
graph.add_edge("act", "observe")
graph.add_edge("revise_plan", "execute_step")
graph.add_conditional_edges("observe", should_continue)
graph.set_entry_point("ground")

agent = graph.compile()

initial_state = {
    "task": "Explore this directory",
    "thought": "",
    "result": "",
    "observation": "",
    "step_count": 1,
    "tool_request": "",
    "plan": [],
    "current_step": 0,
    "environment_facts": "",
    "step_success": False,
    "failure_count": 0
}

final_state = agent.invoke(initial_state)

print("\n✅ Final State:")
print(final_state)
