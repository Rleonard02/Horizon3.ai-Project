# sonarqube_module/scripts/sonarqube_init.py

import os
import time
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Environment Variables
SONARQUBE_URL = os.getenv('SONARQUBE_URL', 'http://sonarqube:9000')
SONARQUBE_ADMIN_USER = os.getenv('SONARQUBE_ADMIN_USER', 'admin')
SONARQUBE_ADMIN_PASSWORD = os.getenv('SONARQUBE_ADMIN_PASSWORD', 'admin')  # Initial default password
NEW_SONARQUBE_ADMIN_PASSWORD = os.getenv('NEW_SONARQUBE_ADMIN_PASSWORD', 'admin')  # Password to change to

# Projects to Create
PROJECTS = [
    {
        "key": "project_testrepo",
        "name": "testrepo",
        "visibility": "public"
    },
    # Add more projects as needed
]

def wait_for_sonarqube():
    """Wait until SonarQube is up and running."""
    logger.info("Waiting for SonarQube to be available...")
    url = f"{SONARQUBE_URL}/api/system/health"
    while True:
        try:
            response = requests.get(url, auth=(SONARQUBE_ADMIN_USER, SONARQUBE_ADMIN_PASSWORD))
            if response.status_code == 200:
                health = response.json()
                if health.get('status') == 'UP':
                    logger.info("SonarQube is up and running.")
                    break
            logger.info("SonarQube not ready yet. Retrying in 10 seconds...")
        except requests.exceptions.ConnectionError:
            logger.info("SonarQube not reachable yet. Retrying in 10 seconds...")
        time.sleep(10)

def change_admin_password():
    """Change the default admin password."""
    logger.info("Changing admin password...")
    url = f"{SONARQUBE_URL}/api/users/change_password"
    data = {
        "login": SONARQUBE_ADMIN_USER,
        "password": NEW_SONARQUBE_ADMIN_PASSWORD,
        "previousPassword": SONARQUBE_ADMIN_PASSWORD
    }
    response = requests.post(url, data=data, auth=(SONARQUBE_ADMIN_USER, SONARQUBE_ADMIN_PASSWORD))
    if response.status_code == 204:
        logger.info("Admin password changed successfully.")
    else:
        logger.error(f"Failed to change admin password: {response.text}")

def create_projects():
    """Create SonarQube projects."""
    for project in PROJECTS:
        key = project['key']
        name = project['name']
        visibility = project.get('visibility', 'private')
        logger.info(f"Creating project: {name} (Key: {key})")
        
        # Check if project already exists
        check_url = f"{SONARQUBE_URL}/api/projects/search"
        params = {'projects': key}
        response = requests.get(check_url, params=params, auth=(SONARQUBE_ADMIN_USER, NEW_SONARQUBE_ADMIN_PASSWORD))
        if response.status_code != 200:
            logger.error(f"Failed to search for project {name}: {response.text}")
            continue
        existing_projects = response.json().get('components', [])
        if existing_projects:
            logger.info(f"Project {name} already exists. Skipping creation.")
            continue

        # Create project
        create_url = f"{SONARQUBE_URL}/api/projects/create"
        data = {
            "name": name,
            "project": key,
            "visibility": visibility
        }
        response = requests.post(create_url, data=data, auth=(SONARQUBE_ADMIN_USER, NEW_SONARQUBE_ADMIN_PASSWORD))
        if response.status_code == 204:
            logger.info(f"Project {name} created successfully.")
        else:
            logger.error(f"Failed to create project {name}: {response.text}")

def generate_token(project_key):
    """Generate a token for SonarQube analysis."""
    logger.info(f"Generating token for project {project_key}...")
    url = f"{SONARQUBE_URL}/api/user_tokens/generate"
    data = {
        "name": f"token_{project_key}",
        "scopes": ["search", "execute_analysis"]
    }
    response = requests.post(url, data=data, auth=(SONARQUBE_ADMIN_USER, NEW_SONARQUBE_ADMIN_PASSWORD))
    if response.status_code == 201:
        token = response.json().get('token')
        logger.info(f"Token generated for project {project_key}: {token}")
        return token
    else:
        logger.error(f"Failed to generate token for project {project_key}: {response.text}")
        return None

def save_tokens(tokens):
    """Save tokens to a shared JSON file."""
    tokens_file = "/shared/sonarqube_module/shared_data/tokens.json"
    try:
        with open(tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        logger.info(f"Tokens saved to {tokens_file}")
    except Exception as e:
        logger.error(f"Failed to save tokens to {tokens_file}: {e}")

def main():
    wait_for_sonarqube()
    change_admin_password()
    create_projects()
    tokens = {}
    for project in PROJECTS:
        key = project['key']
        token = generate_token(key)
        if token:
            tokens[key] = token
    save_tokens(tokens)

if __name__ == "__main__":
    main()
