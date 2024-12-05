#!/usr/bin/env python3

# sonarqube_module/scripts/trigger_sonarqube_analysis.py

import os
import sys
import subprocess

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 trigger_sonarqube_analysis.py <repo_name>")
        sys.exit(1)

    repo_name = sys.argv[1]
    os.environ['TARGET_REPO'] = repo_name  # Pass the repo name to the analysis script

    # Run the analysis script
    subprocess.check_call(["python3", "/sonarqube_app/scripts/run_analysis_and_compare.py", "--tool", "sonarqube"])

if __name__ == "__main__":
    main()
