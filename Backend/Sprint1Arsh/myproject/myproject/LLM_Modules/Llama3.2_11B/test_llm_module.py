from llm_module import analyze_code
import re
import sys
import os

if len(sys.argv) < 2:
    print("Usage: python script.py <source_code_file>")
    sys.exit(1)

input_filename = sys.argv[1]

if not os.path.exists(input_filename):
    print(f"Error: File '{input_filename}' not found.")
    sys.exit(1)

with open(input_filename, 'r', encoding='utf-8') as f:
    code_snippet = f.read()

analysis_output = analyze_code(code_snippet)

if analysis_output:
    def extract_confidence_score(output):
        match = re.search(r'Confidence Score:\s*(\d+)%', output, re.IGNORECASE)

        if match:
            confidence_score = int(match.group(1))
            return confidence_score
        else:
            print("Confidence score not found in the output.")
            return None

    confidence_score = extract_confidence_score(analysis_output)

    if confidence_score is not None:

        markdown_report = re.sub(r'Confidence Score:\s*\d+%\s*', '', analysis_output, flags=re.IGNORECASE).strip()

        output_filename = 'analysis_output.md'
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(f"Confidence Score: {confidence_score}%\n\n")
            f.write(markdown_report)

        print(f"Analysis complete. Confidence Score: {confidence_score}%")
        print(f"Markdown report saved to '{output_filename}'")
    else:
        print("Could not extract confidence score. Here is the full output:")
        print(analysis_output)
else:
    print("Failed to get analysis from the LLM.")
