#!/bin/bash

set -e
set -u

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting the static analysis pipeline..."

# Step 1: Start SonarQube and PostgreSQL services
log "Starting SonarQube and PostgreSQL services..."
cd /app/sonarqube
docker-compose up -d

# Step 2: Wait for SonarQube server to become ready
log "Waiting for SonarQube server to become ready..."
./scripts/wait_for_sonarqube.sh

# Step 3: Create SonarQube token
log "Creating SonarQube token..."
TOKEN=$(python3 /app/scripts/create_token.py pipeline_token)

# Export the token as an environment variable for the current session
export SONARQUBE_TOKEN=$TOKEN
log "SONARQUBE_TOKEN environment variable set."

# Persist the token in the .sonarqube_env file
echo "export SONARQUBE_TOKEN=${TOKEN}" > /app/.sonarqube_env
chmod 600 /app/.sonarqube_env
log "SONARQUBE_TOKEN saved to /app/.sonarqube_env."

# Step 4: Run Static Analysis
python3 /app/scripts/run_analysis_and_compare.py --tool sonarqube

log "Static analysis pipeline completed successfully."
