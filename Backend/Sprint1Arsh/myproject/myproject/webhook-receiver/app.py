from fastapi import FastAPI, Request, HTTPException
import os
import subprocess
from git import Repo
import shutil
import logging
import re

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

MODEL_SCRIPTS = {
    "autotrain-qwen-dpo": "autotrain_qwen_dpo.py",
    "llama-32-11b": "llama_32_11b.py",
    "qwen-25-32b": "qwen_25_32b.py",
    "qwen-25-72b": "qwen_25_72b.py"
}

DEFAULT_MODEL = "qwen-25-72b"

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    logger.info(f"Received payload: {payload}")

    repo_url = payload['repository']['clone_url']
    repo_name = payload['repository']['name']
    commits = payload['commits']
    default_branch = payload['repository']['default_branch']  # Get the default branch name

    # Extract the model name from the last commit message
    commit_message = commits[-1]['message']
    model_match = re.match(r"\[(.*?)\]", commit_message)
    model_name = model_match.group(1).lower() if model_match else DEFAULT_MODEL
    model_script = MODEL_SCRIPTS.get(model_name, MODEL_SCRIPTS[DEFAULT_MODEL])

    logger.info(f"Selected model: {model_name} ({model_script})")

    # Paths
    shared_dir = '/shared'
    repo_path = os.path.join(shared_dir, 'repos', repo_name)
    version2_dir = os.path.join(shared_dir, 'c_source', 'version2')
    llm_output_dir = os.path.join(shared_dir, 'llm_output')

    os.makedirs(version2_dir, exist_ok=True)
    os.makedirs(llm_output_dir, exist_ok=True)

    # Clear previous results in the output directory
    for filename in os.listdir(llm_output_dir):
        file_path = os.path.join(llm_output_dir, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)

    # Clone or pull the repository
    if os.path.exists(repo_path):
        repo = Repo(repo_path)
        origin = repo.remotes.origin
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

    # Save the current version of each changed file
    for file_path in changed_files:
        curr_file = os.path.join(repo_path, file_path)
        if os.path.exists(curr_file):
            shutil.copy(curr_file, os.path.join(version2_dir, os.path.basename(file_path)))

    # Run the selected LLM script on the modified files
    input_directory = version2_dir
    for filename in os.listdir(input_directory):
        if filename.endswith('.c'):
            input_filepath = os.path.join(input_directory, filename)
            output_filename = f"{model_name}_analysis_output.md"
            output_filepath = os.path.join(llm_output_dir, output_filename)

            try:
                result = subprocess.run(
                    ['python', model_script, input_filepath],
                    cwd='/app',
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"LLM analysis completed for {filename}")
                else:
                    logger.error(f"LLM analysis failed for {filename}: {result.stderr}")
            except Exception as e:
                logger.error(f"Exception occurred while running LLM script for {filename}: {e}")

    return {"message": "Webhook processed and LLM analysis completed"}
