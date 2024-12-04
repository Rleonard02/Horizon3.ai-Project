# sonarqube_module/Dockerfile

# Use the official Python slim image
FROM python:3.9-slim

LABEL maintainer="your_email@example.com"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SONARQUBE_URL=http://sonarqube:9000

# Install dependencies
RUN apt-get update && \
    apt-get install -y git curl unzip dos2unix && \
    rm -rf /var/lib/apt/lists/*

# Install SonarScanner
RUN curl -L https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.7.0.2747-linux.zip -o /tmp/sonar-scanner.zip && \
    unzip /tmp/sonar-scanner.zip -d /opt && \
    rm /tmp/sonar-scanner.zip && \
    ln -s /opt/sonar-scanner-4.7.0.2747-linux/bin/sonar-scanner /usr/local/bin/sonar-scanner

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts and module script
COPY scripts/ /app/scripts/
COPY module_script.py /app/

# Ensure scripts are executable (if needed)
RUN chmod +x /app/scripts/*

# Default command (can be overridden by docker-compose)
CMD ["python", "module_script.py"]
