from __future__ import annotations
import dataclasses, uuid
from typing import Any, Dict, Optional
from digital_organism.build import BUILD
from digital_organism.core.utils import stable_hash, utc_now

BASE_TRAITS = {
    "curiosity": .70, "caution": .66, "compression_bias": .56,
    "novelty_sensitivity": .62, "replication_urge": .14, "sleep_threshold": .22,
    "mutation_rate": .07, "memory_selectivity": .60, "immune_sensitivity": .74,
    "communication_openness": .48, "reflection_depth": .58, "social_selectivity": .44,
    "signal_generosity": .44, "substrate_sensitivity": .62, "forensic_curiosity": .66,
}
BASE_DRIVES = {
    "preserve_identity": 1.0, "observe_environment": .86, "compress_experience": .68,
    "adapt_behavior": .58, "replicate_when_fit": .18, "avoid_boundary_violation": 1.0,
    "maintain_homeostasis": .92, "communicate_locally": .52, "reflect_on_experience": .62,
    "participate_in_colony": .56, "map_substrate": .76,
}
BASE_PERMISSIONS = {
    "can_read_habitat": True, "can_write_memory": True, "can_mutate_traits": True,
    "can_replicate": True, "can_read_local_inbox": True, "can_write_local_outbox": True,
    "can_use_colony_router": True, "can_profile_machine_state": True,
    "can_profile_processes": True, "can_profile_network_state": True,
    "can_run_read_only_os_commands": True, "can_run_trace_commands": False,
    "can_capture_process_cmdline": False, "can_scan_user_files": False,
    "can_collect_credentials": False, "can_modify_machine_state": False,
    "can_access_network": False, "can_execute_child": False,
    "can_read_outside_habitat": False, "can_modify_source_code": False,
}

@dataclasses.dataclass
class Genome:
    organism_name: str
    organism_id: str
    lineage_id: str
    generation: int
    parent_id: Optional[str]
    created_at: str
    role: str
    colony_id: Optional[str]
    scenario_role: str
    traits: Dict[str, float]
    drives: Dict[str, float]
    permissions: Dict[str, bool]
    identity_hash: str
    build: Dict[str, Any]

    @staticmethod
    def seed(name="Seed Cell", colony_id=None, scenario_role="general", parent_id=None, lineage_id=None, generation=0):
        oid = "org-" + uuid.uuid4().hex[:12]
        created = utc_now()
        lin = lineage_id or "lin-" + uuid.uuid4().hex[:12]
        traits, drives, permissions = dict(BASE_TRAITS), dict(BASE_DRIVES), dict(BASE_PERMISSIONS)
        if scenario_role == "isolation":
            traits.update({"communication_openness": .22, "social_selectivity": .78, "reflection_depth": .65})
        elif scenario_role == "high_communication":
            traits.update({"communication_openness": .78, "signal_generosity": .72})
            drives.update({"communicate_locally": .78, "participate_in_colony": .82})
        elif scenario_role == "immune_resource_pressure":
            traits.update({"caution": .78, "immune_sensitivity": .86, "compression_bias": .68})
        elif scenario_role == "substrate_mapping":
            traits.update({"substrate_sensitivity": .82, "forensic_curiosity": .82})
            drives.update({"map_substrate": .90})
        identity_hash = stable_hash({"organism_id": oid, "lineage_id": lin, "created_at": created})
        return Genome(name, oid, lin, generation, parent_id, created,
                      "experiment_subject" if scenario_role != "general" else "seed_observer",
                      colony_id, scenario_role, traits, drives, permissions, identity_hash, BUILD)

    @staticmethod
    def from_dict(data):
        data=dict(data); data.setdefault("colony_id", None); data.setdefault("scenario_role","general"); data.setdefault("build", BUILD)
        traits=dict(BASE_TRAITS); traits.update(data.get("traits") or {}); data["traits"]=traits
        drives=dict(BASE_DRIVES); drives.update(data.get("drives") or {}); data["drives"]=drives
        perms=dict(BASE_PERMISSIONS); perms.update(data.get("permissions") or {}); data["permissions"]=perms
        return Genome(**data)

    def to_dict(self): return dataclasses.asdict(self)

    def make_child(self, name=None):
        return Genome.seed(name or f"{self.organism_name} child", self.colony_id, self.scenario_role, self.organism_id, self.lineage_id, self.generation+1)
