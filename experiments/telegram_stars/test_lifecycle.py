"""Offline evaluation only. No Bot instance, credentials, network, or runtime imports.

The one-Star fixture is arbitrary test data, not a proposed product price.
Run with: make test FILE=experiments/telegram_stars/test_lifecycle.py
"""

from dataclasses import dataclass, field

import pytest
from aiogram import Dispatcher
from aiogram.methods import CreateInvoiceLink, SendInvoice
from aiogram.types import (
    BotSubscriptionUpdated,
    LabeledPrice,
    PreCheckoutQuery,
    RefundedPayment,
    SuccessfulPayment,
    Update,
    User,
)

PERIOD = 2_592_000
FIXTURE_PRICE = 1
USER = User(id=42, is_bot=False, first_name="Test")
PAYLOAD = "stars-evaluation-order-42"


@dataclass(frozen=True)
class Charge:
    expires_at: int
    amount: int
    first: bool


@dataclass
class Ledger:
    """Single-order model; deliberately omits production persistence and API calls."""

    charges: dict[str, Charge] = field(default_factory=dict)
    refunds: set[str] = field(default_factory=set)
    renewal_state: str = "unknown"

    def pre_checkout(self, query: PreCheckoutQuery) -> bool:
        return (
            query.from_user.id == USER.id
            and query.invoice_payload == PAYLOAD
            and query.currency == "XTR"
            and query.total_amount == FIXTURE_PRICE
            and not self.charges
        )

    def payment(self, user_id: int, payment: SuccessfulPayment) -> None:
        expiry = payment.subscription_expiration_date
        if (
            user_id != USER.id
            or payment.invoice_payload != PAYLOAD
            or payment.currency != "XTR"
            or payment.total_amount != FIXTURE_PRICE
            or payment.is_recurring is not True
            or expiry is None
            or expiry <= 0
        ):
            raise ValueError("Payment does not match the recurring order")

        charge_id = payment.telegram_payment_charge_id
        charge = Charge(expiry, payment.total_amount, bool(payment.is_first_recurring))
        previous = self.charges.get(charge_id)
        if previous is not None and previous != charge:
            raise ValueError("Conflicting replay requires reconciliation")
        if charge.first and any(
            other.first and other_id != charge_id
            for other_id, other in self.charges.items()
        ):
            raise ValueError("Unexpected second subscription requires support")
        self.charges[charge_id] = charge

    def subscription(self, event: BotSubscriptionUpdated) -> None:
        if (
            event.user.id != USER.id
            or event.invoice_payload != PAYLOAD
            or event.state not in {"active", "canceled", "failed"}
        ):
            raise ValueError("Unknown subscription event requires reconciliation")
        self.renewal_state = event.state

    def refund(self, event: RefundedPayment) -> None:
        if (
            event.invoice_payload != PAYLOAD
            or event.currency != "XTR"
            or event.total_amount != FIXTURE_PRICE
        ):
            raise ValueError("Refund does not match the order")
        self.refunds.add(event.telegram_payment_charge_id)

    def has_access(self, user_id: int, now: int) -> bool:
        return user_id == USER.id and any(
            charge.expires_at - PERIOD <= now < charge.expires_at
            and charge_id not in self.refunds
            for charge_id, charge in self.charges.items()
        )


def successful_payment(
    charge_id: str = "charge-1", expires_at: int = PERIOD, *, first: bool = True
) -> SuccessfulPayment:
    return SuccessfulPayment(
        currency="XTR",
        total_amount=FIXTURE_PRICE,
        invoice_payload=PAYLOAD,
        telegram_payment_charge_id=charge_id,
        provider_payment_charge_id="",
        subscription_expiration_date=expires_at,
        is_recurring=True,
        is_first_recurring=True if first else None,
    )


def refund_event(charge_id: str = "charge-1") -> RefundedPayment:
    return RefundedPayment(
        currency="XTR",
        total_amount=FIXTURE_PRICE,
        invoice_payload=PAYLOAD,
        telegram_payment_charge_id=charge_id,
    )


def test_pre_checkout_and_successful_payment_flow() -> None:
    ledger = Ledger()
    query = PreCheckoutQuery(
        id="query-1",
        from_user=USER,
        currency="XTR",
        total_amount=FIXTURE_PRICE,
        invoice_payload=PAYLOAD,
    )
    assert ledger.pre_checkout(query)
    assert not ledger.has_access(USER.id, 1)
    receipt = Update.model_validate(
        {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "date": 1,
                "chat": {"id": USER.id, "type": "private"},
                "from": USER.model_dump(),
                "successful_payment": successful_payment().model_dump(),
            },
        }
    )
    assert receipt.message is not None
    assert receipt.message.from_user is not None
    assert receipt.message.successful_payment is not None
    ledger.payment(receipt.message.from_user.id, receipt.message.successful_payment)
    assert ledger.has_access(USER.id, 1)
    assert not ledger.has_access(USER.id + 1, 1)
    assert not ledger.pre_checkout(query)


@pytest.mark.parametrize(
    ("user_id", "payload", "currency", "amount"),
    [
        (43, PAYLOAD, "XTR", FIXTURE_PRICE),
        (42, "other-order", "XTR", FIXTURE_PRICE),
        (42, PAYLOAD, "USD", FIXTURE_PRICE),
        (42, PAYLOAD, "XTR", FIXTURE_PRICE + 1),
    ],
)
def test_pre_checkout_rejects_mismatched_order(
    user_id: int, payload: str, currency: str, amount: int
) -> None:
    query = PreCheckoutQuery(
        id="invalid-query",
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        currency=currency,
        total_amount=amount,
        invoice_payload=payload,
    )
    assert not Ledger().pre_checkout(query)


@pytest.mark.parametrize("state", ["canceled", "active", "failed"])
def test_subscription_state_never_grants_or_revokes_paid_time(state: str) -> None:
    ledger = Ledger()
    update = Update(
        update_id=2,
        subscription=BotSubscriptionUpdated(
            user=USER, invoice_payload=PAYLOAD, state=state
        ),
    )
    assert update.subscription is not None
    ledger.subscription(update.subscription)
    assert not ledger.has_access(USER.id, 1)
    ledger.payment(USER.id, successful_payment())
    ledger.subscription(update.subscription)
    assert ledger.renewal_state == state
    assert ledger.has_access(USER.id, PERIOD - 1)
    assert not ledger.has_access(USER.id, PERIOD)


def test_renewal_replays_and_refunds_preserve_other_paid_periods() -> None:
    ledger = Ledger()
    initial = successful_payment()
    renewal = successful_payment("charge-2", 2 * PERIOD, first=False)
    ledger.payment(USER.id, renewal)
    ledger.payment(USER.id, initial)
    ledger.payment(USER.id, renewal)
    assert len(ledger.charges) == 2
    ledger.refund(refund_event())
    ledger.refund(refund_event())
    ledger.payment(USER.id, initial)
    assert not ledger.has_access(USER.id, PERIOD - 1)
    assert ledger.has_access(USER.id, PERIOD)
    assert not ledger.has_access(USER.id, 2 * PERIOD)
    ledger.refund(refund_event("charge-2"))
    assert not ledger.has_access(USER.id, PERIOD)


def test_refund_before_payment_cannot_restore_access() -> None:
    ledger = Ledger()
    ledger.refund(refund_event())
    ledger.payment(USER.id, successful_payment())
    assert not ledger.has_access(USER.id, 1)


@pytest.mark.parametrize(
    "kind",
    [
        "currency",
        "amount",
        "payload",
        "non_recurring",
        "missing_expiry",
        "invalid_expiry",
        "payer",
        "replay",
    ],
)
def test_invalid_success_does_not_create_access(kind: str) -> None:
    ledger = Ledger()
    data = successful_payment().model_dump()
    user_id = USER.id
    if kind == "currency":
        data["currency"] = "USD"
    elif kind == "amount":
        data["total_amount"] = FIXTURE_PRICE + 1
    elif kind == "payload":
        data["invoice_payload"] = "other-order"
    elif kind == "non_recurring":
        data["is_recurring"] = None
    elif kind == "missing_expiry":
        data["subscription_expiration_date"] = None
    elif kind == "invalid_expiry":
        data["subscription_expiration_date"] = 0
    elif kind == "payer":
        user_id += 1
    else:
        ledger.refund(refund_event())
        ledger.payment(USER.id, successful_payment())
        data["subscription_expiration_date"] = 2 * PERIOD
    with pytest.raises(ValueError):
        ledger.payment(user_id, SuccessfulPayment.model_validate(data))
    assert not ledger.has_access(USER.id, 1)


def test_concurrent_subscription_requires_support() -> None:
    ledger = Ledger()
    ledger.payment(USER.id, successful_payment())
    with pytest.raises(ValueError, match="second subscription"):
        ledger.payment(USER.id, successful_payment("unexpected-charge"))
    assert len(ledger.charges) == 1


def test_unknown_subscription_state_requires_reconciliation() -> None:
    ledger = Ledger()
    with pytest.raises(ValueError, match="Unknown subscription"):
        ledger.subscription(
            BotSubscriptionUpdated(
                user=USER, invoice_payload=PAYLOAD, state="future-state"
            )
        )
    assert ledger.renewal_state == "unknown"
    assert not ledger.has_access(USER.id, 1)


def test_mismatched_refund_does_not_revoke_access() -> None:
    ledger = Ledger()
    ledger.payment(USER.id, successful_payment())
    data = refund_event().model_dump()
    data["invoice_payload"] = "other-order"
    with pytest.raises(ValueError, match="Refund does not match"):
        ledger.refund(RefundedPayment.model_validate(data))
    assert ledger.has_access(USER.id, 1)


def test_installed_aiogram_supports_recurring_link_and_subscription_observer() -> None:
    invoice = CreateInvoiceLink(
        title="Offline evaluation",
        description="Not for sale",
        payload=PAYLOAD,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Fixture", amount=FIXTURE_PRICE)],
        subscription_period=PERIOD,
    )
    assert invoice.model_dump()["subscription_period"] == PERIOD
    assert "subscription_period" not in SendInvoice.model_fields
    assert "subscription" in Dispatcher().observers
