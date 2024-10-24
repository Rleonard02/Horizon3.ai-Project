import subprocess
import re
import os
import sys
import time
import yaml
import glob
import shutil

from kubernetes import client, config
from kubernetes.client.rest import ApiException

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

def compile_file(source_path, output_binary):
    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_binary)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        subprocess.check_call(["gcc", "-g", source_path, "-o", output_binary])
        print("Compiled {} to {}".format(source_path, output_binary))
    except subprocess.CalledProcessError as e:
        print("Error compiling {}: {}".format(source_path, e))
        sys.exit(1)

def generate_diff_report(radiff_output_file, decompiled_file1, decompiled_file2, report_file):
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
    print(f"Diff report generated at {report_file}")

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
    config.load_kube_config()
    batch_v1 = client.BatchV1Api()
    with open(job_manifest_path) as f:
        job_manifest = yaml.safe_load(f)
    job_name = job_manifest['metadata']['name']
    try:
        batch_v1.create_namespaced_job(
            body=job_manifest,
            namespace='default')
        print(f"Job {job_name} submitted.")
    except ApiException as e:
        if e.status == 409:
            print(f"Job {job_name} already exists.")
        else:
            print(f"Error submitting job {job_name}: {e}")
            sys.exit(1)

def wait_for_job_completion(job_name, timeout=600):
    config.load_kube_config()
    batch_v1 = client.BatchV1Api()
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            job = batch_v1.read_namespaced_job(name=job_name, namespace='default')
            if job.status.succeeded and job.status.succeeded >= 1:
                print(f"Job {job_name} completed successfully.")
                return True
            elif job.status.failed:
                print(f"Job {job_name} failed.")
                sys.exit(1)
            else:
                print(f"Job {job_name} is still running...")
                time.sleep(5)
        except ApiException as e:
            print(f"Error checking job status: {e}")
            sys.exit(1)
    print(f"Timeout waiting for job {job_name} to complete.")
    sys.exit(1)

def create_pod_to_access_output(pod_manifest_path):
    config.load_kube_config()
    core_v1 = client.CoreV1Api()
    with open(pod_manifest_path) as f:
        pod_manifest = yaml.safe_load(f)
    pod_name = pod_manifest['metadata']['name']
    try:
        core_v1.create_namespaced_pod(
            body=pod_manifest,
            namespace='default')
        print(f"Pod {pod_name} created.")
    except ApiException as e:
        if e.status == 409:
            print(f"Pod {pod_name} already exists.")
        else:
            print(f"Error creating pod {pod_name}: {e}")
            sys.exit(1)

def wait_for_pod_ready(pod_name, timeout=300):
    config.load_kube_config()
    core_v1 = client.CoreV1Api()
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            pod = core_v1.read_namespaced_pod(name=pod_name, namespace='default')
            if pod.status.phase == 'Running':
                print(f"Pod {pod_name} is running.")
                return True
            elif pod.status.phase == 'Failed' or pod.status.phase == 'Unknown':
                print(f"Pod {pod_name} failed.")
                sys.exit(1)
            else:
                print(f"Pod {pod_name} status: {pod.status.phase}")
                time.sleep(5)
        except ApiException as e:
            print(f"Error checking pod status: {e}")
            sys.exit(1)
    print(f"Timeout waiting for pod {pod_name} to be ready.")
    sys.exit(1)

def copy_output_from_pod(pod_name, remote_path, local_path):
    command = ['kubectl', 'cp', f'{pod_name}:{remote_path}', local_path]
    try:
        subprocess.check_call(command)
        print(f"Copied {remote_path} from pod {pod_name} to {local_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error copying files from pod: {e}")
        sys.exit(1)

def delete_pod(pod_name):
    config.load_kube_config()
    core_v1 = client.CoreV1Api()
    try:
        core_v1.delete_namespaced_pod(name=pod_name, namespace='default', body=client.V1DeleteOptions())
        print(f"Pod {pod_name} deleted.")
    except ApiException as e:
        print(f"Error deleting pod {pod_name}: {e}")

def delete_job(job_name):
    config.load_kube_config()
    batch_v1 = client.BatchV1Api()
    try:
        batch_v1.delete_namespaced_job(
            name=job_name,
            namespace='default',
            body=client.V1DeleteOptions(propagation_policy='Foreground'))
        print(f"Job {job_name} deleted.")
    except ApiException as e:
        print(f"Error deleting job {job_name}: {e}")

def get_job_logs(job_name, output_file):
    config.load_kube_config()
    core_v1 = client.CoreV1Api()
    label_selector = f'job-name={job_name}'
    pods = core_v1.list_namespaced_pod(namespace='default', label_selector=label_selector)
    if not pods.items:
        print(f"No pods found for job {job_name}")
        sys.exit(1)
    pod_name = pods.items[0].metadata.name
    logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace='default')
    with open(output_file, 'w') as f:
        f.write(logs)
    print(f"Saved decompiled output from job {job_name} to {output_file}")

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
    c_source1 = "c_source/version1/main.c"
    c_source2 = "c_source/version2/main.c"
    binary_dir = "input_binaries"
    output_dir = "./output"

    # Ensure the directories exist
    if not os.path.exists(binary_dir):
        os.makedirs(binary_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Compile source code locally
    compile_file(c_source1, os.path.join(binary_dir, "binary1.bin"))
    compile_file(c_source2, os.path.join(binary_dir, "binary2.bin"))

    # Copy binaries into the PVC using a temporary Pod
    create_pod_to_access_output('kubernetes/pvc-access-pod.yaml')
    wait_for_pod_ready('pvc-access-pod')

    # Copy local binaries into the Pod's PVC
    for binary in glob.glob(os.path.join(binary_dir, '*.bin')):
        binary_name = os.path.basename(binary)
        command = ['kubectl', 'cp', binary, f'pvc-access-pod:/storage/input_binaries/{binary_name}']
        try:
            subprocess.check_call(command)
            print(f"Copied {binary_name} to pvc-access-pod")
        except subprocess.CalledProcessError as e:
            print(f"Error copying {binary_name} to pvc-access-pod: {e}")
            sys.exit(1)

    # Delete the temporary Pod
    delete_pod('pvc-access-pod')

    # Process each binary file
    decompiled_files = []
    for binary in glob.glob(os.path.join(binary_dir, '*.bin')):
        binary_name = os.path.basename(binary)
        job_name = f'ghidra-decompiler-job-{binary_name.replace(".", "-")}'
        job_yaml = f'kubernetes/ghidra-job-{binary_name.replace(".", "-")}.yaml'

        # Create a job manifest for each binary
        create_ghidra_job_yaml(binary_name, job_name, job_yaml)

        # Submit Kubernetes Job
        submit_kubernetes_job(job_yaml)

        # Wait for Job to complete
        wait_for_job_completion(job_name)

        # Retrieve decompiled output from Ghidra job logs
        decompiled_output_file = os.path.join(output_dir, f'{binary_name}.decompiled.txt')
        get_job_logs(job_name, decompiled_output_file)
        decompiled_files.append(decompiled_output_file)

        # Delete the Job
        delete_job(job_name)

    # Copy decompiled files into the PVC for radiff job
    create_pod_to_access_output('kubernetes/pvc-access-pod.yaml')
    wait_for_pod_ready('pvc-access-pod')

    # Copy decompiled files into the Pod's PVC
    for decompiled_file in decompiled_files:
        filename = os.path.basename(decompiled_file)
        command = ['kubectl', 'cp', decompiled_file, f'pvc-access-pod:/storage/output/{filename}']
        try:
            subprocess.check_call(command)
            print(f"Copied {filename} to pvc-access-pod")
        except subprocess.CalledProcessError as e:
            print(f"Error copying {filename} to pvc-access-pod: {e}")
            sys.exit(1)

    # Delete the temporary Pod
    delete_pod('pvc-access-pod')

    # Submit Radiff Job
    submit_kubernetes_job('kubernetes/radiff-job.yaml')
    wait_for_job_completion('radiff-analysis-job')

    # Create a Pod to access output data
    create_pod_to_access_output('kubernetes/output-access.yaml')
    wait_for_pod_ready('output-access-pod')

    # Copy output files from the Pod
    copy_output_from_pod('output-access-pod', '/output/radiff_output.txt', './output/radiff_output.txt')

    # Delete the temporary Pod
    delete_pod('output-access-pod')

    # Delete the Radiff Job
    delete_job('radiff-analysis-job')

    # Generate the diff report
    generate_diff_report(
        radiff_output_file="./output/radiff_output.txt",
        decompiled_file1="./output/binary1.bin.decompiled.txt",
        decompiled_file2="./output/binary2.bin.decompiled.txt",
        report_file="./output/diff_report.txt"
    )

    print("Diff report generated at ./output/diff_report.txt")
