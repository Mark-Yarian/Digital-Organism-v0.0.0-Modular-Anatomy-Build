from digital_organism.core.utils import load_jsonl, read_json, utc_now, write_json
class ReflectionOrgan:
    def maybe_reflect(self, rt, focus, colony_tick=None):
        if focus!="reflection" and rt.state.age_ticks % 5 != 0: return {"reflected": False}
        episodes=load_jsonl(rt.memory.episodic, limit=30); substrate=read_json(rt.memory.memory_dir/"substrate_capabilities.json", {})
        narrative=f"At organism tick {rt.state.age_ticks}, {rt.genome.organism_name} focus={rt.state.current_focus}, energy={rt.state.energy:.3f}, stress={rt.state.stress:.3f}, health={rt.state.health:.3f}, substrate_maps={rt.state.substrate_map_count}, os_family={substrate.get('os_family')}."
        reflective=read_json(rt.memory.reflective, {"recent_reflections":[],"current_narrative":""})
        reflective["recent_reflections"].append({"ts":utc_now(),"narrative":narrative,"state":rt.state.to_dict(),"recent_event_count":len(episodes)})
        reflective["recent_reflections"]=reflective["recent_reflections"][-100:]; reflective["current_narrative"]=narrative; write_json(rt.memory.reflective, reflective)
        rt.state.reflection_count+=1; return {"reflected": True, "narrative": narrative}
