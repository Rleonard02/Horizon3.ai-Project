#!/usr/bin/env python3

# sonarqube_module/scripts/wait_for_sonarqube.py

import os
import requests
import time
import sys

def wait_for_sonarqube(url="http://sonarqube:9000/api/system/health", timeout=300):
    print(f"Waiting for SonarQube server at {url} to be ready...")
    start_time = time.time()
    while True:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                health = response.json().get('health', '')
                if health == 'GREEN':
                    print("SonarQube server is up and running.")
                    break
                else:
                    print(f"SonarQube server health is {health}. Waiting...")
            else:
                print(f"Received status code {response.status_code}. Waiting...")
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.ReadTimeout:
            pass
        if time.time() - start_time > timeout:
            print("Error: SonarQube server did not become ready in time.", flush=True)
            sys.exit(1)
        time.sleep(5)

if __name__ == "__main__":
    SONARQUBE_URL = os.getenv("SONARQUBE_URL", "http://sonarqube:9000")
    wait_for_sonarqube(url=f"{SONARQUBE_URL}/api/system/health")
