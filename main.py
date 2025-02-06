"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gwu.edu
Created on: 02-06-2025
Updated on: 
"""

import typer
from llm_integration import LLMIntegration
from repository_manager import RepositoryManager
from prompt_engineering import PromptEngineer
from tool_integration import ToolIntegration

app = typer.Typer()

# Global instances for the modules.
llm = LLMIntegration()
prompt_engineer = PromptEngineer()
tool_integration = ToolIntegration()
repo_manager = None  # Will be initialized via the CLI command.

@app.command()
def init_repo(repo_path: str):
    """
    Initialize and load the Git repository.
    :param repo_path: The path to the Git repository.
    """
    global repo_manager
    repo_manager = RepositoryManager(repo_path)
    if repo_manager.load_repository():
        typer.echo(f"Repository loaded successfully from {repo_path}.")
    else:
        typer.echo("Failed to load repository. Please check the path and try again.")

@app.command()
def query(query_text: str):
    """
    Send a query to the AI Coding Agent to analyze the codebase and suggest modifications.
    :param query_text: The user's query or command.
    """
    if repo_manager is None:
        typer.echo("Error: Repository not initialized. Please run 'init-repo' first.")
        raise typer.Exit(code=1)

    # Retrieve code chunks; handles large repositories with chunking.
    code_chunks = repo_manager.get_code_chunks()
    # Build a prompt combining the user's query and the code context.
    prompt = prompt_engineer.build_prompt(query_text, code_chunks)
    typer.echo("Sending prompt to LLM...")
    response = llm.send_prompt(prompt)
    if response:
        typer.echo("LLM Response:")
        typer.echo(response)
    else:
        typer.echo("Failed to get a response from the LLM.")

@app.command()
def lint(file_path: str):
    """
    Run linting on the specified file.
    :param file_path: The path to the file to lint.
    """
    result = tool_integration.run_linter(file_path)
    typer.echo("Linter Output:")
    typer.echo(result)

@app.command()
def test():
    """
    Run tests using the integrated test runner.
    """
    result = tool_integration.run_tests()
    typer.echo("Test Results:")
    typer.echo(result)

@app.command()
def preview(file_path: str, new_content_file: str):
    """
    Generate a diff preview between the original file and the modified file.
    :param file_path: Path to the original file.
    :param new_content_file: Path to the file with new content.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(new_content_file, 'r', encoding='utf-8') as f:
            modified = f.read()
        diff = tool_integration.generate_diff(original, modified)
        if diff:
            typer.echo("Diff Preview:")
            typer.echo(diff)
        else:
            typer.echo("No differences found.")
    except Exception as e:
        typer.echo(f"Error generating diff: {e}")

@app.command()
def apply_changes(file_path: str, new_content_file: str):
    """
    Apply changes to a file after previewing the diff and receiving user confirmation.
    :param file_path: Path to the original file.
    :param new_content_file: Path to the file with new content.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(new_content_file, 'r', encoding='utf-8') as f:
            modified = f.read()
        diff = tool_integration.generate_diff(original, modified)
        typer.echo("Diff Preview:")
        typer.echo(diff)
        confirm = typer.confirm("Do you want to apply these changes?")
        if confirm:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified)
            typer.echo("Changes applied successfully.")
        else:
            typer.echo("Operation cancelled. No changes were made.")
    except Exception as e:
        typer.echo(f"Error applying changes: {e}")

if __name__ == "__main__":
    app()
