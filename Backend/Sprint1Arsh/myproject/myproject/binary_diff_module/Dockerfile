#binary_diff_module/Dockerfile

# Dockerfile in binary-analysis service
FROM python:3.9-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN apt-get update && \
    apt-get install -y gcc curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl

# Copy the script and Kubernetes manifests
COPY module_script.py module_script.py
COPY kubernetes/ /app/kubernetes/

# Set the entrypoint to run module_script.py
CMD ["python", "module_script.py"]