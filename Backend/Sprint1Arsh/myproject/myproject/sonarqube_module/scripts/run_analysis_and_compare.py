#!/usr/bin/env python3

import os
import time
import json
import logging
import subprocess
import requests
import hashlib
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Environment variables
SONARQUBE_URL = os.getenv("SONARQUBE_URL", "http://localhost:9000")
SONARQUBE_TOKEN = os.getenv("SONARQUBE_TOKEN")
INPUT_FILES_DIR = os.getenv("INPUT_FILES_DIR", "/sonarqube_shared/input_files")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/sonarqube_shared/output")

# Validate environment variables
if not SONARQUBE_TOKEN:
    logger.error("Missing environment variable: SONARQUBE_TOKEN")
    exit(1)

# Track processed repositories and their hashes
processed_repos = {}

def calculate_file_hash(file_path):
    """Calculate a SHA256 hash for a single file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
    return sha256.hexdigest()

def calculate_repo_hash(repo_path):
    """Calculate a SHA256 hash for the repository's content."""
    sha256 = hashlib.sha256()
    for root, _, files in os.walk(repo_path):
        for file in sorted(files):  # Ensure consistent ordering
            file_path = os.path.join(root, file)
            sha256.update(calculate_file_hash(file_path).encode('utf-8'))
    return sha256.hexdigest()

def wait_for_sonarqube(timeout=120):
    """Wait for SonarQube server to be ready."""
    logger.info("Waiting for SonarQube server to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(SONARQUBE_URL, timeout=10)
            if response.status_code == 200:
                logger.info("SonarQube server is ready.")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(5)
    logger.error("SonarQube server did not become ready in time.")
    return False

def create_sonarqube_project(project_key, project_name):
    """Create a SonarQube project."""
    api_url = f"{SONARQUBE_URL}/api/projects/create"
    payload = {"name": project_name, "project": project_key}
    response = requests.post(api_url, auth=(SONARQUBE_TOKEN, ''), data=payload)
    if response.status_code == 200:
        logger.info(f"Project '{project_name}' created successfully.")
    elif response.status_code == 400 and "already exists" in response.text:
        logger.info(f"Project '{project_name}' already exists.")
    else:
        logger.error(f"Failed to create project '{project_name}': {response.text}")
        return False
    return True

def run_sonarscanner(repo_path, project_key, project_name):
    """Run SonarScanner for the specified project."""
    logger.info(f"Running SonarScanner for project: {project_name}")
    logger.info(f"SonarScanner will use repo_path: {repo_path}")

    sonar_scanner_cmd = [
        "sonar-scanner",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.projectName={project_name}",
        f"-Dsonar.sources={repo_path}",
        f"-Dsonar.host.url={SONARQUBE_URL}",
        f"-Dsonar.login={SONARQUBE_TOKEN}",
        "-Dsonar.sourceEncoding=UTF-8",
        "-X"    ]
    try:
        result = subprocess.run(
            sonar_scanner_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=repo_path,
            timeout=600
        )
        logger.info(f"SonarScanner output: {result.stdout}")
        if result.stderr:
            logger.error(f"SonarScanner error: {result.stderr}")
        if result.returncode != 0:
            logger.error(f"SonarScanner failed for {project_key}")
            return False
        logger.info(f"SonarScanner completed successfully for project '{project_name}'")
        return True
    except Exception as e:
        logger.error(f"Error running SonarScanner for {project_key}: {e}")
        return False

def fetch_sonarqube_issues(project_key):
    """Fetch issues from SonarQube."""
    api_url = f"{SONARQUBE_URL}/api/issues/search"
    params = {"projectKeys": project_key, "ps": 500}
    try:
        response = requests.get(api_url, auth=(SONARQUBE_TOKEN, ''), params=params)
        if response.status_code == 200:
            logger.info(f"Fetched issues for project {project_key}: {response.json()}")
            return response.json()
        else:
            logger.error(f"Failed to fetch issues for {project_key}: {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching issues for {project_key}: {e}")
        return {}

def save_results(repo_name, vulnerabilities):
    """Save vulnerabilities to the output directory."""
    output_file = os.path.join(OUTPUT_DIR, f"{repo_name}_vulnerabilities.json")
    try:
        with open(output_file, "w") as f:
            json.dump(vulnerabilities, f, indent=4)
        logger.info(f"Results saved for {repo_name} to {output_file}")
    except Exception as e:
        logger.error(f"Error saving results for {repo_name}: {e}")

def process_repository(repo_name):
    """Process and analyze the specified repository."""
    repo_path = os.path.join(INPUT_FILES_DIR, repo_name)
    if not os.path.isdir(repo_path):
        logger.warning(f"{repo_name} is not a directory, skipping...")
        return

    project_key = f"project_{repo_name}"
    project_name = repo_name
    repo_hash = calculate_repo_hash(repo_path)

    # Check if the repository content has changed
    if repo_name in processed_repos and processed_repos[repo_name] == repo_hash:
        logger.info(f"No changes detected in repository: {repo_name}")
        return

    logger.info(f"Starting analysis for repository: {repo_name}")
    if create_sonarqube_project(project_key, project_name):
        if run_sonarscanner(repo_path, project_key, project_name):
            vulnerabilities = fetch_sonarqube_issues(project_key)
            save_results(repo_name, vulnerabilities)
            # Update the hash after successful analysis
            processed_repos[repo_name] = repo_hash
        else:
            logger.error(f"SonarScanner failed for repository: {repo_name}")
        # Clean up temporary files
        scannerwork_path = os.path.join(repo_path, ".scannerwork")
        if os.path.exists(scannerwork_path):
            shutil.rmtree(scannerwork_path)
            logger.info(f"Cleaned up scannerwork directory: {scannerwork_path}")
    else:
        logger.error(f"Failed to create project for repository: {repo_name}")

def monitor_and_analyze():
    """Monitor for new repositories and analyze them."""
    logger.info("Monitoring for new repositories to analyze...")
    while True:
        try:
            repos = os.listdir(INPUT_FILES_DIR)
            for repo in repos:
                process_repository(repo)
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
        time.sleep(10)

if __name__ == "__main__":
    logger.info("Starting SonarQube Analysis Module")
    if wait_for_sonarqube():
        monitor_and_analyze()
    else:
        logger.error("SonarQube server did not start correctly.")
