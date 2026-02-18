package com.aiospandora.rustoracle

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Main Activity - Android Simulation Harness for Rust Oracle Token Validation
 * 
 * This simulation validates:
 * 1. Unsafe token exclusion - tokens outside allowed ranges are blocked/masked
 * 2. Constraint mask latency - measures delay between injection and enforcement (<100μs target)
 * 3. JNI + Rust loop stability - ensures integration sustains repeated calls
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    SimulationScreen()
                }
            }
        }
    }
}

@Composable
fun SimulationScreen() {
    var minToken by remember { mutableStateOf(0) }
    var maxToken by remember { mutableStateOf(1000) }
    var maskMode by remember { mutableStateOf(true) }
    var maskValue by remember { mutableStateOf(0) }
    var tokensPerBatch by remember { mutableStateOf(100) }
    var batchCount by remember { mutableStateOf(10) }
    var unsafeRatio by remember { mutableStateOf(0.2f) }
    
    var isRunning by remember { mutableStateOf(false) }
    var simulationResult by remember { mutableStateOf<SimulationRunner.SimulationResult?>(null) }
    var stabilityResult by remember { mutableStateOf<SimulationRunner.StabilityTestResult?>(null) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    
    val scope = rememberCoroutineScope()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text(
            "Rust Oracle Token Validation",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 16.dp)
        )
        
        Text(
            "Android Simulation Harness - Token Stream Proof-of-Concept",
            fontSize = 14.sp,
            color = Color.Gray,
            modifier = Modifier.padding(bottom = 24.dp)
        )
        
        // Configuration Section
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Configuration", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Spacer(modifier = Modifier.height(12.dp))
                
                ConfigSlider(
                    label = "Min Token: $minToken",
                    value = minToken.toFloat(),
                    onValueChange = { minToken = it.toInt() },
                    valueRange = -1000f..1000f
                )
                
                ConfigSlider(
                    label = "Max Token: $maxToken",
                    value = maxToken.toFloat(),
                    onValueChange = { maxToken = it.toInt() },
                    valueRange = 0f..2000f
                )
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Mask Mode (vs Reject):", modifier = Modifier.weight(1f))
                    Switch(checked = maskMode, onCheckedChange = { maskMode = it })
                }
                
                if (maskMode) {
                    ConfigSlider(
                        label = "Mask Value: $maskValue",
                        value = maskValue.toFloat(),
                        onValueChange = { maskValue = it.toInt() },
                        valueRange = -100f..100f
                    )
                }
                
                ConfigSlider(
                    label = "Tokens per Batch: $tokensPerBatch",
                    value = tokensPerBatch.toFloat(),
                    onValueChange = { tokensPerBatch = it.toInt() },
                    valueRange = 10f..1000f
                )
                
                ConfigSlider(
                    label = "Batch Count: $batchCount",
                    value = batchCount.toFloat(),
                    onValueChange = { batchCount = it.toInt() },
                    valueRange = 1f..100f
                )
                
                ConfigSlider(
                    label = "Unsafe Token Ratio: ${(unsafeRatio * 100).toInt()}%",
                    value = unsafeRatio,
                    onValueChange = { unsafeRatio = it },
                    valueRange = 0f..1f
                )
            }
        }
        
        // Action Buttons
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = {
                    scope.launch {
                        runSimulation(
                            minToken, maxToken, maskMode, maskValue,
                            tokensPerBatch, batchCount, unsafeRatio,
                            onResult = { result, error ->
                                simulationResult = result
                                errorMessage = error
                                isRunning = false
                            },
                            onRunningChanged = { isRunning = it }
                        )
                    }
                },
                enabled = !isRunning,
                modifier = Modifier.weight(1f)
            ) {
                Text("Run Simulation")
            }
            
            Button(
                onClick = {
                    scope.launch {
                        runStabilityTest(
                            minToken, maxToken, maskMode, maskValue,
                            tokensPerBatch, unsafeRatio,
                            onResult = { result, error ->
                                stabilityResult = result
                                errorMessage = error
                                isRunning = false
                            },
                            onRunningChanged = { isRunning = it }
                        )
                    }
                },
                enabled = !isRunning,
                modifier = Modifier.weight(1f)
            ) {
                Text("Stability Test")
            }
        }
        
        if (isRunning) {
            LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
            Spacer(modifier = Modifier.height(16.dp))
        }
        
        // Error Display
        errorMessage?.let { error ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 16.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFFFEBEE))
            ) {
                Text(
                    "Error: $error",
                    color = Color.Red,
                    modifier = Modifier.padding(16.dp)
                )
            }
        }
        
        // Results Display
        simulationResult?.let { result ->
            SimulationResultCard(result)
        }
        
        stabilityResult?.let { result ->
            StabilityResultCard(result)
        }
    }
}

@Composable
fun ConfigSlider(
    label: String,
    value: Float,
    onValueChange: (Float) -> Unit,
    valueRange: ClosedFloatingPointRange<Float>
) {
    Column(modifier = Modifier.padding(vertical = 4.dp)) {
        Text(label, fontSize = 14.sp)
        Slider(
            value = value,
            onValueChange = onValueChange,
            valueRange = valueRange
        )
    }
}

@Composable
fun SimulationResultCard(result: SimulationRunner.SimulationResult) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Simulation Results", fontWeight = FontWeight.Bold, fontSize = 18.sp)
            Spacer(modifier = Modifier.height(12.dp))
            
            ResultRow("Total Batches:", "${result.batchResults.size}")
            ResultRow("Total Tokens:", "${result.totalTokens}")
            ResultRow("Mean Latency:", String.format("%.2f μs", result.meanLatencyUs))
            ResultRow("Max Latency:", String.format("%.2f μs", result.maxLatencyUs))
            ResultRow("P99 Latency:", String.format("%.2f μs", result.p99LatencyUs))
            
            // Latency target indicator
            val targetMet = result.p99LatencyUs < 100.0
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "Target (<100μs):",
                    modifier = Modifier.weight(1f)
                )
                Text(
                    if (targetMet) "✓ MET" else "✗ MISSED",
                    color = if (targetMet) Color.Green else Color.Red,
                    fontWeight = FontWeight.Bold
                )
            }
            
            Divider(modifier = Modifier.padding(vertical = 8.dp))
            
            Text("Token Statistics", fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            
            ResultRow("Safe Tokens:", "${result.stats.safeTokens} (${String.format("%.1f%%", result.stats.safeRate * 100)})")
            ResultRow("Blocked Tokens:", "${result.stats.blockedTokens} (${String.format("%.1f%%", result.stats.blockRate * 100)})")
            ResultRow("Masked Tokens:", "${result.stats.maskedTokens} (${String.format("%.1f%%", result.stats.maskRate * 100)})")
        }
    }
}

@Composable
fun StabilityResultCard(result: SimulationRunner.StabilityTestResult) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Stability Test Results", fontWeight = FontWeight.Bold, fontSize = 18.sp)
            Spacer(modifier = Modifier.height(12.dp))
            
            ResultRow("Iterations:", "${result.iterations}")
            ResultRow("Success:", "${result.successCount}")
            ResultRow("Failures:", "${result.failureCount}")
            
            val successRate = result.successCount.toDouble() / result.iterations * 100
            ResultRow("Success Rate:", String.format("%.2f%%", successRate))
            
            Divider(modifier = Modifier.padding(vertical = 8.dp))
            
            Text("Latency Distribution", fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            
            ResultRow("Mean:", String.format("%.2f μs", result.meanLatencyUs))
            ResultRow("Min:", String.format("%.2f μs", result.minLatencyUs))
            ResultRow("P50:", String.format("%.2f μs", result.p50LatencyUs))
            ResultRow("P99:", String.format("%.2f μs", result.p99LatencyUs))
            ResultRow("Max:", String.format("%.2f μs", result.maxLatencyUs))
            
            if (result.errors.isNotEmpty()) {
                Divider(modifier = Modifier.padding(vertical = 8.dp))
                Text("Errors:", fontWeight = FontWeight.Bold, color = Color.Red)
                result.errors.take(5).forEach { error ->
                    Text(error, fontSize = 12.sp, color = Color.Red)
                }
            }
        }
    }
}

@Composable
fun ResultRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
    ) {
        Text(label, modifier = Modifier.weight(1f))
        Text(value, fontWeight = FontWeight.Medium)
    }
}

suspend fun runSimulation(
    minToken: Int,
    maxToken: Int,
    maskMode: Boolean,
    maskValue: Int,
    tokensPerBatch: Int,
    batchCount: Int,
    unsafeRatio: Float,
    onResult: (SimulationRunner.SimulationResult?, String?) -> Unit,
    onRunningChanged: (Boolean) -> Unit
) {
    onRunningChanged(true)
    
    withContext(Dispatchers.IO) {
        try {
            val oracle = RustOracle.create(minToken, maxToken, maskMode, maskValue)
            val simulator = TokenStreamSimulator(minToken, maxToken, unsafeRatio.toDouble())
            val runner = SimulationRunner(oracle, simulator)
            
            val result = runner.runSimulation(tokensPerBatch, batchCount)
            
            oracle.destroy()
            
            withContext(Dispatchers.Main) {
                onResult(result, null)
            }
        } catch (e: Exception) {
            withContext(Dispatchers.Main) {
                onResult(null, e.message ?: "Unknown error")
            }
        }
    }
}

suspend fun runStabilityTest(
    minToken: Int,
    maxToken: Int,
    maskMode: Boolean,
    maskValue: Int,
    tokensPerBatch: Int,
    unsafeRatio: Float,
    onResult: (SimulationRunner.StabilityTestResult?, String?) -> Unit,
    onRunningChanged: (Boolean) -> Unit
) {
    onRunningChanged(true)
    
    withContext(Dispatchers.IO) {
        try {
            val oracle = RustOracle.create(minToken, maxToken, maskMode, maskValue)
            val simulator = TokenStreamSimulator(minToken, maxToken, unsafeRatio.toDouble())
            val runner = SimulationRunner(oracle, simulator)
            
            val result = runner.runStabilityTest(tokensPerBatch, 1000)
            
            oracle.destroy()
            
            withContext(Dispatchers.Main) {
                onResult(result, null)
            }
        } catch (e: Exception) {
            withContext(Dispatchers.Main) {
                onResult(null, e.message ?: "Unknown error")
            }
        }
    }
}
