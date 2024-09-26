from ghidra.app.script import GhidraScript
from ghidra.program.model.address import Address
from ghidra.program.model.mem import Memory, MemoryAccessException

class BinDiffScript(GhidraScript):

    def run(self):

        self.println("THIS IS A TEST TEST TEST TEST ")
        # Define binary paths
        binary1_path = "/app/input_binaries/binary1.bin"
        binary2_path = "/app/input_binaries/binary2.bin"

        # Import both binaries and run analysis
        program1 = self.importFile(binary1_path)
        self.runAnalysis(program1)

        program2 = self.importFile(binary2_path)
        self.runAnalysis(program2)

        # Compare the memory sections
        self.compare_binaries(program1, program2)

    def compare_binaries(self, program1, program2):
        memory1 = program1.getMemory()
        memory2 = program2.getMemory()

        # Get minimum and maximum addresses for both binaries
        start1 = memory1.getMinAddress()
        start2 = memory2.getMinAddress()
        end1 = memory1.getMaxAddress()
        end2 = memory2.getMaxAddress()

        # Ensure both binaries have similar memory sizes
        if end1.subtract(start1) != end2.subtract(start2):
            self.println("The binaries have different memory sizes.")
            return

        # Read memory contents of both binaries
        length = end1.subtract(start1) + 1
        bytes1 = memory1.getBytes(start1, length)
        bytes2 = memory2.getBytes(start2, length)

        # Create an output file to store differences
        output_file = "/analysis/output/binary_diff_report.txt"
        with open(output_file, "w") as diff_file:
            diff_file.write("Binary comparison report:\n")
            differences_found = False

            # Compare the two memory contents byte by byte
            for i in range(len(bytes1)):
                if bytes1[i] != bytes2[i]:
                    difference = "Difference at address {start1.add(i)}: {bytes1[i]:02x} vs {bytes2[i]:02x}\n"
                    diff_file.write(difference)
                    self.println(difference)
                    differences_found = True

            if not differences_found:
                diff_file.write("No differences found.\n")
                self.println("No differences found.")

        self.println("Binary comparison completed. Report saved to {output_file}")
