from digital_organism.core.utils import load_jsonl, read_json, utc_now, write_json
def conclusion_from(summaries):
    identity_ok=all(s["identity_failures"]==0 for s in summaries)
    if identity_ok: return "Identity continuity was preserved while behavioral, social, and/or substrate-awareness divergence emerged."
    return "Identity instability occurred; experiment conditions or integrity checks should be reviewed."
def generate_report(exp_root, scenario):
    metrics=load_jsonl(exp_root/"metrics.jsonl")
    if not metrics: raise ValueError("No metrics found. Run experiment-run first.")
    by={}
    for m in metrics: by.setdefault(m["organism_id"],[]).append(m)
    summaries=[]
    for oid,rows in by.items():
        first,last=rows[0],rows[-1]; focus={}
        for r in rows: focus[r["focus"]]=focus.get(r["focus"],0)+1
        summaries.append({"organism_id":oid,"name":first["name"],"scenario_role":first["scenario_role"],"ticks":len(rows),"identity_failures":sum(1 for r in rows if not r["identity_stable"]),"avg_stress":round(sum(r["stress"] for r in rows)/len(rows),4),"end_health":last["health"],"total_messages_received":sum(r["messages_received"] for r in rows),"total_messages_sent":sum(r["messages_sent"] for r in rows),"known_peers":last["known_peers"],"mutation_count":last["mutation_count"],"reflection_count":last["reflection_count"],"substrate_map_count":last.get("substrate_map_count",0),"substrate_os_family":last.get("substrate_os_family"),"substrate_visibility_score":last.get("substrate_visibility_score"),"final_trait_drift":last["trait_drift"],"focus_counts":focus})
    md=["# Digital Organism v3.2.0 Observatory Report","",f"Scenario: `{scenario}`","","## Metrics","", "| Organism | Role | Identity Failures | Avg Stress | End Health | Msg In | Msg Out | Known Peers | Mutations | Reflections | Substrate Maps | OS | Visibility | Trait Drift |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|"]
    for s in summaries: md.append(f"| {s['name']} | {s['scenario_role']} | {s['identity_failures']} | {s['avg_stress']} | {s['end_health']} | {s['total_messages_received']} | {s['total_messages_sent']} | {s['known_peers']} | {s['mutation_count']} | {s['reflection_count']} | {s['substrate_map_count']} | {s.get('substrate_os_family')} | {s.get('substrate_visibility_score')} | {s['final_trait_drift']} |")
    md += ["","## Conclusion","", conclusion_from(summaries), ""]
    report_path=exp_root/"final_report.md"; report_path.write_text("\n".join(md), encoding="utf-8")
    drift={"scenario":scenario,"generated_at":utc_now(),"total_metric_rows":len(metrics),"summaries":summaries,"identity_failures_total":sum(s["identity_failures"] for s in summaries),"conclusion":conclusion_from(summaries)}
    write_json(exp_root/"drift_report.json", drift)
    return {"report_created": True, "report_path": str(report_path), "drift_report_path": str(exp_root/"drift_report.json")}
