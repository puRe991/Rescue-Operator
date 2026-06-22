from __future__ import annotations
import numpy as np
try:
    import gymnasium as gym
    from gymnasium import spaces
except Exception:  # lightweight fallback for tests without optional deps
    gym=object
    class spaces:
        class Box:
            def __init__(self, low, high, shape, dtype): self.shape=shape
        class Discrete:
            def __init__(self, n): self.n=n
from .config import Settings
from .simulator import Simulator
from .models import Action, ActionType

class RescueOperatorEnv(gym.Env if hasattr(gym,"Env") else object):
    metadata={"render_modes":[]}
    def __init__(self, settings: Settings|None=None):
        self.settings=settings or Settings(); self.sim=Simulator(self.settings)
        self.observation_space=spaces.Box(low=-1e9, high=1e9, shape=(12,), dtype=np.float32)
        self.action_space=spaces.Discrete(4)
    def reset(self, *, seed=None, options=None):
        if seed is not None: self.settings.seed=seed
        self.sim=Simulator(self.settings); return self._obs(), {}
    def step(self, action:int):
        act=self._decode(action); state,reward,done,info=self.sim.step(act)
        return self._obs(), reward, done, False, info
    def _decode(self, action:int)->Action:
        open_m=next((m for m in self.sim.state.missions.values() if not m.completed and not m.failed), None)
        if action==1 and open_m: return Action(type=ActionType.DISPATCH, mission_id=open_m.id, vehicle_ids=[v.id for v in self.sim.state.vehicles.values() if v.status.value=="available"][:1])
        return Action(type=ActionType.NOOP)
    def _obs(self):
        s=self.sim.state
        return np.array([s.time_minute,len(s.missions),sum(not m.completed and not m.failed for m in s.missions.values()),len(s.vehicles),sum(v.status.value=="available" for v in s.vehicles.values()),sum(v.condition for v in s.vehicles.values()),len(s.personnel),sum(v.water for v in s.vehicles.values()),sum(v.air for v in s.vehicles.values()),s.economy.balance,s.economy.daily_costs,s.patient_deaths], dtype=np.float32)
