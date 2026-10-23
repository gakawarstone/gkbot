# Telegram Stars monetization evaluation

Date: 2026-10-23. Scope: GKBot at `fc19464`, aiogram 3.31.0.

## Decision

**NO-GO for production payments now.** This evaluation recommends keeping the
current product free. It does not record an owner-approved commercial launch
or a permanent rejection of monetization. No feature requires payment, the
current price is 0 Stars, and there is no paid tier or recurring charge.
Existing availability and provider limits continue to apply. Free does not
promise unlimited usage or an uptime guarantee.

The repository has no payment handlers, durable payment ledger, entitlement
checks, usage accounting, or payment support process. `Users` stores only an
ID and username. FSM storage is in memory. Database startup generates schemas
but supplies no billing migration or reconciliation procedure. The image
handler depends on Pollinations and prompt enhancement; AI chat depends on
OpenRouter. Neither path records the cost and delivered units needed to price
a service. See [users](../../bot/models/users.py),
[startup](../../bot/core/bot.py), [database setup](../../bot/configs/db.py),
[image generation](../../bot/handlers/prompt/generate_image.py), and
[AI chat](../../bot/handlers/user/chatgpt/answer.py).

Charging for these paths would add a delivery and support commitment before
we can measure its cost or enforce its terms. Downloads also depend on outside
sites and offer no reliable delivery guarantee. Keep downloads, feeds, utility
commands, TTS, image generation, and AI chat at their existing free access.

## Product candidate and pricing

If the owner reopens this decision, evaluate an optional, capped AI allowance
for private-chat users first. Preserve existing free access and sell additional
capacity only after measuring cost and failure rates. Exclude downloads and
third-party media resale from that proposal. A monthly bot subscription fits
an allowance better than selling channel membership or locking each result.
This is a design candidate, not an approved product.

There is no proposed numeric paid price. The owner must approve `P` Stars per
30 days, a precise paid allowance `Q`, a free allowance `F`, supported models,
input/output limits, and what counts as delivered usage. Test fixtures use
1 Star only to exercise integer amounts; that value is not pricing guidance.

Before choosing `P`, collect provider cost per delivered unit, retries and
failed requests, peak usage, storage/egress costs, support workload, and
refund losses. Evaluate whether `P * 0.013 * fee_factor` covers the bounded
allowance, operating costs, refunds, taxes, and an owner-approved margin.
Use `fee_factor = 0.85` if the topics fee below applies, otherwise 1, then
check actual balance movements and rounding. This is a planning estimate,
not a guaranteed payout. Unknown cost inputs keep this decision at no-go.

## Telegram economics and limits

Rules checked against official sources on the date above. Recheck before
any launch.

Digital services inside Telegram require Stars. Buyers' acquisition costs
vary with taxes and purchase route. Pre-checkout must finish within 10 seconds;
approval alone is not proof of payment.
[Digital goods guide](https://core.telegram.org/bots/payments-stars).

The published reward equivalent is USD 0.013 per Star, subject to change.
Rewards may be unavailable for up to 21 days and depend on Fragment eligibility.
Private-chat topics incur a separate non-refundable 15% fee on subsequent
Stars purchases while enabled. Earned Stars expire after three years.
Refunds and chargebacks can debit the balance. Do not promise a universal
commission percentage or assume the buyer's purchase price equals proceeds.
[Developer terms, sections 6.2.1 through 6.2.7](https://telegram.org/tos/bot-developers#6-payments).

Bot subscriptions use `createInvoiceLink`, `XTR`, one price item, a 30-day
period of 2592000 seconds, and a maximum price of 10000 Stars. Multiple
subscriptions per user are possible. Paid media costs 1 to 25000 Stars.
Channel subscription invites cost 1 to 10000 Stars per 30 days and require
`can_invite_users`.
[Invoice links](https://core.telegram.org/bots/api#createinvoicelink),
[paid media](https://core.telegram.org/bots/api#sendpaidmedia),
[subscription invites](https://core.telegram.org/bots/api#createchatsubscriptioninvitelink).

## Mechanism comparison

- Recurring bot subscription: candidate for a capped AI allowance. Requires
  our ledger, usage accounting, cancellation, and support. Predictable billing
  intervals do not bound provider cost unless we enforce the allowance.
- Paid media: fits a photo or video already ready for delivery. It does not
  represent access to chat, TTS, or a general download service. Generating an
  image before purchase leaves unpaid generation costs. Not selected.
- Subscription invite link: buys membership of a channel. GKBot has no paid
  channel product; channel membership would also require a separate mapping
  to bot entitlements. Not selected.
- One-time Stars invoice: an alternative for finite AI credit packs if the
  owner wants no automatic renewal. It still needs accounting and support.
  Compare it again once real usage is known; no sale is enabled here.

## Conditional design and offline prototype

[The offline prototype](../../experiments/telegram_stars/test_lifecycle.py)
uses real aiogram objects and a small in-memory ledger. It exists to validate
the lifecycle assumptions behind the decision, especially subscription state
changes, receipt replays, and refunds. It never constructs a `Bot`, calls an
API, loads configuration, registers production handlers, or changes access.
The normal test suite does not collect `experiments/`; run it explicitly.

The installed 3.31.0 wheel exposes `Dispatcher.subscription`,
`BotSubscriptionUpdated`, `SuccessfulPayment`, and `RefundedPayment`.
`Update.subscription` carries a user, payload, and state, with no charge ID,
timestamp, or paid-through date. States are `active`, `canceled`, and `failed`.
Only a successful receipt supplies new paid time. An `active` event must
never grant or extend access by itself.
[Subscription updates](https://core.telegram.org/bots/api#botsubscriptionupdated),
[payment receipts](https://core.telegram.org/bots/api#successfulpayment).

The following is the proposed implementation contract if a later decision
approves the candidate. It is not implemented by this documentation PR.

### Durable records

Use database records, never FSM state or usernames, for financial truth:

- Versioned plan: price, currency, period, allowance, models, and terms version.
- Order: random unique payload, Telegram user ID stored as a 64-bit integer,
  immutable plan snapshot, consent version/time, creation and checkout state.
  Each subscription purchase needs its own payload, even for the same user.
- Charge: unique bot ID plus `telegram_payment_charge_id`, order/user,
  first-charge relationship, amount, recurring flags, paid interval, receipt
  update ID and refund state. Retain the first recurring charge for managing
  renewal. Do not assume all renewals share its charge ID.
- Inbox: unique bot/update ID and minimal validated event data. Persist before
  acknowledging processing. Do not let polling advance past an event whose
  only copy is an in-flight coroutine. Add a durable ingestion/replay strategy.
- Refund tombstone: charge ID, even when its receipt has not arrived. Keep
  incoming and outgoing transaction directions distinct because refunds can
  share the original charge ID.
- Usage reservation and support audit: unique request ID, period, reserved and
  delivered units, release outcome, operator, reason, and reconciliation state.

Commit the inbox, charge change, and entitlement projection atomically. Add
explicit migrations, uniqueness constraints, backup restoration checks, and
retention rules before launch. Store only billing data needed for support;
prompts, downloaded files, and credentials do not belong in the ledger.

### Purchase and access

1. Show price, allowance, renewal date, cancellation/refund terms, and support
   contact. Record consent and create a user-bound opaque order. Create a
   recurring link with `create_invoice_link`; `send_invoice` has no
   `subscription_period` in the installed wheel. Send the link privately.
2. At pre-checkout, validate payer, payload, immutable price/currency, consent,
   sale availability, and duplicate-subscription policy. Lock the user's
   pending purchase to prevent two simultaneous initial checkouts. Reject
   invalid or unavailable orders with a useful message within the deadline.
   Never run AI generation or slow provider probes in this handler.
3. On `message.successful_payment`, validate the payer and order again, require
   recurring flags and an expiry, and record the charge exactly once. Store
   the supplied expiry, never add 30 days on every delivery of an update.
   A renewal may arrive without a new pre-checkout callback. A valid payment
   must still be processed if the in-memory checkout state was lost.
4. Access requires a non-refunded paid interval for this Telegram user and
   the requested feature, with `start <= now < expiry`, plus available quota.
   Reserve quota atomically before provider work on every entry path. Commit
   delivered usage once or release the reservation on failure. Enforce model,
   input size, output size, and concurrency caps. Until `Q` and delivery units
   are approved, this gate cannot be implemented correctly.
5. Record subscription state separately from paid intervals. Cancel, failed
   renewal, and re-enable events change renewal status without removing paid
   time. Expiry checks run on every request; an expiry job is housekeeping.
   Unknown states go to reconciliation. Since state events lack timestamps,
   preserve inbox order and treat status as advisory when ordering is unclear.
6. An administrator may request `edit_user_star_subscription` to stop renewal.
   Cancellation preserves the purchased interval. Re-enable allows the user
   to resume renewal; it does not manufacture paid time. Do not assume a
   refund cancels renewal. Track the two actions separately.

Never silently discard an unexpected successful charge. Quarantine mismatched
or duplicate-subscription receipts, alert support, and arrange fulfillment or
refund after verification. The prototype raises `ValueError` at this boundary;
production needs a durable support case instead.

### Refunds, retries, and reconciliation

Full refunds use `refund_star_payment` for the recorded payer and charge.
Write the intent before the API call; mark confirmed only after success or
matching evidence. The API has no partial-amount argument. Revoke only the
refunded charge's interval and unused allowance, preserving other valid paid
periods. A refund tombstone prevents a delayed receipt restoring access.
Consumed generation cannot be recovered; budget that loss.

Handle `message.refunded_payment` as well as operator-initiated refunds. Retry
database/transient API failures with bounded backoff; honor rate-limit delays.
An API timeout is an unknown outcome. Reconcile before repeating a financial
action, and never create another invoice or charge as an automatic retry.
Receipt confirmation messages may be retried independently of entitlement.

Periodically and after downtime, page `get_star_transactions` with overlap,
match charge IDs plus direction, and compare with the ledger and
`get_my_star_balance`. Persist checkpoints and accounting for other Star
movements. A balance match alone proves no individual entitlement.
The transaction history does not supply every receipt's expiry or all renewal
state. Preserve the durable inbox; route incomplete history to an operator
rather than guessing a paid interval. Alert on unknown charges, discrepancies,
refund failures, inbox lag, and reconciliation failure. Suspend new sales
while reconciliation is unhealthy and preserve already verified paid access.

### Prototype coverage and limits

The executable scenarios cover checkout validation, no access at checkout,
receipt ingestion through `Update`, user isolation, renewal, duplicate and
reordered receipts, expiry boundaries, all three subscription states, refunds
before/after receipts, refund replay, conflicting receipts, and a second
initial charge. Refunding an older period preserves a newer paid period.

The model has one user-bound order, a fixed 30-day period, and unlimited test
units. It models an interval as expiry minus the fixed period through expiry.
It proves neither production concurrency nor durability. There are no API
retry, quota, reconciliation, or real Telegram integration tests here. The
separate implementation must test database rollback/restart, concurrent
checkout and usage, provider failures, API timeout outcomes, and test-environment
payment/refund flows before production. No real or test-network payments were
made during evaluation.

## Support obligations and reopening

Before selling, provide `/paysupport`, purchase terms with recorded consent,
and a visible contact path. The operator owns disputes and timely support;
Telegram support does not resolve purchases from this bot.
[Payment support requirements](https://core.telegram.org/bots/payments-stars#going-live).

The owner must name a primary and backup operator and approve response times,
refund eligibility and handling deadlines, outage compensation, account
recovery, data retention, and a reserve for refunds and chargebacks. Support
needs an authenticated lookup by user/order/charge, a paid-through view, an
audited cancel/refund action, and an escalation queue. Never request Telegram
passwords, OTPs, or payment credentials from a customer.

To reopen, the owner must approve the candidate or an alternative, `P`, `Q`,
`F`, delivery rules, cost evidence, and the support policy above. Verify
Fragment eligibility and the actual topics setting without enabling it just
for this experiment. Check the deployed Bot API version separately from the
repository pin, following [compatibility notes](../../services/bot-api/README.md).

After approval, create a separate production implementation task and PR linked
to the revised decision. That task must own migrations, all payment handlers,
quota enforcement, durable ingestion, reconciliation, administrator tools,
test-environment validation, and rollout/disable procedures. Approval of this
evaluation PR alone does not authorize billing. There is no production billing
task to execute while the decision remains no-go.

## Reproduce the evaluation

```bash
uv sync --locked --all-extras
make test FILE=experiments/telegram_stars/test_lifecycle.py
make lint FILE=experiments/telegram_stars/test_lifecycle.py
make test
make test FILE='bot/tests experiments/telegram_stars/test_lifecycle.py'
```

Evaluation results: 22 prototype tests pass; its Ruff, typos, mypy, and pyright
checks pass. The unchanged application suite has 122 passing and 13 skipped
tests. The combined run has 144 passing and 13 skipped tests. Full `make lint`
already stops at 383 unrelated Ruff findings in `bot/` on the starting commit.

No bot token, `.env`, database, or network is needed for the offline prototype
after dependencies are installed. It lives outside `bot/` and is not imported
by production. Keep it outside runtime if this design is revisited.
