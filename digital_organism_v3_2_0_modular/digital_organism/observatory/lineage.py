from digital_organism.core.utils import read_json, utc_now, write_json
def update_lineage(exp_root, organisms):
    lineages={}
    for oid,entry in organisms.items():
        g=entry["genome"]; lin=g.get("lineage_id"); lineages.setdefault(lin,{"members":[]})
        lineages[lin]["members"].append({"organism_id":oid,"name":g.get("organism_name"),"parent_id":g.get("parent_id"),"generation":g.get("generation"),"scenario_role":g.get("scenario_role")})
    write_json(exp_root/"lineage.json", {"updated_at": utc_now(), "lineages": lineages})
