# Training Convergence Detection

## Overview

The `EnhancedConvergenceV2` provides intelligent early stopping and training optimization through phase-aware loss smoothing and hyperparameter recommendations.

## Features

- **Phase Detection**: Automatically detects warmup, training, plateau, and converged phases
- **Loss Smoothing**: Exponential moving average for stable convergence detection
- **Adaptive Patience**: Adjusts patience based on training phase
- **Hyperparameter Recommendations**: Suggests learning rate changes and early stopping

## Basic Usage

```python
from src.training import EnhancedConvergenceV2

# Initialize detector
guardian = EnhancedConvergenceV2(
    initial_patience=10,
    min_delta=1e-4,
    smoothing_alpha=0.3,
    warmup_epochs=5
)

# Training loop
for epoch in range(max_epochs):
    loss = train_epoch(model, data_loader)
    
    # Monitor convergence
    metrics = guardian.watch(
        epoch=epoch,
        loss=loss,
        learning_rate=optimizer.param_groups[0]['lr']
    )
    
    # Act on recommendations
    if metrics.recommended_action == "REDUCE_LR":
        for param_group in optimizer.param_groups:
            param_group['lr'] = metrics.recommended_lr
        print(f"Reduced LR to {metrics.recommended_lr}")
    
    elif metrics.recommended_action == "EARLY_STOP":
        print(f"Early stopping at epoch {epoch}")
        break
    
    # Log metrics
    print(f"Epoch {epoch}:")
    print(f"  Loss: {metrics.loss:.6f}")
    print(f"  Smoothed: {metrics.smoothed_loss:.6f}")
    print(f"  Phase: {metrics.phase}")
    print(f"  Patience: {metrics.patience_remaining}")
```

## Training Phases

### 1. Warmup Phase

High patience, no early stopping:

```python
guardian = EnhancedConvergenceV2(warmup_epochs=5)

# During warmup (epochs 0-4)
metrics = guardian.watch(epoch=2, loss=1.5)
assert metrics.phase == 'warmup'
assert metrics.recommended_action == 'CONTINUE'
```

### 2. Training Phase

Active improvement, normal patience:

```python
# Loss is improving
for epoch in range(10, 50):
    loss = initial_loss * (0.95 ** epoch)  # Decreasing
    metrics = guardian.watch(epoch, loss)
    assert metrics.phase == 'training'
```

### 3. Plateau Phase

Slow improvement, reduced patience:

```python
# Loss plateaus
for epoch in range(50, 60):
    loss = 0.1 + random.uniform(-0.001, 0.001)
    metrics = guardian.watch(epoch, loss)
    
    if metrics.phase == 'plateau':
        # May recommend LR reduction
        if metrics.recommended_action == 'REDUCE_LR':
            learning_rate *= 0.5
```

### 4. Converged Phase

Very low patience, early stop recommended:

```python
# Loss is stable
for epoch in range(60, 70):
    loss = 0.05 + random.uniform(-0.0001, 0.0001)
    metrics = guardian.watch(epoch, loss)
    
    if metrics.phase == 'converged':
        # Should stop soon
        assert metrics.recommended_action in ['EARLY_STOP', 'REDUCE_LR']
```

## Configuration Strategies

### Conservative Strategy

For critical models where you want to ensure convergence:

```python
guardian = EnhancedConvergenceV2(
    initial_patience=20,      # High patience
    min_delta=1e-5,          # Very small improvement threshold
    warmup_epochs=10,        # Long warmup
    plateau_threshold=1e-6   # Very flat plateau detection
)
```

### Aggressive Strategy

For quick experiments or resource-constrained training:

```python
guardian = EnhancedConvergenceV2(
    initial_patience=5,       # Low patience
    min_delta=1e-3,          # Larger improvement needed
    warmup_epochs=2,         # Short warmup
    plateau_threshold=1e-4   # Earlier plateau detection
)
```

### Adaptive Strategy

Adjusts based on loss characteristics:

```python
class AdaptiveConvergence:
    def __init__(self):
        self.guardian = EnhancedConvergenceV2()
        self.loss_history = []
    
    def watch(self, epoch, loss, lr):
        self.loss_history.append(loss)
        
        # Adjust patience based on loss variance
        if len(self.loss_history) > 10:
            variance = np.var(self.loss_history[-10:])
            if variance > 0.1:
                # High variance, increase patience
                self.guardian._current_patience = 20
            else:
                # Low variance, decrease patience
                self.guardian._current_patience = 5
        
        return self.guardian.watch(epoch, loss, lr)
```

## Loss Smoothing

### EMA Smoothing

The detector uses exponential moving average:

```python
# Configure smoothing
guardian = EnhancedConvergenceV2(
    smoothing_alpha=0.3  # 0-1, higher = more responsive
)

# Effect on smoothing:
# alpha=0.1: Very smooth, slow to react
# alpha=0.5: Balanced
# alpha=0.9: Minimal smoothing, fast reaction
```

### Custom Smoothing

```python
class CustomSmoothing(EnhancedConvergenceV2):
    def watch(self, epoch, loss, learning_rate=0.001):
        # Apply your custom smoothing
        smoothed = self.custom_smooth(loss)
        
        # Then use parent's watch
        return super().watch(epoch, smoothed, learning_rate)
    
    def custom_smooth(self, loss):
        # Implement custom smoothing logic
        return loss
```

## Hyperparameter Recommendations

### Learning Rate Reduction

```python
metrics = guardian.watch(epoch, loss, lr=0.001)

if metrics.recommended_action == "REDUCE_LR":
    new_lr = metrics.recommended_lr
    
    # Update optimizer
    for param_group in optimizer.param_groups:
        param_group['lr'] = new_lr
    
    print(f"Learning rate: {0.001} -> {new_lr}")
```

### Scheduled LR with Convergence

```python
# Combine with scheduler
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=5
)

for epoch in range(max_epochs):
    loss = train_epoch()
    metrics = guardian.watch(epoch, loss)
    
    # Use convergence detector's recommendation
    if metrics.recommended_action == "REDUCE_LR":
        scheduler.step(loss)
    elif metrics.recommended_action == "EARLY_STOP":
        break
```

## Monitoring and Visualization

### Training Dashboard

```python
import matplotlib.pyplot as plt

class TrainingMonitor:
    def __init__(self, guardian):
        self.guardian = guardian
        self.epochs = []
        self.losses = []
        self.smoothed_losses = []
        self.phases = []
    
    def update(self, epoch, loss, lr):
        metrics = self.guardian.watch(epoch, loss, lr)
        
        self.epochs.append(epoch)
        self.losses.append(loss)
        self.smoothed_losses.append(metrics.smoothed_loss)
        self.phases.append(metrics.phase)
        
        return metrics
    
    def plot(self):
        plt.figure(figsize=(12, 6))
        
        # Plot losses
        plt.subplot(1, 2, 1)
        plt.plot(self.epochs, self.losses, label='Loss', alpha=0.5)
        plt.plot(self.epochs, self.smoothed_losses, label='Smoothed Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        
        # Plot phases
        plt.subplot(1, 2, 2)
        phase_colors = {
            'warmup': 'blue',
            'training': 'green',
            'plateau': 'orange',
            'converged': 'red'
        }
        for phase in set(self.phases):
            epochs = [e for e, p in zip(self.epochs, self.phases) if p == phase]
            plt.scatter(epochs, [0]*len(epochs), 
                       c=phase_colors[phase], label=phase, s=50)
        plt.xlabel('Epoch')
        plt.legend()
        
        plt.tight_layout()
        plt.show()
```

### Summary Statistics

```python
def training_summary(guardian):
    summary = guardian.get_summary()
    
    print("Training Summary:")
    print(f"  Total epochs: {summary['total_epochs']}")
    print(f"  Best loss: {summary['best_loss']:.6f}")
    print(f"  Best epoch: {summary['best_epoch']}")
    print(f"  Final phase: {summary['current_phase']}")
    print(f"  Total time: {summary['elapsed_time']:.1f}s")
    print(f"  Avg improvement: {summary['avg_improvement_rate']:.6f}")
```

## Best Practices

### 1. Start Conservative

```python
# First run: Conservative settings
guardian = EnhancedConvergenceV2(initial_patience=20)
train_model()
summary = guardian.get_summary()

# Adjust based on results
optimal_epochs = summary['best_epoch']
recommended_patience = max(5, optimal_epochs // 3)
```

### 2. Validate on Separate Set

```python
def train_with_validation():
    train_guardian = EnhancedConvergenceV2()
    val_guardian = EnhancedConvergenceV2()
    
    for epoch in range(max_epochs):
        train_loss = train_epoch()
        val_loss = validate_epoch()
        
        train_metrics = train_guardian.watch(epoch, train_loss)
        val_metrics = val_guardian.watch(epoch, val_loss)
        
        # Stop if validation isn't improving
        if val_metrics.recommended_action == "EARLY_STOP":
            break
```

### 3. Multi-Metric Monitoring

```python
class MultiMetricGuardian:
    def __init__(self):
        self.loss_guardian = EnhancedConvergenceV2()
        self.accuracy_guardian = EnhancedConvergenceV2()
    
    def watch(self, epoch, loss, accuracy, lr):
        loss_metrics = self.loss_guardian.watch(epoch, loss, lr)
        # Invert accuracy for minimization
        acc_metrics = self.accuracy_guardian.watch(epoch, 1-accuracy, lr)
        
        # Stop if either recommends
        if (loss_metrics.recommended_action == "EARLY_STOP" or
            acc_metrics.recommended_action == "EARLY_STOP"):
            return "EARLY_STOP"
        
        return "CONTINUE"
```

## Troubleshooting

### Issue: Early Stop Too Soon

**Symptoms**: Training stops before convergence

**Solution**:
```python
# Increase patience
guardian = EnhancedConvergenceV2(initial_patience=30)

# Or decrease min_delta
guardian = EnhancedConvergenceV2(min_delta=1e-6)
```

### Issue: Never Stops

**Symptoms**: Training runs for all epochs

**Solution**:
```python
# Decrease patience
guardian = EnhancedConvergenceV2(initial_patience=5)

# Or increase min_delta
guardian = EnhancedConvergenceV2(min_delta=1e-3)
```

### Issue: Oscillating Loss

**Symptoms**: Loss jumps up and down

**Solution**:
```python
# Increase smoothing
guardian = EnhancedConvergenceV2(smoothing_alpha=0.1)

# Or add gradient clipping
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```
