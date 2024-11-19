# myproject/codeql_analysis_module/codeql-analysis.py

import os
import time
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Paths
SHARED_DIR = '/shared/codeql_analysis'
INPUT_REPOS_DIR = os.path.join(SHARED_DIR, 'input_repos')
OUTPUT_DIR = os.path.join(SHARED_DIR, 'output', 'results')

# Ensure directories exist
os.makedirs(INPUT_REPOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def perform_codeql_analysis(repo_name, commit_sha, file_path):
    """
    Performs CodeQL analysis on the given C file.
    """
    try:
        # Define the output SARIF file path
        sarif_output_path = os.path.join(OUTPUT_DIR, f"{repo_name}_{commit_sha}_results.sarif")

        # Define the CodeQL database path
        db_path = os.path.join(SHARED_DIR, f"{repo_name}_{commit_sha}_db")

        # Command to create CodeQL database
        create_db_command = [
            "codeql", "database", "create", db_path,
            "--language", "c",
            "--source-root", os.path.dirname(file_path)
        ]

        # Create a CodeQL database
        subprocess.check_call(create_db_command)
        logger.info(f"CodeQL database created for {repo_name} at commit {commit_sha}")

        # Command to run CodeQL analysis
        analyze_command = [
            "codeql", "database", "analyze",
            db_path,
            "/usr/local/share/codeql/c/c.ql",  # Update this path based on your CodeQL queries location
            "--format", "sarifv2.1.0",
            "--output", sarif_output_path
        ]

        # Run CodeQL analysis
        subprocess.check_call(analyze_command)
        logger.info(f"CodeQL analysis completed for {repo_name} at commit {commit_sha}. Results saved to {sarif_output_path}")

        # Clean up CodeQL database
        subprocess.check_call(["rm", "-rf", db_path])
        logger.info(f"CodeQL database for {repo_name} at commit {commit_sha} deleted after analysis.")

    except subprocess.CalledProcessError as e:
        logger.error(f"CodeQL analysis failed for {repo_name} at commit {commit_sha}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during CodeQL analysis for {repo_name} at commit {commit_sha}: {e}")

def main():
    processed_files = set()

    while True:
        try:
            for file in Path(INPUT_REPOS_DIR).glob("*.c"):
                if file.name not in processed_files:
                    logger.info(f"Detected new file for CodeQL analysis: {file.name}")

                    # Extract repo_name and commit_sha from filename (e.g., testrepo_36d35ec43f0da690.c)
                    try:
                        base_name = file.stem  # Remove .c extension
                        repo_name, commit_sha = base_name.split('_', 1)
                    except ValueError:
                        logger.error(f"Invalid file naming convention: {file.name}")
                        continue

                    # Perform CodeQL analysis
                    perform_codeql_analysis(repo_name, commit_sha, str(file))

                    # Mark as processed
                    processed_files.add(file.name)

        except Exception as e:
            logger.error(f"Error in CodeQL analysis loop: {e}")

        # Polling interval
        time.sleep(10)

if __name__ == "__main__":
    main()
