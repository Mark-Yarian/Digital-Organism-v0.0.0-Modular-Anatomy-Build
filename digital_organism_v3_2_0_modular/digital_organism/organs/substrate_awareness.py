from digital_organism.core.utils import read_json, utc_now, write_json
class SubstrateAwarenessOrgan:
    def __init__(self, runtime): self.runtime=runtime
    def map_if_needed(self, reason="scheduled_tick"):
        rt=self.runtime
        if not rt.genome.permissions.get("can_run_read_only_os_commands", False):
            return {"enabled": False, "reason": "substrate_mapping_permission_disabled"}
        should = (not rt.substrate_mapper.substrate_map_path.exists()) or rt.state.age_ticks % 5 == 0 or rt.state.current_focus == "substrate_mapping"
        if not should:
            existing=read_json(rt.substrate_mapper.substrate_map_path,{})
            return {"enabled": True, "mapped_this_tick": False, "existing_interpretation": existing.get("interpretation",{}), "os_profile": existing.get("os_profile",{})}
        result=rt.substrate_mapper.map_substrate(reason=reason); rt.state.substrate_map_count += 1
        sem=read_json(rt.memory.semantic, {"known_patterns": [], "last_meaning": None, "habitat_summary": {}, "substrate_summary": {}})
        sem["substrate_summary"]={"updated_at": utc_now(), "os_family": result["os_profile"].get("os_family"), "visibility_score": result["interpretation"].get("visibility_score"), "mapped_categories": result["interpretation"].get("mapped_categories"), "machine_understanding": result["interpretation"].get("machine_understanding")}
        write_json(rt.memory.semantic, sem)
        return {"enabled": True, "mapped_this_tick": True, "os_profile": result.get("os_profile",{}), "capabilities": result.get("capabilities",{}), "interpretation": result.get("interpretation",{})}
