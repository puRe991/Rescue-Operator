from __future__ import annotations
import json, random
from pathlib import Path
from .models import *
from .config import Settings
from .safety import SafetyLayer

class Simulator:
    def __init__(self, settings: Settings):
        self.settings=settings; self.rng=random.Random(settings.seed); self.safety=SafetyLayer(settings)
        self.state=self.initial_state()
    def initial_state(self)->GameState:
        return GameState(stations={"s1":Station(id="s1",x=0,y=0)}, hospitals={"h1":Hospital(id="h1",x=5,y=5,capacity=10)},
            personnel={f"p{i}":Personnel(id=f"p{i}",qualifications={"basic"}) for i in range(1,7)},
            vehicles={"v1":Vehicle(id="v1",station_id="s1",kind="engine",crew_required=2,modules={"pump"},water=1200,air=100,crew=["p1","p2"]),
                      "v2":Vehicle(id="v2",station_id="s1",kind="ambulance",crew_required=2,modules={"medical"},air=50,crew=["p3","p4"])})
    def step(self, action: Action)->tuple[GameState,float,bool,dict]:
        ok,reasons=self.safety.validate(self.state,action)
        reward=-0.01; info={"valid":ok,"reasons":reasons}
        if not ok:
            self.state.invalid_actions+=1; return self.state,-5,False,info
        if action.type is ActionType.DISPATCH:
            m=self.state.missions[action.mission_id or ""]
            for vid in action.vehicle_ids:
                v=self.state.vehicles[vid]; v.status=VehicleStatus.DISPATCHED; v.condition=max(0,v.condition-0.03); m.assigned_vehicle_ids.append(vid)
            m.completed=True; self.state.economy.balance+=m.reward; reward+=10+m.patient_risk*10
        elif action.type is ActionType.REPAIR and action.target_id in self.state.vehicles:
            v=self.state.vehicles[action.target_id]; v.condition=1; v.status=VehicleStatus.AVAILABLE; self.state.economy.balance-=self.settings.repair_cost
        elif action.type is ActionType.NOOP: reward-=0.1
        self._tick(); return self.state,reward,self.state.time_minute>=60*self.settings.default_hours,info
    def _tick(self):
        self.state.time_minute+=1
        if self.state.time_minute%60==0: self.state.economy.balance-=self.state.economy.daily_costs/24
        if self.rng.random()<0.08: self._spawn_mission()
        for v in self.state.vehicles.values():
            if v.status is VehicleStatus.DISPATCHED and self.rng.random()<0.35: v.status=VehicleStatus.AVAILABLE
        for m in self.state.missions.values():
            if not m.completed and not m.failed:
                m.deadline_minutes=max(0,m.deadline_minutes-1)
                if m.deadline_minutes==0: m.failed=True; self.state.patient_deaths+=1 if m.patient_risk>0.5 else 0
    def _spawn_mission(self):
        i=len(self.state.missions)+1; medical=self.rng.random()<0.45
        self.state.missions[f"m{i}"]=Mission(id=f"m{i}",type=MissionType.MEDICAL if medical else MissionType.FIRE,x=self.rng.uniform(0,10),y=self.rng.uniform(0,10),
            required_modules={"medical"} if medical else {"pump"}, required_water=0 if medical else 500, required_air=20, patient_risk=self.rng.random() if medical else self.rng.random()*0.4,
            escalation_risk=self.rng.random(), deadline_minutes=self.rng.randint(10,45), reward=200 if medical else 350)
    def save(self,path: str|Path): Path(path).write_text(self.state.model_dump_json(indent=2))
