# webhook-receiver/Dockerfile

FROM python:3.9-slim

# Install necessary packages, including git
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables to suppress GitPython warnings
ENV GIT_PYTHON_REFRESH=quiet

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py /app/

# Expose the port
EXPOSE 5001

# Define the default command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001"]
