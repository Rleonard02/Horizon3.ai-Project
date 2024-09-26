import json
import os

def parse_ghidra_results(log_file):
    results = {}
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if "DIFF RESULT:" in line:
                key, value = line.split(":")
                results[key.strip()] = value.strip()
    return results

if __name__ == "__main__":
    log_file = "/app/output_results/ghidra_diff.log"
    output_json = "/app/output_results/diff_result.json"
    
    results = parse_ghidra_results(log_file)
    
    with open(output_json, 'w') as json_file:
        json.dump(results, json_file, indent=4)
    
    print("Results saved to {output_json}")
