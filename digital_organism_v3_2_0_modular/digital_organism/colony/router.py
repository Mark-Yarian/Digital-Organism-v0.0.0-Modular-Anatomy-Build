from pathlib import Path
from typing import Any, Dict
import time
from digital_organism.core.utils import append_jsonl, read_json, utc_now, write_json

class ColonyRouter:
    def __init__(self, ecosystem_root: Path):
        self.root=ecosystem_root.resolve(); self.organisms_dir=self.root/"organisms"; self.signal_pool=self.root/"signal_pool"; self.router_log=self.root/"router_log.jsonl"
        self.organisms_dir.mkdir(parents=True, exist_ok=True); self.signal_pool.mkdir(parents=True, exist_ok=True)
    def discover(self) -> Dict[str, Dict[str, Any]]:
        result={}
        for path in sorted(self.organisms_dir.iterdir()) if self.organisms_dir.exists() else []:
            if not path.is_dir(): continue
            genome=read_json(path/"genome.json",{}); oid=genome.get("organism_id")
            if oid: result[oid]={"slug":path.name,"path":path,"genome":genome,"name":genome.get("organism_name",path.name)}
        return result
    def route(self, colony_tick:int):
        organisms=self.discover(); by_slug={v["slug"]:oid for oid,v in organisms.items()}; routed=[]; dropped=[]
        for sender_id,sender in organisms.items():
            outbox=sender["path"]/"outbox"; routed_dir=outbox/"routed"; routed_dir.mkdir(parents=True, exist_ok=True)
            for msg_path in sorted(outbox.glob("*.json")):
                msg=read_json(msg_path,None)
                if not isinstance(msg,dict): dropped.append({"path":str(msg_path),"reason":"invalid"}); self.archive_message(msg_path,routed_dir); continue
                target=msg.get("to"); audience=msg.get("audience","direct")
                recipients=[oid for oid in organisms if oid != sender_id] if audience=="broadcast" or target=="colony" else ([target] if target in organisms else ([by_slug[target]] if target in by_slug else []))
                if not recipients: dropped.append({"message_id":msg.get("message_id"),"reason":"no_recipient","to":target}); self.archive_message(msg_path,routed_dir); continue
                for rid in recipients:
                    delivered=dict(msg); delivered.update({"ttl": int(delivered.get("ttl",10))-1, "routed_at": utc_now(), "colony_tick": colony_tick, "recipient_id": rid})
                    inbox=organisms[rid]["path"]/"inbox"; inbox.mkdir(parents=True, exist_ok=True); write_json(inbox/f"{colony_tick}-{msg.get('message_id')}-from-{sender_id[:8]}.json", delivered)
                    routed.append({"from":sender_id,"to":rid,"type":msg.get("message_type","message"),"audience":audience,"message_id":msg.get("message_id")})
                write_json(self.signal_pool/f"{colony_tick}-{sender_id[:8]}-{msg.get('message_id')}.json", msg); self.archive_message(msg_path,routed_dir)
        summary={"ts":utc_now(),"colony_tick":colony_tick,"routed_count":len(routed),"dropped_count":len(dropped),"routed":routed,"dropped":dropped}; append_jsonl(self.router_log, summary); return summary
    def archive_message(self,path,routed_dir):
        try:
            target=routed_dir/path.name
            if target.exists(): target=routed_dir/f"{int(time.time())}-{path.name}"
            path.rename(target)
        except Exception: pass
