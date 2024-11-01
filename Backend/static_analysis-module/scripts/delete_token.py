#!/usr/bin/env python3

import os
import requests
import sys

# SonarQube server URL
SONARQUBE_URL = os.getenv("SONARQUBE_URL", "http://localhost:9000")

# Admin credentials (Set these as environment variables)
SONARQUBE_ADMIN_USERNAME = os.getenv("SONARQUBE_ADMIN_USERNAME", "admin")
SONARQUBE_ADMIN_PASSWORD = os.getenv("SONARQUBE_ADMIN_PASSWORD", "admin")  # Ensure this matches .sonarqube_credentials

def delete_token(token_name):
    api_url = f"{SONARQUBE_URL}/api/user_tokens/delete"
    payload = {"name": token_name}
    response = requests.post(api_url, auth=(SONARQUBE_ADMIN_USERNAME, SONARQUBE_ADMIN_PASSWORD), data=payload)

    if response.status_code == 204:
        print(f"Token '{token_name}' deleted successfully.")
    elif response.status_code == 400:
        error_msg = response.json().get("errors", [{}])[0].get("msg", "")
        if "not found" in error_msg:
            print(f"Token '{token_name}' does not exist.")
        else:
            print(f"Failed to delete token '{token_name}'. Status Code: {response.status_code}, Response: {response.text}")
            sys.exit(1)
    else:
        print(f"Failed to delete token '{token_name}'. Status Code: {response.status_code}, Response: {response.text}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 delete_token.py <token_name>")
        sys.exit(1)

    token_name = sys.argv[1]
    delete_token(token_name)

if __name__ == "__main__":
    main()
