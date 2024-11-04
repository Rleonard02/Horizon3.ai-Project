# Use the official Python slim image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SONARQUBE_URL=http://sonarqube:9000
ENV SONARQUBE_DOCKER_URL=http://sonarqube:9000

# Install dependencies
RUN apt-get update && \
    apt-get install -y git curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts and configurations
COPY scripts/ /app/scripts/
COPY sonarqube/ /app/sonarqube/
COPY .sonarqube_env /app/.sonarqube_env

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose SonarQube port if needed
EXPOSE 9000

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
