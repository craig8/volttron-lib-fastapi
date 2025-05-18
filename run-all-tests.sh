#!/bin/bash
# Run regular tests (non-gevent)
echo "Running regular tests (non-gevent)..."
poetry run pytest -k "not gevent_patched" "$@"
REGULAR_RESULT=$?

# Run gevent tests in a fresh process
echo "Running gevent-patched tests..."
poetry run pytest -m "gevent_patched" "$@"
GEVENT_RESULT=$?

# Check results
if [ $REGULAR_RESULT -ne 0 ] || [ $GEVENT_RESULT -ne 0 ]; then
    echo "Some tests failed!"
    exit 1
else
    echo "All tests passed!"
    exit 0
fi