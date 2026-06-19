from dataclasses import dataclass
from typing import List

@dataclass
class CommandSpec:
    name: str
    command: List[str]
    category: str
    intent: str
    description: str
    timeout: int = 8
    max_chars: int = 20000
    requires_explicit_target: bool = False
    enabled_by_default: bool = True
