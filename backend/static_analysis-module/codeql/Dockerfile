# Use Ubuntu as the base image
FROM ubuntu:22.04

# Set non-interactive mode for installations
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    python3 \
    python3-pip \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Create a home directory for the codeql user
RUN mkdir -p /usr/local/codeql-home /opt/codeql

# Clone the latest version of CodeQL queries
RUN git clone --depth 1 https://github.com/github/codeql /usr/local/codeql-home/codeql-repo \
    && git --git-dir /usr/local/codeql-home/codeql-repo/.git log --pretty=reference -1 > /opt/codeql/codeql-repo-last-commit

# Download and install the latest CodeQL CLI version
RUN wget -q https://github.com/github/codeql-cli-binaries/releases/latest/download/codeql-linux64.zip -O /tmp/codeql_linux.zip \
    && unzip /tmp/codeql_linux.zip -d /opt/codeql \
    && rm /tmp/codeql_linux.zip

# Make sure the CodeQL binary is executable
RUN chmod +x /opt/codeql/codeql/codeql

# Set the PATH to include CodeQL
ENV PATH="/opt/codeql/codeql:${PATH}"

# Pre-compile CodeQL queries for faster analysis
RUN codeql query compile --threads=0 /usr/local/codeql-home/codeql-repo/*/ql/src/codeql-suites/*.qls --additional-packs=.

# Define the working directory inside the container
WORKDIR /codeql_workspace

# Keep the container running
CMD ["/bin/bash"]
