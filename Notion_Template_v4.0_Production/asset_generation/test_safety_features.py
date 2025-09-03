#!/usr/bin/env python3
"""Test script to verify safety features are working correctly."""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add the current directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.exceptions import *
from utils.path_validator import PathValidator
from utils.transaction_safety import TransactionManager, CircuitBreaker
from utils.error_handler import ErrorHandler


def test_path_validator():
    """Test path validation and sanitization."""
    print("\n=== Testing Path Validator ===")
    
    validator = PathValidator()
    
    # Test valid paths
    try:
        safe_path = validator.sanitize_path("output/samples")
        print(f"✓ Valid path sanitized: {safe_path}")
    except Exception as e:
        print(f"✗ Valid path failed: {e}")
    
    # Test dangerous paths
    dangerous_paths = [
        "../../../etc/passwd",
        "~/sensitive/data",
        "/etc/shadow",
        "output/../../../dangerous"
    ]
    
    for path in dangerous_paths:
        try:
            validator.sanitize_path(path)
            print(f"✗ SECURITY ISSUE: Dangerous path not caught: {path}")
        except PathTraversalError:
            print(f"✓ Dangerous path blocked: {path}")
        except Exception as e:
            print(f"✓ Path rejected: {path} ({e})")
    
    print("Path validation tests complete!")


async def test_transaction_manager():
    """Test transaction safety manager."""
    print("\n=== Testing Transaction Manager ===")
    
    # Create mock config and logger
    import logging
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    
    config = {
        'budget': {
            'sample_limit': 1.0,
            'production_limit': 25.0
        },
        'logging': {
            'transaction_log': 'test_transactions.json'
        }
    }
    
    manager = TransactionManager(config, logger)
    
    # Test budget checking
    try:
        manager.check_budget(0.5, is_production=False)
        print("✓ Budget check passed for $0.50")
    except BudgetExceededError:
        print("✗ Budget check failed unexpectedly")
    
    try:
        manager.check_budget(2.0, is_production=False)
        print("✗ Budget check should have failed for $2.00")
    except BudgetExceededError:
        print("✓ Budget limit correctly enforced")
    
    # Test transaction execution
    async def mock_api_call():
        return {"output": "mock_image_url"}
    
    async def mock_download(output):
        return True
    
    try:
        result = await manager.execute_with_transaction(
            asset_type="test",
            cost=0.04,
            api_call=mock_api_call,
            download_call=mock_download,
            prompt="test prompt"
        )
        print(f"✓ Transaction executed successfully: {result}")
        print(f"✓ Total cost tracked: ${manager.total_cost:.2f}")
    except Exception as e:
        print(f"✗ Transaction failed: {e}")
    
    # Clean up test file
    if Path('test_transactions.json').exists():
        Path('test_transactions.json').unlink()
    
    print("Transaction manager tests complete!")


def test_circuit_breaker():
    """Test circuit breaker pattern."""
    print("\n=== Testing Circuit Breaker ===")
    
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
    
    # Test normal operation
    assert breaker.can_attempt_call() == True
    print("✓ Circuit breaker allows calls when closed")
    
    # Test failure counting
    for i in range(3):
        breaker.call_failed()
    
    assert breaker.can_attempt_call() == False
    print("✓ Circuit breaker opens after threshold failures")
    
    # Test recovery
    import time
    time.sleep(1.1)
    assert breaker.can_attempt_call() == True
    print("✓ Circuit breaker allows retry after recovery timeout")
    
    # Test reset on success
    breaker.call_succeeded()
    assert breaker.state == 'closed'
    print("✓ Circuit breaker resets on successful call")
    
    print("Circuit breaker tests complete!")


async def test_error_handler():
    """Test error handling and retry logic."""
    print("\n=== Testing Error Handler ===")
    
    import logging
    logger = logging.getLogger("test")
    handler = ErrorHandler(logger)
    
    # Test retry decorator
    attempt_count = 0
    
    @handler.with_retry(max_retries=2, delay=0.1)
    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise NetworkError("Network error")
        return "success"
    
    result = await failing_function()
    print(f"✓ Retry logic worked: {attempt_count} attempts, result: {result}")
    
    # Test error boundary
    @handler.with_error_boundary(default_return="default")
    async def error_function():
        raise ValueError("Test error")
    
    result = await error_function()
    print(f"✓ Error boundary returned default: {result}")
    
    # Check error statistics
    stats = handler.get_error_summary()
    print(f"✓ Error statistics tracked: {stats['total_errors']} errors")
    
    print("Error handler tests complete!")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("SAFETY FEATURES TEST SUITE")
    print("=" * 60)
    
    # Test each component
    test_path_validator()
    await test_transaction_manager()
    test_circuit_breaker()
    await test_error_handler()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())