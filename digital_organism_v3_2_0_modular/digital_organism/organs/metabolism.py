from digital_organism.core.utils import clamp, read_json, utc_now, write_json
class MetabolismOrgan:
    def metabolize(self, genome, state, memory, observation, immune, incoming, focus, substrate):
        p=observation["pressure"]; h=state.hormones
        ed=.020+.020*h["curiosity"]-.030*p.get("resource_pressure",0)-.025*h["urgency"]-.020*h["fatigue"]
        sd=.035*immune["threat"]+.020*p.get("resource_pressure",0)+.012*incoming["count"]-.018*h["confidence"]
        hd=.010-state.stress*.010-immune["threat"]*.020
        if focus=="sleep": ed+=.12; sd-=.08
        elif focus=="communication": ed-=.015
        elif focus=="reflection": ed-=.010
        elif focus=="immune_watch": ed-=.014
        elif focus=="substrate_mapping": ed-=.018
        state.energy=clamp(state.energy+ed,0,1); state.stress=clamp(state.stress+sd,0,1); state.health=clamp(state.health+hd,0,1)
        meaning="stable bounded observation"
        if incoming["count"]>0: meaning="colony signals changed social memory"
        if immune["threat"]>.35: meaning="immune pressure favored caution"
        if p.get("resource_pressure",0)>.3: meaning="resource pressure favored compression"
        if focus=="substrate_mapping": meaning="machine substrate mapping influenced organism focus"
        sem=read_json(memory.semantic, {"known_patterns": [], "last_meaning": None, "habitat_summary": {}, "substrate_summary": {}})
        for sig in observation["signals"]:
            if sig not in sem["known_patterns"]: sem["known_patterns"].append(sig)
        sem["last_meaning"]=meaning; sem["habitat_summary"]={"updated_at": utc_now(), "file_count": observation["file_count"], "dir_count": observation["dir_count"], "signals": observation["signals"], "focus": focus}
        sem["known_patterns"]=sem["known_patterns"][-300:]; write_json(memory.semantic, sem)
        return {"energy_delta": round(ed,4), "stress_delta": round(sd,4), "health_delta": round(hd,4), "meaning": meaning}
