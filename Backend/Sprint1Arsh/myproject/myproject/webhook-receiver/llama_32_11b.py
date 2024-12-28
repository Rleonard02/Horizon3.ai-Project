# llm_qwen.py
import re
import sys
import os
from huggingface_hub import InferenceClient

HUGGINGFACE_API_TOKEN = "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"

# Initialize the Hugging Face Inference Client
client = InferenceClient(api_key=HUGGINGFACE_API_TOKEN)

def analyze_code(code_snippet):
    prompt = f"""
You are a cybersecurity expert specializing in code vulnerability analysis.

Analyze the following code for potential security vulnerabilities.

Provide a detailed report in Markdown format.

At the very beginning of your response, include a line in the following format:

`Confidence Score: [confidence_score]%`

Replace `[confidence_score]` with a number from 0 to 100 indicating your confidence in the need for human review of the code. The goal is to give you code snippets for you to assign priorities to for human review. Think hard about the confidence score. It will be used to rank the given snippet against other snippets to be prioritized for human review.

Do not include any additional text before or after the confidence score line.

Be thorough and concise in your report. Formatting should be simple and clean. 

**Example:**

`Confidence Score: 85%`

# Vulnerability Analysis Report

[Your detailed report here.]

Code:
```{code_snippet}```
    """
    messages = [
        {"role": "user", "content": prompt}
    ]

    try:
        # Make the inference request
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.2-11B-Vision-Instruct",
            messages=messages,
            max_tokens=1512
        )

        # Extract and return the generated text
        return completion.choices[0].message["content"].strip()

    except Exception as e:
        print(f"Error during inference: {e}")
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
        output_filename = f"{base_name}_llama_32_11b_output.md"
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
