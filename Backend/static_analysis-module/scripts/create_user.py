
#!/usr/bin/env python3

import os
import requests
import sys

# SonarQube server URL
SONARQUBE_URL = os.getenv("SONARQUBE_URL", "http://localhost:9000")

# Admin credentials (Set these as environment variables)
SONARQUBE_ADMIN_USERNAME = os.getenv("SONARQUBE_ADMIN_USERNAME", "admin")
SONARQUBE_ADMIN_PASSWORD = os.getenv("SONARQUBE_ADMIN_PASSWORD", "admin")  # Change this in production

def create_user(username, password, email, name):
    api_url = f"{SONARQUBE_URL}/api/users/create"
    payload = {
        "login": username,
        "password": password,
        "name": name,
        "email": email
    }
    response = requests.post(api_url, auth=(SONARQUBE_ADMIN_USERNAME, SONARQUBE_ADMIN_PASSWORD), data=payload)

    if response.status_code == 200:
        print(f"User '{username}' created successfully.")
    elif response.status_code == 400 and "already exists" in response.text:
        print(f"User '{username}' already exists.")
    else:
        print(f"Failed to create user '{username}'. Status Code: {response.status_code}, Response: {response.text}")
        sys.exit(1)

def main():
    if len(sys.argv) != 5:
        print("Usage: python3 create_user.py <username> <password> <email> <name>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    email = sys.argv[3]
    name = sys.argv[4]

    create_user(username, password, email, name)

if __name__ == "__main__":
    main()

