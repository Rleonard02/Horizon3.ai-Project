#!/usr/bin/env python3

# sonarqube_module/scripts/run_analysis_and_compare.py

import os
import argparse
import subprocess
import requests
import time
import tempfile
import json
import sys

# Function to source environment variables from a file
def source_env_file(env_file_path):
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            for line in f:
                if line.startswith("export SONARQUBE_TOKEN="):
                    token = line.strip().split('=')[1]
                    os.environ['SONARQUBE_TOKEN'] = token
    else:
        print("Error: .sonarqube_env file not found and SONARQUBE_TOKEN not set.")
        exit(1)

# SonarQube authentication token (from environment variable)
SONARQUBE_TOKEN = os.getenv("SONARQUBE_TOKEN")
if not SONARQUBE_TOKEN:
    # Attempt to source the .sonarqube_env file
    env_file = os.path.abspath("/sonarqube_app/.sonarqube_env")
    source_env_file(env_file)
    SONARQUBE_TOKEN = os.getenv("SONARQUBE_TOKEN")
    if not SONARQUBE_TOKEN:
        print("Error: SONARQUBE_TOKEN environment variable not set.")
        exit(1)

# SonarQube server URL
SONARQUBE_URL = os.getenv("SONARQUBE_URL", "http://sonarqube:9000")
SONARQUBE_DOCKER_URL = os.getenv("SONARQUBE_DOCKER_URL", "http://sonarqube:9000")  # Adjust if necessary
SONARQUBE_REPORTS_FOLDER = os.path.abspath("/sonarqube_shared/output")
# Define paths
SOURCE_CODE_FOLDER = os.path.abspath("/sonarqube_shared/input_files")

# Function to create a SonarQube project via API
def create_sonarqube_project(project_key, project_name):
    api_url = f"{SONARQUBE_URL}/api/projects/create"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "name": project_name,
        "project": project_key
    }
    try:
        response = requests.post(api_url, auth=(SONARQUBE_TOKEN, ''), headers=headers, data=payload)
    except Exception as e:
        print(f"Exception occurred while creating project '{project_name}': {e}", flush=True)
        sys.exit(1)

    if response.status_code == 200:
        print(f"Project '{project_name}' created successfully.")
    elif response.status_code == 400 and "already exists" in response.text:
        print(f"Project '{project_name}' already exists.")
    else:
        print(f"Failed to create project '{project_name}'. Response: {response.text}", flush=True)
        sys.exit(1)

# Function to run SonarScanner via Docker
def run_sonarscanner(project_key, project_name, source_folder):
    print(f"\n--- Running SonarScanner for project: {project_name} ---")

    # Create a temporary directory for sonar-project.properties
    with tempfile.TemporaryDirectory() as temp_dir:
        properties_file_path = os.path.join(temp_dir, "sonar-project.properties")

        # Write sonar-project.properties content
        with open(properties_file_path, 'w') as f:
            f.write(f"""
sonar.projectKey={project_key}
sonar.projectName={project_name}
sonar.projectVersion=1.0
sonar.sources=.
sonar.sourceEncoding=UTF-8
sonar.login={SONARQUBE_TOKEN}
sonar.scm.enabled=false
sonar.verbose=true
""")

        # Define absolute paths
        abs_properties_file = os.path.abspath(properties_file_path)
        abs_source_folder = os.path.abspath(source_folder)

        # Verify source folder exists
        if not os.path.exists(abs_source_folder):
            print(f"Error: Source folder '{abs_source_folder}' does not exist.")
            return

        # Run SonarScanner Docker container
        scanner_command = [
            "docker", "run", "--rm",
            "-e", f"SONAR_HOST_URL={SONARQUBE_DOCKER_URL}",
            "-v", f"{abs_properties_file}:/opt/sonar-project.properties",
            "-v", f"{abs_source_folder}:/usr/src",
            "sonarsource/sonar-scanner-cli",
            "-X",
            "-Dproject.settings=/opt/sonar-project.properties"
        ]

        try:
            subprocess.run(scanner_command, check=True)
            print(f"SonarScanner analysis for project '{project_name}' completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error during SonarScanner analysis for project '{project_name}': {e}", flush=True)
            sys.exit(1)

# Function to fetch SonarQube issues via API
def fetch_sonarqube_issues(project_key, output_file):
    api_url = f"{SONARQUBE_URL}/api/issues/search"
    params = {
        "projectKeys": project_key,
        "ps": 500  # Page size: adjust as needed
    }
    try:
        response = requests.get(api_url, auth=(SONARQUBE_TOKEN, ''), params=params)
    except Exception as e:
        print(f"Exception occurred while fetching issues for project '{project_key}': {e}", flush=True)
        sys.exit(1)

    if response.status_code == 200:
        with open(output_file, 'w') as f:
            json.dump(response.json(), f, indent=4)
        print(f"Issues for project '{project_key}' saved to '{output_file}'.")
    else:
        print(f"Failed to fetch issues for project '{project_key}'. Response: {response.text}", flush=True)

# Function for SonarQube analysis
def run_sonarqube_analysis(repo_name=None):
    print("\n=== Running SonarQube Analysis ===")

    # Ensure the SonarQube reports folder exists
    os.makedirs(SONARQUBE_REPORTS_FOLDER, exist_ok=True)

    # Determine which repositories to analyze
    if repo_name:
        repos = [repo_name]
    else:
        repos = os.listdir(SOURCE_CODE_FOLDER)

    for repo_name in repos:
        repo_path = os.path.join(SOURCE_CODE_FOLDER, repo_name)
        if not os.path.isdir(repo_path):
            print(f"Skipping {repo_name}: Not a directory.")
            continue

        # Detect C files in the repository
        c_files = []
        for root, dirs, files in os.walk(repo_path):
            c_files.extend([os.path.join(root, f) for f in files if f.endswith('.c') or f.endswith('.h')])

        if not c_files:
            print(f"No C files found in the repository '{repo_name}'. Skipping.")
            continue

        project_key = repo_name
        project_name = repo_name

        # Create SonarQube project
        create_sonarqube_project(project_key, project_name)

        # Run SonarScanner for the project
        run_sonarscanner(project_key, project_name, repo_path)

        # Fetch and save issues to reports folder
        issues_output = os.path.join(SONARQUBE_REPORTS_FOLDER, f"{project_key}_issues.json")
        fetch_sonarqube_issues(project_key, issues_output)

    print("\nSonarQube analysis completed for all projects.")
    print(f"Access the SonarQube web interface at {SONARQUBE_URL} to view the results.")

# Main function to parse arguments and run analysis
def main():
    parser = argparse.ArgumentParser(description="Run static analysis on source code")
    parser.add_argument("--tool", choices=["sonarqube", "all"], default="all",
                        help="Select which tool to run (default: all)")
    parser.add_argument("--repo", help="Specific repository to analyze")
    args = parser.parse_args()

    # Ensure the SonarQube reports folder exists
    os.makedirs(SONARQUBE_REPORTS_FOLDER, exist_ok=True)

    if args.tool in ["sonarqube", "all"]:
        run_sonarqube_analysis(args.repo)

if __name__ == "__main__":
    main()
