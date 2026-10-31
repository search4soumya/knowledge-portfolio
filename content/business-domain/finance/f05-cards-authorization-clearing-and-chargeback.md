---
id: F05
domain: finance
category: Payments
title: "Cards: authorization, clearing, and chargeback"
slug: cards-authorization-clearing-and-chargeback
order: 5
---

A card payment is a three-act play: authorization (may this hold money), clearing (what actually happened), and exception (chargeback, representment, retrieval). The card network, the issuer, the acquirer, and the merchant each have a role. If you only implement authorize-and-capture as two HTTP calls, you will lose the plot when a hotel pre-auth becomes three clearings and a dispute.

## Concept

**Authorization.** The merchant (via acquirer) asks the issuer: is this card open, is fraud acceptable, is available balance or credit enough? The issuer places a hold. Auths expire. Partial reverse and incremental auth exist because the final amount is not known (fuel, hotels, tips).

**Clearing and settlement.** Later, presentments arrive. They should match an auth, or they are unmatched (force post). The hold is released and a posting occurs. Settlement between issuer and acquirer is a network file and a net position, not the customer's posted transaction.

**Chargeback.** The cardholder disputes. A case opens with reason codes, deadlines, and evidence. Money may move back before you are sure. Representment is your reply. This is a legal-ish workflow with a clock. A "refund" button is a different transaction.

**BIN, scheme, and token.** The BIN tells you the product and the issuer. Network tokens and wallets (device PANs) mean the number the merchant saw is not the number on the plastic. Your authorization log must keep both.

## Design implications

Holds must hit available balance (F02) with an expiry job you trust. Stuck holds are a customer incident. Missing holds are fraud.

Match presentments to auths with scheme-defined keys, not "amount plus merchant name." Tips and split shipments will break naive matching.

3-D Secure and other SCA steps are part of the auth path in many regions. They add a challenge and a liability shift. They are not optional decoration if the scheme or the regulator requires them.

Issuer processing (your core) and network connectivity (a processor or a direct connection) are two layers. Know which one you operate.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Full auth-clearing-exception state machine | Any issuer or acquirer | Heavy, but it matches the scheme |
| Capture-only wallet | Closed loop | You are not on the card scheme |
| Processor as a black box | Speed | You cannot explain a hold or a dispute |

Follow a hotel pre-auth, a tip adjust, a clearing, and a chargeback. If your ledger only has "purchase," you are not ready for the scheme file that will arrive on Tuesday.
