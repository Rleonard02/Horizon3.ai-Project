# codeql_analysis_module/Dockerfile

FROM python:3.9-slim

# Install necessary packages
RUN apt-get update && \
    apt-get install -y wget tar build-essential git && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ARG CODEQL_VERSION=2.7.2  # Update to a valid CodeQL CLI version
ENV CODEQL_VERSION=${CODEQL_VERSION}
ENV CODEQL_DIR=/opt/codeql

# Install CodeQL CLI
RUN mkdir -p $CODEQL_DIR && \
    wget https://github.com/github/codeql-cli-binaries/releases/download/v${CODEQL_VERSION}/codeql-linux64.tar.gz -O /tmp/codeql.tar.gz && \
    tar -xzf /tmp/codeql.tar.gz -C $CODEQL_DIR && \
    rm /tmp/codeql.tar.gz && \
    ln -s $CODEQL_DIR/codeql/codeql /usr/local/bin/codeql

# Verify CodeQL installation
RUN codeql --version

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the analysis script
COPY module_script.py /app/

# Ensure the script is executable
RUN chmod +x /app/module_script.py

# Define the default command
CMD ["python", "module_script.py"]
