import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "--co", "-q"],
    capture_output=True,
    text=True,
    cwd="/home/terry/germline"
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)

# Filter lines with ERROR
for line in result.stderr.splitlines():
    if "ERROR" in line:
        print(line)
