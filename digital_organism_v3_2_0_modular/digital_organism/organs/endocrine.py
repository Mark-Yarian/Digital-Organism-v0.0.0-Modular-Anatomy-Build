from digital_organism.core.utils import clamp
class EndocrineOrgan:
    def regulate(self, genome, state, observation, immune, incoming, substrate):
        h=dict(state.hormones); novelty=min(1.0,len(observation["signals"])*.10)
        interp=substrate.get("interpretation") or substrate.get("existing_interpretation") or {}
        visibility=float(interp.get("visibility_score",0) or 0); mapped=float(interp.get("mapped_categories",0) or 0)
        h["curiosity"]=clamp(h["curiosity"]*.88+novelty*.10+genome.traits["curiosity"]*.04,0,1)
        h["caution"]=clamp(h["caution"]*.84+immune["threat"]*.18+genome.traits["caution"]*.05,0,1)
        h["urgency"]=clamp(h["urgency"]*.82+state.stress*.10+immune["threat"]*.15,0,1)
        h["fatigue"]=clamp(h["fatigue"]*.80+(1-state.energy)*.15,0,1)
        h["confidence"]=clamp(h["confidence"]*.86+state.health*.10+visibility*.06,0,1)
        h["social_pressure"]=clamp(h["social_pressure"]*.76+incoming["count"]*.08+observation["pressure"].get("message_pressure",0)*.10,0,1)
        h["colony_affinity"]=clamp(h["colony_affinity"]*.90+genome.drives["participate_in_colony"]*.04+len(state.relationships)*.02,0,1)
        h["substrate_attention"]=clamp(h["substrate_attention"]*.82+genome.traits["substrate_sensitivity"]*.06+min(mapped/8,1)*.05+observation["pressure"].get("substrate_pressure",0)*.06+(0.10 if substrate.get("mapped_this_tick") else 0),0,1)
        state.hormones={k: round(v,4) for k,v in h.items()}; return state.hormones
