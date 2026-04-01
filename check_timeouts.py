import ast
import os

def check_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') or file.endswith('.sh'): # skip some
                continue
            path = os.path.join(root, file)
            try:
                with open(path, 'r') as f:
                    content = f.read()
                if 'subprocess.run' not in content:
                    continue
                
                # Try parsing as python if it looks like python
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
                        if 'subprocess.run(' in line and 'timeout=' not in line:
                            # Check next few lines
                            found_timeout = False
                            for j in range(i, min(i+10, len(lines))):
                                if 'timeout=' in lines[j]:
                                    found_timeout = True
                                    break
                                if ')' in lines[j] and j > i:
                                    break
                            if not found_timeout:
                                print(f"{path}:{i+1}: subprocess.run may miss timeout (rough check)")
            except Exception as e:
                # print(f"Error reading {path}: {e}")
                pass

check_files('effectors/')
