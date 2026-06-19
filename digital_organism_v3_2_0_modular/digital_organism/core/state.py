from __future__ import annotations
import dataclasses
from typing import Any, Dict

@dataclasses.dataclass
class State:
    energy: float = .58
    health: float = .88
    stress: float = .10
    age_ticks: int = 0
    colony_ticks_observed: int = 0
    current_focus: str = "orientation"
    last_action: str = "birth"
    last_received_messages: int = 0
    last_sent_messages: int = 0
    mutation_count: int = 0
    reproduction_count: int = 0
    reflection_count: int = 0
    substrate_map_count: int = 0
    identity_stable: bool = True
    hormones: Dict[str, float] = dataclasses.field(default_factory=lambda: {
        "curiosity": .50, "caution": .50, "urgency": .12, "fatigue": .10,
        "confidence": .50, "social_pressure": .05, "colony_affinity": .20,
        "substrate_attention": .22,
    })
    relationships: Dict[str, Dict[str, Any]] = dataclasses.field(default_factory=dict)

    @staticmethod
    def from_dict(data):
        defaults = dataclasses.asdict(State())
        data = data or {}; merged = defaults; merged.update(data)
        merged["hormones"] = {**defaults["hormones"], **data.get("hormones", {})}
        merged["relationships"] = {**defaults["relationships"], **data.get("relationships", {})}
        return State(**merged)

    def to_dict(self): return dataclasses.asdict(self)
