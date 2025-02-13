"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import os
import json
import typer
import subprocess
from repository_manager import RepositoryManager
from prompt_engineering import PromptEngineer
from llm_integration import LLMIntegration
from tool_integration import ToolIntegration
from test_generator import generate_test_file, generate_custom_test_file
from diff_view import live_diff_view
from autotest import watch_and_run_tests
from executor import run_in_sandbox

app = typer.Typer()
CONFIG_FILE = os.path.expanduser("~/.ai_coding_agent_config.json")

def save_repo_path(repo_path: str):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"repo_path": repo_path}, f)
    except Exception as e:
        typer.echo(f"Error saving repository path: {e}")

def load_repo_path() -> str:
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("repo_path", "")
    except Exception as e:
        typer.echo(f"Error loading repository configuration: {e}")
        return ""

@app.command("init-repo")
def init_repo(repo_path: str):
    repo_manager = RepositoryManager(repo_path)
    if repo_manager.load_repository():
        save_repo_path(repo_path)
        typer.echo(f"Repository loaded successfully from {repo_path}.")
    else:
        typer.echo("Failed to load repository. Please check the path and try again.")

@app.command("query")
def query(query_text: str):
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Error: Repository not initialized. Please run 'init-repo' first.")
        raise typer.Exit(code=1)
    repo_manager = RepositoryManager(repo_path)
    if not repo_manager.load_repository():
        typer.echo("Error: Unable to load the repository from the stored path.")
        raise typer.Exit(code=1)
    code_chunks = repo_manager.get_code_chunks()
    prompt_engineer = PromptEngineer()
    prompt = prompt_engineer.build_prompt(query_text, code_chunks)
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
    tool_integration = ToolIntegration()
    result = tool_integration.run_linter(file_path)
    typer.echo("Linter Output:")
    typer.echo(result)

@app.command("test")
def run_tests():
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
        typer.echo(chunk.get("content")[:200])

@app.command("retrieve")
def retrieve(repo_path: str, query: str):
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
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Repository not initialized. Run 'init-repo' first.")
        raise typer.Exit(code=1)
    generate_test_file(file, repo_path=repo_path)
    typer.echo("Test file generation attempted.")

@app.command("generate-custom-test")
def generate_custom_test(file: str):
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Repository not initialized. Run 'init-repo' first.")
        raise typer.Exit(code=1)
    generate_custom_test_file(file, repo_path=repo_path)
    typer.echo("Custom test file generation attempted.")

@app.command("add-plugin")
def add_plugin(plugin_url: str):
    plugins_dir = os.path.join(os.getcwd(), "plugins")
    os.makedirs(plugins_dir, exist_ok=True)
    plugin_name = os.path.basename(plugin_url)
    if plugin_name.endswith(".git"):
        plugin_name = plugin_name[:-4]
    target_path = os.path.join(plugins_dir, plugin_name)
    if os.path.exists(target_path):
        typer.echo(f"Plugin '{plugin_name}' already exists.")
        raise typer.Exit()
    try:
        typer.echo(f"Cloning plugin from {plugin_url} into {target_path}...")
        subprocess.check_call(["git", "clone", plugin_url, target_path])
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error cloning plugin: {e}")
        raise typer.Exit(code=1)
    plugins_json = os.path.join(plugins_dir, "plugins.json")
    plugins_list = []
    if os.path.exists(plugins_json):
        try:
            with open(plugins_json, "r") as f:
                plugins_list = json.load(f)
        except Exception as e:
            typer.echo(f"Error reading plugins.json: {e}")
    plugins_list.append({"name": plugin_name, "url": plugin_url, "path": target_path})
    try:
        with open(plugins_json, "w") as f:
            json.dump(plugins_list, f, indent=4)
    except Exception as e:
        typer.echo(f"Error writing plugins.json: {e}")
        raise typer.Exit(code=1)
    typer.echo(f"Plugin '{plugin_name}' added successfully.")

@app.command("live-diff")
def live_diff(file_path: str):
    """
    Launch a live diff view for the specified file.
    
    Example:
      python main.py live-diff /path/to/repo/module.py
    """
    live_diff_view(file_path)

@app.command("selective-apply")
def selective_apply_cmd(original_file: str, modified_file: str):
    """
    Interactively review and apply changes from a modified file to the original file.
    
    Example:
      python main.py selective-apply /path/to/repo/module.py /path/to/repo/module_new.py
    """
    from change_selector import selective_apply
    selective_apply(original_file, modified_file)

@app.command("auto-test")
def auto_test(repo_path: str):
    """
    Watch the repository for changes and automatically run tests.
    
    Example:
      python main.py auto-test /path/to/repo
    """
    watch_and_run_tests(repo_path)

@app.command("run-sandbox")
def run_sandbox(code: str):
    """
    Execute the provided code snippet in a sandboxed environment.
    
    Example:
      python main.py run-sandbox "print('Hello from sandbox')"
    """
    output = run_in_sandbox(code)
    typer.echo("Sandboxed Execution Output:")
    typer.echo(output)

if __name__ == "__main__":
    app()
