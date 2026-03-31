#!/bin/bash
# Run E2E tests for FaultRay
# Usage: bash scripts/run_e2e.sh

set -e
echo "Running FaultRay E2E tests..."
python3 -m pytest tests/test_e2e.py -v --tb=short -x 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "E2E tests passed"
else
    echo "E2E tests failed"
fi
exit $EXIT_CODE
