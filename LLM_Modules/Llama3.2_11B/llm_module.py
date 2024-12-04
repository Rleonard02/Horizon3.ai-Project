# llm_module.py

import os
import requests
from pymongo import MongoClient
import logging

HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

# CHANGE TO USE DIFFERENT MODELS FROM HUGGINGFACE INFERENCE API
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-11B-Vision-Instruct" 

headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

def analyze_code(code_snippet):
    prompt = f"""
You are a cybersecurity expert specializing in code vulnerability analysis.

Analyze the following code for potential security vulnerabilities.

Provide a detailed report in Markdown format.

At the very beginning of your response, include a line in the following format:

`Confidence Score: [confidence_score]%`

Replace `[confidence_score]` with a number from 0 to 100 indicating your confidence in the need for human review of the code. The goal is to give you code snippets for you to assign priorities to for human review. Think hard about the confidence score. It will be use to rank the given snippet against other snippets to be prioritized for human review

Do not include any additional text before or after the confidence score line.

Be thorough and concise in your report. Formatting should be simple and clean. 

**Example:**

`Confidence Score: 85%`

# Vulnerability Analysis Report

[Your detailed report here.]

Code:
```{code_snippet}```
    """
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 1000, "temperature": 0.2, "top_p": 0.95},
        "options": {"use_cache": False}
    }
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, dict) and "error" in result:
            print(f"Error from Hugging Face API: {result['error']}")
            return None

        analysis = result[0]["generated_text"]

        # new lines added to save to mongoDB

        # Get MongoDB URI from environment variable
        mongo_uri = os.getenv("MONGO_URI")

        if not mongo_uri:
            raise ValueError("MONGO_URI environment variable is not set!")

        # Connect to MongoDB Atlas
        client = MongoClient(mongo_uri)
        db = client["Analysis"]
        #client.admin.command('ping')
        logger.info("Successfully connected to MongoDB.")
        collection = db["llmAnalysis"]
        #collection.insert_one({"analysis": "test analysis output"})
        document = {
            "analysis": analysis  # Assuming 'analysis' is the string you want to save
        }
        collection.insert_one(document)

        # end of new lines
        return analysis.strip()

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None