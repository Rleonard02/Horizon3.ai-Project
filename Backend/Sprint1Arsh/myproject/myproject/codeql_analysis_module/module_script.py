# codeql_analysis_module/module_script.py

import subprocess
import os
import sys
import time
import logging
import requests
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Environment Variables
API_SERVICE_URL = os.getenv('API_SERVICE_URL', 'http://api-service:8000/update_status')
INPUT_REPOS_DIR = os.getenv('INPUT_REPOS_DIR', '/shared/codeql_analysis_module/input_repos')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/shared/codeql_analysis_module/output')

def update_status(status, progress, message, max_retries=5, initial_delay=2):
    data = {
        "service": "codeql-analysis",
        "status": status,
        "progress": progress,
        "message": message
    }
    attempt = 0
    delay = initial_delay

    while attempt < max_retries:
        try:
            response = requests.post(API_SERVICE_URL, json=data, timeout=5)
            if response.status_code == 200:
                logger.info(f"Successfully updated status: {status}, {progress}%, {message}")
                return True
            else:
                logger.error(f"Failed to update status: {response.status_code} {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Attempt {attempt + 1}: Failed to update status: {e}")

        attempt += 1
        logger.info(f"Retrying in {delay} seconds...")
        time.sleep(delay)
        delay *= 2  # Exponential backoff

    logger.error(f"All {max_retries} attempts to update status failed.")
    return False

def run_codeql_analysis(repo_path, output_path, build_command="make clean && make"):
    try:
        logger.info(f"Running CodeQL analysis on {repo_path}")

        # Initialize CodeQL database with build command
        subprocess.check_call([
            "codeql", "database", "create",
            output_path,
            "--language=cpp",  # Adjust language as needed
            "--source-root", repo_path,
            "--command", build_command
        ])
        logger.info("CodeQL database created successfully.")

        # Run CodeQL queries
        subprocess.check_call([
            "codeql", "database", "analyze",
            output_path,
            "cpp-security-and-quality.qls",  # Specify the query suite
            "--format=json",
            "--output", os.path.join(OUTPUT_DIR, f"{os.path.basename(repo_path)}_codeql_results.json")
        ])
        logger.info("CodeQL analysis completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"CodeQL analysis failed: {e}")
        update_status("failed", 0, "CodeQL analysis failed")
        sys.exit(1)

def generate_vulnerability_report(results_file, report_file):
    try:
        logger.info(f"Generating vulnerability report from {results_file}")
        # Placeholder: In a real scenario, parse JSON and format it into a readable report.
        shutil.copyfile(results_file, report_file)
        logger.info(f"Vulnerability report generated at {report_file}")
    except Exception as e:
        logger.error(f"Failed to generate vulnerability report: {e}")
        update_status("failed", 0, "Vulnerability report generation failed")
        sys.exit(1)

def process_repository(repo_name):
    repo_path = os.path.join(INPUT_REPOS_DIR, repo_name)
    if not os.path.exists(repo_path):
        logger.warning(f"Repository path {repo_path} does not exist.")
        return

    codeql_db_path = os.path.join(OUTPUT_DIR, f"{repo_name}_codeql_db")
    codeql_results = os.path.join(OUTPUT_DIR, f"{repo_name}_codeql_results.json")
    vulnerability_report = os.path.join(OUTPUT_DIR, f"{repo_name}_vulnerability_report.md")

    update_status("running", 10, f"Running CodeQL analysis on {repo_name}")

    run_codeql_analysis(repo_path, codeql_db_path)

    update_status("running", 70, f"Generating vulnerability report for {repo_name}")
    generate_vulnerability_report(codeql_results, vulnerability_report)

    logger.info(f"Vulnerability report for {repo_name} generated successfully.")
    update_status("completed", 100, f"CodeQL analysis for {repo_name} completed")

def monitor_input_repos():
    processed_repos = set()
    while True:
        try:
            repos = os.listdir(INPUT_REPOS_DIR)
            for repo_name in repos:
                if repo_name not in processed_repos:
                    logger.info(f"Detected new repository: {repo_name}")
                    process_repository(repo_name)
                    processed_repos.add(repo_name)
            time.sleep(10)  # Poll every 10 seconds
        except KeyboardInterrupt:
            logger.info("CodeQL Analysis Module terminated by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error while monitoring input_repos: {e}")
            time.sleep(10)

if __name__ == "__main__":
    try:
        monitor_input_repos()
    except KeyboardInterrupt:
        logger.info("CodeQL Analysis Module terminated by user.")
        sys.exit(0)
