from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt

class VehicleStatus(str, Enum):
    AVAILABLE="available"; DISPATCHED="dispatched"; REPAIR="repair"
class MissionType(str, Enum):
    FIRE="fire"; MEDICAL="medical"; TECHNICAL="technical"
class ActionType(str, Enum):
    DISPATCH="dispatch"; REPAIR="repair"; HIRE="hire"; TRAIN="train"; BUY_VEHICLE="buy_vehicle"; BUILD_STATION="build_station"; LOAN="loan"; REPAY_LOAN="repay_loan"; NOOP="noop"

class Personnel(BaseModel):
    id: str; qualifications: set[str] = Field(default_factory=set); available: bool=True
class Vehicle(BaseModel):
    id: str; station_id: str; kind: str; crew_required: int; modules: set[str]=Field(default_factory=set)
    water: NonNegativeFloat=0; air: NonNegativeFloat=0; condition: float=Field(ge=0, le=1, default=1)
    status: VehicleStatus=VehicleStatus.AVAILABLE; crew: list[str]=Field(default_factory=list)
class Station(BaseModel):
    id: str; x: float; y: float; capacity: NonNegativeInt=4
class Hospital(BaseModel):
    id: str; x: float; y: float; capacity: NonNegativeInt; occupied: NonNegativeInt=0
class Mission(BaseModel):
    id: str; type: MissionType; x: float; y: float; required_modules: set[str]=Field(default_factory=set)
    required_water: NonNegativeFloat=0; required_air: NonNegativeFloat=0; min_vehicles: NonNegativeInt=1
    patient_risk: float=Field(ge=0, le=1, default=0); escalation_risk: float=Field(ge=0, le=1, default=0)
    deadline_minutes: NonNegativeInt=30; reward: NonNegativeFloat=100; assigned_vehicle_ids: list[str]=Field(default_factory=list)
    completed: bool=False; failed: bool=False
class Economy(BaseModel):
    balance: float=10000; daily_costs: NonNegativeFloat=1000; loan_balance: NonNegativeFloat=0
class GameState(BaseModel):
    time_minute: NonNegativeInt=0; stations: dict[str, Station]=Field(default_factory=dict)
    vehicles: dict[str, Vehicle]=Field(default_factory=dict); personnel: dict[str, Personnel]=Field(default_factory=dict)
    missions: dict[str, Mission]=Field(default_factory=dict); hospitals: dict[str, Hospital]=Field(default_factory=dict)
    economy: Economy=Field(default_factory=Economy); invalid_actions: NonNegativeInt=0; patient_deaths: NonNegativeInt=0
class Action(BaseModel):
    type: ActionType; mission_id: str|None=None; vehicle_ids: list[str]=Field(default_factory=list); target_id: str|None=None; amount: float=0
class DecisionRecord(BaseModel):
    time_minute: int; state: dict; possible_actions: list[dict]; rejected_actions: list[dict]; rejection_reasons: list[str]
    chosen_action: dict; expected_outcome: str; actual_outcome: str|None=None; reward: float=0; model_confidence: float|None=None; planner: str
