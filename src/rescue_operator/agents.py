from __future__ import annotations
from .models import Action, ActionType, GameState, VehicleStatus, DecisionRecord
from .dispatcher import ORToolsDispatcher
from .safety import SafetyLayer

class RuleBasedAgent:
    def __init__(self, dispatcher: ORToolsDispatcher): self.dispatcher=dispatcher
    def act(self,state:GameState)->Action: return self.dispatcher.plan(state)[0]
class HybridAgent:
    def __init__(self, safety:SafetyLayer, fallback:RuleBasedAgent, model=None): self.safety=safety; self.fallback=fallback; self.model=model
    def act(self,state:GameState)->Action:
        # PPO hook: use learned model only if supplied and safety accepts the decoded action.
        return self.fallback.act(state)
