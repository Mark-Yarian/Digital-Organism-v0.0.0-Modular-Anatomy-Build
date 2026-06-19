from pathlib import Path
from typing import Any, Dict, List, Optional
import shutil, subprocess, time
from digital_organism.build import BUILD
from digital_organism.core.utils import append_jsonl, hash_value, redact_text, utc_now, write_json
from digital_organism.substrate.command_catalog import command_catalog_for
from digital_organism.substrate.command_specs import CommandSpec
from digital_organism.substrate.os_profiles import detect_os_profile
from digital_organism.substrate.safety import command_is_allowed

class SubstrateMappingOrgan:
    def __init__(self, organism_root: Path, memory_dir: Path, allow_trace=False, trace_target: Optional[str]=None, include_command_output=True):
        self.organism_root=organism_root.resolve(); self.memory_dir=memory_dir.resolve()
        self.allow_trace=allow_trace; self.trace_target=trace_target; self.include_command_output=include_command_output
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.substrate_map_path=self.memory_dir/"substrate_map.json"
        self.substrate_commands_path=self.memory_dir/"substrate_commands.jsonl"
        self.substrate_capabilities_path=self.memory_dir/"substrate_capabilities.json"
        self.substrate_errors_path=self.memory_dir/"substrate_command_errors.jsonl"

    def map_substrate(self, reason="scheduled_substrate_mapping") -> Dict[str, Any]:
        os_profile=detect_os_profile(); results=[]; errors=[]
        for spec in command_catalog_for(os_profile):
            if not spec.enabled_by_default: continue
            if spec.requires_explicit_target and not self.allow_trace:
                results.append({"name": spec.name, "category": spec.category, "intent": spec.intent, "description": spec.description, "skipped": True, "reason": "requires_explicit_trace_permission"}); continue
            command=self.prepare_command(spec)
            if not command:
                results.append({"name": spec.name, "category": spec.category, "intent": spec.intent, "description": spec.description, "skipped": True, "reason": "command_preparation_failed"}); continue
            if not command_is_allowed(command):
                err={"name": spec.name, "command": command, "reason":"blocked_by_safety_policy"}; errors.append(err)
                results.append({"name": spec.name, "category": spec.category, "intent": spec.intent, "description": spec.description, "blocked": True, "reason": "blocked_by_safety_policy"}); continue
            result=self.run_command(spec, command); results.append(result)
            if result.get("error"): errors.append({"name": spec.name, "command": command, "error": result.get("error")})
        capabilities=self.derive_capabilities(os_profile, results)
        interpretation=self.interpret(os_profile, capabilities, results)
        substrate_map={"schema":"substrate_mapping_v1","build":BUILD,"reason":reason,"captured_at":utc_now(),"os_profile":os_profile,"filesystem_layout":os_profile.get("layout",{}),"capabilities":capabilities,"interpretation":interpretation,"command_results":results}
        write_json(self.substrate_map_path, substrate_map); write_json(self.substrate_capabilities_path, capabilities)
        for r in results: append_jsonl(self.substrate_commands_path, r)
        for e in errors: append_jsonl(self.substrate_errors_path, e)
        return substrate_map

    def prepare_command(self, spec: CommandSpec):
        command=list(spec.command)
        if "{target}" in command:
            if not self.trace_target: return None
            command=[self.trace_target if p=="{target}" else p for p in command]
        return command

    def run_command(self, spec: CommandSpec, command: List[str]):
        exe=command[0]
        if not shutil.which(exe):
            return {"name": spec.name, "category": spec.category, "intent": spec.intent, "description": spec.description, "command": command, "available": False, "error": f"command_not_found:{exe}"}
        started=time.time()
        try:
            c=subprocess.run(command, capture_output=True, text=True, timeout=spec.timeout, shell=False)
            stdout=c.stdout or ""; stderr=c.stderr or ""
            result={"name": spec.name, "category": spec.category, "intent": spec.intent, "description": spec.description, "command": command, "available": True, "returncode": c.returncode, "duration_seconds": round(time.time()-started,4), "stdout_digest": hash_value(stdout), "stderr_digest": hash_value(stderr), "stdout_length": len(stdout), "stderr_length": len(stderr)}
            if self.include_command_output:
                result.update({"stdout": redact_text(stdout[:spec.max_chars]), "stderr": redact_text(stderr[:spec.max_chars]), "truncated": len(stdout)>spec.max_chars or len(stderr)>spec.max_chars})
            return result
        except subprocess.TimeoutExpired:
            return {"name": spec.name, "category": spec.category, "intent": spec.intent, "description": spec.description, "command": command, "available": True, "error": "timeout", "timeout": spec.timeout}
        except Exception as e:
            return {"name": spec.name, "category": spec.category, "intent": spec.intent, "description": spec.description, "command": command, "available": True, "error": str(e)}

    def derive_capabilities(self, os_profile, results):
        available=[r for r in results if r.get("available") and not r.get("error")]
        cats={}
        for r in available: cats.setdefault(r["category"], []).append(r["name"])
        package_managers={r["name"]: bool(r.get("available") and not r.get("error") and r.get("returncode")==0) for r in results if r.get("category")=="package_managers"}
        return {"os_family": os_profile["os_family"], "available_command_count": len(available), "categories": cats, "package_managers": package_managers, "network_mapping_available": bool(cats.get("network")), "firewall_visibility_available": bool(cats.get("firewall")), "service_visibility_available": bool(cats.get("services")), "process_visibility_available": bool(cats.get("processes")), "storage_visibility_available": bool(cats.get("storage")), "trace_available_but_gated": True}

    def interpret(self, os_profile, capabilities, results):
        total=max(len(results),1); successful=[r for r in results if r.get("available") and not r.get("error")]; errors=[r for r in results if r.get("error")]
        visibility=max(0.0,min(1.0,len(successful)/total))
        if visibility>.75: meaning=f"Strong read-only visibility into {os_profile['os_family']} substrate."
        elif visibility>.45: meaning=f"Partial read-only visibility into {os_profile['os_family']} substrate."
        else: meaning=f"Limited visibility into {os_profile['os_family']} substrate."
        return {"visibility_score": round(visibility,4), "mapped_categories": len(capabilities.get("categories",{})), "error_count": len(errors), "machine_understanding": meaning}
