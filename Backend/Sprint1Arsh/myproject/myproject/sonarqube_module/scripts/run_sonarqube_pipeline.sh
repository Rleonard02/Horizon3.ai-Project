#!/bin/bash

# sonarqube_module/scripts/run_sonarqube_pipeline.sh

set -e
set -u

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting the SonarQube analysis pipeline..."

log "Creating SonarQube token..."
TOKEN=$(python3 create_token.py pipeline_token)

log "SONARQUBE_TOKEN environment variable set."


export SONARQUBE_TOKEN=$TOKEN
SONARQUBE_ENV="/sonarqube_app/.sonarqube_env"

# Persist the token in the .sonarqube_env file
echo "export SONARQUBE_TOKEN=${TOKEN}" > "${SONARQUBE_ENV}"
chmod 600 "${SONARQUBE_ENV}"
log "SONARQUBE_TOKEN saved to "${SONARQUBE_ENV}"."


INPUT_FILES_DIR="/sonarqube_shared/input_files"

log "Monitoring ${INPUT_FILES_DIR} for changes..."

while true; do
    find "${INPUT_FILES_DIR}" -type f | sort > /sonarqube_app/current_state.txt
    if ! diff /sonarqube_app/current_state.txt "${PREV_STATE_FILE}" > /dev/null 2>&1; then
        log "Change detected in ${INPUT_FILES_DIR}, running analysis..."
        cp /sonarqube_app/current_state.txt "${PREV_STATE_FILE}"

        # Run Static Analysis
        python3 /sonarqube_app/scripts/run_analysis_and_compare.py --tool sonarqube

        log "SonarQube analysis completed."
    fi
    sleep 10
done
