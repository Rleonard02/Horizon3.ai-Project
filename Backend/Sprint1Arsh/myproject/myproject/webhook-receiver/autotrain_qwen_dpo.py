# llm_module.py
import re
import sys
import os
import requests

HUGGINGFACE_API_TOKEN = "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"

# CHANGE TO USE DIFFERENT MODELS FROM HUGGINGFACE INFERENCE API
API_URL = "https://f2phldie8tk76tvl.us-east-1.aws.endpoints.huggingface.cloud" 

headers = {
    "Accept" : "application/json",
    "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
    "Content-Type": "application/json" 
}

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
        "parameters": {"max_new_tokens": 500},
        "options": {"use_cache": False}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, dict) and "error" in result:
            print(f"Error from Hugging Face API: {result['error']}")
            return None

        analysis = result[0]["generated_text"]
        return analysis.strip()

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def extract_confidence_score(output):
    """
    Extracts the confidence score from the analysis output.

    Args:
        output (str): The analysis output.

    Returns:
        int: The confidence score, or None if not found.
    """
    match = re.search(r'Confidence Score:\s*(\d+)%', output, re.IGNORECASE)
    if match:
        return int(match.group(1))
    else:
        return None

def main():
    # Check for input arguments
    if len(sys.argv) < 2:
        print("Usage: python qwen_analysis.py <source_code_file>")
        sys.exit(1)

    input_filepath = sys.argv[1]

    # Check if the file exists
    if not os.path.exists(input_filepath):
        print(f"Error: File '{input_filepath}' not found.")
        sys.exit(1)

    # Read the code snippet
    with open(input_filepath, 'r', encoding='utf-8') as f:
        code_snippet = f.read()

    # Analyze the code snippet
    analysis_output = analyze_code(code_snippet)

    if analysis_output:
        confidence_score = extract_confidence_score(analysis_output)

        # Process and save the output
        base_name = os.path.splitext(os.path.basename(input_filepath))[0]
        output_directory = '/shared/llm_output'
        os.makedirs(output_directory, exist_ok=True)
        output_filename = f"{base_name}_autotrain_qwen_dpo_output.md"
        output_filepath = os.path.join(output_directory, output_filename)

        markdown_report = re.sub(r'Confidence Score:\s*\d+%\s*', '', analysis_output, flags=re.IGNORECASE).strip()

        with open(output_filepath, 'w', encoding='utf-8') as f:
            if confidence_score is not None:
                f.write(f"Confidence Score: {confidence_score}%\n\n")
            f.write(markdown_report)

        print(f"Analysis complete for {base_name}. Confidence Score: {confidence_score}%")
        print(f"Markdown report saved to '{output_filepath}'")
    else:
        print("Failed to get analysis from the LLM.")

if __name__ == "__main__":
    main()
