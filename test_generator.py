"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import os
import ast
from llm_integration import LLMIntegration

def get_functions_from_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)
    return [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

def generate_test_file(source_file: str, repo_path: str = None):
    base_name = os.path.basename(source_file)
    module_name, _ = os.path.splitext(base_name)
    test_file_name = f"test_{module_name}.py"
    test_dir = os.path.join(repo_path, "tests") if repo_path else "tests"
    os.makedirs(test_dir, exist_ok=True)
    test_file_path = os.path.join(test_dir, test_file_name)
    if os.path.exists(test_file_path):
        print(f"Test file {test_file_path} already exists.")
        return
    function_names = get_functions_from_file(source_file)
    if not function_names:
        print(f"No functions found in {source_file}. Skipping test generation.")
        return
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write("import unittest\n")
        f.write(f"from {module_name} import {', '.join(function_names)}\n\n")
        f.write(f"class Test{module_name.capitalize()}(unittest.TestCase):\n")
        for func in function_names:
            f.write(f"    def test_{func}(self):\n")
            f.write(f"        # TODO: Implement tests for {func}\n")
            f.write("        self.assertTrue(True)\n\n")
        f.write("if __name__ == '__main__':\n")
        f.write("    unittest.main()\n")
    print(f"Test file generated: {test_file_path}")

def generate_custom_test_file(source_file: str, repo_path: str = None) -> None:
    with open(source_file, "r", encoding="utf-8") as f:
        source_code = f.read()
    prompt = (
        f"Generate comprehensive unit tests for the following Python code:\n\n"
        f"{source_code}\n\n"
        "Provide complete test file code as output."
    )
    llm = LLMIntegration()
    response = llm.send_prompt(prompt)
    if not response:
        print("LLM failed to generate test file content.")
        return
    base_name = os.path.basename(source_file)
    module_name, _ = os.path.splitext(base_name)
    test_file_name = f"test_{module_name}_custom.py"
    test_dir = os.path.join(repo_path, "tests") if repo_path else "tests"
    os.makedirs(test_dir, exist_ok=True)
    test_file_path = os.path.join(test_dir, test_file_name)
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(response)
    print(f"Custom test file generated: {test_file_path}")
