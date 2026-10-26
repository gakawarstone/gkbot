# Telegram Stars monetization evaluation

Date: 2026-10-23. Scope: GKBot at `fc19464`, aiogram 3.31.0.

## Decision

**NO-GO for production payments now.** This evaluation recommends keeping the
current product free. It does not record an owner-approved commercial launch
or a permanent rejection of monetization. No feature requires payment, the
current price is 0 Stars, and there is no paid tier or recurring charge.
Existing availability and provider limits continue to apply. Free does not
promise unlimited usage or an uptime guarantee.

The repository has no payment handlers, durable payment records, entitlement
checks, usage accounting, or payment support process. AI costs and delivered
units are not recorded, so there is no basis for pricing an allowance.
See [users](../../bot/models/users.py),
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

There is no proposed numeric paid price. Before choosing one, measure provider
costs including failures and retries, usage, hosting, support, and refund losses.
The owner must approve a price per 30 days, free and paid allowances, supported
models, request limits, and what counts as delivered usage. Expected proceeds
after the fees below must cover those costs and the owner's required margin.
Unknown costs keep this decision at no-go.

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

## Conditional design

This evaluation does not implement billing or validate production payment
behavior.

Aiogram 3.31.0 supports `Update.subscription`, successful receipts, and refunds.
Subscription states `active`, `canceled`, and `failed` describe renewal status;
they do not provide proof of new paid time.
[Subscription updates](https://core.telegram.org/bots/api#botsubscriptionupdated),
[payment receipts](https://core.telegram.org/bots/api#successfulpayment).

The following requirements cover the candidate's full lifecycle. Database
schema and processing architecture belong to a separate implementation after
product approval.

### Stored data

Persist the payer's Telegram ID, unique order payload, agreed price/allowance
and terms, charge IDs, paid periods, refunds, renewal status, and usage.
Retain the first subscription charge ID for managing renewal. Keep an audit
of administrator actions and pending refund outcomes. Billing records need
backups and a retention policy; in-memory conversation state is insufficient.
These data requirements do not prescribe separate tables or service layers.

### Purchase and access

1. Show the price, allowance, renewal and refund terms, and support contact.
   Record consent and create a user-bound order and private recurring link
   with `create_invoice_link`.
2. At pre-checkout, match payer, payload, price/currency, and agreed terms.
   Reject unavailable sales and unintended duplicate subscriptions within
   the 10-second deadline. Do not grant access at this step.
3. Match `message.successful_payment` to the order and persist its charge ID
   and supplied expiry with the resulting access change. Repeated receipts
   must not grant extra time or allowance. Renewals must work without another
   checkout. Receipts must remain recoverable across a crash or restart.
   Unexpected charges need operator review and fulfillment or refund.
4. Before any paid provider work, check the payer's non-refunded paid period
   and remaining allowance. Concurrent requests must not overspend it; failed
   or canceled work must release unused allowance. The approved product must
   define when delivery consumes units.
5. Check expiry on every paid request. Cancellation and failed renewal preserve
   already paid time. An `active` subscription event alone grants nothing.
   Use `edit_user_star_subscription` to stop renewal when requested; resuming
   renewal also requires payment before access extends. Refund and renewal
   cancellation are separate actions.

### Refunds, retries, and reconciliation

Use `refund_star_payment` for a full refund to the recorded payer, and handle
`message.refunded_payment` too. Revoke only the refunded payment's rights,
preserving other paid periods. Remember the refund even if its receipt arrives
later, so replay cannot restore access. Delivered generation cannot be
recovered; budget that loss.

Persist refund requests and confirmed outcomes. An API timeout leaves the
outcome unknown; reconcile before retrying. Bound transient retries and honor
rate-limit delays. Never create a new purchase as an automatic retry.

Regularly and after downtime, compare stored charges/refunds with
`get_star_transactions`; distinguish incoming charges from outgoing refunds
even when they share an ID. A balance alone does not establish a user's
entitlement. History may not recover the full receipt or expiry, so missing
evidence needs operator review rather than invented access dates. Pause new
sales on unresolved discrepancies while preserving verified paid access.

### Validation required for a future implementation

Test the implemented handlers and storage against the failure cases above,
including payer isolation, duplicate receipts, restart recovery, expiry,
out-of-order refunds, concurrent use, cancellation, and unknown API outcomes.
Validate payment/refund flows in Telegram's test environment before launch.
This evaluation has no billing tests or executable prototype.

## Support obligations and reopening

Before selling, provide `/paysupport`, purchase terms with recorded consent,
and a visible contact path. The operator owns disputes and timely support;
Telegram support does not resolve purchases from this bot.
[Payment support requirements](https://core.telegram.org/bots/payments-stars#going-live).

The owner must name a responsible operator and approve response times, refund
eligibility, outage handling, retention, and a reserve for refunds/chargebacks.
The operator needs to find a purchase and its paid-through date, resolve
unmatched payments, and cancel/refund with an audit trail. This does not
require a new support platform.

Reopen only after owner approval of the product, price, allowances, cost
evidence, and support policy. Verify Fragment eligibility, the actual topics
setting, and the deployed API version using the
[compatibility notes](../../services/bot-api/README.md).

Then create a separate production implementation task and PR covering this
lifecycle, storage changes, test-environment validation, and rollout/disable
procedures. Approval of this evaluation alone does not authorize billing.
