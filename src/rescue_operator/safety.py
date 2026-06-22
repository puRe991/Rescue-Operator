from __future__ import annotations
from .models import Action, ActionType, GameState, VehicleStatus
from .config import Settings

class SafetyLayer:
    def __init__(self, settings: Settings): self.settings=settings
    def validate(self, state: GameState, action: Action) -> tuple[bool, list[str]]:
        reasons=[]
        reserve=state.economy.daily_costs*self.settings.liquidity_reserve_days
        if action.type is ActionType.DISPATCH:
            mission=state.missions.get(action.mission_id or "")
            if not mission or mission.completed or mission.failed: reasons.append("mission unavailable")
            seen=set()
            for vid in action.vehicle_ids:
                v=state.vehicles.get(vid)
                if not v: reasons.append(f"vehicle {vid} missing"); continue
                if vid in seen or v.status is not VehicleStatus.AVAILABLE: reasons.append(f"vehicle {vid} already assigned")
                if len(v.crew)<v.crew_required: reasons.append(f"vehicle {vid} lacks crew")
                if v.condition<self.settings.min_vehicle_condition: reasons.append(f"vehicle {vid} condition too low")
                seen.add(vid)
            if mission:
                modules=set().union(*(state.vehicles[v].modules for v in action.vehicle_ids if v in state.vehicles)) if action.vehicle_ids else set()
                water=sum(state.vehicles[v].water for v in action.vehicle_ids if v in state.vehicles)
                air=sum(state.vehicles[v].air for v in action.vehicle_ids if v in state.vehicles)
                if not mission.required_modules <= modules: reasons.append("required modules missing")
                if water < mission.required_water: reasons.append("insufficient water reserves")
                if air < mission.required_air: reasons.append("insufficient breathing air reserves")
                if len(action.vehicle_ids)<mission.min_vehicles: reasons.append("too few vehicles")
        elif action.type in {ActionType.BUY_VEHICLE, ActionType.BUILD_STATION, ActionType.HIRE, ActionType.TRAIN}:
            cost=action.amount
            if state.economy.balance-cost<reserve: reasons.append("liquidity reserve would be breached")
        elif action.type is ActionType.LOAN:
            if state.economy.loan_balance+action.amount > max(1, state.economy.daily_costs*30): reasons.append("loan not sustainable")
        return not reasons, reasons
