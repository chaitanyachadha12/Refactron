"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import os
import ast

def get_functions_from_file(file_path: str):
    """
    Parse a Python file and return a list of function names.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)
    return [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

def generate_test_file(source_file: str, test_dir: str = "tests"):
    """
    Generate a skeleton test file for the given source file if one does not exist.
    """
    base_name = os.path.basename(source_file)
    module_name, ext = os.path.splitext(base_name)
    test_file_name = f"test_{module_name}.py"
    test_file_path = os.path.join(test_dir, test_file_name)
    
    # Create tests directory if it doesn't exist
    os.makedirs(test_dir, exist_ok=True)

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
            f.write(f"        self.assertTrue(True)\n\n")
        f.write("if __name__ == '__main__':\n")
        f.write("    unittest.main()\n")
    
    print(f"Test file generated: {test_file_path}")
