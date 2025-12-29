#!/usr/bin/env python3
"""
Autonomous Agent CLI
Production wrapper for the core agent system.
"""

import argparse
import json
import logging
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
    
    # Add audit summary for codebase_auditor mode
    if result.get("system_prompt", "").startswith("You are a Codebase Auditor"):
        display_audit_summary(result)
    
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

def display_audit_summary(result: dict):
    """Display audit-specific summary"""
    console.print("\n[bold yellow]Audit Summary:[/bold yellow]")
    
    # Simple pattern matching on results
    final_result = result.get("result", "")
    
    if "import" in final_result.lower():
        import_count = final_result.count("import")
        console.print(f"• Import statements found: {import_count}")
    
    if "todo" in final_result.lower():
        console.print("• TODO comments detected")
    
    if "config" in final_result.lower() or ".env" in final_result or "config.json" in final_result:
        console.print("• Configuration files present")
    
    # Count files analyzed
    if "SUCCESS:" in final_result:
        console.print(f"• Analysis completed successfully")
    
    console.print("")

def main():
    parser = argparse.ArgumentParser(description="🤖 Autonomous Agent CLI")
    parser.add_argument("task", help="Task for the agent to execute")
    parser.add_argument("--config", default="config.json", help="Configuration file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--mode", default="default", choices=["default", "codebase_auditor"], help="Agent mode")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    
    args = parser.parse_args()
    
    setup_logging(args.log_level, args.quiet)
    config = load_config(args.config)
    
    try:
        result = run_agent_with_progress(args.task, config, args.quiet, args.mode)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            if not args.quiet:
                console.print(f"[green]Results saved to {args.output}[/green]")
        
        if not args.quiet:
            display_results(result, args.verbose)
        else:
            # Quiet mode - just print success/failure
            status = "SUCCESS" if result.get("step_success", False) else "FAILED"
            print(f"{status}: {result.get('observation', 'No observation')}")
            
    except Exception as e:
        if args.quiet:
            print(f"ERROR: {e}")
        else:
            console.print(f"[red]Error: {e}[/red]")
        exit(1)

if __name__ == "__main__":
    main()
