from digital_organism.core.utils import clamp, read_json, stable_hash, utc_now, write_json
class ImmuneOrgan:
    def __init__(self, memory): self.memory=memory
    def check(self, genome, state, observation):
        actual=stable_hash({"organism_id": genome.organism_id, "lineage_id": genome.lineage_id, "created_at": genome.created_at})
        stable = actual == genome.identity_hash; threat=0.0 if stable else .60
        threat += float(observation["pressure"].get("immune_pressure",0.0))*genome.traits["immune_sensitivity"]; threat=clamp(threat,0,1)
        state.identity_stable=stable
        mem=read_json(self.memory.immune, {"integrity_checks": [], "threat_history": []})
        mem["integrity_checks"].append({"ts": utc_now(), "identity_stable": stable, "threat": threat}); mem["threat_history"].append(threat)
        mem["integrity_checks"]=mem["integrity_checks"][-300:]; mem["threat_history"]=mem["threat_history"][-300:]; write_json(self.memory.immune, mem)
        return {"identity_stable": stable, "threat": round(threat,4)}
