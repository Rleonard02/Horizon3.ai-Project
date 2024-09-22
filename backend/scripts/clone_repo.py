import subprocess
import sys
import os

def clone_repo(github_url):
    repo_name = github_url.split('/')[-1]  # Extract repo name
    clone_dir = f"./backend/cloned_repos/{repo_name}"  # Define where to clone the repo
    
    # Check if the repo already exists
    if os.path.exists(clone_dir):
        print(f"Repository {repo_name} already exists at {clone_dir}.")
        return clone_dir  # No need to clone, just return the path
    
    try:
        # Clone the repository
        subprocess.run(["git", "clone", github_url, clone_dir], check=True)
        print(f"Repository {repo_name} cloned successfully to {clone_dir}.")
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")
        sys.exit(1)
    
    return clone_dir  # Return the cloned path

if __name__ == "__main__":
    github_url = sys.argv[1]
    clone_repo(github_url)
