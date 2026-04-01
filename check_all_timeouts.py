import ast
import os
import sys

def check_file(path):
    try:
        with open(path, 'r') as f:
            content = f.read()
    except Exception as e:
        return []
    
    if 'subprocess.run' not in content:
        return []
    
    findings = []
    
    # Try parsing as python
    try:
        tree = ast.parse(content)
        is_run_imported = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'subprocess':
                if any(alias.name == 'run' for alias in node.names):
                    is_run_imported = True
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                is_target = False
                if isinstance(node.func, ast.Attribute) and \
                   node.func.attr == 'run' and getattr(node.func.value, 'id', None) == 'subprocess':
                    is_target = True
                elif is_run_imported and isinstance(node.func, ast.Name) and node.func.id == 'run':
                    is_target = True
                
                if is_target:
                    has_timeout = any(k.arg == 'timeout' for k in node.keywords)
                    if not has_timeout:
                        findings.append(f"{path}:{node.lineno}: subprocess.run missing timeout")
    except SyntaxError:
        # Rough check for non-pure-python or scripts with syntax errors (e.g. from shebang)
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if 'subprocess.run(' in line:
                # Search for 'timeout=' until we find a matching closing parenthesis
                found_timeout = False
                bracket_count = 0
                for j in range(i, min(i+20, len(lines))):
                    if 'timeout=' in lines[j]:
                        found_timeout = True
                        break
                    bracket_count += lines[j].count('(') - lines[j].count(')')
                    if bracket_count <= 0 and j > i:
                        break
                if not found_timeout:
                    findings.append(f"{path}:{i+1}: subprocess.run may miss timeout (rough check)")
    return findings

all_files = sys.stdin.read().splitlines()
for file in all_files:
    if os.path.isfile(file):
        for finding in check_file(file):
            print(finding)
