"""System engine"""
import time
from abc import ABC, abstractmethod
from typing import List

class System(ABC):
    def __init__(self):
        self.enabled = True
        self.stats = {'runs': 0, 'total_time': 0.0}
    
    @abstractmethod
    def name(self) -> str:
        pass
    
    def priority(self) -> int:
        return 0
    
    @abstractmethod
    def process(self, world, delta_time: float) -> None:
        pass
    
    def run(self, world, delta_time: float) -> None:
        if not self.enabled:
            return
        start = time.perf_counter()
        self.process(world, delta_time)
        self.stats['runs'] += 1
        self.stats['total_time'] += time.perf_counter() - start

class SystemScheduler:
    def __init__(self):
        self.systems: List[System] = []
    
    def add_system(self, system: System) -> None:
        self.systems.append(system)
        self.systems.sort(key=lambda s: s.priority(), reverse=True)
    
    def tick(self, world, delta_time: float) -> None:
        for system in self.systems:
            system.run(world, delta_time)
