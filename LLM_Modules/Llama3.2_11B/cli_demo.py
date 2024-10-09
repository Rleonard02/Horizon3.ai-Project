# cli_demo.py

import argparse
from llm_module import analyze_code
import json

parser = argparse.ArgumentParser(description='Code Vulnerability Analyzer')
parser.add_argument('file', type=str, help='Path to the code file to analyze')

args = parser.parse_args()

# Read the code from the file
with open(args.file, 'r') as code_file:
    code_snippet = code_file.read()

# Analyze the code
analysis = analyze_code(code_snippet)

# Display the results
if analysis:
    try:
        vulnerabilities = json.loads(analysis)
        for vuln in vulnerabilities:
            print(f"Vulnerability Type: {vuln['vulnerability_type']}")
            print(f"Description: {vuln['description']}")
            print(f"Affected Lines: {vuln['line_numbers']}")
            print(f"Recommendations: {vuln['recommendations']}")
            print("-" * 40)
    except json.JSONDecodeError:
        print("Failed to parse the analysis as JSON.")
        print("Raw analysis output:")
        print(analysis)
else:
    print("No vulnerabilities found or failed to analyze the code.")
