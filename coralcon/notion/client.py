"""Thin Notion write client.

Coral remains the read path. This module only writes dashboard pages and
action tasks when Notion credentials and target IDs are configured.
"""

import json
import os
from pathlib import Path

from coralcon.notion.dashboard_template import build_dashboard_blocks
from coralcon.notion.task_template import build_task_properties

CONFIG_DIR = Path.home() / ".coralcon"
CONFIG_PATH = CONFIG_DIR / "config.json"


class NotionWriteClient:
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()
        self._client = None

    def is_configured(self, target: str = "any") -> bool:
        if not self._token:
            return False
        if target == "dashboard":
            return bool(self.dashboard_page_id)
        if target == "actions":
            return bool(self.actions_db_id)
        return bool(self.dashboard_page_id or self.actions_db_id)

    @property
    def dashboard_page_id(self) -> str | None:
        return os.getenv("NOTION_DASHBOARD_PAGE_ID") or self.config.get("dashboard_page_id")

    @property
    def actions_db_id(self) -> str | None:
        return os.getenv("NOTION_ACTIONS_DATABASE_ID") or self.config.get("actions_db_id")

    @property
    def _token(self) -> str | None:
        return os.getenv("NOTION_TOKEN") or self.config.get("notion_token")

    @property
    def client(self):
        if self._client is None:
            try:
                from notion_client import Client
            except ImportError as exc:
                raise RuntimeError(
                    "notion-client is not installed. Run `pip install -r requirements.txt`."
                ) from exc
            self._client = Client(auth=self._token)
        return self._client

    def update_dashboard(self, insights: dict) -> dict:
        if not self.dashboard_page_id:
            raise RuntimeError("Missing NOTION_DASHBOARD_PAGE_ID or dashboard_page_id in config.")
        blocks = build_dashboard_blocks(insights)
        self.client.blocks.children.append(block_id=self.dashboard_page_id, children=blocks)
        page = self.client.pages.retrieve(page_id=self.dashboard_page_id)
        return {"id": page.get("id"), "url": page.get("url")}

    def create_action_task(self, task: dict) -> dict:
        if not self.actions_db_id:
            raise RuntimeError("Missing NOTION_ACTIONS_DATABASE_ID or actions_db_id in config.")
        return self.client.pages.create(
            parent={"database_id": self.actions_db_id},
            properties=build_task_properties(task),
        )

    def save_setup(self, dashboard_page_id: str | None, actions_db_id: str | None) -> dict:
        config = self._load_config()
        if dashboard_page_id:
            config["dashboard_page_id"] = dashboard_page_id
        if actions_db_id:
            config["actions_db_id"] = actions_db_id

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.config = config
        return config

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            return {}
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
