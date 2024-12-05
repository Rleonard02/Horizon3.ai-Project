#!/bin/bash

# sonarqube_module/entrypoint.sh

set -e

# Start SonarQube in the background
/opt/sonarqube/bin/run.sh &

# Wait for SonarQube to be ready
python3 /sonarqube_app/scripts/wait_for_sonarqube.py

# Run your pipeline script
bash /sonarqube_app/scripts/run_sonarqube_pipeline.sh

# Wait for SonarQube process to exit to keep the container running
wait -n
