"""
Tests for UTe2 Hybrid System Components

Basic validation tests for the core components of the hybrid AI-powered
UTe2 superconductivity simulation system.
"""

import pytest
import yaml
import json
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Import components to test
from ute2_cache import SimulationCache
from ute2_simulation import UTe2SimulationEngine, SimulationResult
from ute2_ai_advisor import AIAdvisor
from ute2_hybrid_engine import HybridExecutionEngine, ExecutionMode


@pytest.fixture
def test_config():
    """Load test configuration"""
    config_path = Path('hybrid_config.yaml')
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        # Return minimal default config
        return {
            'execution': {
                'default_mode': 'local',
                'modes': {
                    'offline': {'enabled': True, 'max_grid_size': 24},
                    'local': {'enabled': True, 'max_grid_size': 64},
                    'hybrid': {'enabled': True, 'cloud_threshold_size': 100},
                    'cloud': {'enabled': False}
                }
            },
            'cache': {
                'enabled': True,
                'storage_path': './test_cache',
                'max_size_mb': 100,
                'ttl_days': 7,
                'compression': True,
                'strategy': {'hash_parameters': ['temperature_K', 'magnetic_field_T', 'k_grid_size']}
            },
            'simulation': {
                'material': {'name': 'UTe2', 'critical_temperature_K': 1.6},
                'defaults': {
                    'temperature_K': 0.5,
                    'magnetic_field_T': 0.0,
                    'k_grid_size': 16
                },
                'solver': {
                    'method': 'sparse',
                    'convergence_threshold': 1e-6,
                    'max_iterations': 1000
                }
            },
            'ai_advisor': {
                'enabled': True,
                'offline_mode': True,
                'learning': {'enabled': True, 'save_frequency': 10}
            }
        }


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory"""
    temp_dir = tempfile.mkdtemp(prefix='ute2_test_cache_')
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestSimulationCache:
    """Tests for caching system"""
    
    def test_cache_initialization(self, test_config, temp_cache_dir):
        """Test cache initialization"""
        test_config['cache']['storage_path'] = temp_cache_dir
        cache = SimulationCache(test_config)
        
        assert cache.enabled
        assert cache.storage_path.exists()
        assert cache.max_size_mb > 0  # Just check it's set
    
    def test_cache_put_get(self, test_config, temp_cache_dir):
        """Test caching and retrieval"""
        test_config['cache']['storage_path'] = temp_cache_dir
        cache = SimulationCache(test_config)
        
        params = {'temperature_K': 0.5, 'magnetic_field_T': 10.0, 'k_grid_size': 16}
        result = {'gap': np.array([1.0, 2.0, 3.0]), 'success': True}
        
        # Cache result
        success = cache.put(params, result)
        assert success
        
        # Retrieve result
        cached = cache.get(params)
        assert cached is not None
        assert cached['success'] is True
        assert np.array_equal(cached['gap'], result['gap'])
    
    def test_cache_miss(self, test_config, temp_cache_dir):
        """Test cache miss for non-existent entry"""
        test_config['cache']['storage_path'] = temp_cache_dir
        cache = SimulationCache(test_config)
        
        params = {'temperature_K': 999.0, 'magnetic_field_T': 999.0, 'k_grid_size': 999}
        cached = cache.get(params)
        
        assert cached is None
    
    def test_cache_stats(self, test_config, temp_cache_dir):
        """Test cache statistics"""
        test_config['cache']['storage_path'] = temp_cache_dir
        cache = SimulationCache(test_config)
        
        stats = cache.get_stats()
        assert 'enabled' in stats
        assert 'total_entries' in stats
        assert 'total_size_mb' in stats
        assert stats['enabled'] == True


class TestSimulationEngine:
    """Tests for simulation engine"""
    
    def test_engine_initialization(self, test_config):
        """Test engine initialization"""
        engine = UTe2SimulationEngine(test_config)
        
        assert engine.material['name'] == 'UTe2'
        assert engine.defaults['temperature_K'] == 0.5
    
    def test_basic_simulation(self, test_config):
        """Test basic simulation run"""
        engine = UTe2SimulationEngine(test_config)
        
        params = {
            'temperature_K': 0.5,
            'magnetic_field_T': 0.0,
            'k_grid_size': 8  # Small for speed
        }
        
        result = engine.run_simulation(params)
        
        assert result.success
        assert result.gap_function is not None
        assert len(result.gap_function) > 0
        assert result.eigenvalues is not None
        assert result.convergence_info is not None
    
    def test_phase_diagram_generation(self, test_config):
        """Test phase diagram generation"""
        engine = UTe2SimulationEngine(test_config)
        
        phase_data = engine.generate_phase_diagram(
            temperature_range=(0.1, 2.0),
            field_range=(0, 40),
            resolution=10  # Small for speed
        )
        
        assert 'temperature' in phase_data
        assert 'magnetic_field' in phase_data
        assert 'phase' in phase_data
        assert phase_data['phase'].shape == (10, 10)
    
    def test_critical_temperature_estimation(self, test_config):
        """Test Tc estimation"""
        engine = UTe2SimulationEngine(test_config)
        
        Tc0 = engine.estimate_critical_temperature(magnetic_field=0.0)
        Tc10 = engine.estimate_critical_temperature(magnetic_field=10.0)
        
        assert Tc0 > 0
        assert Tc10 < Tc0  # Field suppresses Tc


class TestAIAdvisor:
    """Tests for AI advisor"""
    
    def test_advisor_initialization(self, test_config):
        """Test advisor initialization"""
        advisor = AIAdvisor(test_config, 'knowledge_base.json')
        
        assert advisor.enabled
        assert advisor.offline_mode
    
    def test_device_recommendations(self, test_config):
        """Test device-specific recommendations"""
        advisor = AIAdvisor(test_config, 'knowledge_base.json')
        
        recs = advisor.get_device_recommendations('raspberry_pi')
        
        if recs:  # Only test if knowledge base is loaded
            assert 'recommended_k_grid' in recs or 'tips' in recs
    
    def test_parameter_suggestions(self, test_config):
        """Test parameter suggestions"""
        advisor = AIAdvisor(test_config, 'knowledge_base.json')
        
        suggestions = advisor.suggest_parameters(
            temperature=0.5,
            magnetic_field=10.0,
            device_type='laptop'
        )
        
        assert isinstance(suggestions, dict)
    
    def test_troubleshooting_advice(self, test_config):
        """Test troubleshooting advice"""
        advisor = AIAdvisor(test_config, 'knowledge_base.json')
        
        solutions = advisor.get_troubleshooting_advice('convergence_failure')
        
        assert isinstance(solutions, list)
        assert len(solutions) > 0
    
    def test_learning_from_simulation(self, test_config):
        """Test learning mechanism"""
        advisor = AIAdvisor(test_config, 'knowledge_base.json')
        
        params = {'temperature_K': 0.5, 'k_grid_size': 32}
        result = SimulationResult(success=True, parameters=params)
        
        # Should not raise error
        advisor.learn_from_simulation(params, result, {'time': 1.0})
        
        stats = advisor.get_stats()
        assert 'total_simulations_recorded' in stats


class TestHybridExecutionEngine:
    """Tests for hybrid execution engine"""
    
    def test_engine_initialization(self, test_config):
        """Test engine initialization"""
        engine = HybridExecutionEngine(test_config)
        
        assert engine.current_mode in [ExecutionMode.OFFLINE, ExecutionMode.LOCAL, 
                                      ExecutionMode.HYBRID, ExecutionMode.CLOUD]
        assert engine.simulation_engine is not None
        assert engine.cache is not None
        assert engine.advisor is not None
    
    def test_mode_switching(self, test_config):
        """Test execution mode switching"""
        engine = HybridExecutionEngine(test_config)
        
        engine.set_mode('local')
        assert engine.current_mode == ExecutionMode.LOCAL
        
        engine.set_mode('offline')
        assert engine.current_mode == ExecutionMode.OFFLINE
    
    def test_task_submission(self, test_config):
        """Test task submission"""
        engine = HybridExecutionEngine(test_config)
        
        params = {
            'temperature_K': 0.5,
            'magnetic_field_T': 0.0,
            'k_grid_size': 8
        }
        
        task_id = engine.submit_task(params, priority=5)
        
        assert task_id.startswith('task_')
        assert engine.task_queue.qsize() == 1
    
    def test_task_execution(self, test_config, temp_cache_dir):
        """Test task execution"""
        test_config['cache']['storage_path'] = temp_cache_dir
        engine = HybridExecutionEngine(test_config)
        engine.set_mode('local')
        
        params = {
            'temperature_K': 0.5,
            'magnetic_field_T': 0.0,
            'k_grid_size': 8
        }
        
        task_id = engine.submit_task(params)
        result = engine.execute_next_task()
        
        assert result is not None
        assert result.success
        assert result.execution_mode == ExecutionMode.LOCAL
        assert result.execution_time > 0
    
    def test_offline_mode_constraints(self, test_config, temp_cache_dir):
        """Test offline mode resource constraints"""
        test_config['cache']['storage_path'] = temp_cache_dir
        engine = HybridExecutionEngine(test_config)
        engine.set_mode('offline')
        
        # Submit task with large k-grid
        params = {
            'temperature_K': 0.5,
            'magnetic_field_T': 0.0,
            'k_grid_size': 128  # Larger than offline max
        }
        
        task_id = engine.submit_task(params)
        result = engine.execute_next_task()
        
        # Should succeed but with constrained parameters
        assert result.success
    
    def test_status_reporting(self, test_config):
        """Test status reporting"""
        engine = HybridExecutionEngine(test_config)
        
        status = engine.get_status()
        
        assert 'current_mode' in status
        assert 'queued_tasks' in status
        assert 'completed_tasks' in status
        assert 'cache_stats' in status
        assert 'advisor_stats' in status


class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_end_to_end_workflow(self, test_config, temp_cache_dir):
        """Test complete simulation workflow"""
        test_config['cache']['storage_path'] = temp_cache_dir
        
        # Initialize engine
        engine = HybridExecutionEngine(test_config)
        engine.set_mode('local')
        
        # Submit multiple tasks
        params_list = [
            {'temperature_K': 0.5, 'magnetic_field_T': 0.0, 'k_grid_size': 8},
            {'temperature_K': 1.0, 'magnetic_field_T': 10.0, 'k_grid_size': 8},
            {'temperature_K': 0.5, 'magnetic_field_T': 0.0, 'k_grid_size': 8},  # Duplicate for cache test
        ]
        
        for params in params_list:
            engine.submit_task(params)
        
        # Execute all tasks
        results = engine.execute_all_tasks()
        
        assert len(results) == 3
        assert all(r.success for r in results)
        
        # Third task should be cache hit
        assert results[2].metadata.get('cache_hit', False)
        
        # Check system status
        status = engine.get_status()
        assert status['completed_tasks'] == 3
        assert status['cache_stats']['total_entries'] >= 1


def test_configuration_loading():
    """Test configuration file loading"""
    config_path = Path('hybrid_config.yaml')
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'execution' in config
        assert 'simulation' in config
        assert 'cache' in config
        assert 'ai_advisor' in config


def test_knowledge_base_loading():
    """Test knowledge base loading"""
    kb_path = Path('knowledge_base.json')
    
    if kb_path.exists():
        with open(kb_path, 'r') as f:
            kb = json.load(f)
        
        assert 'device_optimizations' in kb
        assert 'simulation_regions' in kb
        assert 'error_handling' in kb


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
