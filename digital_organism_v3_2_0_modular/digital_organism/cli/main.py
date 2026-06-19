import argparse, json, time
from pathlib import Path
from typing import List, Optional
from digital_organism.build import BUILD
from digital_organism.core.genome import Genome
from digital_organism.core.state import State
from digital_organism.core.runtime import OrganismRuntime
from digital_organism.core.utils import append_jsonl, write_json
from digital_organism.observatory.runtime import ObservatoryRuntime
from digital_organism.substrate.mapper import SubstrateMappingOrgan

def cmd_version(args): print(json.dumps(BUILD, indent=2)); return 0
def cmd_init(args):
    root=Path(args.root); root.mkdir(parents=True, exist_ok=True)
    if (root/"genome.json").exists() and not args.force: print(json.dumps({"initialized":False,"reason":"genome_exists_use_force","root":str(root)},indent=2)); return 0
    genome=Genome.seed(name=args.name, scenario_role=args.scenario_role); write_json(root/"genome.json", genome.to_dict()); write_json(root/"state.json", State().to_dict())
    rt=OrganismRuntime(root); append_jsonl(rt.memory.episodic, {"event_type":"birth","payload":{"message":"Organism initialized.","build":BUILD}})
    print(json.dumps({"initialized":True,"root":str(root),"organism_id":genome.organism_id,"lineage_id":genome.lineage_id,"name":genome.organism_name,"scenario_role":genome.scenario_role,"build":BUILD},indent=2)); return 0
def cmd_run(args):
    rt=OrganismRuntime(Path(args.root), args.allow_trace, args.trace_target, not args.no_command_output)
    print(json.dumps({"boot":{"build":BUILD,"organism_id":rt.genome.organism_id,"name":rt.genome.organism_name,"lineage_id":rt.genome.lineage_id}}, indent=2))
    for _ in range(args.ticks):
        r=rt.tick(); print(json.dumps({"tick":r["organism_tick"],"focus":r["focus"],"energy":r["state"]["energy"],"health":r["state"]["health"],"stress":r["state"]["stress"],"substrate_maps":r["state"]["substrate_map_count"],"mutation":r["mutation"],"reproduction":r["reproduction"]}, indent=2))
        if args.delay>0: time.sleep(args.delay)
    return 0
def cmd_status(args): print(json.dumps(OrganismRuntime(Path(args.root)).status(), indent=2)); return 0
def cmd_message(args):
    rt=OrganismRuntime(Path(args.root)); msg=rt.make_message(rt.genome.organism_id,"direct","manual_local_message",args.text); write_json(rt.inbox/f"{int(time.time())}-{msg['message_id']}.json", msg); print(json.dumps({"written":True,"path":str(rt.inbox),"message_id":msg["message_id"]}, indent=2)); return 0
def cmd_substrate_map(args):
    rt=OrganismRuntime(Path(args.root), args.allow_trace, args.trace_target, not args.no_command_output); mapper=SubstrateMappingOrgan(rt.root, rt.memory.memory_dir, args.allow_trace, args.trace_target, not args.no_command_output); result=mapper.map_substrate("manual_cli_substrate_map")
    print(json.dumps({"mapped":True,"build":BUILD,"os_family":result["os_profile"]["os_family"],"visibility_score":result["interpretation"]["visibility_score"],"mapped_categories":result["interpretation"]["mapped_categories"],"machine_understanding":result["interpretation"]["machine_understanding"],"written_to":{"substrate_map":str(mapper.substrate_map_path),"capabilities":str(mapper.substrate_capabilities_path),"commands":str(mapper.substrate_commands_path),"errors":str(mapper.substrate_errors_path)}},indent=2)); return 0
def cmd_experiment_init(args): print(json.dumps(ObservatoryRuntime(Path(args.root), args.allow_trace, args.trace_target, not args.no_command_output).experiment_init(args.scenario, args.force), indent=2)); return 0
def cmd_experiment_run(args): print(json.dumps(ObservatoryRuntime(Path(args.root), args.allow_trace, args.trace_target, not args.no_command_output).experiment_run(args.scenario, args.rounds), indent=2)); return 0
def cmd_experiment_report(args): print(json.dumps(ObservatoryRuntime(Path(args.root)).experiment_report(args.scenario), indent=2)); return 0
def cmd_observatory_status(args): print(json.dumps(ObservatoryRuntime(Path(args.root)).status(), indent=2)); return 0

def build_parser():
    parser=argparse.ArgumentParser(description="Digital Organism v3.2.0"); parser.add_argument("--version", action="store_true"); sub=parser.add_subparsers(dest="command")
    p=sub.add_parser("init"); p.add_argument("--root",default="./habitat"); p.add_argument("--name",default="Seed Cell"); p.add_argument("--scenario-role",default="general"); p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_init)
    p=sub.add_parser("run"); p.add_argument("--root",default="./habitat"); p.add_argument("--ticks",type=int,default=5); p.add_argument("--delay",type=float,default=0.0); p.add_argument("--allow-trace",action="store_true"); p.add_argument("--trace-target",default=None); p.add_argument("--no-command-output",action="store_true"); p.set_defaults(func=cmd_run)
    p=sub.add_parser("status"); p.add_argument("--root",default="./habitat"); p.set_defaults(func=cmd_status)
    p=sub.add_parser("message"); p.add_argument("--root",default="./habitat"); p.add_argument("text"); p.set_defaults(func=cmd_message)
    p=sub.add_parser("substrate-map"); p.add_argument("--root",default="./habitat"); p.add_argument("--allow-trace",action="store_true"); p.add_argument("--trace-target",default=None); p.add_argument("--no-command-output",action="store_true"); p.set_defaults(func=cmd_substrate_map)
    p=sub.add_parser("experiment-init"); p.add_argument("--root",default="./ecosystem"); p.add_argument("--scenario",default="continuity_under_divergence"); p.add_argument("--force",action="store_true"); p.add_argument("--allow-trace",action="store_true"); p.add_argument("--trace-target",default=None); p.add_argument("--no-command-output",action="store_true"); p.set_defaults(func=cmd_experiment_init)
    p=sub.add_parser("experiment-run"); p.add_argument("--root",default="./ecosystem"); p.add_argument("--scenario",default="continuity_under_divergence"); p.add_argument("--rounds",type=int,default=25); p.add_argument("--allow-trace",action="store_true"); p.add_argument("--trace-target",default=None); p.add_argument("--no-command-output",action="store_true"); p.set_defaults(func=cmd_experiment_run)
    p=sub.add_parser("experiment-report"); p.add_argument("--root",default="./ecosystem"); p.add_argument("--scenario",default="continuity_under_divergence"); p.set_defaults(func=cmd_experiment_report)
    p=sub.add_parser("observatory-status"); p.add_argument("--root",default="./ecosystem"); p.set_defaults(func=cmd_observatory_status)
    return parser
def main(argv: Optional[List[str]]=None):
    parser=build_parser(); args=parser.parse_args(argv)
    if args.version: return cmd_version(args)
    if not hasattr(args,"func"): parser.print_help(); return 0
    return args.func(args)
