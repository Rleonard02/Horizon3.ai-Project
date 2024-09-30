import subprocess
import re
import os

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

def run_decompiler():
    # Command to run docker-compose up
    command = ["docker-compose", "up"]

    # Start the decompiler container and capture output
    print("Starting the decompiler container...")
    with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
        with open("./output/decompiled_output.txt", "w") as output_file:
            for line in proc.stdout:
                if line.startswith("ghidra-decompiler  |"):
                    # Remove the prefix and extra logging
                    clean_line = re.sub(r"^ghidra-decompiler  \|\s*", "", line)
                    if "INFO" not in clean_line and "DEBUG" not in clean_line:
                        output_file.write(clean_line)

    print("Decompilation complete. Results stored in ./output/decompiled_output.txt")

if __name__ == "__main__":
    c_source1 = "c_source/version1/main.c"
    c_source2 = "c_source/version2/main.c"
    binary1 = "input_binaries/binary1.bin"
    binary2 = "input_binaries/binary2.bin"
    output_dir = "/analysis/output"


    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Compile C files to binaries
    compile_c_file(c_source1, binary1)
    # compile_c_file(c_source2, binary2)
    
    # Run Ghidra decompilation on the compiled binaries
    run_decompiler()
