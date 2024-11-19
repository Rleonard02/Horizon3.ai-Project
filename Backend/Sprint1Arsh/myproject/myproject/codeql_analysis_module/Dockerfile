# myproject/codeql_analysis_module/Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y git wget unzip && \
    rm -rf /var/lib/apt/lists/*

# Install CodeQL CLI
ENV CODEQL_VERSION=2.19.3

RUN wget https://github.com/github/codeql-cli-binaries/releases/download/v${CODEQL_VERSION}/codeql-linux64.zip -O /tmp/codeql.zip && \
    unzip /tmp/codeql.zip -d /opt/codeql && \
    ln -s /opt/codeql/codeql /usr/local/bin/codeql && \
    rm /tmp/codeql.zip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the CodeQL analysis script
COPY codeql-analysis.py .

# Mount the shared_data volume
VOLUME ["/shared/codeql_analysis"]

CMD ["python3", "codeql-analysis.py"]
