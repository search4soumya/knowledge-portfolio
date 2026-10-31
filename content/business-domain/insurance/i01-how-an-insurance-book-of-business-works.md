---
id: I01
domain: insurance
category: Product and policy
title: How an insurance book of business works
slug: how-an-insurance-book-of-business-works
order: 1
---

An insurer is a factory that turns risk into contracts. It collects premium now, promises to pay claims later, and must still be solvent when later arrives. The "book of business" is the set of in-force policies plus the reserves against them. Software that treats insurance as "a checkout plus a ticket system" will miss the two objects that actually define the firm: the policy and the reserve.

## Concept

**Risk transfer.** The customer pays a premium. The insurer accepts a defined risk (a car, a life, a warehouse, a medical year) under a wording. The wording is the product. Everything else — the app, the agent portal, the claim chat — is how you sell and service that wording.

**The policy** is the in-force contract: who is covered, what is covered, for which period, at which price, with which deductibles and limits. Endorsements change it mid-term. Cancellation and reinstatement are state transitions with money attached. A quote is not a policy. A binder can be a temporary policy. Your data model must know the difference.

**The book.** New business, renewals, and mid-term changes feed the book. Lapse and cancellation shrink it. Actuaries look at the book by product, geography, channel, and year of account. If your system cannot reconstruct "what was in force on this date," you cannot price or reserve.

**Reserves and capital.** When a claim is open, you reserve. When it is incurred but not reported, you still reserve. Capital and reinsurance sit on top so a bad year does not end the company. These are not finance-only afterthoughts. They constrain how fast you can grow a new product in software.

**Lines of business** differ. Life and annuities are long duration. P&C is event-driven. Health insurance is closer to a payer (see the healthcare notes). Do not force one policy admin engine to pretend they are the same without a very good reason.

## What architects should name early

Insured, policyholder, beneficiary, and payor can be four parties. A commercial policy has locations, vehicles, or employees as risk units. A personal auto policy has drivers and vehicles. If you only have a User table, you cannot bind the contract.

Premium is earned over time. Cash received is not earned premium. That single accounting fact explains why insurance ledgers look heavy.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Policy-centric systems of record | Any real carrier | Harder consumer UX until you invest in it |
| Ticket-centric "insurtech" | A thin MGA on someone else's paper | You do not own the book; the carrier does |
| One platform for life, P&C, and health | A slide | You will rebuild the product model three times |

In a review, ask what is in force on a date, who the parties are, and where the reserve for an open claim lives. If those are three opinions, you do not have a book of business. You have apps.
