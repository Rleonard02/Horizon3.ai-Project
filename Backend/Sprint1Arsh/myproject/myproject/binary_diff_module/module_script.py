import subprocess
import re
import os
import sys
import time
import yaml
import glob
import shutil
from pathlib import Path
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging
import requests  # Imported requests module for HTTP requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_SERVICE_URL = "http://api-service:8000/update_status"

def update_status(status, progress, message):
    data = {
        "service": "binary-analysis",
        "status": status,
        "progress": progress,
        "message": message
    }
    try:
        requests.post(API_SERVICE_URL, json=data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update status: {e}")

def extract_function_differences(radiff_output_file):
    differences = []
    with open(radiff_output_file, 'r') as f:
        for line in f:
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

def compile_and_analyze():
    c_source1 = "/bin_shared/c_source/version1/main.c"
    c_source2 = "/bin_shared/c_source/version2/main.c"
    binary_dir = "/bin_shared/input_binaries"
    output_dir = "/bin_shared/output"

    # Ensure directories exist
    Path(binary_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    update_status("running", 10, "Compiling source code")
    # Compile source code
    compile_file(c_source1, os.path.join(binary_dir, "binary1.bin"))
    compile_file(c_source2, os.path.join(binary_dir, "binary2.bin"))

    update_status("running", 20, "Copying binaries to PVC")
    # Copy binaries into the PVC using a temporary Pod
    create_pod_to_access_output('/bin_app/kubernetes/pvc-access-pod.yaml')
    wait_for_pod_ready('pvc-access-pod')

    # Copy local binaries into the Pod's PVC
    for binary in glob.glob(os.path.join(binary_dir, '*.bin')):
        binary_name = os.path.basename(binary)
        command = ['kubectl', 'cp', binary, f'pvc-access-pod:/storage/input_binaries/{binary_name}']
        try:
            subprocess.check_call(command)
            logger.info(f"Copied {binary_name} to pvc-access-pod")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error copying {binary_name} to pvc-access-pod: {e}")
            continue  # Continue processing other binaries

    # Delete the temporary Pod
    delete_pod('pvc-access-pod')

    decompiled_files = []
    for idx, binary in enumerate(glob.glob(os.path.join(binary_dir, '*.bin')), start=1):
        binary_name = os.path.basename(binary)
        job_name = f'ghidra-decompiler-job-{binary_name.replace(".", "-")}'
        job_yaml = f'kubernetes/ghidra-job-{binary_name.replace(".", "-")}.yaml'

        update_status("running", 20 + idx * 10, f"Submitting Ghidra job for {binary_name}")
        # Create a job manifest for each binary
        create_ghidra_job_yaml(binary_name, job_name, job_yaml)

        # Submit Kubernetes Job
        submit_kubernetes_job(job_yaml)

        # Wait for Job to complete
        if not wait_for_job_completion(job_name):
            logger.error(f"Job {job_name} failed or timed out.")
            continue  # Skip to next binary

        # Retrieve decompiled output from Ghidra job logs
        decompiled_output_file = os.path.join(output_dir, f'{binary_name}.decompiled.txt')
        if get_job_logs(job_name, decompiled_output_file):
            decompiled_files.append(decompiled_output_file)
        else:
            logger.error(f"Failed to retrieve logs for job {job_name}")

        # Delete the Job
        delete_job(job_name)

    update_status("running", 60, "Copying decompiled files to PVC")
    # Copy decompiled files into the PVC for radiff job
    create_pod_to_access_output('/bin_app/kubernetes/pvc-access-pod.yaml')
    wait_for_pod_ready('pvc-access-pod')

    # Copy decompiled files into the Pod's PVC
    for decompiled_file in decompiled_files:
        filename = os.path.basename(decompiled_file)
        command = ['kubectl', 'cp', decompiled_file, f'pvc-access-pod:/storage/output/{filename}']
        try:
            subprocess.check_call(command)
            logger.info(f"Copied {filename} to pvc-access-pod")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error copying {filename} to pvc-access-pod: {e}")
            continue  # Continue processing other files

    # Delete the temporary Pod
    delete_pod('pvc-access-pod')

    update_status("running", 70, "Submitting Radiff analysis job")
    # Submit Radiff Job
    submit_kubernetes_job('kubernetes/radiff-job.yaml')
    if not wait_for_job_completion('radiff-analysis-job'):
        logger.error("Radiff analysis job failed or timed out.")
        update_status("failed", 0, "Radiff analysis job failed")
        return

    # Create a Pod to access output data
    create_pod_to_access_output('kubernetes/output-access.yaml')
    wait_for_pod_ready('output-access-pod')

    # Copy output files from the Pod
    if copy_output_from_pod('output-access-pod', '/output/radiff_output.txt', '/bin_shared/output/radiff_output.txt'):
        logger.info("Copied radiff_output.txt from output-access-pod to /bin_shared/output/")
    else:
        logger.error("Failed to copy radiff_output.txt from output-access-pod")

    # Delete the temporary Pod
    delete_pod('output-access-pod')

    # Delete the Radiff Job
    delete_job('radiff-analysis-job')

    update_status("running", 80, "Generating diff report")
    # Generate the diff report
    generate_diff_report(
        radiff_output_file="/bin_shared/output/radiff_output.txt",
        decompiled_file1="/bin_shared/output/binary1.bin.decompiled.txt",
        decompiled_file2="/bin_shared/output/binary2.bin.decompiled.txt",
        report_file="/bin_shared/output/diff_report.txt"
    )

    logger.info("Diff report generated at /bin_shared/output/diff_report.txt")
    update_status("completed", 100, "Binary analysis completed")

def compile_file(source_path, output_binary):
    try:
        subprocess.check_call(["gcc", "-g", source_path, "-o", output_binary])
        logger.info(f"Compiled {source_path} to {output_binary}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error compiling {source_path}: {e}")
        update_status("failed", 0, f"Error compiling {source_path}")
        sys.exit(1)

def generate_diff_report(radiff_output_file, decompiled_file1, decompiled_file2, report_file):
    try:
        # Extract function differences from radiff output
        differences = extract_function_differences(radiff_output_file)

        # Load decompiled files
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
        logger.info(f"Diff report generated at {report_file}")
    except FileNotFoundError as e:
        logger.error(f"File not found during diff report generation: {e}")
        update_status("failed", 0, "File not found during diff report generation")
    except Exception as e:
        logger.error(f"Error generating diff report: {e}")
        update_status("failed", 0, "Error generating diff report")

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

def submit_kubernetes_job(job_manifest_path):
    try:
        config.load_kube_config()
        batch_v1 = client.BatchV1Api()
        with open(job_manifest_path) as f:
            job_manifest = yaml.safe_load(f)
        job_name = job_manifest['metadata']['name']
        batch_v1.create_namespaced_job(
            body=job_manifest,
            namespace='default')
        logger.info(f"Job {job_name} submitted.")
    except ApiException as e:
        if e.status == 409:
            logger.warning(f"Job {job_name} already exists.")
        else:
            logger.error(f"Error submitting job {job_name}: {e}")
            update_status("failed", 0, f"Error submitting job {job_name}")
            sys.exit(1)

def wait_for_job_completion(job_name, timeout=600):
    try:
        config.load_kube_config()
        batch_v1 = client.BatchV1Api()
        start_time = time.time()
        while time.time() - start_time < timeout:
            job = batch_v1.read_namespaced_job(name=job_name, namespace='default')
            if job.status.succeeded and job.status.succeeded >= 1:
                logger.info(f"Job {job_name} completed successfully.")
                return True
            elif job.status.failed and job.status.failed >= 1:
                logger.error(f"Job {job_name} failed.")
                return False
            else:
                logger.info(f"Job {job_name} is still running...")
                time.sleep(5)
        logger.error(f"Timeout waiting for job {job_name} to complete.")
        return False
    except ApiException as e:
        logger.error(f"Error checking job status for {job_name}: {e}")
        return False

def create_pod_to_access_output(pod_manifest_path):
    try:
        config.load_kube_config()
        core_v1 = client.CoreV1Api()
        with open(pod_manifest_path) as f:
            pod_manifest = yaml.safe_load(f)
        pod_name = pod_manifest['metadata']['name']
        core_v1.create_namespaced_pod(
            body=pod_manifest,
            namespace='default')
        logger.info(f"Pod {pod_name} created.")
    except ApiException as e:
        if e.status == 409:
            logger.warning(f"Pod {pod_name} already exists.")
        else:
            logger.error(f"Error creating pod {pod_name}: {e}")
            sys.exit(1)

def wait_for_pod_ready(pod_name, timeout=300):
    try:
        config.load_kube_config()
        core_v1 = client.CoreV1Api()
        start_time = time.time()
        while time.time() - start_time < timeout:
            pod = core_v1.read_namespaced_pod(name=pod_name, namespace='default')
            if pod.status.phase == 'Running':
                logger.info(f"Pod {pod_name} is running.")
                return True
            elif pod.status.phase in ['Failed', 'Unknown']:
                logger.error(f"Pod {pod_name} failed with status: {pod.status.phase}")
                return False
            else:
                logger.info(f"Pod {pod_name} status: {pod.status.phase}")
                time.sleep(5)
        logger.error(f"Timeout waiting for pod {pod_name} to be ready.")
        return False
    except ApiException as e:
        logger.error(f"Error checking pod status for {pod_name}: {e}")
        return False

def copy_output_from_pod(pod_name, remote_path, local_path):
    command = ['kubectl', 'cp', f'{pod_name}:{remote_path}', local_path]
    try:
        subprocess.check_call(command)
        logger.info(f"Copied {remote_path} from pod {pod_name} to {local_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error copying files from pod {pod_name}: {e}")
        return False

def delete_pod(pod_name):
    try:
        config.load_kube_config()
        core_v1 = client.CoreV1Api()
        core_v1.delete_namespaced_pod(name=pod_name, namespace='default', body=client.V1DeleteOptions())
        logger.info(f"Pod {pod_name} deleted.")
    except ApiException as e:
        logger.error(f"Error deleting pod {pod_name}: {e}")

def delete_job(job_name):
    try:
        config.load_kube_config()
        batch_v1 = client.BatchV1Api()
        batch_v1.delete_namespaced_job(
            name=job_name,
            namespace='default',
            body=client.V1DeleteOptions(propagation_policy='Foreground'))
        logger.info(f"Job {job_name} deleted.")
    except ApiException as e:
        logger.error(f"Error deleting job {job_name}: {e}")

def get_job_logs(job_name, output_file):
    config.load_kube_config()
    core_v1 = client.CoreV1Api()
    label_selector = f'job-name={job_name}'
    pods = core_v1.list_namespaced_pod(namespace='default', label_selector=label_selector)
    if not pods.items:
        logger.error(f"No pods found for job {job_name}")
        return False
    pod_name = pods.items[0].metadata.name
    logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace='default')
    with open(output_file, 'w') as f:
        f.write(logs)
    logger.info(f"Saved decompiled output from job {job_name} to {output_file}")
    return True

def create_ghidra_job_yaml(binary_name, job_name, job_yaml_path):
    ghidra_job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_name
        },
        "spec": {
            "template": {
                "metadata": {
                    "labels": {
                        "app": "ghidra-decompiler"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "ghidra-decompiler",
                            "image": "cincan/ghidra-decompiler:latest",
                            "args": [
                                "decompile",
                                f"/app/input_binaries/{binary_name}"
                            ],
                            "volumeMounts": [
                                {
                                    "name": "input-output-storage",
                                    "mountPath": "/app/input_binaries",
                                    "subPath": "input_binaries"
                                }
                            ]
                        }
                    ],
                    "restartPolicy": "Never",
                    "volumes": [
                        {
                            "name": "input-output-storage",
                            "persistentVolumeClaim": {
                                "claimName": "input-output-pvc"
                            }
                        }
                    ]
                }
            }
        }
    }
    with open(job_yaml_path, 'w') as f:
        yaml.dump(ghidra_job_manifest, f)

if __name__ == "__main__":
    shared_dir = '/bin_shared'
    source_dir = Path("/bin_shared/c_source/version1")
    binary_dir = os.path.join(shared_dir, "input_binaries")
    output_dir = os.path.join(shared_dir, "output")

    # Ensure the directories exist
    os.makedirs(binary_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    logger.info("Monitoring for incoming files...")
    update_status("idle", 0, "Waiting for source files")
    while True:
        if source_dir.exists() and any(source_dir.glob("*.c")):
            logger.info("Detected new source files, starting compilation and analysis...")
            update_status("running", 0, "Starting compilation and analysis")
            compile_and_analyze()
            # Remove processed C files to prevent reprocessing
            for file in source_dir.glob("*.c"):
                try:
                    file.unlink()
                    logger.info(f"Deleted processed file: {file}")
                except Exception as e:
                    logger.error(f"Error deleting file {file}: {e}")
            version2_dir = Path("/bin_shared/c_source/version2")
            for file in version2_dir.glob("*.c"):
                try:
                    file.unlink()
                    logger.info(f"Deleted processed file: {file}")
                except Exception as e:
                    logger.error(f"Error deleting file {file}: {e}")
            logger.info("Processing completed, continuing to monitor for new files...")
            update_status("idle", 0, "Waiting for source files")
        time.sleep(5)