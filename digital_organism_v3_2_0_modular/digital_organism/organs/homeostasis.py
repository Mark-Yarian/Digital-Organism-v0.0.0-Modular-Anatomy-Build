from digital_organism.core.utils import clamp
class HomeostasisOrgan:
    def regulate(self, genome, state):
        interventions=[]
        if state.energy < genome.traits["sleep_threshold"]:
            state.energy=clamp(state.energy+.20,0,1); state.stress=clamp(state.stress-.08,0,1); interventions.append("sleep_recovery")
        if state.stress>.72:
            state.stress=clamp(state.stress-.12,0,1); state.energy=clamp(state.energy-.04,0,1); interventions.append("stress_dampening")
        return {"interventions": interventions}
