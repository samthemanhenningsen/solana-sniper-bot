"""Stripe billing — optional. Without STRIPE_* env vars everything runs in free mode.

Model: screening is free, drafting is the paid feature ("pro" plan, one subscription
per customer account). Checkout and webhooks only activate when Stripe is configured.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from .models import User
from .settings import settings

log = logging.getLogger(__name__)

try:
    import stripe  # type: ignore
except ImportError:
    stripe = None


def available() -> bool:
    return stripe is not None and settings.billing_enabled


def create_checkout_url(user: User, db: Session) -> str | None:
    """Create a Stripe Checkout session for the pro subscription; returns the redirect URL."""
    if not available():
        return None
    stripe.api_key = settings.stripe_secret_key
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email, metadata={"grantpilot_user_id": user.id})
        user.stripe_customer_id = customer["id"]
        db.commit()
    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        success_url=f"{settings.base_url}/billing?status=success",
        cancel_url=f"{settings.base_url}/billing?status=cancelled",
    )
    return session["url"]


def handle_webhook(payload: bytes, signature: str, db: Session) -> None:
    """Apply subscription state changes from Stripe webhooks."""
    if not available():
        return
    stripe.api_key = settings.stripe_secret_key
    event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)

    obj = event["data"]["object"]
    customer_id = obj.get("customer")
    if not customer_id:
        return
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user is None:
        return

    if event["type"] in ("checkout.session.completed", "customer.subscription.updated"):
        status = obj.get("status", "active" if event["type"] == "checkout.session.completed" else "")
        user.plan = "pro" if status in ("active", "trialing") else user.plan
    elif event["type"] == "customer.subscription.deleted":
        user.plan = "free"
    db.commit()
    log.info("billing: %s -> user %s plan=%s", event["type"], user.email, user.plan)
