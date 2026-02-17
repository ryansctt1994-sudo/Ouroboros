package com.aiospandora.rustoracle

/**
 * RustOracle - JNI bridge to Rust token validation module
 * 
 * Provides high-performance token constraint enforcement via native Rust code.
 */
class RustOracle private constructor(private val validatorPtr: Long) {
    
    companion object {
        init {
            System.loadLibrary("rustoracle")
        }
        
        /**
         * Create a new RustOracle validator
         * 
         * @param minToken Minimum allowed token value (inclusive)
         * @param maxToken Maximum allowed token value (inclusive)
         * @param maskMode If true, replace unsafe tokens with maskValue; if false, reject them
         * @param maskValue Replacement value for masked tokens
         */
        fun create(
            minToken: Int,
            maxToken: Int,
            maskMode: Boolean,
            maskValue: Int
        ): RustOracle {
            val ptr = nativeCreateValidator(minToken, maxToken, maskMode, maskValue)
            if (ptr == 0L) {
                throw RuntimeException("Failed to create RustOracle validator")
            }
            return RustOracle(ptr)
        }
        
        // Native method declarations
        @JvmStatic
        private external fun nativeCreateValidator(
            minToken: Int,
            maxToken: Int,
            maskMode: Boolean,
            maskValue: Int
        ): Long
        
        @JvmStatic
        private external fun nativeDestroyValidator(validatorPtr: Long)
        
        @JvmStatic
        private external fun nativeValidateBatch(
            validatorPtr: Long,
            inputTokens: IntArray,
            outputTokens: IntArray
        ): Long
        
        @JvmStatic
        private external fun nativeGetStats(validatorPtr: Long, statsArray: LongArray)
        
        @JvmStatic
        private external fun nativeResetStats(validatorPtr: Long)
    }
    
    /**
     * Validate a batch of tokens
     * 
     * @param tokens Input tokens to validate
     * @return ValidationResult containing validated tokens and latency in nanoseconds
     */
    fun validateBatch(tokens: IntArray): ValidationResult {
        val outputTokens = IntArray(tokens.size)
        val latencyNs = nativeValidateBatch(validatorPtr, tokens, outputTokens)
        
        if (latencyNs < 0) {
            throw RuntimeException("Token validation failed with error code: $latencyNs")
        }
        
        // Count how many tokens were actually validated (non-zero or explicitly set)
        // In reject mode, output will be smaller than input
        var validCount = 0
        for (i in outputTokens.indices) {
            if (i >= tokens.size) break
            validCount++
        }
        
        return ValidationResult(
            validatedTokens = outputTokens.copyOf(validCount),
            latencyNs = latencyNs,
            latencyUs = latencyNs / 1000.0
        )
    }
    
    /**
     * Get validation statistics
     */
    fun getStats(): ValidationStats {
        val statsArray = LongArray(4)
        nativeGetStats(validatorPtr, statsArray)
        
        return ValidationStats(
            totalTokens = statsArray[0],
            blockedTokens = statsArray[1],
            maskedTokens = statsArray[2],
            meanLatencyNs = statsArray[3],
            meanLatencyUs = statsArray[3] / 1000.0
        )
    }
    
    /**
     * Reset validation statistics
     */
    fun resetStats() {
        nativeResetStats(validatorPtr)
    }
    
    /**
     * Clean up native resources
     */
    fun destroy() {
        if (validatorPtr != 0L) {
            nativeDestroyValidator(validatorPtr)
        }
    }
    
    /**
     * Auto-cleanup when garbage collected
     */
    protected fun finalize() {
        destroy()
    }
}

/**
 * Result of a token validation batch
 */
data class ValidationResult(
    val validatedTokens: IntArray,
    val latencyNs: Long,
    val latencyUs: Double
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        
        other as ValidationResult
        
        if (!validatedTokens.contentEquals(other.validatedTokens)) return false
        if (latencyNs != other.latencyNs) return false
        
        return true
    }
    
    override fun hashCode(): Int {
        var result = validatedTokens.contentHashCode()
        result = 31 * result + latencyNs.hashCode()
        return result
    }
}

/**
 * Validation statistics from the Rust validator
 */
data class ValidationStats(
    val totalTokens: Long,
    val blockedTokens: Long,
    val maskedTokens: Long,
    val meanLatencyNs: Long,
    val meanLatencyUs: Double
) {
    val safeTokens: Long
        get() = totalTokens - blockedTokens - maskedTokens
    
    val blockRate: Double
        get() = if (totalTokens > 0) blockedTokens.toDouble() / totalTokens else 0.0
    
    val maskRate: Double
        get() = if (totalTokens > 0) maskedTokens.toDouble() / totalTokens else 0.0
    
    val safeRate: Double
        get() = if (totalTokens > 0) safeTokens.toDouble() / totalTokens else 0.0
}
