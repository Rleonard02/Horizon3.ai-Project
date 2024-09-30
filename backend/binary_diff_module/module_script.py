import subprocess
import re
import os
import json
import sys


# Helper function to extract differences from radiff output
def extract_function_differences(radiff_output_file):
    differences = []
    with open(radiff_output_file, 'r') as f:
        for line in f:
            # Regex pattern to parse each line
            pattern = r'^(\S+)\s+(\d+)\s+(\S+)\s+\|\s+(\S+)\s+\(([\d\.]+)\)\s+\|\s+(\S+)\s+(\d+)\s+(\S+)$'
            match = re.match(pattern, line.strip())
            if match:
                func_name1 = match.group(1)
                size1 = int(match.group(2))
                addr1 = match.group(3)
                status = match.group(4)
                similarity = float(match.group(5))
                addr2 = match.group(6)
                size2 = int(match.group(7))
                func_name2 = match.group(8)

                if similarity < 1.0:
                    differences.append({
                        'function_name': func_name1,
                        'similarity': similarity,
                        'address1': addr1,
                        'size1': size1,
                        'address2': addr2,
                        'size2': size2
                    })
    return differences

def compile_c_file(source_path, output_binary):
    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_binary)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        subprocess.call(["gcc", "-g", source_path, "-o", output_binary])
        print("Compiled {} to {}".format(source_path, output_binary))
    except subprocess.CalledProcessError as e:
        print("Error compiling {}: {}".format(source_path, e))



def decompile_binary(binary_path, output_file):
    command = [
        "docker-compose",
        "run",
        "--rm",
        "-T",
        "ghidra-decompiler",
        "decompile",
        binary_path
    ]
    print(f"Decompiling {binary_path}...")
    with open(output_file, "w") as f:
        result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print("Decompilation failed:")
            print(result.stderr)
            sys.exit(1)
    print(f"Decompiled output saved to {output_file}")


def run_radiff():
    cmd = "radiff2 -A -C /app/input_binaries/binary1.bin /app/input_binaries/binary2.bin"
    command = [
        "docker-compose",
        "run",
        "--rm",
        "-T",
        "radiff",
        "/bin/bash",
        "-c",
        cmd
    ]
    print("Starting radiff analysis...")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        print("Radiff analysis failed:")
        print(result.stderr)
        sys.exit(1)
    else:
        with open("./output/radiff_output.txt", "w") as f:
            f.write(result.stdout)
    print("Radiff analysis complete.")



def generate_diff_report(radiff_output_file, decompiled_file1, decompiled_file2, report_file):
    # Extract function differences from radiff output
    differences = extract_function_differences(radiff_output_file)
    
    # Load decompiled code
    with open(decompiled_file1, 'r') as f:
        decompiled_code1 = f.read()
    with open(decompiled_file2, 'r') as f:
        decompiled_code2 = f.read()
    
    # Generate report
    with open(report_file, 'w') as f:
        for diff in differences:
            name = diff['function_name']
            similarity = diff['similarity']
            f.write(f"Function: {name}\n")
            f.write(f"Similarity: {similarity}\n\n")
            # Extract code snippets from decompiled code (simplified example)
            code_snippet1 = extract_function_code(decompiled_code1, name)
            code_snippet2 = extract_function_code(decompiled_code2, name)
            f.write("Code in Binary 1:\n")
            f.write(code_snippet1 + "\n\n")
            f.write("Code in Binary 2:\n")
            f.write(code_snippet2 + "\n\n")
            f.write("=" * 80 + "\n\n")

def extract_function_code(decompiled_code, function_name):
    # Remove 'dbg.' or 'sym.' prefixes if present
    clean_name = function_name.replace('dbg.', '').replace('sym.', '')
    # Regex pattern to match the function definition and body
    pattern = rf"^[\w\s\*\(\)]+{re.escape(clean_name)}\s*\([^)]*\)\s*\{{.*?^\}}"
    matches = re.findall(pattern, decompiled_code, re.MULTILINE | re.DOTALL)
    if matches:
        return matches[0]
    else:
        return f"Function '{clean_name}' code not found in decompiled output."


if __name__ == "__main__":
    c_source1 = "c_source/version1/main.c"
    c_source2 = "c_source/version2/main.c"
    binary1 = "input_binaries/binary1.bin"
    binary2 = "input_binaries/binary2.bin"
    output_dir = "./output"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # compile C files to binaries
    compile_c_file(c_source1, binary1)
    compile_c_file(c_source2, binary2)
    
    # Decompile each binary
    #decompile_binary("/app/input_binaries/binary1.bin", "./output/decompiled_binary1.txt")
    #decompile_binary("/app/input_binaries/binary2.bin", "./output/decompiled_binary2.txt")
    
    # run Radiff analysis
    run_radiff()
    
    # generate diff report
    generate_diff_report(
        radiff_output_file="./output/radiff_output.txt",
        decompiled_file1="./output/decompiled_binary1.txt",
        decompiled_file2="./output/decompiled_binary2.txt",
        report_file="./output/diff_report.txt"
    )




