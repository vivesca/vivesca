#!/usr/bin/env python3
from pathlib import Path
import re

def fix_subprocess_run_in_file(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8")
    except (IsADirectoryError, UnicodeDecodeError):
        return False
    
    # Pattern to match subprocess.run(...) without timeout= anywhere inside
    def add_timeout(match):
        call = match.group(0)
        if "timeout=" in call:
            return call
        
        # Find where to insert timeout=300 before the closing )
        # Handle multi-line calls
        idx = call.rfind(")")
        if idx == -1:
            return call
        
        before = call[:idx].rstrip()
        # Check if there's already a trailing comma
        if before.endswith(","):
            insert = " timeout=300"
        else:
            insert = ", timeout=300"
        
        return before + insert + call[idx:]
    
    # Use regex to find all subprocess.run calls (handles multi-line with DOTALL)
    pattern = re.compile(r"subprocess\.run\([^)]*\)", re.DOTALL)
    new_content = pattern.sub(add_timeout, content)
    
    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"Fixed: {file_path}")
        return True
    return False

def main():
    germline = Path("/home/terry/germline/effectors")
    fixed_count = 0
    for item in germline.iterdir():
        if item.is_file():
            if fix_subprocess_run_in_file(item):
                fixed_count += 1
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
