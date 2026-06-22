from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import ValidationError

from .models import Action, ActionType, GameState
from .simulator import Simulator
from .vision import BrowserScreenReader, ScreenObservation


class ConnectorError(RuntimeError):
    """Raised when a connector cannot read state or execute an action safely."""


class GameConnector(Protocol):
    def get_state(self) -> GameState: ...

    def apply_action(self, action: Action) -> tuple[GameState, float, bool, dict]: ...


@dataclass
class SimulatorConnector:
    simulator: Simulator

    def get_state(self) -> GameState:
        return self.simulator.state

    def apply_action(self, action: Action) -> tuple[GameState, float, bool, dict]:
        return self.simulator.step(action)


@dataclass(frozen=True)
class BrowserSelectorConfig:
    """CSS selectors for the documented browser integration surface."""

    state_json_selector: str = "#rescue-operator-state"
    login_user_selector: str = "input[name='username']"
    login_password_selector: str = "input[name='password']"
    login_submit_selector: str = "button[type='submit']"
    dispatch_button_template: str = "[data-action='dispatch'][data-mission='{mission_id}'][data-vehicle='{vehicle_id}']"
    repair_button_template: str = "[data-action='repair'][data-vehicle='{vehicle_id}']"
    noop_selector: str = "body"


@dataclass
class AuthorizedLiveConnector:
    """Playwright connector for authorized UI automation of the real game.

    The connector only uses browser UI selectors or a page-exposed JSON state block. It deliberately
    does not inspect private APIs, sniff network traffic, bypass CAPTCHA, or attempt anti-cheat evasion.
    """

    base_url: str = "https://game.rescue-operator.com"
    headless: bool = True
    selectors: BrowserSelectorConfig = field(default_factory=BrowserSelectorConfig)
    username_env: str = "RESCUE_OPERATOR_USERNAME"
    password_env: str = "RESCUE_OPERATOR_PASSWORD"
    _playwright: Any = field(default=None, init=False, repr=False)
    _browser: Any = field(default=None, init=False, repr=False)
    _page: Any = field(default=None, init=False, repr=False)
    _screen_reader: BrowserScreenReader = field(default_factory=BrowserScreenReader, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.base_url.startswith("https://game.rescue-operator.com"):
            raise ValueError("live connector is restricted to https://game.rescue-operator.com")

    def start(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise ConnectorError("Playwright is required for --connector live: pip install playwright && playwright install chromium") from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._page = self._browser.new_page()
        self._page.goto(self.base_url, wait_until="domcontentloaded")
        self._login_if_credentials_available()

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._browser = None
        self._playwright = None
        self._page = None

    def read_screen(self, name: str = "live") -> ScreenObservation:
        return self._screen_reader.read(self._require_page(), name=name)

    def get_state(self) -> GameState:
        page = self._require_page()
        raw_state = page.evaluate("() => window.__RESCUE_OPERATOR_STATE__ || null")
        if raw_state is None:
            locator = page.locator(self.selectors.state_json_selector)
            if locator.count() == 0:
                raise ConnectorError("no game state found; configure state_json_selector or expose window.__RESCUE_OPERATOR_STATE__")
            raw_state = locator.first.text_content()
        if isinstance(raw_state, str):
            raw_state = json.loads(raw_state)
        try:
            return GameState.model_validate(raw_state)
        except (TypeError, ValidationError) as exc:
            raise ConnectorError("live game state does not match the Rescue Operator schema") from exc

    def apply_action(self, action: Action) -> tuple[GameState, float, bool, dict]:
        page = self._require_page()
        clicked: list[str] = []
        if action.type is ActionType.DISPATCH:
            if not action.mission_id or not action.vehicle_ids:
                raise ConnectorError("dispatch action requires mission_id and vehicle_ids")
            for vehicle_id in action.vehicle_ids:
                selector = self.selectors.dispatch_button_template.format(mission_id=action.mission_id, vehicle_id=vehicle_id)
                self._click_required(page, selector)
                clicked.append(selector)
        elif action.type is ActionType.REPAIR:
            if not action.target_id:
                raise ConnectorError("repair action requires target_id")
            selector = self.selectors.repair_button_template.format(vehicle_id=action.target_id)
            self._click_required(page, selector)
            clicked.append(selector)
        elif action.type is ActionType.NOOP:
            page.locator(self.selectors.noop_selector).first.wait_for(state="attached", timeout=1_000)
        else:
            raise ConnectorError(f"action {action.type.value} is not mapped to a browser UI command yet")
        page.wait_for_load_state("domcontentloaded")
        screen = self.read_screen(name=f"action_{action.type.value}")
        return self.get_state(), 0.0, False, {"connector": "live", "clicked": clicked, "screen_text": screen.combined_text, "screen_warnings": screen.warnings, "screenshot": screen.screenshot_path}

    def _login_if_credentials_available(self) -> None:
        page = self._require_page()
        username = os.getenv(self.username_env)
        password = os.getenv(self.password_env)
        if not username or not password or page.locator(self.selectors.login_user_selector).count() == 0:
            return
        page.fill(self.selectors.login_user_selector, username)
        page.fill(self.selectors.login_password_selector, password)
        page.click(self.selectors.login_submit_selector)
        page.wait_for_load_state("domcontentloaded")

    def _click_required(self, page: Any, selector: str) -> None:
        locator = page.locator(selector)
        if locator.count() == 0:
            raise ConnectorError(f"required action selector not found: {selector}")
        locator.first.click()

    def _require_page(self) -> Any:
        if self._page is None:
            raise ConnectorError("live connector is not started; call start() before use")
        return self._page
