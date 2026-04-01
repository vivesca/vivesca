import ast
import os

def check_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            if '__pycache__' in path or '.git' in path:
                continue
            try:
                with open(path, 'r') as f:
                    content = f.read()
                if 'subprocess.run' not in content:
                    continue
                
                # Try parsing as python
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
                           node.func.attr == 'run' and getattr(node.func.value, 'id', None) == 'subprocess':
                            has_timeout = any(k.arg == 'timeout' for k in node.keywords)
                            if not has_timeout:
                                print(f"{path}:{node.lineno}: subprocess.run missing timeout")
                except SyntaxError:
                    # Not a valid python file, maybe a script without .py extension
                    # Just do a rough check
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if 'subprocess.run(' in line:
                            # Search for timeout= until the closing parenthesis
                            found_timeout = False
                            bracket_count = 0
                            for j in range(i, min(i+15, len(lines))):
                                if 'timeout=' in lines[j]:
                                    found_timeout = True
                                    break
                                bracket_count += lines[j].count('(') - lines[j].count(')')
                                if bracket_count <= 0 and j > i:
                                    break
                            if not found_timeout:
                                print(f"{path}:{i+1}: subprocess.run may miss timeout (rough check)")
            except Exception as e:
                # print(f"Error reading {path}: {e}")
                pass

check_files('effectors/')
