#!/usr/bin/env python3

import os
import requests
import sys

# SonarQube server URL
SONARQUBE_URL = os.getenv("SONARQUBE_URL", "http://localhost:9000")

# Admin credentials (Set these as environment variables)
SONARQUBE_ADMIN_USERNAME = os.getenv("SONARQUBE_ADMIN_USERNAME", "admin")
SONARQUBE_ADMIN_PASSWORD = os.getenv("SONARQUBE_ADMIN_PASSWORD", "admin")  # Change this in production

def create_token(token_name):
    api_url = f"{SONARQUBE_URL}/api/user_tokens/generate"
    payload = {"name": token_name}
    try:
        response = requests.post(api_url, auth=(SONARQUBE_ADMIN_USERNAME, SONARQUBE_ADMIN_PASSWORD), data=payload)
    except Exception as e:
        print(f"Exception occurred while creating token: {e}", flush=True)
        sys.exit(1)

    if response.status_code == 200:
        token = response.json().get("token")
        return token
    elif response.status_code == 400:
        error_msg = response.json().get("errors", [{}])[0].get("msg", "")
        if "already exists" in error_msg:
            return None
        else:
            print(f"Failed to create token '{token_name}'. Error: {error_msg}", flush=True)
            sys.exit(1)
    else:
        print(f"Failed to create token. Status Code: {response.status_code}, Response: {response.text}", flush=True)
        sys.exit(1)

def delete_token(token_name):
    api_url = f"{SONARQUBE_URL}/api/user_tokens/delete"
    payload = {"name": token_name}
    try:
        response = requests.post(api_url, auth=(SONARQUBE_ADMIN_USERNAME, SONARQUBE_ADMIN_PASSWORD), data=payload)
    except Exception as e:
        print(f"Exception occurred while deleting token: {e}", flush=True)
        sys.exit(1)

    if response.status_code == 204:
        print(f"Token '{token_name}' deleted successfully.", flush=True)
    elif response.status_code == 400:
        error_msg = response.json().get("errors", [{}])[0].get("msg", "")
        if "not found" in error_msg:
            print(f"Token '{token_name}' does not exist.", flush=True)
        else:
            print(f"Failed to delete token '{token_name}'. Status Code: {response.status_code}, Response: {response.text}", flush=True)
            sys.exit(1)
    else:
        print(f"Failed to delete token '{token_name}'. Status Code: {response.status_code}, Response: {response.text}", flush=True)
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 create_token.py <token_name>", flush=True)
        sys.exit(1)

    token_name = sys.argv[1]
    token = create_token(token_name)

    if token:
        print(token, flush=True)
    else:
        # Token already exists, delete it and recreate
        print(f"Token '{token_name}' already exists. Deleting and recreating it...", flush=True)
        delete_token(token_name)
        token = create_token(token_name)
        if token:
            print(token, flush=True)
        else:
            print(f"Failed to create token '{token_name}' after deletion.", flush=True)
            sys.exit(1)

if __name__ == "__main__":
    main()
