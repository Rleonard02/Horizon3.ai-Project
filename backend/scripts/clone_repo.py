import subprocess
import sys
import os

def clone_repo(github_url):
    # Extract repo name without the '.git' suffix
    repo_name = github_url.split('/')[-1].replace('.git', '')
    clone_dir = f"./backend/cloned_repos/{repo_name}"  # Define where to clone the repo

    # Debug print to check the paths
    print(f"Cloning repository {github_url} to {clone_dir}")

    # Check if the repo already exists
    if os.path.exists(clone_dir):
        print(f"Repository {repo_name} already exists at {clone_dir}.")
        return clone_dir  # No need to clone, just return the path

    try:
        # Print the actual git command being run
        clone_command = ["git", "clone", github_url, clone_dir]
        print(f"Running command: {' '.join(clone_command)}")

        # Clone the repository
        result = subprocess.run(clone_command, check=True, capture_output=True, text=True)
        print(f"Repository {repo_name} cloned successfully to {clone_dir}.")
        print(f"Git Output: {result.stdout}")
        print(f"Git Error Output: {result.stderr}")  # Print any error messages too
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e.stderr}")
        sys.exit(1)

    return clone_dir  # Return the cloned path

if __name__ == "__main__":
    github_url = sys.argv[1]
    clone_repo(github_url)
