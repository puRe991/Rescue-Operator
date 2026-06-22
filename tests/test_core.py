from rescue_operator.config import Settings
from rescue_operator.models import Action, ActionType, Mission, MissionType, VehicleStatus
from rescue_operator.simulator import Simulator
from rescue_operator.safety import SafetyLayer
from rescue_operator.dispatcher import ORToolsDispatcher
from rescue_operator.env import RescueOperatorEnv


def test_safety_rejects_undercrewed_vehicle():
    sim=Simulator(Settings())
    sim.state.vehicles["v1"].crew=[]
    sim.state.missions["m1"]=Mission(id="m1", type=MissionType.FIRE, x=1, y=1, required_modules={"pump"}, required_water=10, min_vehicles=1)
    ok,reasons=SafetyLayer(Settings()).validate(sim.state, Action(type=ActionType.DISPATCH, mission_id="m1", vehicle_ids=["v1"]))
    assert not ok
    assert any("lacks crew" in r for r in reasons)


def test_dispatcher_assigns_valid_vehicle_for_medical_priority():
    sim=Simulator(Settings())
    sim.state.missions["m1"]=Mission(id="m1", type=MissionType.MEDICAL, x=1, y=1, required_modules={"medical"}, required_air=10, patient_risk=1)
    action=ORToolsDispatcher(SafetyLayer(Settings())).plan(sim.state)[0]
    assert action.type is ActionType.DISPATCH
    assert action.vehicle_ids == ["v2"]


def test_simulator_completes_dispatch_and_rewards():
    sim=Simulator(Settings(seed=1))
    sim.state.missions["m1"]=Mission(id="m1", type=MissionType.FIRE, x=1, y=1, required_modules={"pump"}, required_water=10, required_air=10, reward=123)
    _,reward,_,info=sim.step(Action(type=ActionType.DISPATCH, mission_id="m1", vehicle_ids=["v1"]))
    assert info["valid"] is True
    assert reward > 0
    assert sim.state.missions["m1"].completed is True
    assert sim.state.vehicles["v1"].status is VehicleStatus.DISPATCHED


def test_gym_environment_shapes():
    env=RescueOperatorEnv(Settings(seed=2))
    obs,_=env.reset(seed=2)
    assert obs.shape == (12,)
    obs,reward,terminated,truncated,info=env.step(0)
    assert obs.shape == (12,)
    assert truncated is False


class _FakeLocator:
    def __init__(self, page, selector):
        self.page=page; self.selector=selector
    @property
    def first(self):
        return self
    def count(self):
        return 1
    def click(self):
        self.page.clicked.append(self.selector)
    def wait_for(self, **kwargs):
        return None
    def text_content(self):
        return self.page.state_json
    def inner_text(self, **kwargs):
        return "Mission m1 Ambulance v2"

class _FakeAccessibility:
    def snapshot(self, interesting_only=False):
        return {"name":"Rescue Operator", "children":[{"name":"Dispatch"}]}

class _FakePage:
    def __init__(self, state_json):
        self.state_json=state_json; self.clicked=[]; self.url="https://game.rescue-operator.com"; self.accessibility=_FakeAccessibility()
    def evaluate(self, script):
        return None
    def locator(self, selector):
        return _FakeLocator(self, selector)
    def wait_for_load_state(self, *args, **kwargs):
        return None
    def screenshot(self, path, full_page=True):
        from pathlib import Path
        Path(path).write_bytes(b"fake image")
    def title(self):
        return "Rescue Operator"

def test_live_connector_maps_dispatch_to_browser_selector():
    from rescue_operator.connectors import AuthorizedLiveConnector
    sim=Simulator(Settings())
    sim.state.missions["m1"]=Mission(id="m1", type=MissionType.MEDICAL, x=1, y=1, required_modules={"medical"})
    connector=AuthorizedLiveConnector("https://game.rescue-operator.com", headless=True)
    connector._page=_FakePage(sim.state.model_dump_json())
    state, reward, done, info = connector.apply_action(Action(type=ActionType.DISPATCH, mission_id="m1", vehicle_ids=["v2"]))
    assert state.time_minute == sim.state.time_minute
    assert reward == 0.0
    assert done is False
    assert info["clicked"] == ["[data-action='dispatch'][data-mission='m1'][data-vehicle='v2']"]
    assert "Mission m1" in info["screen_text"]
    assert info["screenshot"].endswith("action_dispatch.png")
