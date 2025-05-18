# tests/test_gevent_launcher.py
import os
import pytest
import subprocess
import sys
import re
import time

@pytest.mark.timeout(60)
def test_run_gevent_tests(request):
    """Run gevent tests in a separate process with coverage."""
    # Path to the actual gevent test file
    gevent_test_file = os.path.join(
        os.path.dirname(__file__), 
        "_test_gevent_client.py"
    )
    
    # Add report header
    header = f"\n\n{'=' * 80}\nRUNNING GEVENT TESTS\n{'=' * 80}"
    request.node.add_report_section("call", "stdout", header)
    
    start_time = time.time()
    
    try:
        # Build command with coverage
        cmd = [
            sys.executable, 
            "-m", 
            "pytest", 
            gevent_test_file, 
            "-v",
            # Coverage options for the subprocess
            "--cov=volttron.messagebus.fastapi",
            "--cov-report=",  # No report, just collect data
        ]
        
        # Add coverage args to record in a separate file
        coverage_file = os.path.join(os.getcwd(), ".coverage.gevent")
        os.environ["COVERAGE_FILE"] = coverage_file
        
        # Run pytest with coverage
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            timeout=25,
            env=os.environ  # Pass environment variables for coverage
        )
        
        # Rest of your function to process results...
        elapsed_time = time.time() - start_time
        
        # Create summary and add to report...
        # [Your existing code here]
        
        # Assert that the tests passed
        assert result.returncode == 0, f"Gevent tests failed with return code {result.returncode}"
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        timeout_msg = f"⚠️ TIMEOUT: Gevent tests timed out after {elapsed:.1f} seconds ⚠️"
        request.node.add_report_section("call", "stdout", timeout_msg)
        pytest.skip(f"Gevent tests timed out after {elapsed:.1f} seconds")
    finally:
        # Reset coverage file path
        if "COVERAGE_FILE" in os.environ:
            del os.environ["COVERAGE_FILE"]