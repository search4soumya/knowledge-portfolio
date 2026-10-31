---
id: I06
domain: insurance
category: Distribution and capital
title: "Distribution: agents, brokers, and direct"
slug: distribution-agents-brokers-and-direct
order: 6
---

Insurance is sold as much as it is manufactured. Captive agents, independent agents, brokers, aggregators, banks, and a direct digital channel all produce the same policy object — and they all expect different tools, compensation, and ownership of the customer. A channel strategy is an architecture strategy. If you pretend every sale is a logged-in consumer, the independent agent who owns the renewal will leave.

## Concept

**Who owns the relationship.** In many markets the agent of record owns servicing and the renewal. Commissions, contingents, and bonus follow that appointment. Changing agent of record is a legal and operational event. Your policy record must store it with dates.

**Quote and bind in the channel.** An agency management system or a comparative rater will call your rating and bind APIs. Those APIs need the same product model as the direct app (I02, I04). A "partner PDF" that is retyped into PAS is how you get a book you cannot price.

**Compensation.** Commission is a financial product: rates by product and year, chargebacks on cancel, overrides for a principal. It needs a ledger, not a spreadsheet in the sales ops folder. Direct channels have acquisition cost instead; still a number you must attribute to a policy.

**Licensing and appointments.** Who is allowed to sell what, in which state, for which carrier. A bind from an unappointed producer is a compliance event. Check it at bind, not in an annual audit.

## Design implications

Identity is a party model: producer, agency, carrier user, policyholder. SSO for a large agency is a requirement. Sharing one login across a desk is how you lose accountability.

Service after bind may stay with the agent. Your customer app must not silently steal servicing if the contract says otherwise. Permissions on endorsements and claims notices follow the appointment.

Aggregators will scrape or call quotes at volume. Rate-limit, watermark, and decide whether a quote without bind is a cost you accept.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Same PAS, channel-specific experience | You sell through more than one path | You must fund producer tools |
| Direct-only | A simple branded product | Growth may stall where advice is required |
| Custom bind path per broker | A large exclusive deal | Every deal becomes a product |

Ask who is agent of record, how commission is calculated on a mid-term cancel, and whether the producer was appointed in that state at bind. If those live in email, distribution will produce a book finance cannot explain.
