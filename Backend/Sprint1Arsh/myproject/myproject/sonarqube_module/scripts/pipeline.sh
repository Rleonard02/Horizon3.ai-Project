#!/bin/bash

set -e
set -u

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting the SonarQube analysis pipeline..."

# Configuration
SONARQUBE_URL="http://sonarqube:9000"
WAIT_TIME=0
TIMEOUT=120  # Timeout after 120 seconds
INPUT_FILES_DIR="/sonarqube_shared/input_files"
PREV_STATE_FILE="/sonarqube_app/current_state.txt"
RETRIES=5
DELAY=5

# Wait for SonarQube server to be fully ready
log "Waiting for SonarQube server to be ready at ${SONARQUBE_URL}..."

while ! curl -s "${SONARQUBE_URL}/api/system/status" | grep -q "\"status\":\"UP\""; do
    if [ $WAIT_TIME -ge $TIMEOUT ]; then
        log "Error: SonarQube server did not become fully ready in time."
        exit 1
    fi
    log "SonarQube server not fully ready yet. Waiting..."
    sleep 5
    WAIT_TIME=$((WAIT_TIME + 5))
done

log "SonarQube server is ready."

# Create or retrieve SonarQube token
log "Creating SonarQube token..."

TOKEN=""
for i in $(seq 1 $RETRIES); do
    TOKEN=$(python3 ./scripts/create_token.py pipeline_token)
    if [ -n "$TOKEN" ]; then
        log "Token successfully created on attempt $i."
        break
    fi
    log "Token creation failed. Retrying in $DELAY seconds... ($i/$RETRIES)"
    sleep $DELAY
done

if [ -z "$TOKEN" ]; then
    log "Error: Token creation failed after $RETRIES attempts."
    exit 1
fi

log "Generated TOKEN: $TOKEN"

export SONARQUBE_TOKEN=$TOKEN
log "SONARQUBE_TOKEN environment variable set."

# Persist the token in the .sonarqube_env file
echo "export SONARQUBE_TOKEN=${TOKEN}" > ./.sonarqube_env
chmod 600 ./.sonarqube_env
log "SONARQUBE_TOKEN saved to ./.sonarqube_env."

if [ -f ./.sonarqube_env ]; then
    source ./.sonarqube_env
    log "Loaded SONARQUBE_TOKEN from .sonarqube_env."
else
    log "Error: .sonarqube_env not found."
    exit 1
fi


log "Monitoring ${INPUT_FILES_DIR} for changes..."

# Run analysis script in an infinite loop
while true; do
    log "Running SonarQube analysis..."
    python3 ./scripts/run_analysis_and_compare.py --tool sonarqube
    log "SonarQube analysis completed. Waiting before next run..."
    sleep 10  # Adjust delay as needed
done
