#!/bin/bash

# Clean up previous coverage data
echo "Cleaning up previous coverage data..."
coverage erase

# Run regular tests with coverage
echo "Running regular tests with coverage..."
COVERAGE_FILE=.coverage.regular poetry run pytest -k "not gevent_patched" --cov=volttron.messagebus.fastapi --cov-report=

# Run gevent tests with coverage
echo "Running gevent tests with coverage..."
COVERAGE_FILE=.coverage.gevent poetry run python -m pytest tests/test_gevent_launcher.py

# Combine coverage data
echo "Combining coverage data..."
coverage combine .coverage.regular .coverage.gevent

# Generate coverage report
echo "Generating coverage report..."
coverage report --include="src/volttron/messagebus/fastapi/*" --omit="*/__pycache__/*"

# Optionally, generate HTML report
coverage html --include="src/volttron/messagebus/fastapi/*" --omit="*/__pycache__/*"
echo "HTML coverage report generated in htmlcov/index.html"