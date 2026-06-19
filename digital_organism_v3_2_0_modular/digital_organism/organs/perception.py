class PerceptionOrgan:
    def __init__(self, root, memory_dir):
        self.root=root; self.memory_dir=memory_dir; self.inbox=root/"inbox"
    def sense(self, pressure):
        files=list(self.root.rglob("*")); file_count=sum(1 for p in files if p.is_file()); dir_count=sum(1 for p in files if p.is_dir()); total=0
        for p in files:
            try:
                if p.is_file(): total += p.stat().st_size
            except Exception: pass
        signals=["genome_present","memory_present"]
        if any(self.inbox.glob("*.json")): signals.append("colony_message_present")
        if (self.memory_dir/"substrate_map.json").exists(): signals.append("substrate_map_present")
        for k,s in [("message_pressure","message_pressure"),("immune_pressure","immune_pressure"),("resource_pressure","resource_pressure"),("substrate_pressure","substrate_pressure")]:
            if pressure.get(k,0)>0: signals.append(s)
        return {"file_count": file_count, "dir_count": dir_count, "total_size_bytes": total, "signals": signals, "pressure": pressure}
