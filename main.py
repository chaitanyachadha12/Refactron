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

# For autonomous test file generation
from test_generator import generate_test_file
app = typer.Typer()

# Configuration file to persist repository path
CONFIG_FILE = os.path.expanduser("~/.ai_coding_agent_config.json")

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

@app.command("init-repo")
def init_repo(repo_path: str):
    """
    Initialize and load the Git repository.

    Example:
      python main.py init-repo /Users/yourname/projects/my_repo
    """
    repo_manager = RepositoryManager(repo_path)
    if repo_manager.load_repository():
        save_repo_path(repo_path)
        typer.echo(f"Repository loaded successfully from {repo_path}.")
    else:
        typer.echo("Failed to load repository. Please check the path and try again.")

@app.command("query")
def query(query_text: str):
    """
    Send a query to the AI Coding Agent to analyze the codebase and suggest modifications.

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
    
    # Retrieve code chunks (with intelligent chunking)
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

@app.command("lint")
def lint(file_path: str):
    """
    Run linting on the specified file.

    Example:
      python main.py lint /Users/yourname/projects/my_repo/main.py
    """
    tool_integration = ToolIntegration()
    result = tool_integration.run_linter(file_path)
    typer.echo("Linter Output:")
    typer.echo(result)

@app.command("test")
def run_tests():
    """
    Run tests using pytest.
    The test runner will search for test files in the repository path stored in the configuration file.

    Example:
      python main.py test
    """
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Error: Repository not initialized. Please run 'init-repo' first.")
        raise typer.Exit(code=1)
    
    tool_integration = ToolIntegration()
    result = tool_integration.run_tests(repo_path)
    typer.echo("Test Results:")
    typer.echo(result)

@app.command("preview")
def preview(original_file: str, new_file: str):
    """
    Generate a diff preview between the original file and the modified file.

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

@app.command("apply_changes")
def apply_changes(original_file: str, new_file: str):
    """
    Apply changes to a file after previewing the diff and receiving user confirmation.

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

@app.command("scan")
def scan(repo_path: str):
    """
    Scan the repository and display extracted code chunks (using intelligent AST-based chunking for Python files).

    Example:
      python main.py scan --repo-path small_project
    """
    repo_manager = RepositoryManager(repo_path)
    if not repo_manager.load_repository():
        typer.echo("Failed to load repository.")
        raise typer.Exit(code=1)
    chunks = repo_manager.get_code_chunks()
    typer.echo("Extracted code chunks:")
    for chunk in chunks:
        typer.echo(f"\nFile: {chunk.get('file')}, Modified: {chunk.get('modified')}")
        if 'name' in chunk:
            typer.echo(f"Type: {chunk.get('type')}, Name: {chunk.get('name')}")
        typer.echo("Snippet:")
        typer.echo(chunk.get("content")[:200])  # Show first 200 characters

@app.command("retrieve")
def retrieve(repo_path: str, query: str):
    """
    Retrieve and display the prompt built from the most relevant code chunks using the retrieval module.

    Example:
      python main.py retrieve --repo-path small_project --query "How to add two numbers?"
    """
    repo_manager = RepositoryManager(repo_path)
    if not repo_manager.load_repository():
        typer.echo("Failed to load repository.")
        raise typer.Exit(code=1)
    chunks = repo_manager.get_code_chunks()
    prompt_engineer = PromptEngineer()
    prompt = prompt_engineer.build_prompt(query, chunks)
    typer.echo("Generated Prompt:")
    typer.echo(prompt)

@app.command("generate-test")
def generate_test(file: str):
    """
    Generate a skeleton test file for the specified Python file.

    Example:
      python main.py generate-test --file small_project/app.py
    """
    generate_test_file(file)
    typer.echo("Test file generation attempted.")

@app.command("add-plugin")
def add_plugin(plugin_url: str):
    """
    Add an external plugin to Refactron.
    This is a stub command. Actual plugin installation logic should be implemented here.

    Example:
      python main.py add-plugin --plugin-url https://example.com/myplugin.git
    """
    # Stub: Implement your plugin installation logic here
    typer.echo(f"Plugin {plugin_url} added successfully (stub).")

if __name__ == "__main__":
    app()
