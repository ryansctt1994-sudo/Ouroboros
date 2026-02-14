"""Component system"""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Component:
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

class ComponentStorage:
    def __init__(self):
        self.components: Dict[str, Component] = {}
    
    def add(self, entity_id: str, component: Component) -> None:
        self.components[entity_id] = component
    
    def get(self, entity_id: str) -> Component:
        return self.components.get(entity_id)
