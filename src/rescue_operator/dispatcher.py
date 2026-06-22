from __future__ import annotations
from math import hypot
from .models import Action, ActionType, GameState, Mission, VehicleStatus
from .safety import SafetyLayer

class ORToolsDispatcher:
    def __init__(self, safety: SafetyLayer): self.safety=safety
    def priority(self, state: GameState, mission: Mission, vehicle_ids: list[str]) -> float:
        travel=min((self._travel(state, mission, vid) for vid in vehicle_ids), default=30)
        deadline=max(0, (30-mission.deadline_minutes)/30)
        coverage_loss=len(vehicle_ids)/max(1, sum(1 for v in state.vehicles.values() if v.status is VehicleStatus.AVAILABLE))
        wear=sum(1-state.vehicles[v].condition for v in vehicle_ids if v in state.vehicles)
        return mission.patient_risk*10+mission.escalation_risk*8+deadline*7+5+mission.reward/100*2-travel*4-coverage_loss*6-wear*2
    def plan(self, state: GameState) -> list[Action]:
        actions=[]; used=set()
        missions=sorted([m for m in state.missions.values() if not m.completed and not m.failed], key=lambda m: (-m.patient_risk, -m.escalation_risk, m.deadline_minutes))
        for m in missions:
            candidates=[v.id for v in state.vehicles.values() if v.status is VehicleStatus.AVAILABLE and v.id not in used]
            # Prefer vehicles that directly satisfy mission modules, then travel time.
            ranked=sorted(candidates, key=lambda vid: (not bool(m.required_modules & state.vehicles[vid].modules), self._travel(state,m,vid)))
            for n in range(m.min_vehicles, len(ranked)+1):
                a=Action(type=ActionType.DISPATCH, mission_id=m.id, vehicle_ids=ranked[:n])
                ok,_=self.safety.validate(state,a)
                if ok: actions.append(a); used.update(a.vehicle_ids); break
        return actions or [Action(type=ActionType.NOOP)]
    def _travel(self,state:GameState,m:Mission,vid:str)->float:
        v=state.vehicles[vid]; s=state.stations[v.station_id]; return hypot(s.x-m.x,s.y-m.y)
