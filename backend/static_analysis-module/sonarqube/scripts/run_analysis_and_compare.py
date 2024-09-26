import subprocess
import requests
import os
import time
from datetime import datetime
import json

# SonarQube server details
SONARQUBE_URL = "http://localhost:9000"
SONARQUBE_LOGIN = "admin"
SONARQUBE_PASSWORD = "admin"

# Paths
SONAR_PROPERTIES_FILE = os.path.abspath("./sonar_project1.properties")  # Path to the sonar.properties file
SOURCE_CODE_DIR = os.path.abspath("../source_code")  # Path to the source_code folder
REPORTS_FOLDER = os.path.abspath("./reports")  # Path to the reports folder

# Function to update sonar.properties with the correct source file/folder
def update_sonar_properties(project_key, source_path):
    # Read the existing sonar.properties file
    with open(SONAR_PROPERTIES_FILE, "r") as f:
        properties_content = f.readlines()

    # Update the sonar.projectKey and sonar.sources
    with open(SONAR_PROPERTIES_FILE, "w") as f:
        for line in properties_content:
            if line.startswith("sonar.projectKey"):
                f.write(f"sonar.projectKey={project_key}\n")
            elif line.startswith("sonar.sources"):
                f.write(f"sonar.sources={source_path}\n")
            else:
                f.write(line)

# Function to run Sonar Scanner for a given source file/folder
def run_sonar_scanner(project_key, source_path):
    # Update sonar.properties with the new project key and source path
    update_sonar_properties(project_key, source_path)
    
    # Run the Sonar Scanner using Docker
    command = [
        "docker", "run", "--rm",
        "--platform", "linux/amd64",  # Specify the platform (if needed)
        "-e", f"SONAR_HOST_URL={SONARQUBE_URL}",
        "-e", f"SONAR_LOGIN={SONARQUBE_LOGIN}",
        "-e", f"SONAR_PASSWORD={SONARQUBE_PASSWORD}",
        "-v", f"{os.getcwd()}:/usr/src/project",  # Mount the current directory
        "sonarsource/sonar-scanner-cli",
        "-Dsonar.projectKey={project_key}",
        "-Dsonar.projectBaseDir=/usr/src/project/sonarqube"
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    print(result.stdout.decode("utf-8"))
    if result.returncode != 0:
        print("Error:", result.stderr.decode("utf-8"))

# Fetch analysis results from SonarQube API
def fetch_sonar_results(project_key):
    url = f"{SONARQUBE_URL}/api/issues/search?component={project_key}"
    response = requests.get(url, auth=(SONARQUBE_LOGIN, SONARQUBE_PASSWORD))
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching results for {project_key}: {response.status_code}")
        return None

# Save analysis results to a file in the reports folder
def save_report(report_content, report_name):
    # Ensure the reports folder exists
    if not os.path.exists(REPORTS_FOLDER):
        os.makedirs(REPORTS_FOLDER)

    # Write the report to a file
    report_path = os.path.join(REPORTS_FOLDER, report_name)
    with open(report_path, 'w') as report_file:
        report_file.write(report_content)
    
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    # List the files and folders inside the source_code directory
    source_items = [os.path.join(SOURCE_CODE_DIR, item) for item in os.listdir(SOURCE_CODE_DIR) if os.path.isfile(os.path.join(SOURCE_CODE_DIR, item)) or os.path.isdir(os.path.join(SOURCE_CODE_DIR, item))]

    if len(source_items) < 2:
        print("Error: There must be at least two files or folders in the source_code directory for comparison.")
        exit(1)

    # Use only the first two items (files or folders) found for comparison
    source_item_1 = source_items[0]
    source_item_2 = source_items[1]

    # Generate unique project keys for the two items
    project_key_1 = f"project_{os.path.basename(source_item_1)}_{int(time.time())}"
    project_key_2 = f"project_{os.path.basename(source_item_2)}_{int(time.time())}"

    # Run analysis on both items
    print(f"Running analysis for {source_item_1} with project key {project_key_1}...")
    run_sonar_scanner(project_key_1, source_item_1)

    print(f"Running analysis for {source_item_2} with project key {project_key_2}...")
    run_sonar_scanner(project_key_2, source_item_2)

    # Sleep for a few seconds to allow analysis to complete
    time.sleep(10)

    # Fetch results for both versions and save them in separate reports
    print("Fetching results for Version 1...")
    results_v1 = fetch_sonar_results(project_key_1)
    if results_v1:
        report_content_v1 = json.dumps(results_v1, indent=4)
        save_report(report_content_v1, f"analysis_report_{project_key_1}.json")

    print("Fetching results for Version 2...")
    results_v2 = fetch_sonar_results(project_key_2)
    if results_v2:
        report_content_v2 = json.dumps(results_v2, indent=4)
        save_report(report_content_v2, f"analysis_report_{project_key_2}.json")