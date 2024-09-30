import os
import subprocess

# Function to compile C files into binaries
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

# Function to run Ghidra for binary diffing
def run_ghidra_diff(binary1, binary2, output_dir):
    ghidra_headless = "/ghidra/support/analyzeHeadless"
    project_path = "/analysis"
    
    cmd = [
        ghidra_headless,
        project_path,
        "project_name",
        "-import", binary1,
        "-import", binary2,
        "-scriptPath", "/analysis/scripts/",
        "-log", os.path.join(output_dir, "ghidra_diff.log"),
        "-deleteProject"
    ]
    
    try:
        subprocess.call(cmd)
        print("Binary diff completed for {} and {}".format(binary1, binary2))
    except subprocess.CalledProcessError as e:
        print("Error running Ghidra diff: {}".format(e))

if __name__ == "__main__":
    # Define paths to source code and output binary locations
    c_source1 = "/app/c_source/version1/main.c"
    c_source2 = "/app/c_source/version2/main.c"
    binary1 = "/app/input_binaries/binary1.bin"
    binary2 = "/app/input_binaries/binary2.bin"
    output_dir = "/analysis/output"
    
    # Create output directories if they don't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Compile C files to binaries
    # compile_c_file(c_source1, binary1)
    # compile_c_file(c_source2, binary2)
    
    # Run Ghidra binary diff on the compiled binaries
    if os.path.exists(binary1) and os.path.exists(binary2):
        run_ghidra_diff(binary1, binary2, output_dir)
    else:
        print("Error: One or both binaries are missing!")
