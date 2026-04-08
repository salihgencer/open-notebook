from typing import Dict, List, Optional, Type

from extensions.outputs.base import BaseOutputGenerator


class OutputRegistry:
    def __init__(self):
        self._generators: Dict[str, Type[BaseOutputGenerator]] = {}

    def register(self, generator_class: Type[BaseOutputGenerator]) -> None:
        self._generators[generator_class.name] = generator_class

    def get(self, name: str) -> Optional[BaseOutputGenerator]:
        cls = self._generators.get(name)
        return cls() if cls else None

    def list_types(self) -> List[str]:
        return list(self._generators.keys())

    def list_all(self) -> List[Dict[str, str]]:
        return [
            {
                "name": cls.name,
                "title": cls.title,
                "description": cls.description,
            }
            for cls in self._generators.values()
        ]
