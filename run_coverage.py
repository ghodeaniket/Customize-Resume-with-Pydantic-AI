#!/usr/bin/env python3
"""
Generate a test coverage report for the Resume Customizer project.

This script runs the tests and generates a coverage report in both
terminal output and HTML format.
"""

import os
import subprocess
import sys

def run_coverage():
    """Run the tests with coverage and generate reports."""
    print("Running tests with coverage...")
    
    # Create directory for HTML reports if it doesn't exist
    os.makedirs("coverage_reports", exist_ok=True)
    
    # Run pytest with coverage
    cmd = [
        "python3", "-m", "pytest",
        "--cov=resume_customizer",
        "--cov-report=term",
        "--cov-report=html:coverage_reports/html",
        "--cov-report=xml:coverage_reports/coverage.xml",
        "resume_customizer/tests"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print the output
    print(result.stdout)
    
    if result.stderr:
        print("ERRORS:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    
    # Check if coverage report was generated
    if os.path.exists("coverage_reports/html/index.html"):
        print("\nCoverage HTML report generated at: coverage_reports/html/index.html")
    else:
        print("\nFailed to generate HTML coverage report", file=sys.stderr)
    
    if os.path.exists("coverage_reports/coverage.xml"):
        print("Coverage XML report generated at: coverage_reports/coverage.xml")
    else:
        print("Failed to generate XML coverage report", file=sys.stderr)
    
    # Return the command exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_coverage())
