from __future__ import annotations
from pathlib import Path
from .models import Action, ActionType, GameState

class Watchdog:
    def __init__(self, max_noops:int=30, state_path:str="runs/watchdog_state.json"):
        self.max_noops=max_noops; self.noops=0; self.state_path=Path(state_path)
    def inspect(self,state:GameState, action:Action)->bool:
        self.noops = self.noops+1 if action.type is ActionType.NOOP else 0
        bad=self.noops>=self.max_noops or state.invalid_actions>20 or state.economy.balance < -1000
        if bad: self.save(state)
        return bad
    def save(self,state:GameState):
        self.state_path.parent.mkdir(parents=True, exist_ok=True); self.state_path.write_text(state.model_dump_json(indent=2))
