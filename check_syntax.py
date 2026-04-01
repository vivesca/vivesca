import ast
import os
import sys

errors = []
for root, _, files in os.walk('.'):
    for f in files:
        if f.endswith('.py'):
            # Skip hidden dirs, venvs, __pycache__
            parts = root.split(os.sep)
            skip = False
            for part in parts:
                if part.startswith('.') and part != '.':
                    skip = True
                if 'venv' in part:
                    skip = True
            if skip:
                continue
            if '__pycache__' in root:
                continue

            path = os.path.join(root, f)
            try:
                with open(path, 'rb') as fobj:
                    ast.parse(fobj.read(), filename=path)
            except SyntaxError as e:
                errors.append(f'{path}: {e}')

if errors:
    print('\n'.join(errors))
    sys.exit(1)
else:
    print('No syntax errors found!')
