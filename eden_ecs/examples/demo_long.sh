#!/bin/bash
# demo_long.sh - Complete simulation pipeline

echo "🐇 EDEN ECS - COMPLETE SIMULATION PIPELINE"
echo "============================================"
echo

CYCLES=${1:-10000}
INTERVAL=${2:-100}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="simulation_output_${TIMESTAMP}"

echo "📊 Parameters:"
echo "   Cycles: ${CYCLES}"
echo "   Snapshot interval: ${INTERVAL}"
echo "   Output dir: ${OUTPUT_DIR}"
echo

mkdir -p "${OUTPUT_DIR}"
echo "✅ Created output directory"

echo
echo "🌀 Running simulation..."
python3 examples/demo_long.py \
    --cycles "${CYCLES}" \
    --snapshot-interval "${INTERVAL}" \
    --export "${OUTPUT_DIR}/history.json"

if [ $? -ne 0 ]; then
    echo "❌ Simulation failed!"
    exit 1
fi

echo
echo "✅ Simulation complete!"

echo
echo "📊 Running analysis..."
python3 examples/analyze.py "${OUTPUT_DIR}/history.json"

echo
echo "✅ Complete! Results saved to: ${OUTPUT_DIR}/"
echo
echo "Files generated:"
ls -la "${OUTPUT_DIR}/"
