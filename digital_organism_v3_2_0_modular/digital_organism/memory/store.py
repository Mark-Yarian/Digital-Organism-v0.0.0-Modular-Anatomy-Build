from pathlib import Path
from typing import Any, Dict, Optional
from digital_organism.core.utils import append_jsonl, load_jsonl, read_json, utc_now, write_json

class MemoryStore:
    def __init__(self, root: Path):
        self.root=root; self.memory_dir=root/"memory"; self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.episodic=self.memory_dir/"episodic.jsonl"; self.semantic=self.memory_dir/"semantic.json"
        self.social=self.memory_dir/"social.json"; self.reflective=self.memory_dir/"reflective.json"
        self.immune=self.memory_dir/"immune.json"; self.birth_snapshot=self.memory_dir/"birth_snapshot.json"

    def bootstrap(self, genome, state):
        if not self.birth_snapshot.exists(): write_json(self.birth_snapshot, {"created_at": utc_now(), "genome": genome.to_dict(), "state": state.to_dict()})
        if not self.semantic.exists(): write_json(self.semantic, {"known_patterns": [], "last_meaning": None, "habitat_summary": {}, "substrate_summary": {}})
        if not self.social.exists(): write_json(self.social, {"known_organisms": {}, "message_history": [], "relationship_summary": "none"})
        if not self.reflective.exists(): write_json(self.reflective, {"recent_reflections": [], "current_narrative": "not reflected yet"})
        if not self.immune.exists(): write_json(self.immune, {"integrity_checks": [], "threat_history": []})

    def episode(self, event_type: str, payload: Dict[str, Any]): append_jsonl(self.episodic, {"event_type": event_type, "payload": payload})
    def recent_episodes(self, limit: Optional[int]=5): return load_jsonl(self.episodic, limit=limit)
