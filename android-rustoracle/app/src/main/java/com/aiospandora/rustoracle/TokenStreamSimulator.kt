package com.aiospandora.rustoracle

import kotlin.random.Random

/**
 * Token stream simulator for testing constraint enforcement
 */
class TokenStreamSimulator(
    private val safeMin: Int,
    private val safeMax: Int,
    private val unsafeRatio: Double = 0.2 // 20% unsafe tokens by default
) {
    private val random = Random.Default
    
    /**
     * Generate a batch of tokens with a mix of safe and unsafe values
     * 
     * @param count Number of tokens to generate
     * @return Array of tokens
     */
    fun generateBatch(count: Int): IntArray {
        return IntArray(count) { generateToken() }
    }
    
    /**
     * Generate a single token (may be safe or unsafe)
     */
    private fun generateToken(): Int {
        return if (random.nextDouble() < unsafeRatio) {
            // Generate unsafe token (outside allowed range)
            if (random.nextBoolean()) {
                // Below minimum
                safeMin - random.nextInt(1, 1000)
            } else {
                // Above maximum
                safeMax + random.nextInt(1, 1000)
            }
        } else {
            // Generate safe token
            random.nextInt(safeMin, safeMax + 1)
        }
    }
    
    /**
     * Generate a continuous stream of tokens for stress testing
     */
    fun generateStream(tokensPerBatch: Int, batchCount: Int): Sequence<IntArray> {
        return sequence {
            repeat(batchCount) {
                yield(generateBatch(tokensPerBatch))
            }
        }
    }
}

/**
 * Simulation runner for testing token validation
 */
class SimulationRunner(
    private val oracle: RustOracle,
    private val simulator: TokenStreamSimulator
) {
    data class SimulationResult(
        val batchResults: List<BatchResult>,
        val totalLatencyNs: Long,
        val totalTokens: Int,
        val meanLatencyUs: Double,
        val maxLatencyUs: Double,
        val p99LatencyUs: Double,
        val stats: ValidationStats
    )
    
    data class BatchResult(
        val batchNumber: Int,
        val inputSize: Int,
        val outputSize: Int,
        val latencyUs: Double,
        val timestamp: Long
    )
    
    /**
     * Run simulation with specified parameters
     */
    fun runSimulation(
        tokensPerBatch: Int,
        batchCount: Int,
        resetStatsBefore: Boolean = true
    ): SimulationResult {
        if (resetStatsBefore) {
            oracle.resetStats()
        }
        
        val batchResults = mutableListOf<BatchResult>()
        var totalLatencyNs = 0L
        var totalTokens = 0
        val startTime = System.nanoTime()
        
        simulator.generateStream(tokensPerBatch, batchCount).forEachIndexed { index, tokens ->
            val timestamp = System.nanoTime()
            val result = oracle.validateBatch(tokens)
            
            totalLatencyNs += result.latencyNs
            totalTokens += tokens.size
            
            batchResults.add(
                BatchResult(
                    batchNumber = index,
                    inputSize = tokens.size,
                    outputSize = result.validatedTokens.size,
                    latencyUs = result.latencyUs,
                    timestamp = timestamp - startTime
                )
            )
        }
        
        val stats = oracle.getStats()
        val latencies = batchResults.map { it.latencyUs }.sorted()
        
        return SimulationResult(
            batchResults = batchResults,
            totalLatencyNs = totalLatencyNs,
            totalTokens = totalTokens,
            meanLatencyUs = if (batchCount > 0) totalLatencyNs.toDouble() / batchCount / 1000.0 else 0.0,
            maxLatencyUs = latencies.lastOrNull() ?: 0.0,
            p99LatencyUs = if (latencies.isNotEmpty()) {
                val p99Index = (latencies.size * 0.99).toInt().coerceAtMost(latencies.size - 1)
                latencies[p99Index]
            } else {
                0.0
            },
            stats = stats
        )
    }
    
    /**
     * Run stability test - repeated calls under load
     */
    fun runStabilityTest(
        tokensPerBatch: Int,
        iterations: Int,
        onProgress: (iteration: Int, latencyUs: Double) -> Unit = { _, _ -> }
    ): StabilityTestResult {
        oracle.resetStats()
        
        val latencies = mutableListOf<Double>()
        val errors = mutableListOf<String>()
        var successCount = 0
        
        repeat(iterations) { iteration ->
            try {
                val tokens = simulator.generateBatch(tokensPerBatch)
                val result = oracle.validateBatch(tokens)
                latencies.add(result.latencyUs)
                successCount++
                onProgress(iteration, result.latencyUs)
            } catch (e: Exception) {
                errors.add("Iteration $iteration: ${e.message}")
            }
        }
        
        val sortedLatencies = latencies.sorted()
        
        return StabilityTestResult(
            iterations = iterations,
            successCount = successCount,
            failureCount = errors.size,
            meanLatencyUs = latencies.average(),
            minLatencyUs = sortedLatencies.firstOrNull() ?: 0.0,
            maxLatencyUs = sortedLatencies.lastOrNull() ?: 0.0,
            p50LatencyUs = if (sortedLatencies.isNotEmpty()) {
                sortedLatencies[sortedLatencies.size / 2]
            } else {
                0.0
            },
            p99LatencyUs = if (sortedLatencies.isNotEmpty()) {
                val p99Index = (sortedLatencies.size * 0.99).toInt().coerceAtMost(sortedLatencies.size - 1)
                sortedLatencies[p99Index]
            } else {
                0.0
            },
            errors = errors,
            stats = oracle.getStats()
        )
    }
    
    data class StabilityTestResult(
        val iterations: Int,
        val successCount: Int,
        val failureCount: Int,
        val meanLatencyUs: Double,
        val minLatencyUs: Double,
        val maxLatencyUs: Double,
        val p50LatencyUs: Double,
        val p99LatencyUs: Double,
        val errors: List<String>,
        val stats: ValidationStats
    )
}
