"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import os
import json
import typer
from repository_manager import RepositoryManager
from prompt_engineering import PromptEngineer
from llm_integration import LLMIntegration
from tool_integration import ToolIntegration

# Configuration file to persist repository path
CONFIG_FILE = os.path.expanduser("~/.ai_coding_agent_config.json")
app = typer.Typer()

def save_repo_path(repo_path: str):
    """
    Save the repository path in a configuration file.
    """
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"repo_path": repo_path}, f)
    except Exception as e:
        typer.echo(f"Error saving repository path: {e}")

def load_repo_path() -> str:
    """
    Load the repository path from the configuration file.
    """
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("repo_path", "")
    except Exception as e:
        typer.echo(f"Error loading repository configuration: {e}")
        return ""

@app.command()
def init_repo(repo_path: str):
    """
    Initialize and load the Git repository.

    Format:
        python main.py init-repo <repo_path>

    Example:
        python main.py init-repo /Users/yourname/projects/my_repo
    """
    repo_manager = RepositoryManager(repo_path)
    if repo_manager.load_repository():
        save_repo_path(repo_path)
        typer.echo(f"Repository loaded successfully from {repo_path}.")
    else:
        typer.echo("Failed to load repository. Please check the path and try again.")

@app.command()
def query(query_text: str):
    """
    Send a query to the AI Coding Agent to analyze the codebase and suggest modifications.

    Format:
        python main.py query "<query_text>"

    Example:
        python main.py query "Refactor the function that calculates user age."
    """
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Error: Repository not initialized. Please run 'init-repo' first.")
        raise typer.Exit(code=1)
        
    repo_manager = RepositoryManager(repo_path)
    if not repo_manager.load_repository():
        typer.echo("Error: Unable to load the repository from the stored path.")
        raise typer.Exit(code=1)
    
    # Retrieve code chunks (with filtering for large codebases)
    code_chunks = repo_manager.get_code_chunks()
    prompt_engineer = PromptEngineer()
    prompt = prompt_engineer.build_prompt(query_text, code_chunks)
    
    # Initialize LLM integration (endpoint configurable)
    llm = LLMIntegration()  
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

    Format:
        python main.py lint <file_path>

    Example:
        python main.py lint /Users/yourname/projects/my_repo/main.py
    """
    tool_integration = ToolIntegration()
    result = tool_integration.run_linter(file_path)
    typer.echo("Linter Output:")
    typer.echo(result)

@app.command()
def test():
    """
    Run tests using pytest.
    The test runner will search for test files in the repository path stored in the configuration file.
    
    Format:
        python main.py test

    Example:
        python main.py test
    """
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Error: Repository not initialized. Please run 'init-repo' first.")
        raise typer.Exit(code=1)
    
    tool_integration = ToolIntegration()
    # Pass the repository path so that pytest is run with that directory as the current working directory.
    result = tool_integration.run_tests(repo_path)
    typer.echo("Test Results:")
    typer.echo(result)

@app.command()
def preview(original_file: str, new_file: str):
    """
    Generate a diff preview between the original file and the modified file.

    Format:
        python main.py preview <original_file> <new_file>

    Example:
        python main.py preview /Users/yourname/projects/my_repo/module.py /Users/yourname/projects/my_repo/module_new.py
    """
    tool_integration = ToolIntegration()
    try:
        with open(original_file, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(new_file, 'r', encoding='utf-8') as f:
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
def apply_changes(original_file: str, new_file: str):
    """
    Apply changes to a file after previewing the diff and receiving user confirmation.

    Format:
        python main.py apply_changes <original_file> <new_file>

    Example:
        python main.py apply_changes /Users/yourname/projects/my_repo/module.py /Users/yourname/projects/my_repo/module_new.py
    """
    tool_integration = ToolIntegration()
    try:
        with open(original_file, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(new_file, 'r', encoding='utf-8') as f:
            modified = f.read()
        diff = tool_integration.generate_diff(original, modified)
        typer.echo("Diff Preview:")
        typer.echo(diff)
        confirm = typer.confirm("Do you want to apply these changes?")
        if confirm:
            with open(original_file, 'w', encoding='utf-8') as f:
                f.write(modified)
            typer.echo("Changes applied successfully.")
        else:
            typer.echo("Operation cancelled. No changes were made.")
    except Exception as e:
        typer.echo(f"Error applying changes: {e}")

if __name__ == "__main__":
    app()
