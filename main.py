"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import os
import sys
import re
import json
import time
import threading
import subprocess
import typer
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
    """Save the repository path in a configuration file."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"repo_path": repo_path}, f)
    except Exception as e:
        typer.echo(f"Error saving repository path: {e}")

def load_repo_path() -> str:
    """Load the repository path from the configuration file."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("repo_path", "")
    except Exception as e:
        typer.echo(f"Error loading repository configuration: {e}")
        return ""

def resolve_path(path: str, full: bool) -> str:
    """
    Resolve a given file/directory path. If 'full' is False, join it with the repo path.
    """
    if full:
        return path
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Repository not initialized. Run 'init-repo' first.")
        raise typer.Exit(code=1)
    return os.path.join(repo_path, path)

#####################################
# LLM Thinking Indicator
#####################################
def thinking_indicator(stop_event: threading.Event):
    """Prints an in-place 'Thinking...' message updating every 10 seconds until stop_event is set."""
    while not stop_event.is_set():
        sys.stdout.write("\rThinking...   ")
        sys.stdout.flush()
        for _ in range(10):
            if stop_event.is_set():
                break
            time.sleep(1)
    sys.stdout.write("\r" + " " * 20 + "\r")
    sys.stdout.flush()

#####################################
# Utility: Fix a single file for syntax errors
#####################################
def fix_file(file_path: str, auto_apply: bool = False):
    """
    Scan a file for syntax errors. If found, use the LLM to generate a fix.
    If auto_apply is False, prompt the user to apply the fix.
    Returns True if a fix was applied, False otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Try compiling the file
        compile(content, file_path, 'exec')
        typer.echo(f"No syntax errors in {file_path}.")
        return False
    except SyntaxError as e:
        typer.echo(f"Syntax error in {file_path}: {e}")
        llm = LLMIntegration()
        prompt = (
            f"The following file has a syntax error:\n\n{content}\n\n"
            f"The error message is: {e}\n\n"
            "Please provide a fixed version of the file. Provide only the modified file content."
        )
        fix = llm.send_prompt(prompt)
        if fix:
            typer.echo("Proposed fix:")
            typer.echo(fix)
            if auto_apply or typer.confirm("Apply this fix to the file?"):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(fix)
                typer.echo(f"Fix applied to {file_path}.")
                return True
            else:
                typer.echo("Fix not applied.")
                return False
        else:
            typer.echo("LLM did not return a fix.")
            return False

#####################################
# Commands
#####################################

@app.command("init-repo", help="Initialize and load the Git repository.\nExample: python main.py init-repo /path/to/repo")
def init_repo(repo_path: str):
    repo_manager = RepositoryManager(repo_path)
    if repo_manager.load_repository():
        save_repo_path(repo_path)
        typer.echo(f"Repository loaded successfully from {repo_path}.")
    else:
        typer.echo("Failed to load repository. Please check the path and try again.")

@app.command("query", help="Send a query to the AI Coding Agent.\nExample: python main.py query \"How to add two numbers?\"")
def query(query_text: str):
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Error: Repository not initialized. Run 'init-repo' first.")
        raise typer.Exit(code=1)
    repo_manager = RepositoryManager(repo_path)
    if not repo_manager.load_repository():
        typer.echo("Error: Unable to load repository from stored path.")
        raise typer.Exit(code=1)
    code_chunks = repo_manager.get_code_chunks()
    prompt_engineer = PromptEngineer()
    prompt = prompt_engineer.build_prompt(query_text, code_chunks)
    llm = LLMIntegration()
    stop_event = threading.Event()
    indicator_thread = threading.Thread(target=thinking_indicator, args=(stop_event,))
    indicator_thread.start()
    response = llm.send_prompt(prompt)
    stop_event.set()
    indicator_thread.join()
    if response:
        typer.echo("LLM Response:")
        typer.echo(response)
    else:
        typer.echo("Failed to get a response from the LLM.")

@app.command("lint", help="Run linting on files.\nExamples:\n  python main.py lint app/app.py\n  python main.py lint -a\n  python main.py lint app/app.py -s\n  python main.py lint app/app.py -a -s\nUse -p flag for full paths.")
def lint(
    file_path: str = typer.Argument("", help="Path to file (relative to repo) if not using --full-path"),
    all_files: bool = typer.Option(False, "--all", "-a", help="Lint all eligible files (excluding tests)"),
    suggest: bool = typer.Option(False, "--suggest", "-s", help="Automatically apply lint suggestions"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat file_path as a full path")
):
    tool_integration = ToolIntegration()
    results = []
    if all_files:
        repo_path = load_repo_path()
        if not repo_path:
            typer.echo("Repository not initialized. Run 'init-repo' first.")
            raise typer.Exit(code=1)
        for root, dirs, files in os.walk(repo_path):
            if "tests" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    fp = os.path.join(root, file)
                    if suggest:
                        res = tool_integration.apply_lint_suggestions(fp)
                    else:
                        res = tool_integration.run_linter(fp)
                    results.append(f"{fp}:\n{res}\n")
    else:
        resolved_path = resolve_path(file_path, full_path)
        if suggest:
            res = tool_integration.apply_lint_suggestions(resolved_path)
        else:
            res = tool_integration.run_linter(resolved_path)
        results.append(f"{resolved_path}:\n{res}\n")
    typer.echo("\n".join(results))

@app.command("test", help="Run tests using pytest.\nExample: python main.py test\nUse --safety to run safety net checks for failing tests.")
def run_tests(safety: bool = typer.Option(False, "--safety", help="Run safety net: check failing tests and auto-suggest fixes")):
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Repository not initialized. Run 'init-repo' first.")
        raise typer.Exit(code=1)
    tool_integration = ToolIntegration()
    result = tool_integration.run_tests(repo_path)
    typer.echo("Test Results:")
    typer.echo(result)
    if safety and "FAILED" in result:
        import re
        failed_files = set(re.findall(r'(test_[\w_]+\.py)', result))
        for test_file in failed_files:
            full_test_file = os.path.join(repo_path, "tests", test_file)
            if os.path.exists(full_test_file):
                typer.echo(f"\nExamining failing test file: {full_test_file}")
                with open(full_test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                typer.echo("Test file content:")
                typer.echo(content)
                # Check for syntax errors
                try:
                    compile(content, full_test_file, 'exec')
                except SyntaxError as se:
                    typer.echo(f"SyntaxError detected: {se}")
                choice = typer.confirm("Would you like to attempt an LLM-generated fix for this test file?")
                if choice:
                    llm = LLMIntegration()
                    prompt = (
                        "The following test file is failing and/or has syntax errors. Suggest a fix for any issues (including syntax errors) causing deliberate failures:\n\n"
                        f"{content}\n\nProvide only the modified file content."
                    )
                    fix = llm.send_prompt(prompt)
                    if fix:
                        typer.echo("Proposed fix:")
                        typer.echo(fix)
                        apply_fix = typer.confirm("Apply this fix to the test file?")
                        if apply_fix:
                            with open(full_test_file, 'w', encoding='utf-8') as f:
                                f.write(fix)
                            typer.echo("Fix applied.")
                        else:
                            typer.echo("Fix not applied.")
                    else:
                        typer.echo("LLM did not return a fix.")
        rerun = typer.confirm("Would you like to rerun the tests?")
        if rerun:
            run_tests(safety=safety)

@app.command("preview", help="Generate a diff preview between two files.\nExample: python main.py preview app/module.py app/module_new.py\nUse -p flag for full paths.")
def preview(
    original_file: str = typer.Argument(..., help="Path to original file (relative to repo if -p not used)"),
    new_file: str = typer.Argument(..., help="Path to modified file (relative to repo if -p not used)"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat provided paths as full paths")
):
    orig = resolve_path(original_file, full_path)
    new = resolve_path(new_file, full_path)
    tool_integration = ToolIntegration()
    try:
        with open(orig, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(new, 'r', encoding='utf-8') as f:
            modified = f.read()
        diff = tool_integration.generate_diff(original, modified)
        if diff:
            typer.echo("Diff Preview:")
            typer.echo(diff)
        else:
            typer.echo("No differences found.")
    except Exception as e:
        typer.echo(f"Error generating diff: {e}")

@app.command("apply_changes", help="Apply changes to a file after previewing diff and confirmation.\nExample: python main.py apply_changes app/module.py app/module_new.py\nUse -p flag for full paths.")
def apply_changes(
    original_file: str = typer.Argument(..., help="Path to original file"),
    new_file: str = typer.Argument(..., help="Path to modified file"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat provided paths as full paths")
):
    orig = resolve_path(original_file, full_path)
    new = resolve_path(new_file, full_path)
    tool_integration = ToolIntegration()
    try:
        with open(orig, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(new, 'r', encoding='utf-8') as f:
            modified = f.read()
        diff = tool_integration.generate_diff(original, modified)
        typer.echo("Diff Preview:")
        typer.echo(diff)
        confirm = typer.confirm("Do you want to apply these changes?")
        if confirm:
            with open(orig, 'w', encoding='utf-8') as f:
                f.write(modified)
            typer.echo("Changes applied successfully.")
        else:
            typer.echo("Operation cancelled. No changes were made.")
    except Exception as e:
        typer.echo(f"Error applying changes: {e}")

@app.command("scan", help="Scan the repository and display extracted code chunks using AST-based chunking.\nExample: python main.py scan app\nUse -p for full path.")
def scan(
    repo_path: str = typer.Argument(..., help="Repository path or subfolder (relative if -p not used)"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat repo_path as a full path")
):
    resolved_repo = resolve_path(repo_path, full_path)
    repo_manager = RepositoryManager(resolved_repo)
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

@app.command("retrieve", help="Retrieve and display a prompt built from relevant code chunks.\nExample: python main.py retrieve app \"How to add two numbers?\"\nUse -p flag for full path.")
def retrieve(
    repo_path: str = typer.Argument(..., help="Repository path (relative if -p not used)"),
    query: str = typer.Argument(..., help="The query to send to the LLM"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat repo_path as a full path")
):
    resolved_repo = resolve_path(repo_path, full_path)
    repo_manager = RepositoryManager(resolved_repo)
    if not repo_manager.load_repository():
        typer.echo("Failed to load repository.")
        raise typer.Exit(code=1)
    chunks = repo_manager.get_code_chunks()
    prompt_engineer = PromptEngineer()
    prompt = prompt_engineer.build_prompt(query, chunks)
    typer.echo("Generated Prompt:")
    typer.echo(prompt)

@app.command("generate-test", help="Generate a skeletal test file for a Python source file.\nExample: python main.py generate-test app/app.py\nUses repo's tests folder. Use -p for full path.")
def generate_test(
    file: str = typer.Argument(..., help="Source file path (relative if -p not used)"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat file as a full path")
):
    resolved_file = resolve_path(file, full_path)
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Repository not initialized. Run 'init-repo' first.")
        raise typer.Exit(code=1)
    generate_test_file(resolved_file, repo_path=repo_path)
    typer.echo("Test file generation attempted.")

@app.command("generate-custom-test", help="Generate a customized test file using the LLM for a Python source file.\nExample: python main.py generate-custom-test app/app.py\nUses repo's tests folder. Use -p for full path.")
def generate_custom_test(
    file: str = typer.Argument(..., help="Source file path (relative if -p not used)"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat file as a full path")
):
    resolved_file = resolve_path(file, full_path)
    repo_path = load_repo_path()
    if not repo_path:
        typer.echo("Repository not initialized. Run 'init-repo' first.")
        raise typer.Exit(code=1)
    generate_custom_test_file(resolved_file, repo_path=repo_path)
    typer.echo("Custom test file generation attempted.")

@app.command("add-plugin", help="Add an external plugin to Refactron by cloning its git repo.\nExample: python main.py add-plugin https://example.com/myplugin.git")
def add_plugin(plugin_url: str):
    pattern = r'^(https?://[^\s/$.?#].[^\s]*)\.git$'
    if not re.match(pattern, plugin_url):
        typer.echo("Invalid plugin URL. Ensure it starts with http(s):// and ends with .git")
        raise typer.Exit(code=1)
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

@app.command("live-diff", help="Launch a live diff view for a specified file.\nExample: python main.py live-diff app/module.py\nUse -p for full path.")
def live_diff(
    file_path: str = typer.Argument(..., help="File path for live diff (relative if -p not used)"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat file_path as a full path")
):
    resolved_file = resolve_path(file_path, full_path)
    live_diff_view(resolved_file)

@app.command("selective-apply", help="Interactively review and apply changes from a modified file to the original file.\nExample: python main.py selective-apply app/module.py app/module_new.py\nUse -p for full paths.")
def selective_apply_cmd(
    original_file: str = typer.Argument(..., help="Original file path (relative if -p not used)"),
    modified_file: str = typer.Argument(..., help="Modified file path (relative if -p not used)"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat provided paths as full paths")
):
    resolved_orig = resolve_path(original_file, full_path)
    resolved_mod = resolve_path(modified_file, full_path)
    from change_selector import selective_apply
    selective_apply(resolved_orig, resolved_mod)

@app.command("auto-test", help="Watch the repository for changes and automatically run tests.\nExample: python main.py auto-test app\nUse -p for full path.")
def auto_test(
    repo_path: str = typer.Argument(..., help="Repository path (relative if -p not used)"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat repo_path as a full path")
):
    resolved_repo = resolve_path(repo_path, full_path)
    watch_and_run_tests(resolved_repo)

@app.command("run-sandbox", help="Execute a code snippet in a sandboxed environment.\nExample: python main.py run-sandbox \"print('Hello from sandbox')\"")
def run_sandbox(code: str):
    output = run_in_sandbox(code)
    typer.echo("Sandboxed Execution Output:")
    typer.echo(output)

@app.command("fix", help="Scan for syntax errors in file(s) and attempt to fix them using the LLM.\nExamples:\n  python main.py fix app/app.py\n  python main.py fix -a\n  python main.py fix app/app.py -s\n  python main.py fix -a -s\nUse -p for full paths.")
def fix(
    file: str = typer.Argument("", help="File path (relative if -p not used). Leave empty with -a to process all files."),
    all_files: bool = typer.Option(False, "--all", "-a", help="Process all eligible files (exclude tests folder)"),
    auto_apply: bool = typer.Option(False, "--suggest", "-s", help="Automatically apply fixes without prompting"),
    full_path: bool = typer.Option(False, "--full-path", "-p", help="Treat provided path(s) as full paths")
):
    repo_path = load_repo_path()
    if all_files:
        if not repo_path:
            typer.echo("Repository not initialized. Run 'init-repo' first.")
            raise typer.Exit(code=1)
        fixed_any = False
        for root, dirs, files in os.walk(repo_path):
            if "tests" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    current_file = os.path.join(root, f)
                    typer.echo(f"\nProcessing {current_file}...")
                    if fix_file(current_file, auto_apply):
                        fixed_any = True
        if not fixed_any:
            typer.echo("No syntax errors detected in any files.")
    else:
        if not file:
            typer.echo("Please provide a file path or use --all flag.")
            raise typer.Exit(code=1)
        resolved_file = resolve_path(file, full_path)
        if fix_file(resolved_file, auto_apply):
            typer.echo(f"Fixed syntax errors in {resolved_file}.")
        else:
            typer.echo(f"No fixes applied for {resolved_file}.")

if __name__ == "__main__":
    app()
