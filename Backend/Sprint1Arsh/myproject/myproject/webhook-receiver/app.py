# webhook-receiver/app.py

import os
import json
import logging
import shutil
from git import Repo
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# Paths for Binary Analysis
BINARY_SHARED_DIR = '/bin_shared'
BINARY_REPOS_DIR = os.path.join(BINARY_SHARED_DIR, 'repos')
BINARY_VERSION1_DIR = os.path.join(BINARY_SHARED_DIR, 'c_source', 'version1')
BINARY_VERSION2_DIR = os.path.join(BINARY_SHARED_DIR, 'c_source', 'version2')

# Paths for SonarQube
SONARQUBE_SHARED_DIR = '/sonarqube_shared'
SONARQUBE_REPOS_DIR = os.path.join(SONARQUBE_SHARED_DIR, 'repos')
SONARQUBE_INPUT_FILES_DIR = os.path.join(SONARQUBE_SHARED_DIR, 'input_files')

@app.post("/webhook")
async def webhook(request: Request):
    
    payload = await request.json()
    logger.info(f"Received payload: {payload}")

    # Extract repository information
    repo_url = payload['repository']['clone_url']
    repo_name = payload['repository']['name']
    commits = payload['commits']
    default_branch = payload['repository']['default_branch']

    # Get the current and previous commits from 'after' and 'before'
    current_commit = payload['after']
    parent_commit = payload['before']

    # Ensure directories exist for Binary Analysis
    os.makedirs(BINARY_VERSION1_DIR, exist_ok=True)
    os.makedirs(BINARY_VERSION2_DIR, exist_ok=True)
    os.makedirs(BINARY_REPOS_DIR, exist_ok=True)

    # Clone or pull the repository for Binary Analysis
    binary_repo_path = os.path.join(BINARY_REPOS_DIR, repo_name)
    if os.path.exists(binary_repo_path):
        repo = Repo(binary_repo_path)
        origin = repo.remotes.origin
        repo.git.checkout(default_branch)
        origin.pull()
    else:
        repo = Repo.clone_from(repo_url, binary_repo_path)

    # Identify changed C files
    changed_c_files = set()
    for commit_data in commits:
        for file_path in commit_data.get('modified', []):
            if file_path.endswith('.c'):
                changed_c_files.add(file_path)

    # Process each changed C file
    for file_path in changed_c_files:
        # Checkout previous commit and save the file
        repo.git.checkout(parent_commit)
        prev_file = os.path.join(binary_repo_path, file_path)
        if os.path.exists(prev_file):
            shutil.copy(prev_file, os.path.join(BINARY_VERSION1_DIR, os.path.basename(file_path)))
        else:
            open(os.path.join(BINARY_VERSION1_DIR, os.path.basename(file_path)), 'w').close()

        # Checkout current commit and save the file
        repo.git.checkout(current_commit)
        curr_file = os.path.join(binary_repo_path, file_path)
        if os.path.exists(curr_file):
            shutil.copy(curr_file, os.path.join(BINARY_VERSION2_DIR, os.path.basename(file_path)))
        else:
            open(os.path.join(BINARY_VERSION2_DIR, os.path.basename(file_path)), 'w').close()

    # Reset to default branch
    repo.git.checkout(default_branch)

    logger.info("Binary analysis files prepared.")

    # Now handle SonarQube file copying
    # Ensure directories exist for SonarQube
    os.makedirs(SONARQUBE_REPOS_DIR, exist_ok=True)
    os.makedirs(SONARQUBE_INPUT_FILES_DIR, exist_ok=True)

    # Clone or update repository for SonarQube Analysis
    repo_path_sonarqube = os.path.join(SONARQUBE_REPOS_DIR, repo_name)
    if os.path.exists(repo_path_sonarqube):
        logger.info(f"Updating existing repository for SonarQube Analysis: {repo_path_sonarqube}")
        repo_sonar = Repo(repo_path_sonarqube)
        origin = repo_sonar.remotes.origin
        repo_sonar.git.checkout(default_branch)
        origin.pull()
    else:
        logger.info(f"Cloning repository for SonarQube Analysis to: {repo_path_sonarqube}")
        repo_sonar = Repo.clone_from(repo_url, repo_path_sonarqube)
        repo_sonar.git.checkout(default_branch)

    # Copy only the version2 (current) files to SonarQube input_files
    try:
        # Ensure the input_files directory for this repo exists
        repo_destination_sonarqube = os.path.join(SONARQUBE_INPUT_FILES_DIR, repo_name)
        os.makedirs(repo_destination_sonarqube, exist_ok=True)

        # Iterate over version2 files and copy them to SonarQube input_files
        for file_name in os.listdir(BINARY_VERSION2_DIR):
            src_file = os.path.join(BINARY_VERSION2_DIR, file_name)
            dest_file = os.path.join(repo_destination_sonarqube, file_name)
            if os.path.isfile(src_file):
                shutil.copy(src_file, dest_file)
                logger.info(f"Copied {file_name} to SonarQube input_files")
            else:
                logger.warning(f"Skipping non-file {file_name}")

        logger.info(f"SonarQube input_files prepared for repository: {repo_name}")
    except Exception as e:
        logger.error(f"Failed to copy files to SonarQube input_files: {e}")
        raise HTTPException(status_code=500, detail="Failed to copy files for SonarQube Analysis.")

    return {"message": "Webhook processed for binary analysis and SonarQube analysis."}
