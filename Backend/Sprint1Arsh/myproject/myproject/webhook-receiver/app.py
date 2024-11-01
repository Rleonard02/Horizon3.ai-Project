#webhook-receiver/app.py
from fastapi import FastAPI, Request, HTTPException
import os
import subprocess
from git import Repo
import shutil
import logging

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    logger.info(f"Received payload: {payload}")

    repo_url = payload['repository']['clone_url']
    repo_name = payload['repository']['name']
    commits = payload['commits']
    default_branch = payload['repository']['default_branch']  # Get the default branch name

    # Get the current and previous commits from 'after' and 'before'
    current_commit = payload['after']
    parent_commit = payload['before']

    # Paths
    shared_dir = '/shared'
    repo_path = os.path.join(shared_dir, 'repos', repo_name)
    version1_dir = os.path.join(shared_dir, 'c_source', 'version1')
    version2_dir = os.path.join(shared_dir, 'c_source', 'version2')

    # Ensure directories exist
    os.makedirs(version1_dir, exist_ok=True)
    os.makedirs(version2_dir, exist_ok=True)

    # Clone or pull the repository
    if os.path.exists(repo_path):
        repo = Repo(repo_path)
        origin = repo.remotes.origin
        # Ensure we are on the default branch before pulling
        repo.git.checkout(default_branch)
        origin.pull()
    else:
        repo = Repo.clone_from(repo_url, repo_path)

    # Identify changed C files
    changed_files = set()
    for commit_data in commits:
        for file_path in commit_data.get('modified', []):
            if file_path.endswith('.c'):
                changed_files.add(file_path)

    # Process each changed file
    for file_path in changed_files:
        # Checkout previous commit and save the file
        repo.git.checkout(parent_commit)
        prev_file = os.path.join(repo_path, file_path)
        if os.path.exists(prev_file):
            shutil.copy(prev_file, os.path.join(version1_dir, os.path.basename(file_path)))
        else:
            # If file didn't exist in previous commit, create an empty file
            open(os.path.join(version1_dir, os.path.basename(file_path)), 'w').close()

        # Checkout current commit and save the file
        repo.git.checkout(current_commit)
        curr_file = os.path.join(repo_path, file_path)
        if os.path.exists(curr_file):
            shutil.copy(curr_file, os.path.join(version2_dir, os.path.basename(file_path)))
        else:
            # If file was deleted in current commit, create an empty file
            open(os.path.join(version2_dir, os.path.basename(file_path)), 'w').close()

    # Reset to default branch
    repo.git.checkout(default_branch)  # Use the default branch from the payload

    # Invoke the binary analysis module
    # try:
    #     subprocess.check_call(["python", "/app/module_script.py"])
    # except subprocess.CalledProcessError as e:
    #     logger.error(f"Binary analysis failed: {e}")
    #     raise HTTPException(status_code=500, detail="Binary analysis failed")

    return {"message": "Webhook processed and binary analysis triggered"}
