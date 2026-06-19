import random, time
from digital_organism.core.utils import clamp, read_json, short_hash, utc_now, write_json
class CommunicationOrgan:
    def process_inbox(self, rt):
        messages=[]
        for path in sorted(rt.inbox.glob("*.json")):
            msg=read_json(path,None)
            if isinstance(msg,dict):
                messages.append(msg); sender=msg.get("from")
                if sender and sender != rt.genome.organism_id:
                    rel=rt.state.relationships.setdefault(sender, {"messages_received":0,"messages_sent":0,"affinity":.5,"first_seen":utc_now(),"last_seen":None})
                    rel["messages_received"]+=1; rel["last_seen"]=utc_now(); rel["affinity"]=round(clamp(rel["affinity"]+.015,0,1),4)
            try: path.rename(path.with_suffix(".json.consumed"))
            except Exception: pass
        rt.state.last_received_messages=len(messages)
        social=read_json(rt.memory.social, {"known_organisms": {}, "message_history": [], "relationship_summary": "none"})
        for msg in messages:
            sender=msg.get("from","unknown")
            if sender!="unknown": social["known_organisms"][sender]=rt.state.relationships.get(sender,{})
            social["message_history"].append({"ts":utc_now(),"direction":"received","from":sender,"type":msg.get("message_type","message"),"digest":short_hash(msg)})
        social["message_history"]=social["message_history"][-300:]; social["relationship_summary"]=f"known_peers={len(social['known_organisms'])}"; write_json(rt.memory.social, social)
        return {"count": len(messages), "messages": messages}
    def maybe_emit_signals(self, rt, peer_ids, focus, incoming):
        if rt.genome.scenario_role=="isolation": rt.state.last_sent_messages=0; return {"sent":0,"messages":[]}
        messages=[]; chance=rt.genome.traits["communication_openness"]*.20+rt.state.hormones["social_pressure"]*.15+rt.state.hormones["colony_affinity"]*.08
        if focus=="communication": chance += .22
        for msg in incoming["messages"]:
            if len(messages)>=2: break
            sender=msg.get("from")
            if sender and sender != rt.genome.organism_id: messages.append(rt.make_message(sender,"direct","reply",f"{rt.genome.organism_name} acknowledges signal."))
        if len(messages)<2 and random.random()<chance:
            candidates=[p for p in peer_ids if p != rt.genome.organism_id]; target="colony" if not candidates or random.random()<=.45 else random.choice(candidates)
            messages.append(rt.make_message(target, "broadcast" if target=="colony" else "direct", random.choice(["status","observation","reflection","substrate_note"]), f"{rt.genome.organism_name} reports focus={rt.state.current_focus}."))
        for msg in messages: write_json(rt.outbox/f"{int(time.time())}-{msg['message_id']}.json", msg)
        rt.state.last_sent_messages=len(messages); return {"sent": len(messages), "messages": messages}
