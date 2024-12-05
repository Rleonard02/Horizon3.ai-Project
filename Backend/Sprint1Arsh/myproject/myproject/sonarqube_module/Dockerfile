# sonarqube_module/Dockerfile

FROM sonarqube:community

# Switch to root user to install packages
USER root

# Install necessary packages
RUN apt-get update && apt-get install -y curl unzip python3 python3-pip git dos2unix \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy scripts and entrypoint into the container
COPY scripts /app/scripts
COPY entrypoint.sh /app/entrypoint.sh

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /app/scripts/requirements.txt

# Install Sonar Scanner CLI
RUN curl -o sonar-scanner-cli.zip -L "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.6.2.2472-linux.zip" \
    && unzip sonar-scanner-cli.zip -d /opt \
    && rm sonar-scanner-cli.zip

# Install C++ Community Plugin
RUN mkdir -p /opt/sonarqube/extensions/plugins
RUN curl -L -o /opt/sonarqube/extensions/plugins/sonar-cxx-plugin.jar \
    https://github.com/SonarOpenCommunity/sonar-cxx/releases/download/cxx-2.1.0/sonar-cxx-plugin-2.1.0.3143.jar

# Convert line endings
RUN dos2unix /app/entrypoint.sh && \
    dos2unix /app/scripts/*.sh && \
    dos2unix /app/scripts/*.py

# Ensure scripts are executable
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/scripts/*.sh /app/scripts/*.py

# Switch back to the sonarqube user
USER sonarqube

# Set the entrypoint to the custom script
ENTRYPOINT ["/app/entrypoint.sh"]

# Expose the default SonarQube port (already exposed in base image)
EXPOSE 9000
