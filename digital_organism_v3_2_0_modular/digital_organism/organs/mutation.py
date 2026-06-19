import random
from digital_organism.core.genome import BASE_TRAITS
from digital_organism.core.utils import clamp, write_json
class MutationOrgan:
    def maybe_mutate(self, rt, observation, immune, focus):
        if not rt.genome.permissions.get("can_mutate_traits", False): return {"mutated": False, "reason": "disabled"}
        pressure=immune["threat"]*.25+rt.state.stress*.20+rt.state.hormones["social_pressure"]*.10+rt.state.hormones["substrate_attention"]*.08+(.15 if focus in {"adaptation","immune_watch","communication","substrate_mapping"} else 0)
        chance=clamp(rt.genome.traits["mutation_rate"]+pressure*.10,0,.24)
        if random.random()>chance: return {"mutated": False, "pressure": round(pressure,4), "chance": round(chance,4)}
        trait=random.choice(list(BASE_TRAITS.keys())); old=rt.genome.traits[trait]; delta=random.uniform(-.04,.04)
        if trait in {"caution","immune_sensitivity"} and immune["threat"]>.2: delta=abs(delta)
        if trait=="compression_bias" and observation["pressure"].get("resource_pressure",0)>.2: delta=abs(delta)
        if trait=="replication_urge" and rt.state.stress>.35: delta=-abs(delta)
        if trait in {"substrate_sensitivity","forensic_curiosity"} and focus=="substrate_mapping": delta=abs(delta)*.6
        new=clamp(old+delta,0,1); rt.genome.traits[trait]=round(new,4); rt.state.mutation_count+=1; write_json(rt.genome_path, rt.genome.to_dict())
        return {"mutated": True, "trait": trait, "old": round(old,4), "new": round(new,4), "delta": round(new-old,4), "pressure": round(pressure,4)}
