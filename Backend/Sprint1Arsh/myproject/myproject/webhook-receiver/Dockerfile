FROM python:3.9-slim

WORKDIR /app

# Install git and dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py app.py

VOLUME ["/shared"]

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001"]
