# Use the official SonarQube image
FROM sonarqube:community

# Install Sonar Scanner CLI
RUN apt-get update && apt-get install -y curl unzip \
    && curl -o sonar-scanner-cli.zip -L "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.6.2.2472-linux.zip" \
    && unzip sonar-scanner-cli.zip -d /opt \
    && rm sonar-scanner-cli.zip

# Expose the default SonarQube port
EXPOSE 9000

# Run SonarQube in the background and the scanner in the foreground
CMD ["bash", "-c", "/opt/sonarqube/bin/run.sh & /opt/sonar-scanner-cli-4.6.2.2472-linux/bin/sonar-scanner -Dsonar.projectKey=my_project -Dsonar.sources=/usr/src/project"]
