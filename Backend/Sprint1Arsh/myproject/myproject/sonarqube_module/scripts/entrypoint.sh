#!/bin/bash

set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Wait for SonarQube to become ready
SONARQUBE_URL="http://sonarqube:9000"
log "Waiting for SonarQube server to become ready..."
WAIT_TIME=0
TIMEOUT=180  # Timeout after 180 seconds
while ! curl -sSf "$SONARQUBE_URL" > /dev/null; do
    if [ $WAIT_TIME -ge $TIMEOUT ]; then
        log "Error: SonarQube server did not become ready in time."
        exit 1
    fi
    log "SonarQube not ready yet. Waiting..."
    sleep 5
    WAIT_TIME=$((WAIT_TIME + 5))
done
log "SonarQube server is ready."

# Run analysis script
bash /sonarqube_app/scripts/pipeline.sh
