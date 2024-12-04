# webhook-receiver/app.py

from fastapi import FastAPI, Request, HTTPException
import os
from git import Repo
import shutil
import logging

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# Paths
shared_dir = '/shared'

# SonarQube Analysis Paths
sonarqube_shared_dir = os.path.join(shared_dir, 'sonarqube_module', 'shared_data')
sonarqube_repos_dir = os.path.join(sonarqube_shared_dir, 'repos')
sonarqube_input_repos = os.path.join(sonarqube_shared_dir, 'input_repos')
sonarqube_output_dir = os.path.join(sonarqube_shared_dir, 'output')

# Binary Analysis Paths
binary_shared_dir = os.path.join(shared_dir, 'binary_diff_module', 'shared_data')
binary_repos_dir = os.path.join(binary_shared_dir, 'repos')
binary_input_repos = os.path.join(binary_shared_dir, 'input_repos')
binary_output_dir = os.path.join(binary_shared_dir, 'output')

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    logger.info(f"Received payload: {payload}")

    # Extract repository information
    repo_info = payload.get('repository', {})
    repo_url = repo_info.get('clone_url')
    repo_name = repo_info.get('name')
    commits = payload.get('commits', [])
    default_branch = repo_info.get('default_branch', 'main')  # e.g., 'main' or 'master'

    if not repo_url or not repo_name:
        logger.error("Invalid payload: Missing repository information.")
        raise HTTPException(status_code=400, detail="Invalid payload: Missing repository information.")

    # Define repository paths
    repo_path_sonarqube = os.path.join(sonarqube_repos_dir, repo_name)
    repo_path_binary = os.path.join(binary_repos_dir, repo_name)

    # Ensure directories exist
    os.makedirs(sonarqube_repos_dir, exist_ok=True)
    os.makedirs(sonarqube_input_repos, exist_ok=True)
    os.makedirs(sonarqube_output_dir, exist_ok=True)
    os.makedirs(binary_repos_dir, exist_ok=True)
    os.makedirs(binary_input_repos, exist_ok=True)
    os.makedirs(binary_output_dir, exist_ok=True)

    # Clone or pull the repository for SonarQube Analysis
    try:
        if os.path.exists(repo_path_sonarqube):
            repo_sonarqube = Repo(repo_path_sonarqube)
            origin_sonarqube = repo_sonarqube.remotes.origin
            # Ensure we are on the default branch before pulling
            repo_sonarqube.git.checkout(default_branch)
            origin_sonarqube.pull()
            logger.info(f"Updated existing repository for SonarQube Analysis: {repo_path_sonarqube}")
        else:
            logger.info(f"Cloning repository for SonarQube Analysis to: {repo_path_sonarqube}")
            Repo.clone_from(repo_url, repo_path_sonarqube)
            logger.info("Repository cloned for SonarQube Analysis successfully.")
    except Exception as e:
        logger.error(f"Failed to clone or update repository for SonarQube Analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to clone or update repository for SonarQube Analysis.")

    # Clone or pull the repository for Binary Analysis
    try:
        if os.path.exists(repo_path_binary):
            repo_binary = Repo(repo_path_binary)
            origin_binary = repo_binary.remotes.origin
            # Ensure we are on the default branch before pulling
            repo_binary.git.checkout(default_branch)
            origin_binary.pull()
            logger.info(f"Updated existing repository for Binary Analysis: {repo_path_binary}")
        else:
            logger.info(f"Cloning repository for Binary Analysis to: {repo_path_binary}")
            Repo.clone_from(repo_url, repo_path_binary)
            logger.info("Repository cloned for Binary Analysis successfully.")
    except Exception as e:
        logger.error(f"Failed to clone or update repository for Binary Analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to clone or update repository for Binary Analysis.")

    # Copy the SonarQube repository to input_repos for analysis
    try:
        repo_destination_sonarqube = os.path.join(sonarqube_input_repos, repo_name)
        if os.path.exists(repo_destination_sonarqube):
            logger.warning(f"Repository {repo_name} already exists in SonarQube Analysis input_repos. Overwriting...")
            shutil.rmtree(repo_destination_sonarqube)
        shutil.copytree(repo_path_sonarqube, repo_destination_sonarqube)
        logger.info(f"Copied repository {repo_name} to SonarQube Analysis input_repos")
    except Exception as e:
        logger.error(f"Failed to copy repository to SonarQube Analysis input_repos: {e}")
        raise HTTPException(status_code=500, detail="Failed to copy repository for SonarQube Analysis.")

    # Copy the Binary Analysis repository to input_repos for analysis
    try:
        repo_destination_binary = os.path.join(binary_input_repos, repo_name)
        if os.path.exists(repo_destination_binary):
            logger.warning(f"Repository {repo_name} already exists in Binary Analysis input_repos. Overwriting...")
            shutil.rmtree(repo_destination_binary)
        shutil.copytree(repo_path_binary, repo_destination_binary)
        logger.info(f"Copied repository {repo_name} to Binary Analysis input_repos")
    except Exception as e:
        logger.error(f"Failed to copy repository to Binary Analysis input_repos: {e}")
        raise HTTPException(status_code=500, detail="Failed to copy repository for Binary Analysis.")

    # Return success message
    return {"message": "Webhook processed and repository updated for analysis"}
