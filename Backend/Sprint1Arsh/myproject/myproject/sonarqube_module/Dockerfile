# Base image with Python for script execution
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory inside the container
WORKDIR /sonarqube_app

ENV PATH="/opt/sonar-scanner-cli-4.6.2.2472-linux/bin:${PATH}"

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Download and install the Sonar Scanner CLI
RUN curl -o sonar-scanner-cli.zip -L "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.6.2.2472-linux.zip" \
    && ls -lh sonar-scanner-cli.zip \
    && unzip -l sonar-scanner-cli.zip \
    && unzip sonar-scanner-cli.zip -d /opt \
    && mv /opt/sonar-scanner-4.6.2.2472-linux /opt/sonar-scanner-cli-4.6.2.2472-linux \
    && ls -l /opt \
    && rm sonar-scanner-cli.zip



# Add SonarScanner to PATH
ENV PATH="/opt/sonar-scanner-cli-4.6.2.2472-linux/bin:${PATH}"

# Copy analysis scripts into the container
COPY scripts /sonarqube_app/scripts

# Install Python dependencies for your script (if needed)
RUN pip install --no-cache-dir -r /sonarqube_app/scripts/requirements.txt

# Ensure entrypoint script is executable
RUN chmod +x /sonarqube_app/scripts/entrypoint.sh

# Set the default entrypoint to execute the analysis script
ENTRYPOINT ["bash", "/sonarqube_app/scripts/entrypoint.sh"]
