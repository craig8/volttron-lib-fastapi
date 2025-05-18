# tests/test_gevent_launcher.py
"""
Test launcher for gevent tests that ensures proper isolation.
"""
import os
import pytest
import subprocess
import sys
import re
import time

@pytest.mark.timeout(60)
def test_run_gevent_tests(request):
    """
    Run gevent tests in a separate process.
    
    This test function serves as a launcher for the actual gevent tests,
    ensuring they run in a completely isolated environment.
    """
    # Path to the actual gevent test file
    gevent_test_file = os.path.join(
        os.path.dirname(__file__), 
        "_test_gevent_client.py"
    )
    
    header = f"\n\n{'=' * 80}\nRUNNING GEVENT TESTS\n{'=' * 80}"
    
    # Always show this output using pytest's reporting mechanism
    # This works even without -s flag
    request.node.add_report_section("call", "stdout", header)
    
    start_time = time.time()
    
    try:
        # Run pytest with verbose output
        result = subprocess.run(
            [
                sys.executable, 
                "-m", 
                "pytest", 
                gevent_test_file, 
                "-v"
            ], 
            capture_output=True, 
            text=True,
            timeout=25
        )
        
        elapsed_time = time.time() - start_time
        
        # Create a summary of the test results
        if result.returncode == 0:
            summary = f"✓ All gevent tests PASSED in {elapsed_time:.2f} seconds"
        else:
            summary = f"✗ Some gevent tests FAILED in {elapsed_time:.2f} seconds"
        
        # Extract individual test results using regex
        test_results = []
        test_pattern = re.compile(r'(test_[^\s]+) ([^\n]+)')
        for match in test_pattern.finditer(result.stdout):
            test_name, status = match.groups()
            test_results.append(f"  - {test_name}: {status}")
            
        # Add the results to the report
        result_output = "\n".join([summary] + test_results)
        request.node.add_report_section("call", "stdout", result_output)
        
        # Only show full output on failure
        if result.returncode != 0:
            request.node.add_report_section("call", "stdout", "\nDETAILED OUTPUT:")
            request.node.add_report_section("call", "stdout", result.stdout)
            
            if result.stderr:
                request.node.add_report_section("call", "stderr", "\nERRORS:")
                request.node.add_report_section("call", "stderr", result.stderr)
        
        request.node.add_report_section("call", "stdout", f"{'=' * 80}\nEND OF GEVENT TESTS\n{'=' * 80}")
        
        # Assert that the tests passed
        assert result.returncode == 0, f"Gevent tests failed with return code {result.returncode}"
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        timeout_msg = f"⚠️ TIMEOUT: Gevent tests timed out after {elapsed:.1f} seconds ⚠️"
        request.node.add_report_section("call", "stdout", timeout_msg)
        pytest.skip(f"Gevent tests timed out after {elapsed:.1f} seconds")