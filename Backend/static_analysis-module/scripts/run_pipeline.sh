#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error

# Function to log messages with timestamps
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting the static analysis pipeline..."

# Step 1: Start SonarQube and PostgreSQL services
log "Starting SonarQube and PostgreSQL services..."
./start_services.sh

# Step 2: Wait for SonarQube server to become ready
log "Waiting for SonarQube server to become ready..."
WAIT_TIME=0
TIMEOUT=120  # Timeout after 120 seconds
while ! curl -sSf http://localhost:9000 > /dev/null; do
    if [ $WAIT_TIME -ge $TIMEOUT ]; then
        log "Error: SonarQube server did not become ready in time."
        exit 1
    fi
    log "SonarQube not ready yet. Waiting..."
    sleep 5
    WAIT_TIME=$((WAIT_TIME + 5))
done
log "SonarQube server is ready."

# Step 3: Create SonarQube token


log "Creating SonarQube token..."
TOKEN=$(python3 create_token.py pipeline_token)


# Export the token as an environment variable for the current session
export SONARQUBE_TOKEN=$TOKEN
log "SONARQUBE_TOKEN environment variable set."

# Persist the token in the .sonarqube_env file
echo "export SONARQUBE_TOKEN=${TOKEN}" > ../.sonarqube_env
chmod 600 ../.sonarqube_env
log "SONARQUBE_TOKEN saved to ../.sonarqube_env."

# Step 4: Run Static Analysis three times
#for i in {1..3}; do
    #log "Running SonarQube analysis iteration $i..."
   # ./run_analysis_and_compare.py --tool sonarqube
   # log "Completed SonarQube analysis iteration $i."
   # sleep 2  # Optional: Wait for 2 seconds before the next iteration
#done

log "Static analysis pipeline completed successfully."
