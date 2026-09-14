import typer
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
from auditagent.graph import build_graph
from auditagent.utils.repo import clone_repo

load_dotenv() # Load environment variables

app = typer.Typer()
console = Console()

@app.command()
def scan(
    repo_url: str = typer.Argument(..., help="The Git repository URL or local path to scan"),
    output_file: str = typer.Option("audit_report.md", "--output", "-o", help="File to save the report to")
):
    """
    Run an autonomous security and compliance audit on a repository.
    """
    console.print(f"[bold blue]Starting AuditAgent scan for:[/bold blue] {repo_url}")
    
    # Simple check if it's a remote URL or local path
    if repo_url.startswith("http://") or repo_url.startswith("https://") or repo_url.startswith("git@"):
        console.print("Cloning repository...")
        repo_path = clone_repo(repo_url)
    else:
        repo_path = repo_url
        
    console.print("Initializing LangGraph workflow...")
    workflow = build_graph()
    
    initial_state = {
        "repository_path": repo_path,
        "metadata": {},
        "findings": [],
        "verified_findings": [],
        "final_report": "",
        "errors": []
    }
    
    console.print("Running agents (this may take a few moments)...")
    try:
        # Run the graph
        final_state = workflow.invoke(initial_state)
        
        report = final_state.get("final_report", "")
        if report:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            console.print(f"[bold green]Scan complete![/bold green] Report saved to {output_file}")
            # Optionally print a preview
            # console.print(Markdown(report))
        else:
            console.print("[bold red]Scan completed but no report was generated.[/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]Error during scan:[/bold red] {str(e)}")

if __name__ == "__main__":
    app()
