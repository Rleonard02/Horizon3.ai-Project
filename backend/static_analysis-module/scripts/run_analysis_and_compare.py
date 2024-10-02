import os
import argparse
import subprocess

# Define paths to tools
SONARQUBE_FOLDER = "../sonarqube"
CODEQL_FOLDER = "../codeql"
COVERITY_FOLDER = "../coverity"
SOURCE_CODE_FOLDER = "../source_code"

# Define paths to reports folders
SONARQUBE_REPORTS_FOLDER = "../sonarqube/reports"
CODEQL_REPORTS_FOLDER = "../codeql/reports"
COVERITY_REPORTS_FOLDER = "../coverity/reports"


# Utility function to run Docker commands
def run_docker(container_name, tool_name, compose_file):
    try:
        print(f"Running {tool_name} analysis using Docker container: {container_name}")
        subprocess.run(["docker-compose", "-f", compose_file, "up", "--build", container_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while running {tool_name}: {e}")

# Function for SonarQube analysis
def run_sonarqube_analysis():
    print("Running SonarQube Analysis...")
    run_docker("sonarqube", "SonarQube", f"{SONARQUBE_FOLDER}/docker-compose.yml")
    
    # Move or copy SonarQube report to the specific SonarQube reports folder
    report_src = f"{SONARQUBE_REPORTS_FOLDER}/sonarqube_output.txt"
    if os.path.exists(report_src):
        print(f"SonarQube report saved to {report_src}")
    else:
        print("SonarQube report not found.")

# Function for CodeQL analysis
def run_codeql_analysis():
    print("Running CodeQL Analysis...")

    try:
        # Check if the source_code folder exists
        if not os.path.exists(SOURCE_CODE_FOLDER):
            print(f"Error: source_code folder not found at {SOURCE_CODE_FOLDER}")
            return

        print("source_code folder found. Listing contents:")
        code_files = [f for f in os.listdir(SOURCE_CODE_FOLDER) if os.path.isfile(os.path.join(SOURCE_CODE_FOLDER, f))]

        print(f"Found files: {code_files}")
        if len(code_files) == 0:
            print("Error: No code files found to analyze.")
            return

        # Run CodeQL analysis using the codeql service
        run_docker("codeql", "CodeQL", f"{CODEQL_FOLDER}/docker-compose.yml")

        # Check the report
        report_src = f"{CODEQL_REPORTS_FOLDER}/codeql_output.sarif"

        if os.path.exists(report_src):
            print(f"CodeQL report saved to {report_src}")
        else:
            print(f"CodeQL report not found.")

    except subprocess.CalledProcessError as e:
        print(f"Error during CodeQL analysis: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Main function to parse arguments and run analysis
def main():
    parser = argparse.ArgumentParser(description="Run static analysis on source code")
    parser.add_argument("--tool", choices=["sonarqube", "codeql", "coverity", "all"], default="all",
                        help="Select which tool to run (default: all)")
    args = parser.parse_args()

    # Ensure each tool's reports folder exists
    os.makedirs(SONARQUBE_REPORTS_FOLDER, exist_ok=True)
    os.makedirs(CODEQL_REPORTS_FOLDER, exist_ok=True)
    os.makedirs(COVERITY_REPORTS_FOLDER, exist_ok=True)

    # Choose tool based on user input
    if args.tool == "sonarqube":
        run_sonarqube_analysis()
    elif args.tool == "codeql":
        run_codeql_analysis()
    elif args.tool == "coverity":
        run_coverity_analysis()
    elif args.tool == "all":
        run_sonarqube_analysis()
        run_codeql_analysis()
        run_coverity_analysis()
    else:
        print("Invalid tool selected. Use --help for available options.")

if __name__ == "__main__":
    main()
