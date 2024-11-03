from llm_module import analyze_code
import os
import re
import sys
import time

shared_dir = "/shared"
source_code_dir_v1 = os.path.join(shared_dir, "c_source", "version1")
source_code_dir_v2 = os.path.join(shared_dir, "c_source", "version2")
output_dir = os.path.join(shared_dir, "output")

def read_code_files():
    code_snippets = []
    for version_dir in [source_code_dir_v1, source_code_dir_v2]:
        for filename in os.listdir(version_dir):
            if filename.endswith(".c"):
                filepath = os.path.join(version_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    code_snippets.append(f.read())
    return code_snippets

def read_analysis_outputs():
    analysis_files = ["radiff_output.txt", "diff_report.txt"]
    contents = []
    for filename in analysis_files:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                contents.append(f.read())
        else:
            print(f"File {filename} does not exist.")
    return contents

def main():
    print("LLM Module started, waiting for analysis outputs...")
    while True:
        if os.path.exists(os.path.join(output_dir, "diff_report.txt")):
            print("Detected analysis outputs, starting LLM processing...")
            code_snippets = read_code_files()
            analysis_outputs = read_analysis_outputs()
            combined_input = "\n".join(code_snippets + analysis_outputs)

            analysis_result = analyze_code(combined_input)

            if analysis_result:
                # Extract confidence score and generate report
                match = re.search(r'Confidence Score:\s*(\d+)%', analysis_result, re.IGNORECASE)
                if match:
                    confidence_score = int(match.group(1))
                    markdown_report = re.sub(r'Confidence Score:\s*\d+%\s*', '', analysis_result, flags=re.IGNORECASE).strip()
                    output_filename = os.path.join(output_dir, 'llm_analysis_output.md')
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Confidence Score: {confidence_score}%\n\n")
                        f.write(markdown_report)
                    print(f"LLM analysis complete. Confidence Score: {confidence_score}%")
                    print(f"Markdown report saved to '{output_filename}'")
                else:
                    print("Could not extract confidence score. Here is the full output:")
                    print(analysis_result)
            else:
                print("Failed to get analysis from the LLM.")
            
            # Clean up or wait for next inputs
            time.sleep(5)
        else:
            # Wait for the analysis outputs to be generated
            time.sleep(5)

if __name__ == "__main__":
    main()
