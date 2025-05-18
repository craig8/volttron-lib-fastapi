# dead_code_check.py
import ast
import os
import sys
from collections import defaultdict

def find_defined_functions(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())
    
    definitions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            definitions.append(node.name)
    return definitions

def find_called_functions(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())
    
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # Handle method calls like obj.method()
                calls.append(node.func.attr)
    return calls

def scan_directories(app_dir, test_dir=None):
    all_dirs = [app_dir]
    if test_dir:
        all_dirs.append(test_dir)
        
    defined_functions = defaultdict(list)
    called_functions = []
    
    # Scan all directories for function definitions and calls
    for directory in all_dirs:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # Get defined functions and their file
                    for func_name in find_defined_functions(file_path):
                        defined_functions[func_name].append(file_path)
                    
                    # Get called functions
                    called_functions.extend(find_called_functions(file_path))
    
    # Find functions that are defined but never called
    potential_dead_code = []
    for func_name, files in defined_functions.items():
        # Skip special methods, test functions and fixture functions
        if (not func_name.startswith('_') and 
            not func_name.startswith('test_') and
            func_name != 'fixture' and
            func_name not in called_functions):
            potential_dead_code.append((func_name, files))
    
    return potential_dead_code

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dead_code_check.py <app_directory> [test_directory]")
        sys.exit(1)
    
    app_dir = sys.argv[1]
    test_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    potential_dead_code = scan_directories(app_dir, test_dir)
    
    if potential_dead_code:
        print("Potential dead code found:")
        for func_name, files in potential_dead_code:
            print(f"Function '{func_name}' defined in {files} but never called")
    else:
        print("No potential dead code found.")