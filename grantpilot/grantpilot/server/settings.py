"""Server configuration — everything comes from environment variables."""

from __future__ import annotations

import os
import secrets


class Settings:
    def __init__(self) -> None:
        self.database_url = os.environ.get("GRANTPILOT_DB", "sqlite:///grantpilot.db")
        # Sessions are invalidated on restart unless a stable secret is provided.
        self.secret_key = os.environ.get("GRANTPILOT_SECRET") or secrets.token_hex(32)
        self.scheduler_enabled = os.environ.get("GRANTPILOT_SCHEDULER", "1") == "1"
        self.stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        self.stripe_price_id = os.environ.get("STRIPE_PRICE_ID", "")
        self.stripe_webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        self.base_url = os.environ.get("GRANTPILOT_BASE_URL", "http://localhost:8000")

    @property
    def billing_enabled(self) -> bool:
        return bool(self.stripe_secret_key and self.stripe_price_id)


settings = Settings()
