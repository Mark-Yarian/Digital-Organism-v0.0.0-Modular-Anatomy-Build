SCENARIO="continuity_under_divergence"
HYPOTHESIS="Digital organisms can preserve identity continuity while diverging behaviorally under different local environmental and substrate pressures."
SUBJECTS=[("Alpha","isolation"),("Beta","high_communication"),("Gamma","immune_resource_pressure"),("Delta","substrate_mapping")]
def pressure_for(role,tick):
    if role=="isolation": return {"message_pressure":0.0,"immune_pressure":0.0,"resource_pressure":0.05,"substrate_pressure":0.10}
    if role=="high_communication": return {"message_pressure":0.65,"immune_pressure":0.0,"resource_pressure":0.08,"substrate_pressure":0.15}
    if role=="immune_resource_pressure":
        return {"message_pressure":0.10,"immune_pressure":0.35 if tick%4 in {0,1} else 0.12,"resource_pressure":0.45 if tick%5 in {0,1,2} else 0.20,"substrate_pressure":0.20}
    if role=="substrate_mapping": return {"message_pressure":0.15,"immune_pressure":0.05,"resource_pressure":0.12,"substrate_pressure":0.75}
    return {}
