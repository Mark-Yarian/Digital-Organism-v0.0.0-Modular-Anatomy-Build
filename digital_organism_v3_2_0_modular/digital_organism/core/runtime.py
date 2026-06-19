from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
from digital_organism.build import BUILD
from digital_organism.core.genome import Genome
from digital_organism.core.state import State
from digital_organism.core.utils import read_json, utc_now, write_json
from digital_organism.memory.store import MemoryStore
from digital_organism.substrate.mapper import SubstrateMappingOrgan
from digital_organism.organs.perception import PerceptionOrgan
from digital_organism.organs.immune import ImmuneOrgan
from digital_organism.organs.substrate_awareness import SubstrateAwarenessOrgan
from digital_organism.organs.communication import CommunicationOrgan
from digital_organism.organs.endocrine import EndocrineOrgan
from digital_organism.organs.nervous_system import NervousSystemOrgan
from digital_organism.organs.metabolism import MetabolismOrgan
from digital_organism.organs.mutation import MutationOrgan
from digital_organism.organs.reproduction import ReproductionOrgan
from digital_organism.organs.reflection import ReflectionOrgan
from digital_organism.organs.homeostasis import HomeostasisOrgan

class OrganismRuntime:
    def __init__(self, root: Path, allow_trace=False, trace_target: Optional[str]=None, include_command_output=True):
        self.root=root.resolve(); self.root.mkdir(parents=True, exist_ok=True)
        self.genome_path=self.root/"genome.json"; self.state_path=self.root/"state.json"
        self.inbox=self.root/"inbox"; self.outbox=self.root/"outbox"; self.offspring=self.root/"offspring"
        for d in [self.inbox,self.outbox,self.offspring]: d.mkdir(parents=True, exist_ok=True)
        if not self.genome_path.exists(): write_json(self.genome_path, Genome.seed().to_dict())
        if not self.state_path.exists(): write_json(self.state_path, State().to_dict())
        self.genome=Genome.from_dict(read_json(self.genome_path,{})); self.state=State.from_dict(read_json(self.state_path,{}))
        self.memory=MemoryStore(self.root); self.memory.bootstrap(self.genome,self.state)
        self.substrate_mapper=SubstrateMappingOrgan(self.root, self.memory.memory_dir, allow_trace and self.genome.permissions.get("can_run_trace_commands",False), trace_target, include_command_output)
        self.perception=PerceptionOrgan(self.root,self.memory.memory_dir); self.immune=ImmuneOrgan(self.memory); self.substrate_awareness=SubstrateAwarenessOrgan(self)
        self.communication=CommunicationOrgan(); self.endocrine=EndocrineOrgan(); self.nervous=NervousSystemOrgan(); self.metabolism=MetabolismOrgan()
        self.mutation=MutationOrgan(); self.reproduction=ReproductionOrgan(); self.reflection=ReflectionOrgan(); self.homeostasis=HomeostasisOrgan()

    def make_message(self, to, audience, message_type, body):
        return {"message_id":"msg-"+uuid.uuid4().hex[:16],"colony_id":self.genome.colony_id,"from":self.genome.organism_id,"from_name":self.genome.organism_name,"to":to,"audience":audience,"message_type":message_type,"created_at":utc_now(),"ttl":10,"body":body}

    def tick(self, colony_tick=None, pressure: Optional[Dict[str,float]]=None, peer_ids: Optional[List[str]]=None):
        pressure=pressure or {}; peer_ids=peer_ids or []
        self.state.age_ticks += 1
        if colony_tick is not None: self.state.colony_ticks_observed=colony_tick
        observation=self.perception.sense(pressure)
        immune=self.immune.check(self.genome,self.state,observation)
        substrate=self.substrate_awareness.map_if_needed("organism_tick")
        incoming=self.communication.process_inbox(self)
        hormones=self.endocrine.regulate(self.genome,self.state,observation,immune,incoming,substrate)
        focus=self.nervous.choose_focus(self.genome,self.state,observation,immune,incoming,substrate)
        metabolism=self.metabolism.metabolize(self.genome,self.state,self.memory,observation,immune,incoming,focus,substrate)
        mutation=self.mutation.maybe_mutate(self,observation,immune,focus)
        outgoing=self.communication.maybe_emit_signals(self,peer_ids,focus,incoming)
        reflection=self.reflection.maybe_reflect(self,focus,colony_tick)
        reproduction=self.reproduction.maybe_reproduce(self,focus,immune)
        homeostasis=self.homeostasis.regulate(self.genome,self.state)
        self.state.last_action=focus; self.save()
        record={"ts":utc_now(),"build":BUILD,"colony_tick":colony_tick,"organism_tick":self.state.age_ticks,"organism_id":self.genome.organism_id,"name":self.genome.organism_name,"scenario_role":self.genome.scenario_role,"state":self.state.to_dict(),"observation":observation,"immune":immune,"substrate":substrate,"incoming":incoming,"hormones":hormones,"focus":focus,"metabolism":metabolism,"mutation":mutation,"outgoing":outgoing,"reflection":reflection,"reproduction":reproduction,"homeostasis":homeostasis}
        self.memory.episode("tick",record); return record

    def status(self):
        return {"build":BUILD,"birth_report":{"organism_name":self.genome.organism_name,"organism_id":self.genome.organism_id,"lineage_id":self.genome.lineage_id,"generation":self.genome.generation,"parent_id":self.genome.parent_id,"colony_id":self.genome.colony_id,"scenario_role":self.genome.scenario_role},"state":self.state.to_dict(),"semantic":read_json(self.memory.semantic,{}),"social":read_json(self.memory.social,{}),"reflective":read_json(self.memory.reflective,{}),"immune":read_json(self.memory.immune,{}),"substrate_capabilities":read_json(self.memory.memory_dir/"substrate_capabilities.json",{}),"recent_episodes":self.memory.recent_episodes(limit=5)}

    def save(self):
        write_json(self.genome_path,self.genome.to_dict()); write_json(self.state_path,self.state.to_dict())
