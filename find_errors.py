import sys
import pytest
import os
os.chdir("/home/terry/germline")

# Capture collection errors
class ErrorCollector:
    def __init__(self):
        self.errors = []
    
    def pytest_collectreport(self, report):
        if report.failed:
            self.errors.append(report)

collector = ErrorCollector()
pytest.main(["--co", "-q"], plugins=[collector])

for report in collector.errors:
    print(f"Collection error in {report.nodeid}:")
    print(report.longrepr)
    print()
