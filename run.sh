#!/bin/bash

# Ensure the script runs in the directory of the script itself
cd "$(dirname "$0")"

echo "========================================"
echo "Step 1: Running automated test suite..."
echo "========================================"

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment 'venv' not found. Please set up the project first."
    exit 1
fi

# Run pytest within the virtual environment
venv/bin/pytest

# Capture the exit code of pytest
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "========================================"
    echo "✔ All tests passed successfully!"
    echo "Step 2: Starting the application..."
    echo "========================================"
    # Start the FastAPI server using uvicorn
    exec venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
else
    echo "========================================"
    echo "❌ Test suite failed with exit code $TEST_EXIT_CODE."
    echo "Aborting application startup."
    echo "========================================"
    exit $TEST_EXIT_CODE
fi
