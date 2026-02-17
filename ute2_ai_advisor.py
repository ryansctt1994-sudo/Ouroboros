"""
UTe2 Hybrid System - AI Advisor

Offline-first AI advisor for resource optimization and learning from simulations.
Provides intelligent recommendations based on historical patterns and device constraints.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AIAdvisor:
    """AI-powered advisor for simulation optimization"""
    
    def __init__(self, config: Dict[str, Any], knowledge_base_path: str = "knowledge_base.json"):
        """
        Initialize AI Advisor
        
        Args:
            config: Configuration dictionary
            knowledge_base_path: Path to knowledge base JSON
        """
        self.config = config.get('ai_advisor', {})
        self.enabled = self.config.get('enabled', True)
        self.offline_mode = self.config.get('offline_mode', True)
        self.learning_config = self.config.get('learning', {})
        self.optimization_config = self.config.get('optimization', {})
        
        # Load knowledge base
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base = self._load_knowledge_base()
        
        # Learning history
        self.simulation_history: List[Dict[str, Any]] = []
        self.save_counter = 0
        
        logger.info(f"AI Advisor initialized (offline_mode={self.offline_mode})")
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file"""
        try:
            if self.knowledge_base_path.exists():
                with open(self.knowledge_base_path, 'r') as f:
                    kb = json.load(f)
                logger.info(f"Loaded knowledge base from {self.knowledge_base_path}")
                return kb
            else:
                logger.warning(f"Knowledge base not found at {self.knowledge_base_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return {}
    
    def _save_knowledge_base(self):
        """Save updated knowledge base to file"""
        try:
            with open(self.knowledge_base_path, 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
            logger.debug("Knowledge base saved")
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")
    
    def get_device_recommendations(self, device_type: str = "laptop") -> Dict[str, Any]:
        """
        Get optimization recommendations for specific device
        
        Args:
            device_type: Device type (raspberry_pi, laptop, desktop, hpc_cluster)
            
        Returns:
            Recommendation dictionary
        """
        if not self.enabled:
            return {}
        
        device_opts = self.knowledge_base.get('device_optimizations', {}).get(device_type, {})
        
        if not device_opts:
            logger.warning(f"No optimizations found for device type: {device_type}")
            return self._get_default_recommendations()
        
        logger.info(f"Retrieved recommendations for {device_type}")
        return device_opts
    
    def _get_default_recommendations(self) -> Dict[str, Any]:
        """Get default recommendations when device type unknown"""
        return {
            'recommended_k_grid': 32,
            'precision': 'float64',
            'memory_limit_mb': 2048,
            'tips': ['Use balanced settings for unknown device']
        }
    
    def suggest_parameters(self, 
                          temperature: Optional[float] = None,
                          magnetic_field: Optional[float] = None,
                          device_type: str = "laptop") -> Dict[str, Any]:
        """
        Suggest optimal simulation parameters
        
        Args:
            temperature: Temperature in Kelvin (optional)
            magnetic_field: Magnetic field in Tesla (optional)
            device_type: Device type for resource constraints
            
        Returns:
            Suggested parameters
        """
        if not self.enabled:
            return {}
        
        suggestions = {}
        
        # Get device-specific constraints
        device_opts = self.get_device_recommendations(device_type)
        suggestions['k_grid_size'] = device_opts.get('recommended_k_grid', 32)
        suggestions['precision'] = device_opts.get('precision', 'float64')
        
        # Get region-specific optimizations
        if magnetic_field is not None:
            region = self._identify_simulation_region(magnetic_field)
            region_opts = self.knowledge_base.get('simulation_regions', {}).get(region, {})
            
            if region_opts:
                optimal_params = region_opts.get('optimal_parameters', {})
                suggestions.update(optimal_params)
                suggestions['region'] = region
                suggestions['notes'] = region_opts.get('notes', '')
        
        # Adjust for temperature if provided
        if temperature is not None:
            if temperature < 0.5:
                suggestions['convergence_threshold'] = 1e-7
            elif temperature > 2.0:
                suggestions['convergence_threshold'] = 1e-5
        
        # Add solver strategy recommendation
        strategy = self._recommend_solver_strategy(device_type, magnetic_field)
        suggestions['solver_strategy'] = strategy
        
        logger.info(f"Generated parameter suggestions: {suggestions}")
        return suggestions
    
    def _identify_simulation_region(self, magnetic_field: float) -> str:
        """
        Identify which simulation region applies for given field
        
        Args:
            magnetic_field: Magnetic field in Tesla
            
        Returns:
            Region name
        """
        regions = self.knowledge_base.get('simulation_regions', {})
        
        for region_name, region_data in regions.items():
            field_range = region_data.get('magnetic_field_range_T', [0, 0])
            if field_range[0] <= magnetic_field <= field_range[1]:
                return region_name
        
        return 'unknown'
    
    def _recommend_solver_strategy(self, 
                                   device_type: str,
                                   magnetic_field: Optional[float] = None) -> str:
        """
        Recommend solver strategy based on device and simulation type
        
        Args:
            device_type: Device type
            magnetic_field: Magnetic field (optional)
            
        Returns:
            Strategy name
        """
        # Fast preview for limited devices
        if device_type == 'raspberry_pi':
            return 'fast_preview'
        
        # High accuracy for reentrant region on capable devices
        if magnetic_field is not None and 40 <= magnetic_field <= 65:
            if device_type in ['desktop', 'hpc_cluster']:
                return 'high_accuracy'
        
        # Standard for most cases
        return 'standard'
    
    def learn_from_simulation(self, 
                             parameters: Dict[str, Any],
                             result: Any,
                             performance_metrics: Optional[Dict[str, Any]] = None):
        """
        Learn from simulation results to improve future recommendations
        
        Args:
            parameters: Simulation parameters used
            result: Simulation result
            performance_metrics: Optional performance data (time, memory, etc.)
        """
        if not self.enabled or not self.learning_config.get('enabled', True):
            return
        
        # Record simulation
        record = {
            'timestamp': datetime.now().isoformat(),
            'parameters': parameters,
            'success': getattr(result, 'success', True),
            'performance': performance_metrics or {}
        }
        
        self.simulation_history.append(record)
        
        # Analyze and update knowledge base
        self._analyze_patterns()
        
        # Save periodically
        self.save_counter += 1
        save_freq = self.learning_config.get('save_frequency', 10)
        if self.save_counter >= save_freq:
            self._update_learned_insights()
            self._save_knowledge_base()
            self.save_counter = 0
            logger.info("Learned insights updated")
    
    def _analyze_patterns(self):
        """Analyze simulation history for patterns"""
        max_history = self.learning_config.get('max_history', 1000)
        
        # Keep only recent history
        if len(self.simulation_history) > max_history:
            self.simulation_history = self.simulation_history[-max_history:]
        
        # Simple pattern detection (would use ML in full implementation)
        # For now, just track success rates by parameter ranges
        RECENT_HISTORY_WINDOW = 10  # Number of recent simulations to analyze
        if len(self.simulation_history) >= RECENT_HISTORY_WINDOW:
            success_count = sum(1 for r in self.simulation_history[-RECENT_HISTORY_WINDOW:] if r['success'])
            logger.debug(f"Recent success rate: {success_count}/{RECENT_HISTORY_WINDOW}")
    
    def _update_learned_insights(self):
        """Update learned insights in knowledge base"""
        insights = self.knowledge_base.get('learned_insights', {})
        
        insights['last_updated'] = datetime.now().isoformat()
        insights['total_simulations'] = len(self.simulation_history)
        
        # Add simple statistics
        if self.simulation_history:
            recent = self.simulation_history[-100:]  # Last 100 simulations
            success_rate = sum(1 for r in recent if r['success']) / len(recent)
            
            insights['recent_success_rate'] = success_rate
            insights['total_records'] = len(self.simulation_history)
        
        self.knowledge_base['learned_insights'] = insights
    
    def get_troubleshooting_advice(self, error_type: str) -> List[str]:
        """
        Get troubleshooting advice for common errors
        
        Args:
            error_type: Type of error encountered
            
        Returns:
            List of suggested solutions
        """
        if not self.enabled:
            return []
        
        error_handling = self.knowledge_base.get('error_handling', {})
        error_info = error_handling.get(error_type, {})
        
        solutions = error_info.get('solutions', [])
        
        if solutions:
            logger.info(f"Provided {len(solutions)} solutions for {error_type}")
        else:
            logger.warning(f"No troubleshooting advice found for {error_type}")
            solutions = ["Check logs for detailed error information"]
        
        return solutions
    
    def optimize_for_resource_constraints(self, 
                                          max_memory_mb: Optional[int] = None,
                                          max_time_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Optimize parameters for resource constraints
        
        Args:
            max_memory_mb: Maximum memory available
            max_time_seconds: Maximum execution time
            
        Returns:
            Optimized parameters
        """
        if not self.optimization_config.get('auto_suggest', True):
            return {}
        
        optimized = {}
        
        # Memory optimization
        if max_memory_mb is not None:
            if max_memory_mb < 1024:
                optimized['k_grid_size'] = 16
                optimized['precision'] = 'float32'
                optimized['solver_method'] = 'sparse'
            elif max_memory_mb < 4096:
                optimized['k_grid_size'] = 32
                optimized['precision'] = 'float64'
                optimized['solver_method'] = 'sparse'
            else:
                optimized['k_grid_size'] = 64
                optimized['precision'] = 'float64'
                optimized['solver_method'] = 'dense'
        
        # Time optimization
        if max_time_seconds is not None:
            if max_time_seconds < 60:
                optimized['max_iterations'] = 100
                optimized['k_grid_size'] = min(optimized.get('k_grid_size', 32), 24)
            elif max_time_seconds < 300:
                optimized['max_iterations'] = 500
        
        logger.info(f"Generated resource-optimized parameters: {optimized}")
        return optimized
    
    def get_tips_for_region(self, region: str) -> List[str]:
        """
        Get specific tips for simulating a particular region
        
        Args:
            region: Region name (e.g., 'reentrant', 'low_field')
            
        Returns:
            List of tips
        """
        regions = self.knowledge_base.get('simulation_regions', {})
        region_data = regions.get(region, {})
        
        tips = []
        if 'notes' in region_data:
            tips.append(region_data['notes'])
        
        if 'optimal_parameters' in region_data:
            tips.append(f"Recommended parameters: {region_data['optimal_parameters']}")
        
        return tips
    
    def get_stats(self) -> Dict[str, Any]:
        """Get advisor statistics"""
        return {
            'enabled': self.enabled,
            'offline_mode': self.offline_mode,
            'total_simulations_recorded': len(self.simulation_history),
            'knowledge_base_loaded': bool(self.knowledge_base),
            'learning_enabled': self.learning_config.get('enabled', True)
        }
