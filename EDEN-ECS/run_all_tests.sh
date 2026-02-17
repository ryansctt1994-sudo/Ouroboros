#!/bin/bash
echo "======================================"
echo "EDEN-ECS v2.0.0 Test Suite"
echo "======================================"
echo ""

# Track results
passed=0
failed=0

run_test() {
    echo "Running $1..."
    if python "$1" > /tmp/test_output.txt 2>&1; then
        grep -E "(✅|passing|PASS)" /tmp/test_output.txt | tail -3
        ((passed++))
        echo "✅ PASS"
    else
        cat /tmp/test_output.txt
        ((failed++))
        echo "❌ FAIL"
    fi
    echo ""
}

# Run all tests
run_test "test_core.py"
run_test "test_timestep.py"
run_test "test_loyalty_enhanced.py"
run_test "test_quantum.py"
run_test "test_memory.py"
run_test "test_balance_system.py"

echo "======================================"
echo "Test Summary"
echo "======================================"
echo "Passed: $passed"
echo "Failed: $failed"
echo "Total:  $((passed + failed))"
echo ""

if [ $failed -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed"
    exit 1
fi
