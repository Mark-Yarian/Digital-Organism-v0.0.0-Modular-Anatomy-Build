class NervousSystemOrgan:
    def choose_focus(self, genome, state, observation, immune, incoming, substrate):
        h=state.hormones; novelty=min(1.0,len(observation["signals"])*.10)
        interp=substrate.get("interpretation") or substrate.get("existing_interpretation") or {}
        visibility=float(interp.get("visibility_score",0) or 0); mapped=float(interp.get("mapped_categories",0) or 0)
        scores={
            "sleep": h["fatigue"]+(.25 if state.energy<.28 else 0),
            "immune_watch": immune["threat"]+h["caution"]*.25,
            "communication": incoming["count"]*.20+h["social_pressure"]*.40+h["colony_affinity"]*.15,
            "reflection": genome.traits["reflection_depth"]*.35+state.age_ticks*.004,
            "adaptation": novelty*.40+h["curiosity"]*.20,
            "replication_check": state.energy*state.health*genome.traits["replication_urge"]*genome.drives["replicate_when_fit"],
            "observation": .20+genome.drives["observe_environment"]*.20,
            "substrate_mapping": h["substrate_attention"]*.30+genome.drives["map_substrate"]*.12+(.08 if visibility<.45 else 0)+min(mapped/10,1)*.05,
        }
        focus=max(scores, key=scores.get); state.current_focus=focus; return focus
