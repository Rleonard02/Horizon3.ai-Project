FROM python:3.9-slim

WORKDIR /app

# Install git and dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy and install main requirements
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install LLM requirements
COPY llm_requirements.txt llm_requirements.txt
RUN pip install --no-cache-dir -r llm_requirements.txt

# Copy application and LLM scripts
COPY app.py app.py
COPY autotrain_qwen_dpo.py autotrain_qwen_dpo.py
COPY llama_32_11b.py llama_32_11b.py
COPY llama_31_70b.py llama_31_70b.py
COPY qwen_25_32b.py qwen_25_32b.py
COPY qwen_25_72b.py qwen_25_72b.py


VOLUME ["/shared"]

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001"]
