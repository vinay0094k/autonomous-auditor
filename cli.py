#!/usr/bin/env python3
"""
Autonomous Agent CLI
Production wrapper for the core agent system.
"""

import argparse
import json
import logging
import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import print as rprint
from agent import AgentState, ground, plan, execute_step, act, observe, revise_plan, should_continue, init_memory, load_system_prompt
from langgraph.graph import StateGraph, END

console = Console()

def setup_logging(level: str = "INFO", quiet: bool = False):
    """Configure logging"""
    if quiet:
        logging.basicConfig(level=logging.ERROR, handlers=[logging.FileHandler('agent.log')])
    else:
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('agent.log'),
                logging.StreamHandler()
            ]
        )

def load_config(config_path: str = "config.json") -> dict:
    """Load configuration"""
    default_config = {
        "model": "llama3.2:1b",
        "max_steps": 8,
        "retry_limit": 2,
        "memory_db": "agent_memory.db"
    }
    
    if Path(config_path).exists():
        with open(config_path) as f:
            user_config = json.load(f)
            default_config.update(user_config)
    
    return default_config

def create_agent():
    """Create the agent graph"""
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
    
    return graph.compile()

def run_agent_with_progress(task: str, config: dict, quiet: bool = False, mode: str = "default") -> dict:
    """Run the agent with progress display"""
    if not quiet:
        console.print(Panel(f"[bold blue]Task:[/bold blue] {task}", title="🤖 Autonomous Agent"))
    
    init_memory()
    agent = create_agent()
    
    initial_state = {
        "task": task,
        "thought": "",
        "result": "",
        "observation": "",
        "step_count": 1,
        "tool_request": "",
        "plan": [],
        "current_step": 0,
        "environment_facts": "",
        "step_success": False,
        "failure_count": 0,
        "system_prompt": load_system_prompt(mode)
    }
    
    if quiet:
        return agent.invoke(initial_state)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task_id = progress.add_task("Executing...", total=config.get("max_steps", 8))
        
        class ProgressAgent:
            def __init__(self, agent, progress, task_id):
                self.agent = agent
                self.progress = progress
                self.task_id = task_id
                self.step = 0
            
            def invoke(self, state):
                result = self.agent.invoke(state)
                self.progress.update(self.task_id, completed=result.get("step_count", 1))
                return result
        
        progress_agent = ProgressAgent(agent, progress, task_id)
        return progress_agent.invoke(initial_state)

def display_results(result: dict, verbose: bool = False):
    """Display results in a nice format"""
    
    # Status
    status = "✅ Success" if result.get("step_success", False) else "❌ Failed"
    console.print(f"\n[bold green]{status}[/bold green]")
    
    # Add audit summary for specialized modes
    if result.get("system_prompt", "").startswith("You are a Codebase Auditor"):
        display_audit_summary(result, "codebase")
    elif result.get("system_prompt", "").startswith("You are a Config Inspector"):
        display_audit_summary(result, "config")
    elif result.get("system_prompt", "").startswith("You are a Repo Hygiene Agent"):
        display_audit_summary(result, "repo")
    
    # Summary table
    table = Table(title="Execution Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Steps Completed", str(result.get("step_count", 0)))
    table.add_row("Plan Steps", str(len(result.get("plan", []))))
    table.add_row("Current Step", str(result.get("current_step", 0)))
    table.add_row("Failures", str(result.get("failure_count", 0)))
    
    console.print(table)
    
    # Plan executed
    if result.get("plan"):
        console.print("\n[bold]Plan Executed:[/bold]")
        for i, step in enumerate(result["plan"], 1):
            status_icon = "✅" if i <= result.get("current_step", 0) else "⏳"
            action = step.get("action", "unknown")
            target = step.get("target", "")
            console.print(f"  {status_icon} {i}. {action} {target}")
    
    # Verbose output
    if verbose:
        console.print(f"\n[bold]Final Result:[/bold] {result.get('result', 'No result')}")
        console.print(f"[bold]Last Thought:[/bold] {result.get('thought', 'No thought')}")

def display_audit_summary(result: dict, mode: str = "codebase"):
    """Format output according to specified format"""
    
    if format_type == "json":
        return json.dumps({
            "task": result.get("task", ""),
            "status": "success" if result.get("step_success", False) else "failed",
            "mode": mode,
            "steps_completed": result.get("step_count", 0),
            "plan_steps": len(result.get("plan", [])),
            "failures": result.get("failure_count", 0),
            "result": result.get("result", ""),
            "plan": result.get("plan", []),
            "timestamp": datetime.datetime.now().isoformat()
        }, indent=2)
    
    elif format_type == "markdown":
        status_icon = "✅" if result.get("step_success", False) else "❌"
        md = f"""# Audit Report

**Status**: {status_icon} {"Success" if result.get("step_success", False) else "Failed"}  
**Mode**: {mode}  
**Task**: {result.get("task", "")}  
**Steps Completed**: {result.get("step_count", 0)}  
**Failures**: {result.get("failure_count", 0)}  

## Plan Executed
"""
        for i, step in enumerate(result.get("plan", []), 1):
            status = "✅" if i <= result.get("current_step", 0) else "⏳"
            action = step.get("action", "unknown")
            target = step.get("target", "")
            md += f"{status} {i}. {action} {target}\n"
        
        md += f"\n## Result\n```\n{result.get('result', 'No result')}\n```\n"
        return md
    
    elif format_type == "summary":
        status = "SUCCESS" if result.get("step_success", False) else "FAILED"
        return f"{status}: {result.get('observation', 'No observation')} | Steps: {result.get('step_count', 0)} | Failures: {result.get('failure_count', 0)}"
    
    else:  # console format
        return None  # Use existing display_results function
    """Display audit-specific summary"""
    if mode == "codebase":
        console.print("\n[bold yellow]Codebase Audit Summary:[/bold yellow]")
        final_result = result.get("result", "")
        
        if "import" in final_result.lower():
            import_count = final_result.count("import")
            console.print(f"• Import statements found: {import_count}")
        
        if "todo" in final_result.lower():
            console.print("• TODO comments detected")
        
        if "config" in final_result.lower() or ".env" in final_result or "config.json" in final_result:
            console.print("• Configuration files present")
            
    elif mode == "config":
        console.print("\n[bold yellow]Config Inspection Summary:[/bold yellow]")
        final_result = result.get("result", "")
        
        if ".env" in final_result:
            console.print("• Environment files detected")
        
        if "config.json" in final_result or "settings" in final_result.lower():
            console.print("• Configuration files found")
            
        if "debug" in final_result.lower() or "localhost" in final_result.lower():
            console.print("• Development flags detected")
        
        if "dev" in final_result.lower() or "test" in final_result.lower():
            console.print("• Environment indicators found")
            
    elif mode == "repo":
        console.print("\n[bold yellow]Repository Hygiene Summary:[/bold yellow]")
        final_result = result.get("result", "")
        
        if "README" in final_result:
            console.print("• README file present")
        
        if "LICENSE" in final_result:
            console.print("• LICENSE file present")
            
        if ".log" in final_result or "log" in final_result.lower():
            console.print("• Log files detected")
        
        if "TODO" in final_result:
            todo_count = final_result.count("TODO")
            console.print(f"• TODO markers found: {todo_count}")
            
        if ".tmp" in final_result or ".class" in final_result:
            console.print("• Build artifacts detected")
    
    # Count files analyzed
    if "SUCCESS:" in result.get("result", ""):
        console.print(f"• Analysis completed successfully")
    
    console.print("")

def format_output(result: dict, format_type: str, mode: str = "default") -> str:
    """Format output according to specified format"""
    
    if format_type == "json":
        return json.dumps({
            "task": result.get("task", ""),
            "status": "success" if result.get("step_success", False) else "failed",
            "mode": mode,
            "steps_completed": result.get("step_count", 0),
            "plan_steps": len(result.get("plan", [])),
            "failures": result.get("failure_count", 0),
            "result": result.get("result", ""),
            "plan": result.get("plan", []),
            "environment_facts": result.get("environment_facts", ""),
            "observation": result.get("observation", ""),
            "timestamp": datetime.datetime.now().isoformat(),
            "exit_code": result.get("exit_code", 0)
        }, indent=2)
    
    elif format_type == "markdown":
        status_icon = "✅" if result.get("step_success", False) else "❌"
        md = f"""# Audit Report

**Status**: {status_icon} {"Success" if result.get("step_success", False) else "Failed"}  
**Mode**: {mode}  
**Task**: {result.get("task", "")}  
**Steps Completed**: {result.get("step_count", 0)}  
**Failures**: {result.get("failure_count", 0)}  

## Plan Executed
"""
        for i, step in enumerate(result.get("plan", []), 1):
            status = "✅" if i <= result.get("current_step", 0) else "⏳"
            action = step.get("action", "unknown")
            target = step.get("target", "")
            md += f"{status} {i}. {action} {target}\n"
        
        md += f"\n## Result\n```\n{result.get('result', 'No result')}\n```\n"
        return md
    
    elif format_type == "summary":
        status = "SUCCESS" if result.get("step_success", False) else "FAILED"
        return f"{status}: {result.get('observation', 'No observation')} | Steps: {result.get('step_count', 0)} | Failures: {result.get('failure_count', 0)}"
    
    else:  # console format
        return None  # Use existing display_results function

def determine_exit_code(result: dict) -> int:
    """Determine exit code based on result"""
    if not result.get("step_success", False):
        return 2  # Failure
    
    # Check for warnings based on content
    final_result = result.get("result", "").lower()
    observation = result.get("observation", "").lower()
    
    # Warning conditions
    warning_indicators = [
        "todo" in final_result and final_result.count("todo") > 10,
        "fixme" in final_result,
        "debug" in final_result,
        "localhost" in final_result,
        "password" in final_result or "secret" in final_result,
        result.get("failure_count", 0) > 0
    ]
    
    if any(warning_indicators):
        return 1  # Warning
    
    return 0  # Success

def main():
    parser = argparse.ArgumentParser(
        description="A deterministic, CI-native repository hygiene gate that enforces policy using bounded, explainable analysis — not heuristics or learning.",
        epilog="""
Examples:
  %(prog)s "Audit this codebase"
  %(prog)s --mode codebase_auditor "Find TODO comments"
  %(prog)s --mode codebase_auditor "Search for import statements" --verbose
  %(prog)s "List files" --quiet --out results.json

Exit Codes:
  0 - Success (no issues found)
  1 - Warning (issues found, but not critical)
  2 - Failure (critical issues or execution failed)

For more information, visit: https://github.com/yourusername/autonomous-auditor
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("task", help="Task for the agent to execute")
    parser.add_argument("--config", default="config.json", help="Configuration file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--mode", default="default", choices=["default", "codebase_auditor", "config_inspector", "repo_hygiene"], help="Agent mode")
    parser.add_argument("--format", default="console", choices=["console", "json", "markdown", "summary"], help="Output format")
    parser.add_argument("--out", help="Output file for results")
    parser.add_argument("--json", action="store_true", help="Output results as JSON to stdout")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    
    args = parser.parse_args()
    
    setup_logging(args.log_level, args.quiet)
    config = load_config(args.config)
    
    try:
        result = run_agent_with_progress(args.task, config, args.quiet, args.mode)
        
        # Determine exit code
        exit_code = determine_exit_code(result)
        
        # Add metadata for report artifacts
        if args.out:
            # Enhanced metadata for artifacts
            metadata = {
                "timestamp": datetime.datetime.now().isoformat(),
                "repo_path": str(Path.cwd()),
                "specialization": args.mode,
                "version": "v1.0.0",
                "exit_code": exit_code
            }
            
            # Try to get commit hash
            try:
                import subprocess
                commit_hash = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], 
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                metadata["commit_hash"] = commit_hash
            except:
                metadata["commit_hash"] = "unknown"
            
            result.update(metadata)
        
        # Determine mode for output formatting
        mode = args.mode if args.mode != "default" else "general"
        
        # Handle different output formats
        if args.format != "console":
            formatted_output = format_output(result, args.format, mode)
            
            if args.out:
                with open(args.out, 'w') as f:
                    f.write(formatted_output)
                if not args.quiet:
                    console.print(f"[green]Results saved to {args.out}[/green]")
            else:
                print(formatted_output)
        else:
            # Console format (existing behavior)
            if args.out:
                with open(args.out, 'w') as f:
                    json.dump(result, f, indent=2)
                if not args.quiet:
                    console.print(f"[green]Results saved to {args.out}[/green]")
            
            if args.json:
                # Legacy --json flag support
                json_output = {
                    "task": result.get("task", ""),
                    "status": "success" if result.get("step_success", False) else "failed",
                    "steps_completed": result.get("step_count", 0),
                    "plan_steps": len(result.get("plan", [])),
                    "failures": result.get("failure_count", 0),
                    "result": result.get("result", ""),
                    "plan": result.get("plan", []),
                    "exit_code": exit_code
                }
                print(json.dumps(json_output, indent=2))
            elif not args.quiet:
                display_results(result, args.verbose)
            else:
                # Quiet mode - just print success/failure
                status = "SUCCESS" if result.get("step_success", False) else "FAILED"
                print(f"{status}: {result.get('observation', 'No observation')}")
        
        # Exit with appropriate code
        exit(exit_code)
            
    except Exception as e:
        if args.quiet:
            print(f"ERROR: {e}")
        else:
            console.print(f"[red]Error: {e}[/red]")
        exit(2)  # Always exit 2 for exceptions

if __name__ == "__main__":
    main()
