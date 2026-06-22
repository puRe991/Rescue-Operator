from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel
import yaml

class Settings(BaseModel):
    seed: int=42; min_vehicle_condition: float=0.25; liquidity_reserve_days: int=5
    default_hours: int=168; repair_cost: float=250; hire_cost: float=500; vehicle_cost: float=2500; station_cost: float=5000
    live_url: str="https://game.rescue-operator.com"; live_headless: bool=True
    browser_selectors: dict[str, str]={}
    assumptions: list[str]=[]

def load_settings(path: str|Path="config/default.yaml") -> Settings:
    p=Path(path)
    if not p.exists(): return Settings()
    return Settings.model_validate(yaml.safe_load(p.read_text()) or {})
