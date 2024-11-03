#!/bin/bash
set -e

# Wait for the necessary files to be present
while [ ! -f "/shared/output/diff_report.txt" ] || [ ! -f "/shared/output/binary1.bin.decompiled.txt" ] || [ ! -f "/shared/output/binary2.bin.decompiled.txt" ]; do
  echo "Waiting for necessary files..."
  sleep 5
done

echo "Necessary files found. Starting LLM analysis..."

# Run the test_llm_module.py script
python test_llm_module.py

# Optionally keep the container running
# tail -f /dev/null
