#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting SonarQube and PostgreSQL services using Docker Compose..."

# Navigate to the sonarqube directory
cd "$(dirname "$0")/../sonarqube"

# Start Docker Compose services in detached mode
docker compose up -d

# Check if Docker Compose started successfully
if [ $? -ne 0 ]; then
    log "Error: Failed to start Docker Compose services."
    exit 1
fi

log "SonarQube and PostgreSQL services started successfully."