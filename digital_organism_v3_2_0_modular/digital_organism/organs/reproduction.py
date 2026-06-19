from digital_organism.core.state import State
from digital_organism.core.utils import clamp, write_json
class ReproductionOrgan:
    def maybe_reproduce(self, rt, focus, immune):
        if focus!="replication_check": return {"reproduced": False, "reason": "not_replication_focus"}
        if rt.state.energy<.82 or rt.state.health<.72 or rt.state.stress>.30: return {"reproduced": False, "reason": "fitness_threshold_not_met"}
        if immune["threat"]>.18: return {"reproduced": False, "reason": "immune_caution"}
        if rt.state.reproduction_count>=1: return {"reproduced": False, "reason": "experiment_child_limit"}
        child=rt.genome.make_child(); child_root=rt.offspring/f"child-{child.organism_id}"; child_root.mkdir(parents=True, exist_ok=True)
        write_json(child_root/"genome.json", child.to_dict()); write_json(child_root/"state.json", State(energy=.45, health=.82, stress=.12).to_dict())
        (child_root/"README.md").write_text("Dormant child organism created by local digital mitosis. Not auto-executed.\n", encoding="utf-8")
        rt.state.reproduction_count+=1; rt.state.energy=clamp(rt.state.energy-.18,0,1)
        return {"reproduced": True, "child_id": child.organism_id, "child_path": str(child_root)}
