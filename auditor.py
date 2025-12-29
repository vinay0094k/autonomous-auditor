#!/usr/bin/env python3
"""
Codebase Auditor - Specialized Security & Quality Analysis Agent
Built on the frozen autonomous agent core.
"""

import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from cli import run_agent_with_progress, load_config, setup_logging

console = Console()

class CodebaseAuditor:
    """Specialized agent for codebase security and quality analysis"""
    
    AUDIT_TASKS = {
        "security": "Find potential security issues: search for 'password', 'secret', 'api_key', 'token' in code files",
        "todos": "Find all TODO, FIXME, HACK comments that need attention",
        "imports": "Analyze import statements and dependencies in Python files", 
        "configs": "Find and examine configuration files like .env, config.json, settings files",
        "credentials": "Search for hardcoded credentials, keys, or sensitive data",
        "quality": "Find code quality issues: search for 'print(', 'console.log', debug statements"
    }
    
    def __init__(self, config_path="config.json"):
        self.config = load_config(config_path)
    
    def run_audit(self, audit_type: str, quiet: bool = False) -> dict:
        """Run a specific audit type"""
        if audit_type not in self.AUDIT_TASKS:
            raise ValueError(f"Unknown audit type: {audit_type}")
        
        task = self.AUDIT_TASKS[audit_type]
        
        if not quiet:
            console.print(Panel(
                f"[bold blue]Audit Type:[/bold blue] {audit_type.upper()}\n"
                f"[bold green]Task:[/bold green] {task}",
                title="🔍 Codebase Auditor"
            ))
        
        return run_agent_with_progress(task, self.config, quiet)
    
    def run_full_audit(self, quiet: bool = False) -> dict:
        """Run all audit types as separate focused tasks"""
        results = {}
        
        # Fixed sequence of specific audit tasks
        audit_tasks = [
            ("structure", "List all Python files and directories"),
            ("todos", "Find TODO comments"),
            ("fixmes", "Find FIXME comments"), 
            ("imports", "Find import statements"),
            ("configs", "Find configuration files like .env, config.json")
        ]
        
        if not quiet:
            console.print("[bold yellow]Running Full Codebase Audit...[/bold yellow]\n")
        
        for audit_name, task in audit_tasks:
            if not quiet:
                console.print(f"[cyan]Running {audit_name} audit...[/cyan]")
            
            try:
                result = run_agent_with_progress(task, self.config, quiet=True, mode="codebase_auditor")
                results[audit_name] = {
                    "status": "success" if result.get("step_success") else "failed",
                    "result": result.get("result", "No result"),
                    "steps": result.get("step_count", 0)
                }
            except Exception as e:
                results[audit_name] = {
                    "status": "error",
                    "result": str(e),
                    "steps": 0
                }
        
        if not quiet:
            self.display_audit_summary(results)
        
        return results
    
    def display_audit_summary(self, results: dict):
        """Display audit results summary"""
        table = Table(title="Audit Summary")
        table.add_column("Audit Type", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Steps", style="yellow")
        table.add_column("Result Preview", style="white")
        
        for audit_type, result in results.items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            status = f"{status_icon} {result['status']}"
            preview = result["result"][:50] + "..." if len(result["result"]) > 50 else result["result"]
            
            table.add_row(
                audit_type.upper(),
                status,
                str(result["steps"]),
                preview
            )
        
        console.print(table)

def main():
    parser = argparse.ArgumentParser(description="🔍 Codebase Auditor - Security & Quality Analysis")
    parser.add_argument("--audit", choices=list(CodebaseAuditor.AUDIT_TASKS.keys()) + ["full"], 
                       default="full", help="Type of audit to run")
    parser.add_argument("--config", default="config.json", help="Configuration file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--list", action="store_true", help="List available audit types")
    
    args = parser.parse_args()
    
    if args.list:
        console.print("[bold]Available Audit Types:[/bold]\n")
        for audit_type, description in CodebaseAuditor.AUDIT_TASKS.items():
            console.print(f"[cyan]{audit_type}[/cyan]: {description}")
        return
    
    setup_logging(args.log_level, args.quiet)
    auditor = CodebaseAuditor(args.config)
    
    try:
        if args.audit == "full":
            results = auditor.run_full_audit(args.quiet)
            if args.quiet:
                success_count = sum(1 for r in results.values() if r["status"] == "success")
                print(f"AUDIT_COMPLETE: {success_count}/{len(results)} audits successful")
        else:
            result = auditor.run_audit(args.audit, args.quiet)
            if args.quiet:
                status = "SUCCESS" if result.get("step_success") else "FAILED"
                print(f"{status}: {result.get('observation', 'No observation')}")
                
    except Exception as e:
        if args.quiet:
            print(f"ERROR: {e}")
        else:
            console.print(f"[red]Error: {e}[/red]")
        exit(1)

if __name__ == "__main__":
    main()
