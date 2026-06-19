import shutil, uuid
from pathlib import Path
from typing import Optional
from digital_organism.build import BUILD
from digital_organism.colony.router import ColonyRouter
from digital_organism.core.genome import Genome
from digital_organism.core.runtime import OrganismRuntime
from digital_organism.core.state import State
from digital_organism.core.utils import append_jsonl, read_json, safe_slug, utc_now, write_json
from digital_organism.experiments.continuity_under_divergence import SCENARIO, SUBJECTS, HYPOTHESIS, pressure_for
from digital_organism.observatory.metrics import collect_metrics
from digital_organism.observatory.lineage import update_lineage
from digital_organism.observatory.signal_graph import update_signal_graph
from digital_organism.observatory.reports import generate_report

class ObservatoryRuntime:
    def __init__(self, root: Path, allow_trace=False, trace_target: Optional[str]=None, include_command_output=True):
        self.root=root.resolve(); self.organisms_dir=self.root/"organisms"; self.signal_pool=self.root/"signal_pool"; self.experiments_dir=self.root/"experiments"; self.colony_state=self.root/"colony_state.json"; self.router=ColonyRouter(self.root)
        self.organisms_dir.mkdir(parents=True, exist_ok=True); self.signal_pool.mkdir(parents=True, exist_ok=True); self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.allow_trace=allow_trace; self.trace_target=trace_target; self.include_command_output=include_command_output
    def experiment_init(self, scenario=SCENARIO, force=False):
        if scenario != SCENARIO: raise ValueError(f"Only scenario currently implemented: {SCENARIO}")
        if force and self.root.exists():
            for child in self.root.iterdir():
                shutil.rmtree(child) if child.is_dir() else child.unlink()
            self.organisms_dir.mkdir(parents=True, exist_ok=True); self.signal_pool.mkdir(parents=True, exist_ok=True); self.experiments_dir.mkdir(parents=True, exist_ok=True); self.router=ColonyRouter(self.root)
        colony_id="col-"+uuid.uuid4().hex[:12]; write_json(self.colony_state, {"build":BUILD,"colony_id":colony_id,"created_at":utc_now(),"colony_ticks":0,"scenario":scenario})
        created=[]
        for name,role in SUBJECTS:
            org_root=self.organisms_dir/safe_slug(name); org_root.mkdir(parents=True, exist_ok=True)
            genome=Genome.seed(name=name, colony_id=colony_id, scenario_role=role); write_json(org_root/"genome.json", genome.to_dict()); write_json(org_root/"state.json", State().to_dict())
            rt=OrganismRuntime(org_root); append_jsonl(rt.memory.episodic, {"event_type":"birth","payload":{"scenario_role":role,"colony_id":colony_id,"build":BUILD}})
            created.append({"name":name,"slug":safe_slug(name),"organism_id":genome.organism_id,"scenario_role":role,"lineage_id":genome.lineage_id})
        exp_root=self.experiments_dir/scenario; exp_root.mkdir(parents=True, exist_ok=True); write_json(exp_root/"config.json", {"build":BUILD,"experiment_id":"exp-"+uuid.uuid4().hex[:12],"scenario":scenario,"created_at":utc_now(),"hypothesis":HYPOTHESIS,"subjects":created}); (exp_root/"metrics.jsonl").write_text("", encoding="utf-8"); write_json(exp_root/"lineage.json",{"lineages":{}}); write_json(exp_root/"signal_graph.json",{"nodes":[],"edges":[]})
        return {"initialized":True,"root":str(self.root),"colony_id":colony_id,"created":created}
    def experiment_run(self, scenario=SCENARIO, rounds=25):
        exp_root=self.experiments_dir/scenario
        if not exp_root.exists(): raise ValueError("Experiment not initialized. Run experiment-init first.")
        state=read_json(self.colony_state,{})
        summaries=[]
        for _ in range(rounds):
            tick=int(state.get("colony_ticks",0))+1; pre=self.router.route(tick); organisms=self.router.discover(); peer_ids=list(organisms.keys()); metrics=[]
            for oid,entry in sorted(organisms.items(), key=lambda x: x[1]["slug"]):
                rt=OrganismRuntime(entry["path"], self.allow_trace, self.trace_target, self.include_command_output)
                result=rt.tick(colony_tick=tick, pressure=pressure_for(rt.genome.scenario_role,tick), peer_ids=peer_ids)
                m=collect_metrics(result, entry["path"], scenario); append_jsonl(exp_root/"metrics.jsonl", m); metrics.append(m)
            post=self.router.route(tick); state["colony_ticks"]=tick; state["last_tick"]=utc_now(); state["last_route"]={"pre":pre,"post":post}; write_json(self.colony_state,state); update_lineage(exp_root, organisms); update_signal_graph(self.root, exp_root, organisms)
            summaries.append({"colony_tick":tick,"organisms":len(metrics),"messages_routed":pre["routed_count"]+post["routed_count"],"mutations":sum(1 for m in metrics if m["mutation_happened"]),"identity_failures":sum(1 for m in metrics if not m["identity_stable"])})
        return {"ran":True,"scenario":scenario,"rounds":rounds,"last_round":summaries[-1] if summaries else None}
    def experiment_report(self, scenario=SCENARIO): return generate_report(self.experiments_dir/scenario, scenario)
    def status(self):
        organisms=self.router.discover(); roster=[]
        for oid,e in organisms.items():
            st=read_json(e["path"]/"state.json",{}); roster.append({"slug":e["slug"],"name":e["name"],"organism_id":oid,"scenario_role":e["genome"].get("scenario_role"),"age_ticks":st.get("age_ticks"),"focus":st.get("current_focus"),"energy":st.get("energy"),"health":st.get("health"),"stress":st.get("stress")})
        return {"build":BUILD,"colony_state":read_json(self.colony_state,{}),"organisms":roster}
