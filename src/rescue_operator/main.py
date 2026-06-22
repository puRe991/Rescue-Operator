from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agents import HybridAgent, RuleBasedAgent
from .config import load_settings
from .connectors import AuthorizedLiveConnector, BrowserSelectorConfig, ConnectorError, SimulatorConnector
from .dispatcher import ORToolsDispatcher
from .safety import SafetyLayer
from .simulator import Simulator
from .storage import SQLiteStore
from .watchdog import Watchdog


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--headless", action="store_true")
    p.add_argument("--autonomous", action="store_true")
    p.add_argument("--hours", type=int, default=None)
    p.add_argument("--speed", default="max")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--config", default="config/default.yaml")
    p.add_argument("--connector", choices=["simulator", "live"], default="simulator")
    args = p.parse_args(argv)
    settings = load_settings(args.config)
    if args.seed is not None:
        settings.seed = args.seed
    if args.hours is not None:
        settings.default_hours = args.hours

    sim = Simulator(settings)
    connector = _build_connector(args.connector, settings, sim)
    safety = SafetyLayer(settings)
    dispatcher = ORToolsDispatcher(safety)
    agent = HybridAgent(safety, RuleBasedAgent(dispatcher))
    watchdog = Watchdog()
    store = SQLiteStore()
    Path("runs").mkdir(exist_ok=True)
    log = Path("runs/decisions.jsonl").open("w")
    done = False
    state = connector.get_state()
    try:
        while not done:
            state_for_decision = connector.get_state()
            action = agent.act(state_for_decision)
            if watchdog.inspect(state_for_decision, action):
                action = RuleBasedAgent(dispatcher).act(state_for_decision)
            state, reward, done, info = connector.apply_action(action)
            if args.connector == "live":
                done = state.time_minute >= 60 * settings.default_hours
            record = {"time_minute": state.time_minute, "action": action.model_dump(), "reward": reward, "info": info}
            log.write(json.dumps(record, default=str) + "\n")
            store.save_state(state)
    finally:
        if hasattr(connector, "close"):
            connector.close()
        sim.save("runs/final_state.json")
        store.close()
        log.close()
    print(json.dumps({"hours": settings.default_hours, "balance": state.economy.balance, "invalid_actions": state.invalid_actions, "patient_deaths": state.patient_deaths}))


def _build_connector(name: str, settings, sim: Simulator):
    if name == "simulator":
        return SimulatorConnector(sim)
    selectors = BrowserSelectorConfig(**settings.browser_selectors)
    connector = AuthorizedLiveConnector(base_url=settings.live_url, headless=settings.live_headless, selectors=selectors)
    try:
        connector.start()
    except ConnectorError:
        raise
    return connector


if __name__ == "__main__":
    main()
