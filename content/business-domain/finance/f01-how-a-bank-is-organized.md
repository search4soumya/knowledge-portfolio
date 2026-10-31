---
id: F01
domain: finance
category: Core banking
title: How a bank is organized
slug: how-a-bank-is-organized
order: 1
---

A bank is a set of books that must balance, wrapped in licenses that say who you may take deposits from and who you may lend to. Retail, commercial, and markets look like three products. They share a customer, a ledger, a payment rail, and a regulator. If you design a "neobank app" without naming those four, you are designing a card wrapper and calling it a bank.

## Concept

**The balance sheet.** Deposits are liabilities. Loans and securities are assets. Capital is the residual. Every product you ship moves that sheet: a payment, a drawdown, a trade. Architecture that cannot post to a ledger is not banking architecture. It is a UI.

**Lines of business.** Retail: accounts, cards, consumer credit, mortgages. Commercial: cash management, trade finance, commercial loans. Markets: trading, custody, brokerage. Operations and risk sit across them. A shared customer platform is useful. A shared product engine for a checking account and a derivatives book is usually a fantasy.

**Core versus channels.** The core (or cores) hold accounts and postings. Channels (mobile, branch, open banking, corporate host-to-host) originate instructions. Channels must be idempotent clients of the core, not second ledgers. Two balances for one account is an incident, not a microservice pattern.

**Licenses and partners.** Many digital brands are not the licensed bank. They sit on a sponsor bank, a BaaS platform, or a BIN sponsor. That is a legal architecture. Your incident response, your customer complaint path, and your deposit insurance story must name the licensed entity.

## What to keep separate

Customer (party), account, product, and transaction are four objects. A household or a corporate hierarchy is a graph of parties. KYC lives on the party. Balance lives on the account. Interest lives on the product. Do not flatten them so a "user" has "a wallet."

Intraday cash and end-of-day position are different questions. Markets and payments care about intraday. The general ledger cares about the close. Both must reconcile.

## Trade-offs

| Approach | When it wins | Cost / risk |
|---|---|---|
| Licensed bank with a real core | You own the deposit | Capital, compliance, and a slow core |
| Brand on a sponsor / BaaS | Speed to a card and an account | You do not own the ledger or the license |
| One "financial OS" for all products | A slide | You will rebuild markets anyway |

In a review, ask who the licensed entity is, which system is the ledger for a retail account, and how a channel retry cannot double-post. If those answers disagree, you do not have a bank. You have apps that spend money.
