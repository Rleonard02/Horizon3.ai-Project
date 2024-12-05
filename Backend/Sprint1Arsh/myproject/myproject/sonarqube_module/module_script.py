#!/usr/bin/env python3

# sonarqube_module/module_script.py

import os
import time
import subprocess
import logging
import requests
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
SONARQUBE_URL = os.getenv('SONARQUBE_URL', 'http://sonarqube:9000')
SONARQUBE_ADMIN_TOKEN = os.getenv('SONARQUBE_ADMIN_TOKEN')
API_SERVICE_URL = os.getenv('API_SERVICE_URL', 'http://api-service:8000/update_status')

# Directories
INPUT_FILES_DIR = os.getenv('INPUT_FILES_DIR', '/sonarqube_shared/input_files')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/sonarqube_shared/output')

# Path to tokens
TOKENS_FILE = '/sonarqube_shared/'

# Keep track of processed repositories
processed_repos = set()

def load_tokens():
    if not os.path.exists(TOKENS_FILE):
        logger.error(f"Tokens file {TOKENS_FILE} not found.")
        return {}
    with open(TOKENS_FILE, 'r') as f:
        tokens = json.load(f)
    logger.debug(f"Loaded tokens: {tokens}")
    return tokens

def run_sonarscanner(repo_path, project_key, project_name, token):
    sonar_scanner_cmd = [
        'sonar-scanner',
        f'-Dsonar.projectKey={project_key}',
        f'-Dsonar.projectName={project_name}',
        f'-Dsonar.sources=.',
        f'-Dsonar.host.url={SONARQUBE_URL}',
        f'-Dsonar.login={token}'
    ]

    logger.info(f'Running SonarScanner for project {project_key} at {repo_path}')
    try:
        result = subprocess.run(
            sonar_scanner_cmd,
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600  # 10 minutes timeout, adjust as needed
        )
        if result.returncode != 0:
            logger.error(f"SonarScanner failed for project {project_key}: {result.stderr}")
            return False
        logger.info(f"SonarScanner completed for project {project_key}")
        logger.debug(f"SonarScanner Output:\n{result.stdout}")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"SonarScanner timed out for project {project_key}")
        return False
    except Exception as e:
        logger.error(f"Exception during SonarScanner for project {project_key}: {e}")
        return False

def check_analysis_status(project_key):
    api_url = f"{SONARQUBE_URL}/api/ce/component?component={project_key}"
    headers = {'Authorization': f'Bearer {SONARQUBE_ADMIN_TOKEN}'}
    while True:
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to get analysis status for {project_key}: {response.text}")
                return False
            data = response.json()
            if data.get('pending'):
                logger.info(f"Analysis for {project_key} is still pending...")
                time.sleep(5)
                continue
            tasks = data.get('tasks', [])
            if not tasks:
                logger.warning(f"No tasks found for project {project_key}")
                return False
            task = tasks[0]
            status = task.get('status')
            if status == 'SUCCESS':
                logger.info(f"Analysis for {project_key} completed successfully")
                return True
            elif status == 'FAILED':
                logger.error(f"Analysis for {project_key} failed")
                return False
            else:
                logger.info(f"Analysis for {project_key} status: {status}")
                time.sleep(5)
        except Exception as e:
            logger.error(f"Exception while checking analysis status for {project_key}: {e}")
            return False

def get_vulnerabilities(project_key):
    api_url = f"{SONARQUBE_URL}/api/issues/search"
    headers = {'Authorization': f'Bearer {SONARQUBE_ADMIN_TOKEN}'}
    params = {
        'componentKeys': project_key,
        'types': 'VULNERABILITY',
        'ps': 500  # Page size, adjust as needed
    }
    try:
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to get vulnerabilities for {project_key}: {response.text}")
            return None
        data = response.json()
        issues = data.get('issues', [])
        logger.info(f"Retrieved {len(issues)} vulnerabilities for project {project_key}")
        return issues
    except Exception as e:
        logger.error(f"Exception while retrieving vulnerabilities for {project_key}: {e}")
        return None

def notify_api_service(repo_name, vulnerabilities):
    payload = {
        'repository': repo_name,
        'vulnerabilities': vulnerabilities
    }
    try:
        response = requests.post(API_SERVICE_URL, json=payload)
        if response.status_code == 200:
            logger.info(f"Successfully notified API service for repository {repo_name}")
        else:
            logger.error(f"Failed to notify API service for repository {repo_name}: {response.text}")
    except Exception as e:
        logger.error(f"Exception while notifying API service: {e}")

def process_repository(repo_name, tokens):
    repo_path = os.path.join(INPUT_FILES_DIR, repo_name)
    if not os.path.isdir(repo_path):
        logger.warning(f"Repository path {repo_path} is not a directory. Skipping.")
        return

    project_key = f"project_{repo_name}"
    project_name = repo_name

    token = tokens.get(project_key)
    if not token:
        logger.error(f"No token found for project {project_key}. Skipping analysis.")
        return

    # Run SonarScanner
    success = run_sonarscanner(repo_path, project_key, project_name, token)
    if not success:
        logger.error(f"Skipping vulnerabilities extraction due to SonarScanner failure for {repo_name}")
        return

    # Wait for analysis to complete
    success = check_analysis_status(project_key)
    if not success:
        logger.error(f"Skipping vulnerabilities extraction due to analysis failure for {repo_name}")
        return

    # Get vulnerabilities
    vulnerabilities = get_vulnerabilities(project_key)
    if vulnerabilities is None:
        logger.error(f"Failed to retrieve vulnerabilities for {repo_name}")
        return

    # Save vulnerabilities as JSON
    output_file = os.path.join(OUTPUT_DIR, f"{repo_name}_vulnerabilities.json")
    try:
        with open(output_file, 'w') as f:
            json.dump(vulnerabilities, f, indent=2)
        logger.info(f"Vulnerabilities for {repo_name} saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write vulnerabilities to {output_file}: {e}")
        return

    # Notify API service
    notify_api_service(repo_name, vulnerabilities)

def main():
    logger.info("SonarQube Analysis Module started")
    tokens = load_tokens()

    while True:
        try:
            repos = os.listdir(INPUT_FILES_DIR)
            logger.debug(f"Found repositories: {repos}")
            for repo in repos:
                repo_path = os.path.join(INPUT_FILES_DIR, repo)
                if repo in processed_repos:
                    logger.debug(f"Repository {repo} already processed. Skipping.")
                    continue
                if not os.path.isdir(repo_path):
                    logger.debug(f"Path {repo_path} is not a directory. Skipping.")
                    continue
                logger.info(f"Processing repository: {repo}")
                process_repository(repo, tokens)
                processed_repos.add(repo)
        except Exception as e:
            logger.error(f"Exception in main loop: {e}")

        # Sleep before next check
        time.sleep(10)

if __name__ == "__main__":
    main()
