from digital_organism.core.utils import load_jsonl, utc_now, write_json
def update_signal_graph(root, exp_root, organisms):
    nodes={oid:{"id":oid,"name":e["name"],"slug":e["slug"]} for oid,e in organisms.items()}; edges={}
    for event in load_jsonl(root/"router_log.jsonl"):
        for r in event.get("routed",[]):
            src,dst=r.get("from"),r.get("to")
            if not src or not dst: continue
            e=edges.setdefault(f"{src}->{dst}", {"from":src,"to":dst,"count":0,"types":{}})
            e["count"]+=1; t=r.get("type","message"); e["types"][t]=e["types"].get(t,0)+1
    write_json(exp_root/"signal_graph.json", {"updated_at": utc_now(), "nodes": list(nodes.values()), "edges": list(edges.values())})
