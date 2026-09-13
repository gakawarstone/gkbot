# Evaluate Telegram Stars monetization

- STATUS: OPEN
- PRIORITY: 4

## Problem

Aiogram supports paid media, recurring Stars subscriptions, payment lifecycle updates, and subscription invite links. The bot has media downloads and AI generation that could be gated, but it has no payment handlers, entitlement model, pricing, or support policy. Adding isolated payment calls would create an incomplete billing flow.

## Plan

1. Decide which feature, if any, should require payment and define the free tier.
2. Compare recurring Stars subscriptions, paid media, and subscription invite links against that product model.
3. Define entitlement storage, expiry, refunds, retries, reconciliation, and administrator support.
4. Prototype the complete pre-checkout, successful payment, subscription update, and access-check flow.
5. Write a go or no-go decision before adding production payment code.

## Acceptance criteria

- The decision records pricing, gated features, Telegram fees and limits, and user support obligations.
- A chosen design covers the full payment and entitlement lifecycle.
- A no-go result leaves no partial payment code in production.
- Production implementation is tracked separately if approved.

